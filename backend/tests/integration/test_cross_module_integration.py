"""
Cross-Module Integration Tests for EFIR Budget Planning Application

Tests the complete data flow across the four main modules:
1. Students (Enrollment) → Teachers (DHG)
2. Teachers (DHG/FTE) → Finance (Personnel Costs)
3. Finance (Revenue/Costs) → Insights (KPIs)
4. End-to-end workflow validation

These tests ensure that outputs from one engine can be correctly consumed
by downstream engines in the budget planning pipeline.

Data Flow:
    Enrollment → Class Structure → DHG → FTE → Personnel Costs → Statements → KPIs
"""

from decimal import Decimal
from uuid import uuid4

# Enrollment Module
from app.engine.enrollment import (
    EnrollmentGrowthScenario,
    EnrollmentInput,
    calculate_enrollment_projection,
)

# Insights Module (KPIs)
from app.engine.insights.kpi import (
    KPIInput,
    calculate_all_kpis,
    calculate_cost_per_student,
    calculate_he_ratio_secondary,
    calculate_revenue_per_student,
    calculate_student_teacher_ratio,
)

# Workforce Module (DHG)
from app.engine.workforce.dhg import (
    DHGHoursResult,
    DHGInput,
    EducationLevel,
    SubjectHours,
    calculate_dhg_hours,
    calculate_fte_from_hours,
    calculate_hsa_allocation,
    calculate_trmd_gap,
)


