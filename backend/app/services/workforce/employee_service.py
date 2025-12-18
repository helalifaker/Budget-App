"""
Employee Service for workforce management.

Handles employee CRUD operations with:
- Auto-generation of employee codes (EMP001, EMP002, etc.)
- Budget version scoping
- Base 100 vs Planned (placeholder) distinction
- Salary management with GOSI calculations
- EOS provision tracking
"""

import uuid
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.engine.workforce.eos import EOSProvisionInput, calculate_eos_provision
from app.engine.workforce.gosi import GOSIInput, Nationality, calculate_gosi
from app.models import (
    AEFEPosition,
    Employee,
    EmployeeCategory,
    EmployeeNationality,
    EmployeeSalary,
    EOSProvision,
)
from app.services.base import BaseService
from app.services.exceptions import ValidationError


class EmployeeService(BaseService[Employee]):
    """
    Service for managing employees.

    Provides:
    - CRUD operations with employee code auto-generation
    - Filtering by budget version, category, status
    - Salary management with GOSI calculations
    - EOS provision calculations
    - Placeholder employee creation from DHG gap
    """

    def __init__(self, session: AsyncSession):
        """Initialize employee service."""
        super().__init__(Employee, session)

    async def _generate_employee_code(self, version_id: uuid.UUID) -> str:
        """
        Generate next employee code for budget version.

        Format: EMP001, EMP002, etc.

        Args:
            version_id: Budget version UUID

        Returns:
            Next available employee code
        """
        # Find highest existing code number for this version
        query = (
            select(Employee.employee_code)
            .where(Employee.version_id == version_id)
            .where(Employee.deleted_at.is_(None))
            .where(Employee.employee_code.like("EMP%"))
        )
        result = await self.session.execute(query)
        codes = [row[0] for row in result.fetchall()]

        if not codes:
            return "EMP001"

        # Extract numbers and find max
        numbers = []
        for code in codes:
            try:
                num = int(code[3:])
                numbers.append(num)
            except ValueError:
                continue

        next_num = max(numbers) + 1 if numbers else 1
        return f"EMP{next_num:03d}"

    async def get_by_version(
        self,
        version_id: uuid.UUID,
        include_inactive: bool = False,
        category: EmployeeCategory | None = None,
        is_placeholder: bool | None = None,
    ) -> list[Employee]:
        """
        Get all employees for a budget version.

        Args:
            version_id: Budget version UUID
            include_inactive: Include inactive employees
            category: Filter by category
            is_placeholder: Filter by placeholder status

        Returns:
            List of employees
        """
        query = (
            select(Employee)
            .where(Employee.version_id == version_id)
            .where(Employee.deleted_at.is_(None))
        )

        if not include_inactive:
            query = query.where(Employee.is_active.is_(True))

        if category:
            query = query.where(Employee.category == category)

        if is_placeholder is not None:
            query = query.where(Employee.is_placeholder == is_placeholder)

        query = query.order_by(Employee.employee_code)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create_employee(
        self,
        version_id: uuid.UUID,
        data: dict[str, Any],
        user_id: uuid.UUID | None = None,
    ) -> Employee:
        """
        Create a new employee with auto-generated code.

        Args:
            version_id: Budget version UUID
            data: Employee data
            user_id: User ID for audit trail

        Returns:
            Created employee
        """
        # Generate employee code
        employee_code = await self._generate_employee_code(version_id)

        # Prepare data
        employee_data = {
            **data,
            "version_id": version_id,
            "employee_code": employee_code,
        }

        return await self.create(employee_data, user_id)

    async def create_placeholder(
        self,
        version_id: uuid.UUID,
        category: EmployeeCategory,
        cycle_id: uuid.UUID | None = None,
        subject_id: uuid.UUID | None = None,
        fte: Decimal = Decimal("1.00"),
        estimated_salary_sar: Decimal | None = None,
        notes: str | None = None,
        user_id: uuid.UUID | None = None,
    ) -> Employee:
        """
        Create a placeholder employee from DHG gap analysis.

        Placeholders are marked with is_placeholder=True and use
        placeholder names until validated.

        Args:
            version_id: Budget version UUID
            category: Employee category
            cycle_id: Academic cycle
            subject_id: Subject
            fte: FTE requirement
            estimated_salary_sar: Estimated salary
            notes: Notes (e.g., from DHG gap)
            user_id: User ID for audit trail

        Returns:
            Created placeholder employee
        """
        # Generate placeholder name based on category
        placeholder_name = f"Placeholder - {category.value.replace('_', ' ').title()}"

        data = {
            "full_name": placeholder_name,
            "nationality": EmployeeNationality.EXPATRIATE,  # Default
            "category": category,
            "hire_date": date.today(),  # Placeholder date
            "cycle_id": cycle_id,
            "subject_id": subject_id,
            "fte": fte,
            "is_placeholder": True,
            "is_active": True,
            "notes": notes or "Created from DHG gap analysis - pending validation",
        }

        employee = await self.create_employee(version_id, data, user_id)

        # Create estimated salary if provided
        if estimated_salary_sar:
            await self.add_salary(
                employee_id=employee.id,
                version_id=version_id,
                basic_salary_sar=estimated_salary_sar * Decimal("0.50"),  # 50% basic
                housing_allowance_sar=estimated_salary_sar * Decimal("0.25"),  # 25%
                transport_allowance_sar=estimated_salary_sar * Decimal("0.10"),  # 10%
                other_allowances_sar=estimated_salary_sar * Decimal("0.15"),  # 15%
                effective_from=date.today(),
                user_id=user_id,
            )

        return employee

    async def validate_placeholder(
        self,
        employee_id: uuid.UUID,
        full_name: str,
        nationality: EmployeeNationality,
        hire_date: date,
        additional_data: dict[str, Any] | None = None,
        user_id: uuid.UUID | None = None,
    ) -> Employee:
        """
        Validate a placeholder employee, converting to Base 100.

        Args:
            employee_id: Employee UUID
            full_name: Actual name
            nationality: Nationality
            hire_date: Actual hire date
            additional_data: Additional fields to update
            user_id: User ID for audit trail

        Returns:
            Updated employee
        """
        employee = await self.get_by_id(employee_id)

        if not employee.is_placeholder:
            raise ValidationError("Employee is not a placeholder")

        update_data = {
            "full_name": full_name,
            "nationality": nationality,
            "hire_date": hire_date,
            "is_placeholder": False,
            **(additional_data or {}),
        }

        return await self.update(employee_id, update_data, user_id)

    async def add_salary(
        self,
        employee_id: uuid.UUID,
        version_id: uuid.UUID,
        basic_salary_sar: Decimal,
        housing_allowance_sar: Decimal,
        transport_allowance_sar: Decimal,
        other_allowances_sar: Decimal,
        effective_from: date,
        effective_to: date | None = None,
        user_id: uuid.UUID | None = None,
    ) -> EmployeeSalary:
        """
        Add salary record for employee with GOSI calculations.

        Args:
            employee_id: Employee UUID
            version_id: Budget version UUID
            basic_salary_sar: Basic salary
            housing_allowance_sar: Housing allowance
            transport_allowance_sar: Transport allowance
            other_allowances_sar: Other allowances
            effective_from: Effective from date
            effective_to: Effective to date
            user_id: User ID for audit trail

        Returns:
            Created salary record
        """
        # Get employee to determine nationality
        employee = await self.get_by_id(employee_id)

        # Calculate gross salary
        gross_salary = (
            basic_salary_sar
            + housing_allowance_sar
            + transport_allowance_sar
            + other_allowances_sar
        )

        # Convert nationality for GOSI calculation
        gosi_nationality = (
            Nationality.SAUDI
            if employee.nationality == EmployeeNationality.SAUDI
            else Nationality.EXPATRIATE
        )

        # Calculate GOSI
        gosi_result = calculate_gosi(
            GOSIInput(
                gross_salary_sar=gross_salary,
                nationality=gosi_nationality,
            )
        )

        # Close previous salary if exists
        await self._close_previous_salary(employee_id, effective_from)

        # Create salary record
        salary = EmployeeSalary(
            version_id=version_id,
            employee_id=employee_id,
            effective_from=effective_from,
            effective_to=effective_to,
            basic_salary_sar=basic_salary_sar,
            housing_allowance_sar=housing_allowance_sar,
            transport_allowance_sar=transport_allowance_sar,
            other_allowances_sar=other_allowances_sar,
            gross_salary_sar=gross_salary,
            gosi_employer_rate=gosi_result.employer_rate,
            gosi_employee_rate=gosi_result.employee_rate,
            gosi_employer_sar=gosi_result.employer_contribution_sar,
            gosi_employee_sar=gosi_result.employee_contribution_sar,
        )

        if user_id:
            salary.created_by_id = user_id
            salary.updated_by_id = user_id

        self.session.add(salary)
        await self.session.flush()

        return salary

    async def _close_previous_salary(
        self,
        employee_id: uuid.UUID,
        effective_from: date,
    ) -> None:
        """Close previous open salary record."""
        query = (
            select(EmployeeSalary)
            .where(EmployeeSalary.employee_id == employee_id)
            .where(EmployeeSalary.effective_to.is_(None))
            .where(EmployeeSalary.deleted_at.is_(None))
        )
        result = await self.session.execute(query)
        previous = result.scalar_one_or_none()

        if previous and previous.effective_from < effective_from:
            previous.effective_to = effective_from
            await self.session.flush()

    async def get_current_salary(
        self,
        employee_id: uuid.UUID,
    ) -> EmployeeSalary | None:
        """
        Get current active salary for employee.

        Args:
            employee_id: Employee UUID

        Returns:
            Current salary or None
        """
        query = (
            select(EmployeeSalary)
            .where(EmployeeSalary.employee_id == employee_id)
            .where(EmployeeSalary.effective_to.is_(None))
            .where(EmployeeSalary.deleted_at.is_(None))
            .order_by(EmployeeSalary.effective_from.desc())
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def calculate_eos_provision(
        self,
        employee_id: uuid.UUID,
        version_id: uuid.UUID,
        as_of_date: date | None = None,
        user_id: uuid.UUID | None = None,
    ) -> EOSProvision:
        """
        Calculate and store EOS provision for employee.

        Args:
            employee_id: Employee UUID
            version_id: Budget version UUID
            as_of_date: Date for calculation (defaults to today)
            user_id: User ID for audit trail

        Returns:
            Created EOS provision record
        """
        as_of_date = as_of_date or date.today()

        # Get employee
        employee = await self.get_by_id(employee_id)

        # Skip AEFE employees (not applicable)
        if employee.category in (
            EmployeeCategory.AEFE_DETACHED,
            EmployeeCategory.AEFE_FUNDED,
        ):
            raise ValidationError("EOS is not applicable for AEFE employees")

        # Get current salary
        salary = await self.get_current_salary(employee_id)
        if not salary:
            raise ValidationError(f"No salary found for employee {employee.employee_code}")

        # Calculate provision
        provision_result = calculate_eos_provision(
            EOSProvisionInput(
                hire_date=employee.hire_date,
                as_of_date=as_of_date,
                basic_salary_sar=salary.basic_salary_sar,
            )
        )

        # Create provision record
        provision = EOSProvision(
            version_id=version_id,
            employee_id=employee_id,
            as_of_date=as_of_date,
            years_of_service=provision_result.years_of_service,
            months_of_service=provision_result.months_of_service,
            base_salary_sar=salary.basic_salary_sar,
            years_1_to_5_amount_sar=provision_result.years_1_to_5_amount_sar,
            years_6_plus_amount_sar=provision_result.years_6_plus_amount_sar,
            provision_amount_sar=provision_result.provision_amount_sar,
        )

        if user_id:
            provision.created_by_id = user_id
            provision.updated_by_id = user_id

        self.session.add(provision)
        await self.session.flush()

        return provision

    async def get_salary_history(
        self,
        employee_id: uuid.UUID,
    ) -> list[EmployeeSalary]:
        """
        Get all salary records for employee ordered by effective date.

        Args:
            employee_id: Employee UUID

        Returns:
            List of salary records ordered by effective_from (descending)
        """
        query = (
            select(EmployeeSalary)
            .where(EmployeeSalary.employee_id == employee_id)
            .where(EmployeeSalary.deleted_at.is_(None))
            .order_by(EmployeeSalary.effective_from.desc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_eos_provision(
        self,
        employee_id: uuid.UUID,
    ) -> EOSProvision | None:
        """
        Get most recent EOS provision for employee.

        Args:
            employee_id: Employee UUID

        Returns:
            Most recent EOS provision or None
        """
        query = (
            select(EOSProvision)
            .where(EOSProvision.employee_id == employee_id)
            .where(EOSProvision.deleted_at.is_(None))
            .order_by(EOSProvision.as_of_date.desc())
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def calculate_all_eos(
        self,
        version_id: uuid.UUID,
        as_of_date: date,
        user_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        """
        Calculate EOS provision for all eligible employees.

        Excludes AEFE employees (Detached and Funded).

        Args:
            version_id: Budget version UUID
            as_of_date: Date for calculation
            user_id: User ID for audit trail

        Returns:
            Dictionary with calculated_count and total_provision_sar
        """
        employees = await self.get_by_version(version_id)
        calculated = 0
        total = Decimal("0.00")

        for emp in employees:
            # Skip AEFE employees - not eligible for EOS
            if emp.category in (
                EmployeeCategory.AEFE_DETACHED,
                EmployeeCategory.AEFE_FUNDED,
            ):
                continue

            try:
                provision = await self.calculate_eos_provision(
                    employee_id=emp.id,
                    version_id=version_id,
                    as_of_date=as_of_date,
                    user_id=user_id,
                )
                total += provision.provision_amount_sar
                calculated += 1
            except ValidationError:
                # Skip employees without salary
                continue

        return {
            "calculated_count": calculated,
            "total_provision_sar": total,
        }

    async def get_eos_summary(
        self,
        version_id: uuid.UUID,
        as_of_date: date | None = None,
    ) -> dict[str, Any]:
        """
        Get EOS summary statistics for a budget version.

        Args:
            version_id: Budget version UUID
            as_of_date: Filter by as_of_date (optional)

        Returns:
            Summary dictionary
        """
        query = (
            select(EOSProvision)
            .where(EOSProvision.version_id == version_id)
            .where(EOSProvision.deleted_at.is_(None))
        )
        if as_of_date:
            query = query.where(EOSProvision.as_of_date <= as_of_date)

        result = await self.session.execute(query)
        provisions = list(result.scalars().all())

        total_provision = sum(
            (p.provision_amount_sar for p in provisions),
            Decimal("0.00"),
        )

        return {
            "version_id": str(version_id),
            "employee_count": len(provisions),
            "total_provision_sar": total_provision,
            "as_of_date": str(as_of_date) if as_of_date else None,
        }

    async def get_workforce_summary(
        self,
        version_id: uuid.UUID,
    ) -> dict[str, Any]:
        """
        Get workforce summary statistics.

        Args:
            version_id: Budget version UUID

        Returns:
            Summary dictionary with counts and totals
        """
        employees = await self.get_by_version(
            version_id,
            include_inactive=False,
        )

        # Calculate counts
        by_category: dict[str, int] = {}
        by_nationality: dict[str, int] = {}
        base_100_count = 0
        planned_count = 0
        total_fte = Decimal("0.00")

        for emp in employees:
            # Category counts
            cat_key = emp.category.value
            by_category[cat_key] = by_category.get(cat_key, 0) + 1

            # Nationality counts
            nat_key = emp.nationality.value
            by_nationality[nat_key] = by_nationality.get(nat_key, 0) + 1

            # Base 100 vs Planned
            if emp.is_placeholder:
                planned_count += 1
            else:
                base_100_count += 1

            # FTE
            total_fte += emp.fte

        # Get AEFE position counts
        aefe_query = (
            select(AEFEPosition)
            .where(AEFEPosition.version_id == version_id)
            .where(AEFEPosition.deleted_at.is_(None))
        )
        aefe_result = await self.session.execute(aefe_query)
        aefe_positions = list(aefe_result.scalars().all())

        filled = sum(1 for p in aefe_positions if p.is_filled)
        vacant = len(aefe_positions) - filled

        # Get payroll totals (for local employees only)
        total_monthly_payroll = Decimal("0.00")
        total_gosi_employer = Decimal("0.00")

        for emp in employees:
            if emp.category not in (
                EmployeeCategory.AEFE_DETACHED,
                EmployeeCategory.AEFE_FUNDED,
            ):
                salary = await self.get_current_salary(emp.id)
                if salary:
                    total_monthly_payroll += salary.gross_salary_sar
                    total_gosi_employer += salary.gosi_employer_sar

        # Get total EOS provision
        eos_query = (
            select(func.sum(EOSProvision.provision_amount_sar))
            .where(EOSProvision.version_id == version_id)
            .where(EOSProvision.deleted_at.is_(None))
        )
        eos_result = await self.session.execute(eos_query)
        total_eos = eos_result.scalar_one() or Decimal("0.00")

        return {
            "version_id": version_id,
            "total_employees": len(employees),
            "active_employees": len(employees),
            "base_100_count": base_100_count,
            "planned_count": planned_count,
            "by_category": by_category,
            "by_nationality": by_nationality,
            "total_fte": total_fte,
            "aefe_positions_filled": filled,
            "aefe_positions_vacant": vacant,
            "total_monthly_payroll_sar": total_monthly_payroll,
            "total_gosi_employer_sar": total_gosi_employer,
            "total_eos_provision_sar": total_eos,
        }
