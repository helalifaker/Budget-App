"""
Admin API endpoints.

Provides REST API for administrative operations:
- Historical data import
- Template downloads
- System configuration
"""

import io
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import UserDep
from app.services.historical_import_service import (
    HistoricalImportService,
    ImportModule,
    ImportPreviewResult,
    ImportResult,
    generate_template,
)

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


def get_import_service(db: AsyncSession = Depends(get_db)) -> HistoricalImportService:
    """
    Dependency to get historical import service instance.

    Args:
        db: Database session

    Returns:
        HistoricalImportService instance
    """
    return HistoricalImportService(db)


# ==============================================================================
# Historical Import Endpoints
# ==============================================================================


class ImportHistoryItem(BaseModel):
    """Import history item."""

    fiscal_year: int
    module: str
    record_count: int
    last_imported: str | None


@router.post(
    "/historical/preview",
    response_model=ImportPreviewResult,
)
async def preview_historical_import(
    file: Annotated[UploadFile, File(description="Excel or CSV file to import")],
    fiscal_year: Annotated[int, Form(description="Target fiscal year")],
    module: Annotated[str | None, Form(description="Module filter")] = None,
    import_service: HistoricalImportService = Depends(get_import_service),
    user: UserDep = ...,
):
    """
    Preview historical data import without saving.

    Upload an Excel (.xlsx) or CSV file to preview the import. Returns
    validation results and record counts without actually importing.

    Args:
        file: Excel or CSV file
        fiscal_year: Target fiscal year for the data
        module: Optional module filter (enrollment, dhg, revenue, costs, capex)
        import_service: Import service
        user: Current authenticated user

    Returns:
        ImportPreviewResult with validation details
    """
    # Validate file type
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided",
        )

    if not file.filename.endswith((".xlsx", ".xls", ".csv")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Use .xlsx or .csv",
        )

    # Read file content
    content = await file.read()

    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty file",
        )

    # Parse module if provided
    import_module: ImportModule | None = None
    if module:
        try:
            import_module = ImportModule(module.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid module: {module}. Use: enrollment, dhg, revenue, costs, capex",
            )

    # Preview import
    try:
        result = await import_service.preview_import(
            file_content=content,
            filename=file.filename,
            fiscal_year=fiscal_year,
            module=import_module,
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing file: {e!s}",
        )


@router.post(
    "/historical/import",
    response_model=ImportResult,
)
async def import_historical_data(
    file: Annotated[UploadFile, File(description="Excel or CSV file to import")],
    fiscal_year: Annotated[int, Form(description="Target fiscal year")],
    module: Annotated[str | None, Form(description="Module filter")] = None,
    overwrite: Annotated[bool, Form(description="Overwrite existing data")] = False,
    import_service: HistoricalImportService = Depends(get_import_service),
    user: UserDep = ...,
):
    """
    Import historical actuals from Excel/CSV file.

    Upload an Excel (.xlsx) or CSV file to import historical data.
    Use the preview endpoint first to validate data before importing.

    Args:
        file: Excel or CSV file
        fiscal_year: Target fiscal year for the data
        module: Optional module filter (enrollment, dhg, revenue, costs, capex)
        overwrite: Whether to replace existing data for this year/module
        import_service: Import service
        user: Current authenticated user

    Returns:
        ImportResult with import status

    Example:
        POST /api/v1/admin/historical/import
        Content-Type: multipart/form-data

        file: (binary)
        fiscal_year: 2024
        module: enrollment
        overwrite: false
    """
    # Validate file type
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided",
        )

    if not file.filename.endswith((".xlsx", ".xls", ".csv")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Use .xlsx or .csv",
        )

    # Read file content
    content = await file.read()

    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty file",
        )

    # Parse module if provided
    import_module: ImportModule | None = None
    if module:
        try:
            import_module = ImportModule(module.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid module: {module}. Use: enrollment, dhg, revenue, costs, capex",
            )

    # Import data
    try:
        result = await import_service.import_data(
            file_content=content,
            filename=file.filename,
            fiscal_year=fiscal_year,
            module=import_module,
            overwrite=overwrite,
            user_id=user.user_id,
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error importing file: {e!s}",
        )


@router.get(
    "/historical/history",
    response_model=list[ImportHistoryItem],
)
async def get_import_history(
    fiscal_year: Annotated[int | None, Query(description="Filter by fiscal year")] = None,
    module: Annotated[str | None, Query(description="Filter by module")] = None,
    limit: Annotated[int, Query(description="Max records", ge=1, le=100)] = 50,
    import_service: HistoricalImportService = Depends(get_import_service),
    user: UserDep = ...,
):
    """
    Get history of imported historical data.

    Returns summary of what historical data has been imported,
    grouped by fiscal year and module.

    Args:
        fiscal_year: Optional filter by year
        module: Optional filter by module
        limit: Maximum records to return (1-100)
        import_service: Import service
        user: Current authenticated user

    Returns:
        List of ImportHistoryItem summaries
    """
    # Parse module if provided
    import_module: ImportModule | None = None
    if module:
        try:
            import_module = ImportModule(module.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid module: {module}",
            )

    history = await import_service.get_import_history(
        fiscal_year=fiscal_year,
        module=import_module,
        limit=limit,
    )

    return [ImportHistoryItem(**item) for item in history]


@router.get(
    "/historical/template/{module}",
    responses={
        200: {
            "content": {
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {}
            },
            "description": "Excel template file",
        }
    },
)
async def download_template(
    module: str,
    user: UserDep = ...,
):
    """
    Download Excel template for a module.

    Args:
        module: Module type (enrollment, dhg, revenue, costs, capex)
        user: Current authenticated user

    Returns:
        Excel file download
    """
    try:
        import_module = ImportModule(module.lower())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid module: {module}. Use: enrollment, dhg, revenue, costs, capex",
        )

    # Generate template
    template_bytes = generate_template(import_module)

    # Return as file download
    filename = f"historical_{module}_template.xlsx"

    return StreamingResponse(
        io.BytesIO(template_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.delete(
    "/historical/{fiscal_year}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_historical_data(
    fiscal_year: int,
    module: Annotated[str | None, Query(description="Module filter")] = None,
    import_service: HistoricalImportService = Depends(get_import_service),
    user: UserDep = ...,
):
    """
    Delete historical data for a fiscal year.

    Args:
        fiscal_year: Fiscal year to delete
        module: Optional module filter
        import_service: Import service
        user: Current authenticated user
    """
    import_module: ImportModule | None = None
    if module:
        try:
            import_module = ImportModule(module.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid module: {module}",
            )

    await import_service._delete_existing(fiscal_year, import_module)
    await import_service.session.commit()

    return None