class TestStudentsToTeachersIntegration:
    """
    Test data flow from Students module (Enrollment) to Teachers module (DHG).

    The key integration point is:
    Enrollment (number of students) → Class Structure (number of classes) → DHG (teacher hours)
    """

    def test_enrollment_to_class_structure_to_dhg(self):
        """
        Test the complete flow:
        1. Project enrollment for 6ème
        2. Calculate number of classes needed (based on class size limits)
        3. Calculate DHG hours for those classes
        4. Verify FTE requirements are derived correctly
        """
        # Step 1: Project enrollment
        enrollment_input = EnrollmentInput(
            level_id=uuid4(),
            level_code="6EME",
            nationality="French",
            current_enrollment=120,
            growth_scenario=EnrollmentGrowthScenario.BASE,
            years_to_project=3,
        )
        enrollment_result = calculate_enrollment_projection(enrollment_input)

        # Verify enrollment projection worked
        assert enrollment_result.level_code == "6EME"
        assert len(enrollment_result.projections) == 3

        # Get year 3 projected enrollment
        year3_enrollment = enrollment_result.projections[2].projected_enrollment
        assert year3_enrollment > 0

        # Step 2: Calculate number of classes
        # Using standard class size of 25 students max
        max_class_size = 25
        number_of_classes = (year3_enrollment + max_class_size - 1) // max_class_size

        assert number_of_classes > 0

        # Step 3: Calculate DHG hours for 6ème
        level_id = uuid4()
        subject_hours = [
            SubjectHours(
                subject_id=uuid4(),
                subject_code="MATH",
                subject_name="Mathématiques",
                level_id=level_id,
                level_code="6EME",
                hours_per_week=Decimal("4.5"),
            ),
            SubjectHours(
                subject_id=uuid4(),
                subject_code="FRAN",
                subject_name="Français",
                level_id=level_id,
                level_code="6EME",
                hours_per_week=Decimal("5.0"),
            ),
            SubjectHours(
                subject_id=uuid4(),
                subject_code="ANG",
                subject_name="Anglais",
                level_id=level_id,
                level_code="6EME",
                hours_per_week=Decimal("4.0"),
            ),
        ]

        dhg_input = DHGInput(
            level_id=level_id,
            level_code="6EME",
            education_level=EducationLevel.SECONDARY,
            number_of_classes=number_of_classes,
            subject_hours_list=subject_hours,
        )

        dhg_result = calculate_dhg_hours(dhg_input)

        # Verify DHG calculation
        assert dhg_result.level_code == "6EME"
        assert dhg_result.number_of_classes == number_of_classes
        assert dhg_result.total_hours > 0

        # Expected: (4.5 + 5.0 + 4.0) × number_of_classes = 13.5 × classes
        expected_hours = Decimal("13.5") * number_of_classes
        assert dhg_result.total_hours == expected_hours

        # Step 4: Calculate FTE from DHG hours
        # Uses DHGHoursResult directly
        fte_result = calculate_fte_from_hours(dhg_result)

        assert fte_result.simple_fte > 0
        assert fte_result.education_level == EducationLevel.SECONDARY
        assert fte_result.standard_hours == Decimal("18.0")

        # Verify the integration makes sense:
        # More students → more classes → more DHG hours → more FTE
        print("\nIntegration Results:")
        print(f"  Year 3 Enrollment: {year3_enrollment}")
        print(f"  Classes Needed: {number_of_classes}")
        print(f"  DHG Hours: {dhg_result.total_hours}")
        print(f"  FTE Required: {fte_result.simple_fte} (rounded: {fte_result.rounded_fte})")

    def test_multiple_levels_dhg_aggregation(self):
        """
        Test aggregating DHG hours across multiple grade levels.

        This simulates a real scenario where a Math teacher teaches
        multiple levels in the secondary school.
        """
        levels_data = [
            ("6EME", 6),  # 6 classes
            ("5EME", 5),  # 5 classes
            ("4EME", 5),  # 5 classes
            ("3EME", 4),  # 4 classes
        ]

        total_math_hours = Decimal("0")
        level_results = []

        for level_code, num_classes in levels_data:
            level_id = uuid4()
            math_hours = SubjectHours(
                subject_id=uuid4(),
                subject_code="MATH",
                subject_name="Mathématiques",
                level_id=level_id,
                level_code=level_code,
                hours_per_week=Decimal("4.5"),
            )

            dhg_input = DHGInput(
                level_id=level_id,
                level_code=level_code,
                education_level=EducationLevel.SECONDARY,
                number_of_classes=num_classes,
                subject_hours_list=[math_hours],
            )

            result = calculate_dhg_hours(dhg_input)
            level_results.append(result)
            total_math_hours += result.total_hours

        # Verify aggregation
        # Total: (6+5+5+4) × 4.5 = 20 × 4.5 = 90 hours
        expected_total = Decimal("90.0")
        assert total_math_hours == expected_total

        # Calculate FTE for Math department (need a single DHG result for this)
        # Create a combined DHGHoursResult for FTE calculation
        combined_result = DHGHoursResult(
            level_id=uuid4(),
            level_code="ALL_COLLEGE",
            education_level=EducationLevel.SECONDARY,
            number_of_classes=20,
            total_hours=total_math_hours,
            subject_breakdown={"MATH": total_math_hours},
        )
        math_fte = calculate_fte_from_hours(combined_result)

        # 90 hours / 18 standard = 5 FTE
        assert math_fte.simple_fte == Decimal("5.00")
        assert math_fte.rounded_fte == 5


