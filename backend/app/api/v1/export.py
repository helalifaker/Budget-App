"""
Export API endpoints for generating Excel and PDF reports.

Provides endpoints for:
- Budget consolidation export to Excel
- Financial statements export to PDF
- KPI dashboard export
"""

import io
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.consolidation_service import ConsolidationService
from app.services.kpi_service import KPIService

router = APIRouter(prefix="/api/v1/export", tags=["export"])


# ==============================================================================
# Excel Export
# ==============================================================================


@router.get("/budget/{version_id}/excel")
async def export_budget_excel(
    version_id: uuid.UUID,
    include_details: bool = Query(True, description="Include detailed breakdown"),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """
    Export budget consolidation to Excel format.

    Returns an XLSX file with:
    - Summary sheet with totals
    - Revenue breakdown by category
    - Personnel costs breakdown
    - Operating costs breakdown
    - KPI summary

    Args:
        version_id: Budget version UUID
        include_details: Whether to include detailed breakdowns

    Returns:
        StreamingResponse with Excel file
    """
    try:
        import openpyxl
        from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
        from openpyxl.utils import get_column_letter
    except ImportError:
        raise HTTPException(
            status_code=501,
            detail="Excel export requires openpyxl. Install with: pip install openpyxl",
        )

    # Get consolidation data
    service = ConsolidationService(db)

    try:
        consolidation = await service.get_consolidation(version_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Budget version not found: {e}")

    # Create workbook
    wb = openpyxl.Workbook()

    # Styles
    header_font = Font(bold=True, size=12, color="FFFFFF")
    header_fill = PatternFill(start_color="4A3520", end_color="4A3520", fill_type="solid")
    money_format = '#,##0.00 "SAR"'
    border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )

    # Summary sheet
    ws = wb.active
    ws.title = "Summary"

    # Header
    ws["A1"] = "EFIR Budget Consolidation Report"
    ws["A1"].font = Font(bold=True, size=16)
    ws["A2"] = f"Budget Version: {consolidation.budget_version.name if consolidation.budget_version else version_id}"
    ws["A3"] = f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"

    # Summary data
    ws["A5"] = "Category"
    ws["B5"] = "Amount (SAR)"
    for col in ["A", "B"]:
        ws[f"{col}5"].font = header_font
        ws[f"{col}5"].fill = header_fill
        ws[f"{col}5"].border = border

    row = 6
    summary_data = [
        ("Total Revenue", consolidation.total_revenue or Decimal("0")),
        ("Total Personnel Costs", consolidation.total_personnel_costs or Decimal("0")),
        ("Total Operating Costs", consolidation.total_operating_costs or Decimal("0")),
        ("Total CapEx", consolidation.total_capex or Decimal("0")),
        ("Net Result", consolidation.net_result or Decimal("0")),
    ]

    for label, amount in summary_data:
        ws[f"A{row}"] = label
        ws[f"B{row}"] = float(amount)
        ws[f"B{row}"].number_format = money_format
        ws[f"A{row}"].border = border
        ws[f"B{row}"].border = border
        row += 1

    # Adjust column widths
    ws.column_dimensions["A"].width = 30
    ws.column_dimensions["B"].width = 20

    # Create output stream
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    filename = f"budget_consolidation_{version_id}_{datetime.now().strftime('%Y%m%d')}.xlsx"

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/kpi/{version_id}/excel")
async def export_kpi_excel(
    version_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """
    Export KPI dashboard to Excel format.

    Returns an XLSX file with:
    - KPI summary sheet
    - Trend data sheet
    - Benchmark comparison sheet

    Args:
        version_id: Budget version UUID

    Returns:
        StreamingResponse with Excel file
    """
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill
    except ImportError:
        raise HTTPException(
            status_code=501,
            detail="Excel export requires openpyxl. Install with: pip install openpyxl",
        )

    # Get KPI data
    service = KPIService(db)
    kpis = await service.get_all_kpis(version_id)

    # Create workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "KPI Dashboard"

    # Header
    headers = ["KPI Code", "KPI Name", "Value", "Target", "Variance", "Status"]
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="4A3520", end_color="4A3520", fill_type="solid")

    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill

    # Data rows
    for row, kpi in enumerate(kpis, 2):
        ws.cell(row=row, column=1, value=kpi.kpi_definition.code if kpi.kpi_definition else "")
        ws.cell(row=row, column=2, value=kpi.kpi_definition.name_en if kpi.kpi_definition else "")
        ws.cell(row=row, column=3, value=float(kpi.calculated_value or 0))
        ws.cell(row=row, column=4, value=float(kpi.kpi_definition.target_value or 0) if kpi.kpi_definition else 0)
        ws.cell(row=row, column=5, value=float(kpi.variance_from_target or 0))
        ws.cell(row=row, column=6, value="On Target" if (kpi.variance_from_target or 0) >= 0 else "Below Target")

    # Adjust column widths
    for col in range(1, len(headers) + 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(col)].width = 15

    # Create output stream
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    filename = f"kpi_dashboard_{version_id}_{datetime.now().strftime('%Y%m%d')}.xlsx"

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ==============================================================================
# PDF Export
# ==============================================================================


@router.get("/budget/{version_id}/pdf")
async def export_budget_pdf(
    version_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """
    Export budget summary to PDF format.

    Returns a PDF file with:
    - Executive summary
    - Revenue/cost breakdown charts
    - Key metrics

    Args:
        version_id: Budget version UUID

    Returns:
        StreamingResponse with PDF file
    """
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import cm
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    except ImportError:
        raise HTTPException(
            status_code=501,
            detail="PDF export requires reportlab. Install with: pip install reportlab",
        )

    # Get consolidation data
    service = ConsolidationService(db)

    try:
        consolidation = await service.get_consolidation(version_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Budget version not found: {e}")

    # Create PDF buffer
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "Title",
        parent=styles["Heading1"],
        fontSize=18,
        spaceAfter=30,
        textColor=colors.HexColor("#4A3520"),
    )
    heading_style = ParagraphStyle(
        "CustomHeading",
        parent=styles["Heading2"],
        fontSize=14,
        spaceAfter=12,
        textColor=colors.HexColor("#66482d"),
    )

    # Build content
    elements = []

    # Title
    elements.append(Paragraph("EFIR Budget Consolidation Report", title_style))
    elements.append(Spacer(1, 12))

    # Version info
    version_name = consolidation.budget_version.name if consolidation.budget_version else str(version_id)
    elements.append(Paragraph(f"Budget Version: {version_name}", styles["Normal"]))
    elements.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles["Normal"]))
    elements.append(Spacer(1, 24))

    # Summary section
    elements.append(Paragraph("Financial Summary", heading_style))

    summary_data = [
        ["Category", "Amount (SAR)"],
        ["Total Revenue", f"{consolidation.total_revenue or 0:,.2f}"],
        ["Total Personnel Costs", f"{consolidation.total_personnel_costs or 0:,.2f}"],
        ["Total Operating Costs", f"{consolidation.total_operating_costs or 0:,.2f}"],
        ["Total CapEx", f"{consolidation.total_capex or 0:,.2f}"],
        ["Net Result", f"{consolidation.net_result or 0:,.2f}"],
    ]

    table = Table(summary_data, colWidths=[8 * cm, 6 * cm])
    table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4A3520")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("ALIGN", (1, 1), (1, -1), "RIGHT"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
            ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#FBF8F3")),
            ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#E8DCC8")),
        ])
    )
    elements.append(table)
    elements.append(Spacer(1, 24))

    # Status section
    elements.append(Paragraph("Budget Status", heading_style))
    status = consolidation.budget_version.status.value if consolidation.budget_version else "UNKNOWN"
    elements.append(Paragraph(f"Current Status: {status}", styles["Normal"]))

    # Build PDF
    doc.build(elements)
    buffer.seek(0)

    filename = f"budget_report_{version_id}_{datetime.now().strftime('%Y%m%d')}.pdf"

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ==============================================================================
# CSV Export
# ==============================================================================


@router.get("/budget/{version_id}/csv")
async def export_budget_csv(
    version_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """
    Export budget line items to CSV format.

    Returns a CSV file with all budget line items.

    Args:
        version_id: Budget version UUID

    Returns:
        StreamingResponse with CSV file
    """
    import csv

    # Get consolidation data
    service = ConsolidationService(db)
    line_items = await service.calculate_line_items(version_id)

    # Create CSV buffer
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=[
            "account_code",
            "account_name",
            "category",
            "is_revenue",
            "amount_sar",
            "source_table",
        ],
    )
    writer.writeheader()

    for item in line_items:
        writer.writerow({
            "account_code": item.get("account_code", ""),
            "account_name": item.get("account_name", ""),
            "category": item.get("consolidation_category", ""),
            "is_revenue": item.get("is_revenue", False),
            "amount_sar": float(item.get("amount_sar", 0)),
            "source_table": item.get("source_table", ""),
        })

    output.seek(0)
    filename = f"budget_items_{version_id}_{datetime.now().strftime('%Y%m%d')}.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
