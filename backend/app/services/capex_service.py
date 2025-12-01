"""
CapEx service for capital expenditure planning operations.

Handles CapEx plan management, depreciation calculation,
and multi-year CapEx planning.
"""

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.planning import CapExPlan
from app.services.base import BaseService
from app.services.exceptions import ValidationError


class CapExService:
    """
    Service for CapEx planning operations.

    Provides business logic for capital expenditure planning and depreciation.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize CapEx service.

        Args:
            session: Async database session
        """
        self.session = session
        self.capex_plan_service = BaseService(CapExPlan, session)

    async def get_capex_plan(
        self,
        version_id: uuid.UUID,
    ) -> list[CapExPlan]:
        """
        Get CapEx plan for a budget version.

        Args:
            version_id: Budget version UUID

        Returns:
            List of CapExPlan instances
        """
        return await self.capex_plan_service.get_all(
            filters={"budget_version_id": version_id}
        )

    async def get_capex_by_id(
        self,
        capex_id: uuid.UUID,
    ) -> CapExPlan:
        """
        Get CapEx entry by ID.

        Args:
            capex_id: CapEx entry UUID

        Returns:
            CapExPlan instance

        Raises:
            NotFoundError: If entry not found
        """
        return await self.capex_plan_service.get_by_id(capex_id)

    async def create_capex_entry(
        self,
        version_id: uuid.UUID,
        account_code: str,
        description: str,
        category: str,
        quantity: int,
        unit_cost_sar: Decimal,
        acquisition_date: date,
        useful_life_years: int,
        notes: str | None = None,
        user_id: uuid.UUID | None = None,
    ) -> CapExPlan:
        """
        Create CapEx plan entry.

        Args:
            version_id: Budget version UUID
            account_code: PCG account code (20xxx-21xxx)
            description: Asset description
            category: Category (equipment, IT, furniture, building, software)
            quantity: Number of units
            unit_cost_sar: Cost per unit (SAR)
            acquisition_date: Expected acquisition date
            useful_life_years: Depreciation life (years)
            notes: CapEx notes
            user_id: User ID for audit trail

        Returns:
            CapExPlan instance

        Raises:
            ValidationError: If validation fails
        """
        if not account_code.startswith(("20", "21")):
            raise ValidationError(
                f"CapEx account code must start with 20 or 21, got {account_code}",
                field="account_code",
            )

        if quantity < 1:
            raise ValidationError(
                f"Quantity must be at least 1, got {quantity}",
                field="quantity",
            )

        if useful_life_years < 1 or useful_life_years > 50:
            raise ValidationError(
                f"Useful life must be between 1 and 50 years, got {useful_life_years}",
                field="useful_life_years",
            )

        total_cost_sar = Decimal(quantity) * unit_cost_sar

        data = {
            "budget_version_id": version_id,
            "account_code": account_code,
            "description": description,
            "category": category,
            "quantity": quantity,
            "unit_cost_sar": unit_cost_sar,
            "total_cost_sar": total_cost_sar,
            "acquisition_date": acquisition_date,
            "useful_life_years": useful_life_years,
            "notes": notes,
        }

        return await self.capex_plan_service.create(data, user_id=user_id)

    async def update_capex_entry(
        self,
        capex_id: uuid.UUID,
        account_code: str | None = None,
        description: str | None = None,
        category: str | None = None,
        quantity: int | None = None,
        unit_cost_sar: Decimal | None = None,
        acquisition_date: date | None = None,
        useful_life_years: int | None = None,
        notes: str | None = None,
        user_id: uuid.UUID | None = None,
    ) -> CapExPlan:
        """
        Update CapEx plan entry.

        Args:
            capex_id: CapEx entry UUID
            account_code: PCG account code
            description: Asset description
            category: Category
            quantity: Number of units
            unit_cost_sar: Cost per unit
            acquisition_date: Acquisition date
            useful_life_years: Depreciation life
            notes: CapEx notes
            user_id: User ID for audit trail

        Returns:
            Updated CapExPlan instance

        Raises:
            NotFoundError: If entry not found
            ValidationError: If validation fails
        """
        capex = await self.get_capex_by_id(capex_id)

        update_data = {}

        if account_code is not None:
            if not account_code.startswith(("20", "21")):
                raise ValidationError(
                    f"CapEx account code must start with 20 or 21, got {account_code}",
                    field="account_code",
                )
            update_data["account_code"] = account_code

        if description is not None:
            update_data["description"] = description

        if category is not None:
            update_data["category"] = category

        if quantity is not None:
            if quantity < 1:
                raise ValidationError(
                    f"Quantity must be at least 1, got {quantity}",
                    field="quantity",
                )
            update_data["quantity"] = quantity

        if unit_cost_sar is not None:
            update_data["unit_cost_sar"] = unit_cost_sar

        if acquisition_date is not None:
            update_data["acquisition_date"] = acquisition_date

        if useful_life_years is not None:
            if useful_life_years < 1 or useful_life_years > 50:
                raise ValidationError(
                    f"Useful life must be between 1 and 50 years, got {useful_life_years}",
                    field="useful_life_years",
                )
            update_data["useful_life_years"] = useful_life_years

        if notes is not None:
            update_data["notes"] = notes

        # Recalculate total cost if quantity or unit cost changed
        final_quantity = update_data.get("quantity", capex.quantity)
        final_unit_cost = update_data.get("unit_cost_sar", capex.unit_cost_sar)
        update_data["total_cost_sar"] = Decimal(final_quantity) * final_unit_cost

        return await self.capex_plan_service.update(
            capex_id,
            update_data,
            user_id=user_id,
        )

    async def delete_capex_entry(
        self,
        capex_id: uuid.UUID,
    ) -> bool:
        """
        Delete CapEx plan entry.

        Args:
            capex_id: CapEx entry UUID

        Returns:
            True if deleted successfully

        Raises:
            NotFoundError: If entry not found
        """
        return await self.capex_plan_service.delete(capex_id)

    async def calculate_depreciation(
        self,
        capex_id: uuid.UUID,
        calculation_year: int,
    ) -> dict:
        """
        Calculate depreciation for a CapEx asset.

        Uses straight-line depreciation method:
            annual_depreciation = acquisition_cost / useful_life_years
            accumulated_depreciation = annual_depreciation × years_elapsed
            book_value = acquisition_cost - accumulated_depreciation

        Args:
            capex_id: CapEx entry UUID
            calculation_year: Year to calculate depreciation for

        Returns:
            Dictionary with depreciation details

        Raises:
            NotFoundError: If entry not found
            ValidationError: If calculation year is invalid
        """
        capex = await self.get_capex_by_id(capex_id)

        acquisition_year = capex.acquisition_date.year

        if calculation_year < acquisition_year:
            raise ValidationError(
                f"Calculation year ({calculation_year}) cannot be before acquisition year ({acquisition_year})",
                field="calculation_year",
            )

        # Calculate years elapsed since acquisition
        years_elapsed = calculation_year - acquisition_year

        # Straight-line depreciation
        annual_depreciation = capex.total_cost_sar / Decimal(capex.useful_life_years)
        annual_depreciation = annual_depreciation.quantize(Decimal("0.01"))

        # Calculate accumulated depreciation (capped at useful life)
        if years_elapsed >= capex.useful_life_years:
            accumulated_depreciation = capex.total_cost_sar
            is_fully_depreciated = True
        else:
            accumulated_depreciation = annual_depreciation * Decimal(years_elapsed)
            accumulated_depreciation = accumulated_depreciation.quantize(Decimal("0.01"))
            is_fully_depreciated = False

        # Calculate book value
        book_value = capex.total_cost_sar - accumulated_depreciation
        book_value = book_value.quantize(Decimal("0.01"))

        return {
            "asset_id": capex.id,
            "asset_description": capex.description,
            "account_code": capex.account_code,
            "category": capex.category,
            "acquisition_cost": capex.total_cost_sar,
            "acquisition_date": capex.acquisition_date,
            "useful_life_years": capex.useful_life_years,
            "annual_depreciation": annual_depreciation,
            "years_elapsed": years_elapsed,
            "accumulated_depreciation": accumulated_depreciation,
            "book_value": book_value,
            "calculation_year": calculation_year,
            "is_fully_depreciated": is_fully_depreciated,
        }

    async def get_depreciation_schedule(
        self,
        capex_id: uuid.UUID,
        years_ahead: int = 10,
    ) -> list[dict]:
        """
        Get multi-year depreciation schedule for an asset.

        Args:
            capex_id: CapEx entry UUID
            years_ahead: Number of years to project

        Returns:
            List of depreciation calculations by year

        Raises:
            NotFoundError: If entry not found
        """
        capex = await self.get_capex_by_id(capex_id)

        acquisition_year = capex.acquisition_date.year
        schedule = []

        for year_offset in range(years_ahead + 1):
            calculation_year = acquisition_year + year_offset

            # Stop if beyond useful life
            if year_offset > capex.useful_life_years:
                break

            depreciation = await self.calculate_depreciation(capex_id, calculation_year)
            schedule.append(depreciation)

        return schedule

    async def get_capex_summary(
        self,
        version_id: uuid.UUID,
    ) -> dict:
        """
        Get CapEx summary for a budget version.

        Args:
            version_id: Budget version UUID

        Returns:
            Dictionary with CapEx summary statistics
        """
        capex_plans = await self.get_capex_plan(version_id)

        total_capex = Decimal("0")
        capex_by_category = {}
        capex_by_account = {}

        for plan in capex_plans:
            total_capex += plan.total_cost_sar

            # By category
            if plan.category not in capex_by_category:
                capex_by_category[plan.category] = {
                    "total_cost": Decimal("0"),
                    "item_count": 0,
                }
            capex_by_category[plan.category]["total_cost"] += plan.total_cost_sar
            capex_by_category[plan.category]["item_count"] += 1

            # By account
            if plan.account_code not in capex_by_account:
                capex_by_account[plan.account_code] = Decimal("0")
            capex_by_account[plan.account_code] += plan.total_cost_sar

        return {
            "total_capex": total_capex,
            "capex_by_category": capex_by_category,
            "capex_by_account": capex_by_account,
            "item_count": len(capex_plans),
        }

    async def get_annual_depreciation(
        self,
        version_id: uuid.UUID,
        calculation_year: int,
    ) -> dict:
        """
        Calculate total annual depreciation for all assets in a version.

        Args:
            version_id: Budget version UUID
            calculation_year: Year to calculate depreciation for

        Returns:
            Dictionary with annual depreciation totals
        """
        capex_plans = await self.get_capex_plan(version_id)

        total_depreciation = Decimal("0")
        depreciation_by_category = {}

        for plan in capex_plans:
            # Only calculate if asset has been acquired by calculation year
            if plan.acquisition_date.year <= calculation_year:
                depreciation = await self.calculate_depreciation(plan.id, calculation_year)

                total_depreciation += depreciation["annual_depreciation"]

                # By category
                if plan.category not in depreciation_by_category:
                    depreciation_by_category[plan.category] = Decimal("0")
                depreciation_by_category[plan.category] += depreciation["annual_depreciation"]

        return {
            "calculation_year": calculation_year,
            "total_annual_depreciation": total_depreciation,
            "depreciation_by_category": depreciation_by_category,
        }