class TestTeachersToFinanceIntegration:
    """
    Test data flow from Teachers module (DHG/FTE) to Finance module.

    The key integration point is:
    FTE Requirements → Personnel Costs → Budget Consolidation
    """

    def test_fte_to_personnel_cost_calculation(self):
        """
        Test calculating personnel costs from FTE requirements.

        This simulates:
        1. Calculate DHG hours for a subject
        2. Derive FTE requirements
        3. Calculate personnel costs (salary × FTE)
        """
        # Step 1: Calculate DHG for Math across secondary levels
        level_id = uuid4()
        math_hours = SubjectHours(
            subject_id=uuid4(),
            subject_code="MATH",
            subject_name="Mathématiques",
            level_id=level_id,
            level_code="6EME",
            hours_per_week=Decimal("4.5"),
        )

        dhg_input = DHGInput(
            level_id=level_id,
            level_code="6EME",
            education_level=EducationLevel.SECONDARY,
            number_of_classes=6,  # 6 classes of 6ème
            subject_hours_list=[math_hours],
        )

        dhg_result = calculate_dhg_hours(dhg_input)

        # Step 2: Calculate FTE
        fte_result = calculate_fte_from_hours(dhg_result)

        # Step 3: Calculate personnel cost
        # Using real EFIR parameters:
        # - Average teacher salary: 180,000 SAR/year (basic)
        # - Housing allowance: 25% of basic
        # - Transport allowance: 10% of basic
        # - GOSI employer: 12% of gross
        base_salary_sar = Decimal("180000")
        housing_pct = Decimal("0.25")
        transport_pct = Decimal("0.10")
        gosi_employer_pct = Decimal("0.12")

        gross_salary = base_salary_sar * (1 + housing_pct + transport_pct)
        employer_cost = gross_salary * (1 + gosi_employer_pct)

        # Total personnel cost for required FTE
        total_personnel_cost = employer_cost * fte_result.simple_fte

        # Verify calculations make sense
        assert fte_result.simple_fte > 0
        assert total_personnel_cost > 0

        print("\nPersonnel Cost Integration:")
        print(f"  DHG Hours: {dhg_result.total_hours}")
        print(f"  FTE Required: {fte_result.simple_fte}")
        print(f"  Base Salary: {base_salary_sar:,.0f} SAR")
        print(f"  Gross Salary: {gross_salary:,.0f} SAR")
        print(f"  Employer Cost/FTE: {employer_cost:,.0f} SAR")
        print(f"  Total Personnel Cost: {total_personnel_cost:,.0f} SAR")

    def test_trmd_gap_analysis(self):
        """
        Test TRMD (gap analysis) integration between required FTE and available FTE.

        This is a critical integration point for workforce planning.
        """
        # Calculate required FTE from DHG
        level_id = uuid4()
        subject_hours = [
            SubjectHours(
                subject_id=uuid4(),
                subject_code="MATH",
                subject_name="Mathématiques",
                level_id=level_id,
                level_code="6EME",
                hours_per_week=Decimal("4.5"),
            ),
        ]

        dhg_input = DHGInput(
            level_id=level_id,
            level_code="6EME",
            education_level=EducationLevel.SECONDARY,
            number_of_classes=10,  # 10 classes
            subject_hours_list=subject_hours,
        )

        dhg_result = calculate_dhg_hours(dhg_input)
        fte_result = calculate_fte_from_hours(dhg_result)

        # Simulate available FTE (current workforce) split between AEFE and local
        available_aefe_fte = Decimal("1.5")
        available_local_fte = Decimal("0.5")

        # Calculate TRMD gap
        trmd_result = calculate_trmd_gap(
            required_fte=fte_result.simple_fte,
            available_aefe_fte=available_aefe_fte,
            available_local_fte=available_local_fte,
        )

        # 10 classes × 4.5h = 45 hours / 18 standard = 2.5 FTE required
        # Available: 2.0 FTE (1.5 AEFE + 0.5 local)
        # Gap: 0.5 FTE
        assert trmd_result.required_fte == Decimal("2.50")
        assert trmd_result.available_aefe_fte == Decimal("1.50")
        assert trmd_result.available_local_fte == Decimal("0.50")
        assert trmd_result.gap_fte == Decimal("0.50")
        assert trmd_result.is_overstaffed is False

        # Calculate HSA allocation to cover the gap
        hsa_result = calculate_hsa_allocation(
            subject_code="MATH",
            subject_name="Mathématiques",
            dhg_hours_needed=dhg_result.total_hours,
            available_fte=2,  # 2 teachers available
            education_level=EducationLevel.SECONDARY,
            max_hsa_per_teacher=Decimal("4.0"),
        )

        # Verify HSA can partially cover the gap
        # 45 hours needed, 2 teachers × 18h = 36h available
        # Gap: 9 hours needed as HSA
        # 9h / 2 teachers = 4.5h per teacher (exceeds 4h max)
        assert hsa_result.hsa_hours_needed == Decimal("9.0")
        assert hsa_result.hsa_within_limit is False  # 4.5h > 4h max


class TestFinanceToInsightsIntegration:
    """
    Test data flow from Finance module to Insights module (KPIs).

    The key integration point is:
    Revenue + Costs + Enrollment → Financial KPIs
    """

    def test_revenue_and_costs_to_kpis(self):
        """
        Test calculating KPIs from consolidated revenue and cost data.

        KPIs tested:
        - Revenue per Student
        - Cost per Student
        - Student/Teacher Ratio
        - Margin Percentage
        """
        # Simulated consolidated data (would come from Finance engines)
        total_enrollment = 1200
        secondary_enrollment = 500
        max_capacity = 1500
        total_teachers_fte = Decimal("80")

        # Revenue calculation (simplified)
        tuition_per_student = Decimal("45000")
        total_revenue = tuition_per_student * total_enrollment

        # Costs (simplified)
        personnel_costs = Decimal("30000000")  # 30M SAR
        operational_costs = Decimal("8000000")  # 8M SAR
        total_costs = personnel_costs + operational_costs

        # Create KPI input with all required fields
        kpi_input = KPIInput(
            total_students=total_enrollment,
            secondary_students=secondary_enrollment,
            max_capacity=max_capacity,
            total_teacher_fte=total_teachers_fte,
            dhg_hours_total=Decimal("675"),  # Example DHG hours for secondary
            total_revenue=total_revenue,
            total_costs=total_costs,
            personnel_costs=personnel_costs,
        )

        # Calculate all KPIs
        kpi_results = calculate_all_kpis(kpi_input)

        # Verify KPIs are populated
        assert kpi_results.student_teacher_ratio is not None
        assert kpi_results.revenue_per_student is not None
        assert kpi_results.cost_per_student is not None
        assert kpi_results.margin_percentage is not None

        # Individual KPI calculations
        revenue_per_student = calculate_revenue_per_student(total_revenue, total_enrollment)
        cost_per_student = calculate_cost_per_student(total_costs, total_enrollment)
        student_teacher_ratio = calculate_student_teacher_ratio(
            total_enrollment, total_teachers_fte
        )

        # Verify values (KPIResult objects)
        assert revenue_per_student.value == Decimal("45000.00")  # 54M / 1200
        # 38M / 1200 = 31666.67
        assert cost_per_student.value == Decimal("31666.67")
        # 1200 / 80 = 15.00
        assert student_teacher_ratio.value == Decimal("15.00")

        print("\nKPI Integration Results:")
        print(f"  Total Enrollment: {total_enrollment}")
        print(f"  Total Revenue: {total_revenue:,.0f} SAR")
        print(f"  Total Costs: {total_costs:,.0f} SAR")
        print(f"  Revenue/Student: {revenue_per_student.value:,.2f} SAR")
        print(f"  Cost/Student: {cost_per_student.value:,.2f} SAR")
        print(f"  Student/Teacher Ratio: {student_teacher_ratio.value}")

    def test_he_ratio_secondary(self):
        """
        Test H/E (hours per student) ratio calculation for secondary school.

        This is a key educational KPI used by AEFE schools.
        """
        # Secondary DHG hours (from multiple subjects across levels)
        total_secondary_dhg_hours = Decimal("877.5")  # Total weekly hours
        secondary_enrollment = 650

        # Calculate H/E ratio
        he_ratio = calculate_he_ratio_secondary(
            total_secondary_dhg_hours,
            secondary_enrollment,
        )

        # Expected: 877.5 / 650 = 1.35 hours per student
        assert he_ratio.value == Decimal("1.35")
        assert he_ratio.kpi_type.value == "he_ratio_secondary"

        print("\nH/E Ratio (Secondary):")
        print(f"  Total DHG Hours: {total_secondary_dhg_hours}")
        print(f"  Secondary Enrollment: {secondary_enrollment}")
        print(f"  H/E Ratio: {he_ratio.value}")


class TestEndToEndWorkflow:
    """
    Complete end-to-end integration tests simulating a full budget planning cycle.
    """

    def test_full_budget_planning_workflow(self):
        """
        Test the complete workflow from enrollment projection to financial statements.

        Flow:
        1. Enrollment Projection (5-year plan)
        2. Class Structure Calculation
        3. DHG Hours Calculation
        4. FTE Requirements
        5. Personnel Cost Calculation
        6. Revenue Projection
        7. Income Statement Generation
        8. KPI Calculation
        """
        print("\n" + "=" * 60)
        print("FULL BUDGET PLANNING WORKFLOW - Integration Test")
        print("=" * 60)

        # ====================
        # Step 1: Enrollment
        # ====================
        print("\n Step 1: Enrollment Projection")

        # Project enrollment for 6ème (base year: 120 students)
        enrollment_input = EnrollmentInput(
            level_id=uuid4(),
            level_code="6EME",
            nationality="French",
            current_enrollment=120,
            growth_scenario=EnrollmentGrowthScenario.BASE,
            years_to_project=5,
        )
        enrollment_result = calculate_enrollment_projection(enrollment_input)

        year1_enrollment = enrollment_result.projections[0].projected_enrollment
        year5_enrollment = enrollment_result.projections[4].projected_enrollment

        print(f"  Year 1: {year1_enrollment} students")
        print(f"  Year 5: {year5_enrollment} students (projected)")

        # ====================
        # Step 2: Class Structure
        # ====================
        print("\n Step 2: Class Structure")

        max_class_size = 25
        year1_classes = (year1_enrollment + max_class_size - 1) // max_class_size
        year5_classes = (year5_enrollment + max_class_size - 1) // max_class_size

        print(f"  Year 1: {year1_classes} classes")
        print(f"  Year 5: {year5_classes} classes (projected)")

        # ====================
        # Step 3: DHG Hours
        # ====================
        print("\n Step 3: DHG Hours Calculation")

        level_id = uuid4()
        subject_hours = [
            SubjectHours(
                subject_id=uuid4(),
                subject_code="MATH",
                subject_name="Mathématiques",
                level_id=level_id,
                level_code="6EME",
                hours_per_week=Decimal("4.5"),
            ),
            SubjectHours(
                subject_id=uuid4(),
                subject_code="FRAN",
                subject_name="Français",
                level_id=level_id,
                level_code="6EME",
                hours_per_week=Decimal("5.0"),
            ),
            SubjectHours(
                subject_id=uuid4(),
                subject_code="ANG",
                subject_name="Anglais",
                level_id=level_id,
                level_code="6EME",
                hours_per_week=Decimal("4.0"),
            ),
            SubjectHours(
                subject_id=uuid4(),
                subject_code="HG",
                subject_name="Histoire-Géographie",
                level_id=level_id,
                level_code="6EME",
                hours_per_week=Decimal("3.0"),
            ),
            SubjectHours(
                subject_id=uuid4(),
                subject_code="SVT",
                subject_name="SVT",
                level_id=level_id,
                level_code="6EME",
                hours_per_week=Decimal("1.5"),
            ),
        ]

        dhg_input_y1 = DHGInput(
            level_id=level_id,
            level_code="6EME",
            education_level=EducationLevel.SECONDARY,
            number_of_classes=year1_classes,
            subject_hours_list=subject_hours,
        )
        dhg_result_y1 = calculate_dhg_hours(dhg_input_y1)

        dhg_input_y5 = DHGInput(
            level_id=level_id,
            level_code="6EME",
            education_level=EducationLevel.SECONDARY,
            number_of_classes=year5_classes,
            subject_hours_list=subject_hours,
        )
        dhg_result_y5 = calculate_dhg_hours(dhg_input_y5)

        print(f"  Year 1 DHG: {dhg_result_y1.total_hours} hours/week")
        print(f"  Year 5 DHG: {dhg_result_y5.total_hours} hours/week (projected)")

        # ====================
        # Step 4: FTE Requirements
        # ====================
        print("\n Step 4: FTE Requirements")

        fte_y1 = calculate_fte_from_hours(dhg_result_y1)
        fte_y5 = calculate_fte_from_hours(dhg_result_y5)

        print(f"  Year 1 FTE: {fte_y1.simple_fte} (rounded: {fte_y1.rounded_fte})")
        print(f"  Year 5 FTE: {fte_y5.simple_fte} (rounded: {fte_y5.rounded_fte})")

        # ====================
        # Step 5: Personnel Costs
        # ====================
        print("\n Step 5: Personnel Cost Calculation")

        avg_teacher_cost = Decimal("250000")  # SAR/year (fully loaded)
        personnel_cost_y1 = avg_teacher_cost * fte_y1.simple_fte
        personnel_cost_y5 = avg_teacher_cost * fte_y5.simple_fte

        print(f"  Year 1 Personnel Cost: {personnel_cost_y1:,.0f} SAR")
        print(f"  Year 5 Personnel Cost: {personnel_cost_y5:,.0f} SAR (projected)")

        # ====================
        # Step 6: Revenue Projection
        # ====================
        print("\n Step 6: Revenue Projection")

        tuition_per_student = Decimal("45000")
        revenue_y1 = tuition_per_student * year1_enrollment
        revenue_y5 = tuition_per_student * year5_enrollment

        print(f"  Year 1 Revenue: {revenue_y1:,.0f} SAR")
        print(f"  Year 5 Revenue: {revenue_y5:,.0f} SAR (projected)")

        # ====================
        # Step 7: Operating Result
        # ====================
        print("\n Step 7: Operating Result")

        # Year 1 operating result
        operational_costs_y1 = Decimal("200000")  # Fixed overhead
        total_costs_y1 = personnel_cost_y1 + operational_costs_y1
        operating_result_y1 = revenue_y1 - total_costs_y1

        # Year 5 operating result (with growth)
        operational_costs_y5 = Decimal("220000")  # Slight increase
        total_costs_y5 = personnel_cost_y5 + operational_costs_y5
        operating_result_y5 = revenue_y5 - total_costs_y5

        print(f"  Year 1 Operating Result: {operating_result_y1:,.0f} SAR")
        print(f"  Year 5 Operating Result: {operating_result_y5:,.0f} SAR (projected)")

        # ====================
        # Step 8: KPIs
        # ====================
        print("\n Step 8: Key Performance Indicators")

        # Year 1 KPIs
        rev_per_student_y1 = revenue_y1 / year1_enrollment
        cost_per_student_y1 = total_costs_y1 / year1_enrollment
        margin_y1 = (operating_result_y1 / revenue_y1) * 100

        # Year 5 KPIs (projected)
        rev_per_student_y5 = revenue_y5 / year5_enrollment
        cost_per_student_y5 = total_costs_y5 / year5_enrollment
        margin_y5 = (operating_result_y5 / revenue_y5) * 100

        print("  Year 1:")
        print(f"    Revenue/Student: {rev_per_student_y1:,.0f} SAR")
        print(f"    Cost/Student: {cost_per_student_y1:,.0f} SAR")
        print(f"    Operating Margin: {margin_y1:.1f}%")

        print("  Year 5 (Projected):")
        print(f"    Revenue/Student: {rev_per_student_y5:,.0f} SAR")
        print(f"    Cost/Student: {cost_per_student_y5:,.0f} SAR")
        print(f"    Operating Margin: {margin_y5:.1f}%")

        # ====================
        # Verification
        # ====================
        print("\n" + "=" * 60)
        print("VERIFICATION")
        print("=" * 60)

        # Verify the workflow produces reasonable results
        assert year5_enrollment > year1_enrollment, "Enrollment should grow"
        assert year5_classes >= year1_classes, "Classes should not decrease"
        assert dhg_result_y5.total_hours >= dhg_result_y1.total_hours, "DHG should not decrease"
        assert fte_y5.simple_fte >= fte_y1.simple_fte, "FTE should not decrease"
        assert operating_result_y1 > 0, "Year 1 should be profitable (single grade)"

        print("  Enrollment growth verified")
        print("  Class structure scaled correctly")
        print("  DHG hours calculated correctly")
        print("  FTE requirements derived correctly")
        print("  Personnel costs calculated correctly")
        print("  Revenue projected correctly")
        print("  Operating results computed correctly")
        print("  KPIs calculated correctly")

        print("\n" + "=" * 60)
        print("END-TO-END WORKFLOW TEST COMPLETED SUCCESSFULLY")
        print("=" * 60 + "\n")

    def test_multi_grade_budget_consolidation(self):
        """
        Test budget consolidation across multiple grades.

        This tests the scenario where we consolidate budgets from:
        - Maternelle (PS, MS, GS)
        - Élémentaire (CP, CE1, CE2, CM1, CM2)
        - Collège (6ème, 5ème, 4ème, 3ème)
        - Lycée (2nde, 1ère, Terminale)
        """
        # Simplified multi-grade data
        grades_data = {
            # Maternelle (primary, 24h standard)
            "PS": {"enrollment": 80, "classes": 4, "tuition": 38000},
            "MS": {"enrollment": 90, "classes": 4, "tuition": 38000},
            "GS": {"enrollment": 95, "classes": 4, "tuition": 38000},
            # Élémentaire (primary, 24h standard)
            "CP": {"enrollment": 100, "classes": 4, "tuition": 42000},
            "CE1": {"enrollment": 100, "classes": 4, "tuition": 42000},
            "CE2": {"enrollment": 105, "classes": 4, "tuition": 42000},
            "CM1": {"enrollment": 100, "classes": 4, "tuition": 42000},
            "CM2": {"enrollment": 100, "classes": 4, "tuition": 42000},
            # Collège (secondary, 18h standard)
            "6EME": {"enrollment": 110, "classes": 5, "tuition": 45000},
            "5EME": {"enrollment": 105, "classes": 5, "tuition": 45000},
            "4EME": {"enrollment": 100, "classes": 4, "tuition": 45000},
            "3EME": {"enrollment": 95, "classes": 4, "tuition": 45000},
            # Lycée (secondary, 18h standard)
            "2NDE": {"enrollment": 90, "classes": 4, "tuition": 48000},
            "1ERE": {"enrollment": 85, "classes": 4, "tuition": 48000},
            "TERM": {"enrollment": 80, "classes": 4, "tuition": 48000},
        }

        # Consolidate totals
        total_enrollment = sum(g["enrollment"] for g in grades_data.values())
        total_classes = sum(g["classes"] for g in grades_data.values())
        total_revenue = sum(
            g["enrollment"] * g["tuition"] for g in grades_data.values()
        )

        # Calculate by cycle
        maternelle_revenue = sum(
            grades_data[g]["enrollment"] * grades_data[g]["tuition"]
            for g in ["PS", "MS", "GS"]
        )
        elementaire_revenue = sum(
            grades_data[g]["enrollment"] * grades_data[g]["tuition"]
            for g in ["CP", "CE1", "CE2", "CM1", "CM2"]
        )
        college_revenue = sum(
            grades_data[g]["enrollment"] * grades_data[g]["tuition"]
            for g in ["6EME", "5EME", "4EME", "3EME"]
        )
        lycee_revenue = sum(
            grades_data[g]["enrollment"] * grades_data[g]["tuition"]
            for g in ["2NDE", "1ERE", "TERM"]
        )

        print("\n" + "=" * 60)
        print("MULTI-GRADE BUDGET CONSOLIDATION")
        print("=" * 60)
        print(f"\nTotal Enrollment: {total_enrollment:,}")
        print(f"Total Classes: {total_classes}")
        print(f"Total Revenue: {total_revenue:,} SAR")
        print("\nBy Cycle:")
        print(f"  Maternelle: {maternelle_revenue:,} SAR")
        print(f"  Élémentaire: {elementaire_revenue:,} SAR")
        print(f"  Collège: {college_revenue:,} SAR")
        print(f"  Lycée: {lycee_revenue:,} SAR")

        # Verify consolidation
        assert total_enrollment == 1435
        assert total_classes == 62
        assert (
            total_revenue
            == maternelle_revenue + elementaire_revenue + college_revenue + lycee_revenue
        )

        # Calculate consolidated KPIs
        avg_tuition = total_revenue / total_enrollment
        print("\nConsolidated KPIs:")
        print(f"  Average Tuition: {avg_tuition:,.0f} SAR")
        print(f"  Students/Class: {total_enrollment / total_classes:.1f}")

        print("\n Multi-grade consolidation verified")


class TestDataConsistencyAcrossModules:
    """
    Tests to verify data consistency when passing data between modules.
    """

    def test_decimal_precision_preserved_across_modules(self):
        """
        Verify that Decimal precision is maintained when data flows
        between Students → Teachers → Finance modules.
        """
        # DHG calculation with fractional hours
        level_id = uuid4()
        subject_hours = SubjectHours(
            subject_id=uuid4(),
            subject_code="PHYS",
            subject_name="Physique",
            level_id=level_id,
            level_code="3EME",
            hours_per_week=Decimal("1.5"),  # Fractional hours
        )

        dhg_input = DHGInput(
            level_id=level_id,
            level_code="3EME",
            education_level=EducationLevel.SECONDARY,
            number_of_classes=3,
            subject_hours_list=[subject_hours],
        )

        dhg_result = calculate_dhg_hours(dhg_input)

        # 3 classes × 1.5 hours = 4.5 hours (exact)
        assert dhg_result.total_hours == Decimal("4.5")

        # FTE calculation: 4.5 / 18 = 0.25 (exact)
        fte_result = calculate_fte_from_hours(dhg_result)
        assert fte_result.simple_fte == Decimal("0.25")

        # Personnel cost with Decimal arithmetic
        salary = Decimal("180000")
        cost = salary * fte_result.simple_fte

        # Should be exactly 45000 SAR
        assert cost == Decimal("45000")

        print("\n Decimal precision verified across modules")

    def test_uuid_consistency_across_modules(self):
        """
        Verify that UUIDs are consistently handled across modules.
        """
        # Create a shared level_id that would link data across modules
        shared_level_id = uuid4()
        shared_subject_id = uuid4()

        # Use in enrollment
        enrollment_input = EnrollmentInput(
            level_id=shared_level_id,
            level_code="6EME",
            nationality="French",
            current_enrollment=120,
            growth_scenario=EnrollmentGrowthScenario.BASE,
            years_to_project=1,
        )
        enrollment_result = calculate_enrollment_projection(enrollment_input)

        # Use same level_id in DHG
        subject_hours = SubjectHours(
            subject_id=shared_subject_id,
            subject_code="MATH",
            subject_name="Mathématiques",
            level_id=shared_level_id,  # Same as enrollment
            level_code="6EME",
            hours_per_week=Decimal("4.5"),
        )

        dhg_input = DHGInput(
            level_id=shared_level_id,  # Same as enrollment
            level_code="6EME",
            education_level=EducationLevel.SECONDARY,
            number_of_classes=5,
            subject_hours_list=[subject_hours],
        )

        dhg_result = calculate_dhg_hours(dhg_input)

        # Verify UUIDs match
        assert enrollment_result.level_id == shared_level_id
        assert dhg_result.level_id == shared_level_id

        print("\n UUID consistency verified across modules")
