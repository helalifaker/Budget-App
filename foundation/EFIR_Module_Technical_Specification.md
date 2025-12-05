# EFIR School Budget Planning Application
## Module Technical Specification for Development

**Version:** 1.0  
**Date:** November 2025  
**Document Type:** Technical Development Specification  
**Status:** Ready for Development

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Module Architecture](#2-module-architecture)
3. [Module 1: System Configuration](#module-1-system-configuration)
4. [Module 2: Class Size Parameters](#module-2-class-size-parameters)
5. [Module 3: Subject Hours Configuration](#module-3-subject-hours-configuration)
6. [Module 4: Teacher Cost Parameters](#module-4-teacher-cost-parameters)
7. [Module 5: Fee Structure Configuration](#module-5-fee-structure-configuration)
8. [Module 6: Timetable Constraints](#module-6-timetable-constraints)
9. [Module 7: Enrollment Planning](#module-7-enrollment-planning)
10. [Module 8: Teacher Workforce Planning (DHG)](#module-8-teacher-workforce-planning-dhg)
11. [Module 9: Facility Planning](#module-9-facility-planning)
12. [Module 10: Revenue Planning](#module-10-revenue-planning)
13. [Module 11: Cost Planning](#module-11-cost-planning)
14. [Module 12: CapEx Planning](#module-12-capex-planning)
15. [Module 13: Budget Consolidation](#module-13-budget-consolidation)
16. [Module 14: Financial Statements](#module-14-financial-statements)
17. [Module 15: Statistical Analysis (KPIs)](#module-15-statistical-analysis-kpis)
18. [Module 16: Dashboards & Reporting](#module-16-dashboards--reporting)
19. [Module 17: Budget vs Actual Analysis](#module-17-budget-vs-actual-analysis)
20. [Module 18: 5-Year Strategic Plan](#module-18-5-year-strategic-plan)
21. [Data Flow Diagram](#data-flow-diagram)
22. [Technology Stack](#technology-stack)

---

## 1. System Overview

### 1.1 Purpose

This application provides integrated planning from workforce planning through annual budget and 5-year strategic planning for École Française Internationale de Riyad (EFIR), a French international school operating under AEFE guidelines in Saudi Arabia.

### 1.2 Budget Period Structure

| Period | Months | Description |
|--------|--------|-------------|
| Period 1 | January - June | Current academic year continuation |
| Summer | July - August | Minimal operations |
| Period 2 | September - December | New academic year start |
| Calendar Year | January - December | Financial reporting period |

### 1.3 Key Characteristics

- **Primary Currency:** SAR (Saudi Riyal)
- **Secondary Currency:** EUR (for AEFE reporting)
- **Working Days:** Sunday - Thursday
- **Weekend:** Friday - Saturday
- **AEFE Status:** Conventionné
- **Academic Year:** September to June

---

## 2. Module Architecture

### 2.1 Module Categories

| Category | Modules | Purpose |
|----------|---------|---------|
| **Configuration (1-6)** | System, Class Size, Subject Hours, Teacher Costs, Fees, Timetable | Master data and parameters |
| **Planning (7-12)** | Enrollment, Workforce, Facility, Revenue, Cost, CapEx | Operational planning |
| **Consolidation (13-14)** | Budget Consolidation, Financial Statements | Financial integration |
| **Analysis (15-17)** | KPIs, Dashboards, Budget vs Actual | Monitoring and reporting |
| **Strategic (18)** | 5-Year Plan | Long-term planning |

### 2.2 Data Flow Summary

```
Enrollment → Class Structure → DHG Hours → Teacher FTE → Personnel Costs
     ↓              ↓              ↓             ↓              ↓
   Revenue    Facility Needs   Curriculum    AEFE/Local    Cost Planning
     ↓              ↓              ↓             ↓              ↓
     └──────────────┴──────────────┴─────────────┴──────────────┘
                                   ↓
                        Budget Consolidation
                                   ↓
                        Financial Statements
                                   ↓
                          5-Year Plan
```

---

## Module 1: System Configuration

### 1.1 Purpose
Foundation module establishing organizational structure, academic calendar, chart of accounts, cost centers, and system parameters.

### 1.2 Inputs

| Input | Data Type | Source | Description |
|-------|-----------|--------|-------------|
| `school_id` | UUID | System | Unique identifier |
| `school_name` | String | Manual | "École Française Internationale de Riyad" |
| `aefe_status` | Enum | Manual | Direct / Conventionné / Homologué |
| `fiscal_year_start` | Integer | Manual | Month (1-12), typically 1 for January |
| `academic_year_start` | Integer | Manual | Month (1-12), typically 9 for September |
| `base_currency` | String | Manual | ISO code: "SAR" |
| `secondary_currency` | String | Manual | ISO code: "EUR" |
| `exchange_rate_sar_eur` | Decimal | Manual/API | Current exchange rate |

### 1.3 Configuration Data Structures

#### Academic Structure
```
cycles[] = [
  { id, name: "Maternelle", levels: ["PS", "MS", "GS"] },
  { id, name: "Élémentaire", levels: ["CP", "CE1", "CE2", "CM1", "CM2"] },
  { id, name: "Collège", levels: ["6ème", "5ème", "4ème", "3ème"] },
  { id, name: "Lycée", levels: ["2nde", "1ère", "Terminale"] }
]
```

#### Chart of Accounts (French PCG)
```
accounts[] = [
  { code: "70110", name: "Scolarité T1", type: "Revenue", ifrs_mapping: "Tuition" },
  { code: "70120", name: "Scolarité T2", type: "Revenue", ifrs_mapping: "Tuition" },
  { code: "64110", name: "Salaires enseignement", type: "Expense", ifrs_mapping: "Personnel" },
  { code: "64800", name: "AEFE salaires résidents", type: "Expense", ifrs_mapping: "Personnel" },
  ...
]
```

#### Cost Centers
```
cost_centers[] = [
  { id, code: "MAT", name: "Maternelle", budget_holder_id },
  { id, code: "ELEM", name: "Élémentaire", budget_holder_id },
  { id, code: "COL", name: "Collège", budget_holder_id },
  { id, code: "LYC", name: "Lycée", budget_holder_id },
  { id, code: "ADM", name: "Administration", budget_holder_id }
]
```

### 1.4 Outputs

| Output | Consumers | Description |
|--------|-----------|-------------|
| `academic_structure` | All modules | Cycles, levels, sections |
| `chart_of_accounts` | Cost Planning, Financial Statements | Account hierarchy |
| `cost_centers` | Cost Planning, Reporting | Budget allocation units |
| `calendar_config` | All modules | Academic and fiscal calendars |
| `currency_settings` | All modules | Currency codes and rates |

### 1.5 Validation Rules

1. Fiscal year must be defined before creating budget periods
2. Exchange rates must be updated before AEFE cost calculations
3. All cost centers must have an assigned budget holder
4. Account codes must follow PCG numbering conventions

---

## Module 2: Class Size Parameters

### 2.1 Purpose
Define class formation rules that drive workforce and facility calculations.

### 2.2 Inputs

| Input | Data Type | Default | Description |
|-------|-----------|---------|-------------|
| `cycle_id` | UUID | Required | Reference to academic cycle |
| `level_id` | UUID | Optional | Specific level override |
| `min_class_size` | Integer | 15 | Minimum to open a class |
| `target_class_size` | Integer | 24 | Optimal number per class |
| `max_class_size` | Integer | 28 | Maximum allowed |
| `atsem_required` | Boolean | True (Maternelle) | ATSEM assistant needed |
| `atsem_ratio` | Decimal | 1.0 | ATSEM per class ratio |
| `effective_date` | Date | Required | When parameters take effect |

### 2.3 Default Parameters by Cycle

| Cycle | Min | Target | Max | ATSEM |
|-------|-----|--------|-----|-------|
| Maternelle | 15 | 22 | 26 | 1.0 per class |
| Élémentaire | 18 | 24 | 28 | N/A |
| Collège | 20 | 26 | 30 | N/A |
| Lycée | 20 | 26 | 32 | N/A |

### 2.4 Calculations

#### Number of Classes
```python
def calculate_classes(enrollment: int, target_size: int, max_size: int) -> int:
    """
    Calculate number of classes needed for a given enrollment.
    """
    if enrollment <= max_size:
        return 1
    
    # Calculate based on target size
    classes_needed = math.ceil(enrollment / target_size)
    
    # Verify average doesn't exceed max
    avg_size = enrollment / classes_needed
    if avg_size > max_size:
        classes_needed += 1
    
    return classes_needed
```

#### ATSEM Requirements (Maternelle only)
```python
def calculate_atsem(num_classes: int, atsem_ratio: float) -> int:
    """
    Calculate ATSEM assistants needed.
    """
    return math.ceil(num_classes * atsem_ratio)
```

### 2.5 Outputs

| Output | Consumers | Description |
|--------|-----------|-------------|
| `class_count_by_level` | Workforce Planning, Facility Planning | Number of classes per level |
| `atsem_requirements` | Cost Planning | ATSEM positions needed |
| `average_class_size` | KPIs | Actual average per class |

### 2.6 Business Rules

1. `min_class_size < target_class_size ≤ max_class_size`
2. Level-specific parameters override cycle defaults
3. Parameter changes trigger recalculation of downstream modules
4. Historical parameters retained for audit

---

## Module 3: Subject Hours Configuration

### 3.1 Purpose
Define curriculum structure and teaching hours required per subject, driving secondary workforce calculations.

### 3.2 Inputs

| Input | Data Type | Source | Description |
|-------|-----------|--------|-------------|
| `subject_id` | UUID | System | Unique identifier |
| `subject_name` | String | Manual | Display name (e.g., "Mathématiques") |
| `subject_code` | String | Manual | Short code (e.g., "MATH") |
| `subject_type` | Enum | Manual | Core / Elective / Local / Specialization |
| `level_id` | UUID | Reference | Academic level |
| `hours_per_week` | Decimal | Manual | Weekly teaching hours |
| `requires_block` | Boolean | Manual | Needs 2-hour blocks |
| `requires_special_room` | Boolean | Manual | Lab or special facility |
| `room_type` | String | Conditional | Type if special room needed |

### 3.3 Standard Curriculum Hours Matrix (Collège)

| Subject | 6ème | 5ème | 4ème | 3ème |
|---------|------|------|------|------|
| Français | 4.5 | 4.5 | 4.5 | 4.0 |
| Mathématiques | 4.5 | 3.5 | 3.5 | 3.5 |
| Histoire-Géographie | 3.0 | 3.0 | 3.0 | 3.5 |
| Anglais (LV1) | 4.0 | 3.0 | 3.0 | 3.0 |
| Espagnol (LV2) | - | 2.5 | 2.5 | 2.5 |
| Arabic (LVB) | 2.5 | 2.5 | 2.5 | 2.5 |
| SVT | 3.0 | 1.5 | 1.5 | 1.5 |
| Physique-Chimie | - | 1.5 | 1.5 | 1.5 |
| EPS | 4.0 | 3.0 | 3.0 | 3.0 |
| Arts Plastiques | 1.0 | 1.0 | 1.0 | 1.0 |
| Éducation Musicale | 1.0 | 1.0 | 1.0 | 1.0 |
| Technologie | 1.5 | 1.5 | 1.5 | 1.5 |

### 3.4 Calculations

#### Total Subject Hours (Secondary)
```python
def calculate_total_subject_hours(
    subject_id: str,
    classes_by_level: dict,
    hours_matrix: dict
) -> float:
    """
    Calculate total weekly hours for a subject across all classes.
    
    Returns: Total hours = Σ(classes_per_level × hours_per_week_per_level)
    """
    total_hours = 0
    for level_id, num_classes in classes_by_level.items():
        hours_per_week = hours_matrix.get((subject_id, level_id), 0)
        total_hours += num_classes * hours_per_week
    return total_hours
```

### 3.5 Outputs

| Output | Consumers | Description |
|--------|-----------|-------------|
| `subject_hours_matrix` | Workforce Planning | Hours by subject and level |
| `total_hours_by_subject` | DHG Calculation | Total weekly hours per subject |
| `room_requirements` | Facility Planning | Special room needs by subject |

### 3.6 Business Rules

1. Core subjects cannot be deleted, only deactivated
2. Local subjects (Arabic) require Ministry approval
3. Total weekly hours per level must not exceed 30 hours
4. Changes trigger workforce recalculation

---

## Module 4: Teacher Cost Parameters

### 4.1 Purpose
Define salary scales, benefits, and allowances for AEFE and local teachers.

### 4.2 Inputs - AEFE Teachers

| Input | Data Type | Unit | Description |
|-------|-----------|------|-------------|
| `teacher_type` | Enum | - | "AEFE_DETACHE" / "AEFE_FUNDED" |
| `grade_echelon` | String | - | Teacher grade (e.g., "Certifié Classe Normale") |
| `prrd_contribution` | Decimal | EUR/year | School contribution to AEFE (~41,863 EUR) |
| `isvl_allowance` | Decimal | EUR/year | Local living allowance |
| `housing_allowance` | Decimal | EUR/month | Housing support |
| `standard_hours` | Integer | hours/week | 18 (secondary) / 24 (primary) |

### 4.3 Inputs - Local Teachers

| Input | Data Type | Unit | Description |
|-------|-----------|------|-------------|
| `position_category` | String | - | Position type |
| `base_salary_monthly` | Decimal | SAR | Base salary |
| `housing_allowance_il` | Decimal | SAR | Standard: 2,500 |
| `transport_allowance_it` | Decimal | SAR | Standard: 500 |
| `responsibility_premium` | Decimal | SAR | Management roles |
| `social_charges_pct` | Decimal | % | Employer contributions |
| `standard_hours` | Integer | hours/week | 18 or 24 |
| `max_overtime_hours` | Integer | hours/week | Typically 2-4 |
| `overtime_rate_hourly` | Decimal | SAR | HSA rate |

### 4.4 Local Teacher Salary Matrix

| Position | Count | Base Range (SAR) | Avg Net (SAR) |
|----------|-------|------------------|---------------|
| Professeur des écoles | 30 | 8,000 - 12,750 | 12,500 |
| Enseignant second degré | 43 | 4,000 - 12,000 | 12,613 |
| Enseignant langue étrangère | 24 | 3,700 - 14,250 | 13,500 |
| Professeur EPS | 4 | 8,500 - 12,250 | 13,062 |
| ASEM | 13 | 5,800 - 8,500 | 9,900 |
| Assistant d'éducation | 12 | 7,000 - 9,000 | 10,575 |

### 4.5 Calculations

#### AEFE Teacher Annual Cost
```python
def calculate_aefe_teacher_cost(
    prrd_contribution: float,
    exchange_rate: float
) -> dict:
    """
    Calculate annual cost for AEFE detached teacher.
    
    Returns cost in both EUR and SAR.
    """
    cost_eur = prrd_contribution  # ~41,863 EUR
    cost_sar = cost_eur * exchange_rate
    
    return {
        "annual_cost_eur": cost_eur,
        "annual_cost_sar": cost_sar,
        "monthly_cost_sar": cost_sar / 12
    }
```

#### Local Teacher Annual Cost
```python
def calculate_local_teacher_cost(
    base_salary: float,
    housing_allowance: float,
    transport_allowance: float,
    responsibility_premium: float,
    social_charges_pct: float,
    overtime_hours_annual: float,
    overtime_rate: float
) -> dict:
    """
    Calculate total annual cost for local teacher.
    """
    # Monthly gross
    monthly_gross = base_salary + housing_allowance + transport_allowance + responsibility_premium
    
    # Annual base
    annual_base = monthly_gross * 12
    
    # Social charges (on base salary only)
    annual_social_charges = base_salary * 12 * social_charges_pct
    
    # Overtime (HSA) - paid over 10 months
    annual_overtime = overtime_hours_annual * overtime_rate
    
    # Total employer cost
    total_annual_cost = annual_base + annual_social_charges + annual_overtime
    
    return {
        "monthly_gross": monthly_gross,
        "annual_base": annual_base,
        "annual_social_charges": annual_social_charges,
        "annual_overtime": annual_overtime,
        "total_annual_cost": total_annual_cost
    }
```

### 4.6 Outputs

| Output | Consumers | Description |
|--------|-----------|-------------|
| `aefe_cost_per_teacher` | Workforce Planning | Annual PRRD cost in SAR |
| `local_cost_per_position` | Workforce Planning | Full cost by position type |
| `overtime_rates` | Cost Planning | HSA calculation rates |
| `social_charges_rates` | Cost Planning | Employer contribution rates |

### 4.7 Business Rules

1. AEFE costs always calculated in EUR, then converted to SAR
2. Standard hours: Primary = 24h/week, Secondary = 18h/week
3. Overtime capped at max_overtime_hours per teacher
4. Annual increments applied at academic year start (September)

---

## Module 5: Fee Structure Configuration

### 5.1 Purpose
Define tuition fees by level and nationality category for revenue calculations.

### 5.2 Inputs

| Input | Data Type | Description |
|-------|-----------|-------------|
| `level_id` | UUID | Academic level reference |
| `nationality_category` | Enum | French / Saudi / Other |
| `annual_tuition` | Decimal | Annual tuition in SAR |
| `vat_treatment` | Enum | TTC (inclusive) / HT (exempt) |
| `dai_fee` | Decimal | Annual enrollment fee |
| `registration_fee` | Decimal | One-time for new students |
| `first_enrollment_fee` | Decimal | First-time enrollment |
| `effective_academic_year` | String | Year these fees apply |

### 5.3 Fee Matrix (2025-2026)

| Level | French (TTC) | Saudi (HT) | Other (TTC) | DAI |
|-------|--------------|------------|-------------|-----|
| Maternelle PS | 30,000 | 34,783 | 40,000 | 5,000 |
| Maternelle MS-GS | 34,500 | 35,650 | 41,000 | 5,000 |
| Élémentaire | 34,500 | 35,650 | 41,000 | 5,000 |
| Collège | 34,500 | 35,650 | 41,000 | 5,000 |
| Lycée | 38,500 | 40,000 | 46,000 | 5,000 |

### 5.4 Other Fees

| Fee Type | French (TTC) | Saudi (HT) | Other (TTC) |
|----------|--------------|------------|-------------|
| Registration (new) | 1,150 | 1,000 | 1,150 |
| First Enrollment | 2,300 | 2,000 | 2,300 |
| DNB Exam (3ème) | 287.50 | 250 | 287.50 |
| E.A Exam (1ère) | 575 | 500 | 575 |
| Baccalauréat | 1,495 | 1,300 | 1,495 |

### 5.5 Discount Rules

| Discount Type | Rule | Application |
|---------------|------|-------------|
| Sibling (3rd+) | 25% of tuition | Automatic |
| Staff | Varies | Manual tracking |
| Scholarship | Per case | Requires approval |

### 5.6 Payment Schedule

| Trimester | Period | Due Date | % of Total |
|-----------|--------|----------|------------|
| T1 | Sep - Dec | August 20 | 40% |
| T2 | Jan - Mar | January 1 | 30% |
| T3 | Apr - Jun | April 1 | 30% |

### 5.7 Calculations

#### Annual Revenue per Student
```python
def calculate_student_revenue(
    level_id: str,
    nationality: str,
    is_new_student: bool,
    sibling_rank: int,
    fee_matrix: dict,
    discount_rules: dict
) -> dict:
    """
    Calculate total annual revenue for a student.
    """
    # Get base fees
    tuition = fee_matrix[(level_id, nationality)]["annual_tuition"]
    dai = fee_matrix[(level_id, nationality)]["dai_fee"]
    
    # Apply sibling discount (3rd child+)
    tuition_discount = 0
    if sibling_rank >= 3:
        tuition_discount = tuition * discount_rules["sibling_pct"]  # 25%
    
    net_tuition = tuition - tuition_discount
    
    # Add registration fees for new students
    registration = 0
    first_enrollment = 0
    if is_new_student:
        registration = fee_matrix[(level_id, nationality)]["registration_fee"]
        first_enrollment = fee_matrix[(level_id, nationality)]["first_enrollment_fee"]
    
    total_revenue = net_tuition + dai + registration + first_enrollment
    
    return {
        "gross_tuition": tuition,
        "tuition_discount": tuition_discount,
        "net_tuition": net_tuition,
        "dai": dai,
        "registration": registration,
        "first_enrollment": first_enrollment,
        "total_annual_revenue": total_revenue
    }
```

### 5.8 Outputs

| Output | Consumers | Description |
|--------|-----------|-------------|
| `fee_matrix` | Revenue Planning | Complete fee structure |
| `discount_rules` | Revenue Planning | Discount configurations |
| `payment_schedule` | Cash Flow | Timing of payments |

---

## Module 6: Timetable Constraints

### 6.1 Purpose
Define scheduling rules that impact peak teacher demand and workforce requirements.

### 6.2 Inputs

| Input | Data Type | Description |
|-------|-----------|-------------|
| `constraint_type` | Enum | Schedule / Subject / Resource / Teacher |
| `constraint_name` | String | Descriptive name |
| `applies_to` | String | Levels/subjects affected |
| `rule_definition` | JSON | Detailed parameters |
| `is_mandatory` | Boolean | Hard constraint vs preference |
| `priority` | Integer | Conflict resolution order |

### 6.3 Key Constraints

| Constraint | Type | Rule | Impact |
|------------|------|------|--------|
| Parallel Classes | Schedule | Same level taught simultaneously | Increases peak demand |
| Wednesday PM Off | Teacher | AEFE contract requirement | Reduces available slots |
| Block Scheduling | Subject | Sciences need 2-hour blocks | Affects room allocation |
| Lab Capacity | Resource | Max simultaneous lab classes | Limits parallel science |
| Morning Preference | Subject | Core subjects before 12:00 | Concentrates demand |
| Max Consecutive | Teacher | 3 hours max without break | Affects scheduling |

### 6.4 School Day Structure (EFIR)

| Slot | Time | Duration | Notes |
|------|------|----------|-------|
| S1 | 7:30 - 8:30 | 1h | Morning 1 |
| S2 | 8:30 - 9:30 | 1h | Morning 2 |
| Break | 9:30 - 9:45 | 15m | - |
| S3 | 9:45 - 10:45 | 1h | Morning 3 |
| S4 | 10:45 - 11:45 | 1h | Morning 4 |
| Lunch | 11:45 - 12:30 | 45m | - |
| S5 | 12:30 - 13:30 | 1h | Afternoon 1 |
| S6 | 13:30 - 14:30 | 1h | Afternoon 2 |

### 6.5 Calculations

#### Peak Demand Factor
```python
def calculate_peak_demand_factor(
    num_classes_per_level: dict,
    parallel_class_enabled: bool
) -> float:
    """
    Calculate the multiplier for peak teacher demand.
    
    When parallel classes are enabled, all classes at the same level
    need the same subject taught simultaneously.
    """
    if not parallel_class_enabled:
        return 1.0
    
    # Peak demand = max classes at any single level
    max_parallel_classes = max(num_classes_per_level.values())
    
    # This affects staffing: need enough teachers for peak slot
    return max_parallel_classes
```

### 6.6 Outputs

| Output | Consumers | Description |
|--------|-----------|-------------|
| `peak_demand_factor` | Workforce Planning | Teacher requirement multiplier |
| `available_slots` | Scheduling | Weekly teaching slots |
| `room_constraints` | Facility Planning | Simultaneous usage limits |

---

## Module 7: Enrollment Planning

### 7.1 Purpose
Project student enrollment by level and nationality, driving revenue and class structure calculations.

### 7.2 Inputs

| Input | Data Type | Source | Description |
|-------|-----------|--------|-------------|
| `budget_period_id` | UUID | System | Reference to budget period |
| `academic_period_id` | UUID | System | Period 1 or Period 2 |
| `level_id` | UUID | Reference | Academic level |
| `nationality_category` | Enum | Manual | French / Saudi / Other |
| `month` | Integer | Manual | Month of projection (1-12) |
| `projected_count` | Integer | Manual | Total students projected |
| `new_students` | Integer | Manual | New enrollments |
| `returning_students` | Integer | Calculated | Re-enrollments |

### 7.3 Historical Enrollment Data

| Academic Year | Maternelle | Élémentaire | Collège | Lycée | Total | Growth |
|---------------|------------|-------------|---------|-------|-------|--------|
| 2021-2022 | 251 | 556 | 389 | 238 | 1,434 | -6.4% |
| 2022-2023 | 267 | 574 | 413 | 245 | 1,499 | +4.8% |
| 2023-2024 | 249 | 607 | 450 | 281 | 1,587 | +5.9% |
| 2024-2025 | 280 | 650 | 510 | 356 | 1,796 | +13.2% |

### 7.4 Nationality Distribution (2023-2024)

| Category | Students | Percentage |
|----------|----------|------------|
| French | 503 | 31.7% |
| Saudi | 60 | 3.8% |
| Other | 1,024 | 64.5% |

### 7.5 Calculations

#### Class Structure from Enrollment
```python
def calculate_class_structure(
    enrollment_by_level: dict,
    class_size_params: dict
) -> dict:
    """
    Calculate number of classes and average size per level.
    
    Returns: {level_id: {num_classes, avg_size, atsem_needed}}
    """
    class_structure = {}
    
    for level_id, enrollment in enrollment_by_level.items():
        params = class_size_params[level_id]
        
        # Calculate classes needed
        num_classes = calculate_classes(
            enrollment, 
            params["target_size"],
            params["max_size"]
        )
        
        avg_size = enrollment / num_classes if num_classes > 0 else 0
        
        # ATSEM for Maternelle
        atsem_needed = 0
        if params.get("atsem_required", False):
            atsem_needed = calculate_atsem(num_classes, params["atsem_ratio"])
        
        class_structure[level_id] = {
            "enrollment": enrollment,
            "num_classes": num_classes,
            "avg_size": round(avg_size, 1),
            "atsem_needed": atsem_needed
        }
    
    return class_structure
```

#### Re-enrollment Rate
```python
def calculate_reenrollment_rate(
    prior_year_enrollment: int,
    returning_students: int
) -> float:
    """
    Calculate re-enrollment rate for planning.
    """
    if prior_year_enrollment == 0:
        return 0.0
    return returning_students / prior_year_enrollment
```

### 7.6 Outputs

| Output | Consumers | Description |
|--------|-----------|-------------|
| `enrollment_by_level` | Revenue, Workforce, Facility | Student counts |
| `enrollment_by_nationality` | Revenue Planning | Nationality breakdown |
| `class_structure` | Workforce Planning | Classes per level |
| `new_vs_returning` | Revenue Planning | Fee calculation basis |

### 7.7 Business Rules

1. Projections required for both Period 1 and Period 2
2. Total enrollment cannot exceed maximum capacity (~1,875)
3. Enrollment changes trigger class structure recalculation
4. Historical re-enrollment rates inform projections

---

## Module 8: Teacher Workforce Planning (DHG)

### 8.1 Purpose
Calculate teacher requirements using DHG (Dotation Horaire Globale) methodology, managing AEFE and local positions.

### 8.2 Inputs

| Input | Source Module | Description |
|-------|---------------|-------------|
| `class_structure` | Enrollment Planning | Classes per level |
| `subject_hours_matrix` | Subject Hours | Hours per subject/level |
| `class_size_params` | Class Size Parameters | ATSEM requirements |
| `teacher_cost_params` | Teacher Cost | Salary scales |
| `timetable_constraints` | Timetable Constraints | Peak demand factors |
| `aefe_positions` | Manual | AEFE allocation (28 total) |

### 8.3 AEFE Position Structure

| Category | Count | Cost Bearer | School Contribution |
|----------|-------|-------------|---------------------|
| Détachés (Residents) | 24 | School (PRRD) | ~41,863 EUR/teacher |
| Funded by AEFE | 4 | AEFE | None |
| **Total AEFE** | **28** | - | - |

### 8.4 Calculations

#### Primary Workforce (Class-Based Model)
```python
def calculate_primary_workforce(
    class_structure: dict,
    primary_levels: list,
    specialist_ratio: float = 0.35
) -> dict:
    """
    Calculate primary teacher requirements.
    
    Primary model: 1 generalist teacher per class + specialists for 
    languages, PE, arts (approximately 30-40% additional)
    """
    total_classes = sum(
        class_structure[level]["num_classes"] 
        for level in primary_levels
    )
    
    # Generalist teachers (1 per class)
    generalist_fte = total_classes
    
    # Specialists (languages, PE, arts) ~35% additional
    specialist_fte = math.ceil(total_classes * specialist_ratio)
    
    # ATSEM for Maternelle
    atsem_fte = sum(
        class_structure[level]["atsem_needed"]
        for level in primary_levels
        if level.startswith("PS") or level.startswith("MS") or level.startswith("GS")
    )
    
    return {
        "generalist_fte": generalist_fte,
        "specialist_fte": specialist_fte,
        "atsem_fte": atsem_fte,
        "total_teaching_fte": generalist_fte + specialist_fte
    }
```

#### Secondary Workforce (DHG Hours-Based Model)
```python
def calculate_secondary_workforce_dhg(
    class_structure: dict,
    subject_hours_matrix: dict,
    secondary_levels: list,
    standard_hours: int = 18,
    peak_demand_factor: float = 1.0
) -> dict:
    """
    Calculate secondary teacher requirements using DHG methodology.
    
    DHG Formula:
    - Total Hours = Σ(classes × hours_per_subject_per_level)
    - Simple FTE = Total Hours ÷ Standard Teaching Hours (18)
    - Adjusted FTE = Simple FTE × Peak Demand Factor
    """
    workforce_by_subject = {}
    
    for subject_id in subject_hours_matrix.keys():
        total_hours = 0
        
        for level in secondary_levels:
            num_classes = class_structure.get(level, {}).get("num_classes", 0)
            hours_per_week = subject_hours_matrix.get((subject_id, level), 0)
            total_hours += num_classes * hours_per_week
        
        # Simple FTE calculation
        simple_fte = total_hours / standard_hours
        
        # Apply peak demand factor for constraint adjustment
        adjusted_fte = simple_fte * peak_demand_factor
        
        workforce_by_subject[subject_id] = {
            "total_hours": total_hours,
            "simple_fte": round(simple_fte, 2),
            "adjusted_fte": math.ceil(adjusted_fte),
            "peak_factor": peak_demand_factor
        }
    
    return workforce_by_subject
```

#### DHG Summary (Example)
```python
def generate_dhg_summary(
    workforce_by_subject: dict
) -> dict:
    """
    Generate DHG summary report.
    """
    total_hours = sum(s["total_hours"] for s in workforce_by_subject.values())
    total_simple_fte = sum(s["simple_fte"] for s in workforce_by_subject.values())
    total_adjusted_fte = sum(s["adjusted_fte"] for s in workforce_by_subject.values())
    
    return {
        "subjects": workforce_by_subject,
        "total_hours": total_hours,
        "total_simple_fte": round(total_simple_fte, 1),
        "total_adjusted_fte": total_adjusted_fte
    }
```

### 8.5 Gap Analysis (TRMD)
```python
def calculate_staffing_gap(
    required_fte: dict,
    aefe_positions: dict,
    current_local_staff: dict
) -> dict:
    """
    Calculate staffing gap (TRMD - Tableau de Répartition des Moyens).
    
    Gap = Required FTE - AEFE Positions - Current Local Staff
    Positive gap = need to recruit or use overtime (HSA)
    """
    gap_analysis = {}
    
    for subject_id, required in required_fte.items():
        aefe = aefe_positions.get(subject_id, 0)
        local = current_local_staff.get(subject_id, 0)
        
        available = aefe + local
        gap = required["adjusted_fte"] - available
        
        # Determine how to fill gap
        hsa_possible = min(gap * 18, available * 4)  # Max 4 HSA per teacher
        recruitment_needed = max(0, gap - (hsa_possible / 18))
        
        gap_analysis[subject_id] = {
            "besoins": required["adjusted_fte"],  # Needs
            "hp_aefe": aefe,  # AEFE hours/positions
            "hp_local": local,  # Local hours/positions
            "deficit": gap,
            "hsa_proposed": hsa_possible,
            "recruitment_needed": math.ceil(recruitment_needed)
        }
    
    return gap_analysis
```

### 8.6 Outputs

| Output | Consumers | Description |
|--------|-----------|-------------|
| `primary_workforce` | Cost Planning | Primary FTE requirements |
| `secondary_workforce_dhg` | Cost Planning | Secondary FTE by subject |
| `atsem_requirements` | Cost Planning | Support staff needs |
| `gap_analysis` | HR, Cost Planning | TRMD deficit report |
| `hsa_allocation` | Cost Planning | Overtime distribution |

### 8.7 H/E Ratio Reference (AEFE Benchmark)

| Students/Class | H/E Collège | H/E Lycée |
|----------------|-------------|-----------|
| 20 | 1.71 | 1.97 |
| 24 | 1.46 | 1.68 |
| 26 | 1.27 | 1.40 |
| 28 | 1.38 | 1.46 |

---

## Module 9: Facility Planning

### 9.1 Purpose
Track facility inventory and utilization to inform CapEx decisions.

### 9.2 Inputs

| Input | Data Type | Description |
|-------|-----------|-------------|
| `facility_id` | UUID | Unique identifier |
| `facility_name` | String | Room or facility name |
| `facility_type` | Enum | Classroom / Lab / Sports / Arts / Admin |
| `capacity` | Integer | Maximum occupancy |
| `building` | String | Building location |
| `equipment` | JSON | Equipment list |
| `operating_cost_monthly` | Decimal | Monthly cost in SAR |

### 9.3 Calculations

#### Classroom Requirement
```python
def calculate_classroom_requirement(
    class_structure: dict
) -> int:
    """
    Classroom requirement = Total number of classes.
    """
    return sum(level["num_classes"] for level in class_structure.values())
```

#### Utilization Rate
```python
def calculate_utilization(
    hours_used: float,
    hours_available: float
) -> float:
    """
    Utilization = Hours Used / Hours Available
    Target: 70-85%
    """
    if hours_available == 0:
        return 0.0
    return hours_used / hours_available
```

### 9.4 Outputs

| Output | Consumers | Description |
|--------|-----------|-------------|
| `facility_inventory` | CapEx Planning | Current facilities |
| `capacity_gap` | CapEx Planning | Additional needs |
| `utilization_rates` | KPIs | Efficiency metrics |
| `operating_costs` | Cost Planning | Facility costs |

---

## Module 10: Revenue Planning

### 10.1 Purpose
Calculate projected revenue from all sources based on enrollment and fee structure.

### 10.2 Inputs

| Input | Source Module | Description |
|-------|---------------|-------------|
| `enrollment_data` | Enrollment Planning | Students by level/nationality |
| `fee_matrix` | Fee Structure | Fees by level/nationality |
| `discount_rules` | Fee Structure | Sibling and other discounts |
| `payment_schedule` | Fee Structure | Timing of payments |
| `new_vs_returning` | Enrollment Planning | For registration fees |

### 10.3 Revenue Categories

| Category | Source | Calculation Method |
|----------|--------|-------------------|
| Tuition | Enrollment × Fees | Automatic |
| DAI | Enrollment × DAI Rate | Automatic |
| Registration | New Students × Fee | Automatic |
| First Enrollment | New Students × Fee | Automatic |
| Exam Fees | Specific Levels × Fee | Automatic |
| Garderie | Estimate | Manual/Estimate |
| Grants/AEFE | AEFE Allocation | Manual |
| Other Income | Various | Manual |

### 10.4 Calculations

#### Gross Tuition Revenue
```python
def calculate_gross_tuition_revenue(
    enrollment_by_level_nationality: dict,
    fee_matrix: dict
) -> dict:
    """
    Calculate gross tuition revenue before discounts.
    """
    revenue = {}
    total = 0
    
    for (level_id, nationality), count in enrollment_by_level_nationality.items():
        fee = fee_matrix[(level_id, nationality)]["annual_tuition"]
        level_revenue = count * fee
        revenue[(level_id, nationality)] = level_revenue
        total += level_revenue
    
    return {"by_segment": revenue, "total": total}
```

#### Sibling Discounts
```python
def calculate_sibling_discounts(
    families: list,
    fee_matrix: dict,
    discount_pct: float = 0.25
) -> float:
    """
    Calculate total sibling discounts (3rd child and beyond).
    """
    total_discount = 0
    
    for family in families:
        # Sort children by enrollment order (oldest first)
        children = sorted(family["children"], key=lambda x: x["enrollment_date"])
        
        for i, child in enumerate(children):
            if i >= 2:  # 3rd child onwards
                tuition = fee_matrix[(child["level"], child["nationality"])]["annual_tuition"]
                total_discount += tuition * discount_pct
    
    return total_discount
```

#### Monthly Revenue Distribution
```python
def distribute_revenue_monthly(
    annual_revenue: float,
    payment_schedule: dict
) -> dict:
    """
    Distribute annual revenue across months based on payment schedule.
    
    Default: T1=40%, T2=30%, T3=30%
    """
    monthly = {}
    
    # T1: September - December (40%)
    t1_monthly = annual_revenue * 0.40 / 4
    for month in [9, 10, 11, 12]:
        monthly[month] = t1_monthly
    
    # T2: January - March (30%)
    t2_monthly = annual_revenue * 0.30 / 3
    for month in [1, 2, 3]:
        monthly[month] = t2_monthly
    
    # T3: April - June (30%)
    t3_monthly = annual_revenue * 0.30 / 3
    for month in [4, 5, 6]:
        monthly[month] = t3_monthly
    
    # Summer: July - August (minimal)
    monthly[7] = 0
    monthly[8] = 0
    
    return monthly
```

### 10.5 Revenue Summary (Budget 2024 Reference)

| Category | Amount (SAR) | % of Total |
|----------|--------------|------------|
| Tuition Revenue | ~60,000,000 | 88.9% |
| Registration/DAI | ~5,000,000 | 7.4% |
| Exam Fees | ~500,000 | 0.7% |
| Other Income | ~2,000,000 | 3.0% |
| **Total Revenue** | **67,516,928** | **100%** |

### 10.6 Outputs

| Output | Consumers | Description |
|--------|-----------|-------------|
| `revenue_by_category` | Budget Consolidation | Revenue breakdown |
| `revenue_by_month` | Cash Flow | Monthly distribution |
| `net_tuition` | Financial Statements | After discounts |
| `revenue_by_period` | Budget Consolidation | Period 1 vs Period 2 |

---

## Module 11: Cost Planning

### 11.1 Purpose
Consolidate all operating costs using driver-based calculations and direct inputs.

### 11.2 Inputs

| Input | Source Module | Description |
|-------|---------------|-------------|
| `workforce_costs` | Workforce Planning | Personnel costs |
| `facility_costs` | Facility Planning | Operating costs |
| `driver_values` | Various | Enrollment, headcount, etc. |
| `cost_rates` | Configuration | Rate per driver unit |
| `direct_costs` | Manual | Non-driver costs |

### 11.3 Cost Categories

| Category | Driver | Calculation |
|----------|--------|-------------|
| Teaching Staff (Local) | FTE × Salary | Automatic |
| Teaching Staff (AEFE) | Positions × PRRD | Automatic |
| ATSEM | FTE × Salary | Automatic |
| Administrative Staff | Headcount × Salary | Semi-automatic |
| AEFE Licensing | Fixed annual | Manual |
| Rent | Fixed annual | Manual |
| Utilities | Historical pattern | Driver-based |
| Maintenance | Square meters × Rate | Driver-based |
| Educational Supplies | Enrollment × Rate | Driver-based |
| Depreciation | Asset register | Automatic |

### 11.4 Calculations

#### Personnel Costs
```python
def calculate_personnel_costs(
    workforce_plan: dict,
    teacher_cost_params: dict,
    exchange_rate: float
) -> dict:
    """
    Calculate total personnel costs from workforce planning.
    """
    costs = {
        "local_teaching": 0,
        "aefe_prrd": 0,
        "atsem": 0,
        "administrative": 0,
        "hsa_overtime": 0
    }
    
    # Local teaching staff
    for position_type, count in workforce_plan["local_teachers"].items():
        cost_per = teacher_cost_params["local"][position_type]["total_annual_cost"]
        costs["local_teaching"] += count * cost_per
    
    # AEFE teachers (school-paid PRRD)
    aefe_detached = workforce_plan["aefe_positions"]["detached"]
    prrd_per_teacher_sar = teacher_cost_params["aefe"]["prrd_contribution"] * exchange_rate
    costs["aefe_prrd"] = aefe_detached * prrd_per_teacher_sar
    
    # ATSEM
    atsem_count = workforce_plan["atsem_fte"]
    atsem_cost_per = teacher_cost_params["local"]["atsem"]["total_annual_cost"]
    costs["atsem"] = atsem_count * atsem_cost_per
    
    # HSA (overtime)
    hsa_hours = workforce_plan["total_hsa_hours"]
    hsa_rate = teacher_cost_params["local"]["hsa_rate"]
    costs["hsa_overtime"] = hsa_hours * hsa_rate
    
    return costs
```

#### Driver-Based Operating Costs
```python
def calculate_driver_costs(
    drivers: dict,
    cost_rates: dict
) -> dict:
    """
    Calculate costs using driver formulas.
    
    Cost = Driver Value × Rate
    """
    costs = {}
    
    # Educational supplies: Enrollment × Rate per student
    costs["educational_supplies"] = (
        drivers["total_enrollment"] * cost_rates["supplies_per_student"]
    )
    
    # Maintenance: Square meters × Rate
    costs["maintenance"] = (
        drivers["total_sqm"] * cost_rates["maintenance_per_sqm"]
    )
    
    # Utilities: Historical pattern with inflation
    costs["utilities"] = (
        drivers["prior_year_utilities"] * (1 + cost_rates["utility_inflation"])
    )
    
    return costs
```

### 11.5 Cost Summary (Budget 2024 Reference)

| Category | Amount (SAR) | % of Revenue |
|----------|--------------|--------------|
| Teaching Staff (Local) | 16,355,839 | 24.2% |
| Administrative Staff | 5,272,255 | 7.8% |
| AEFE Contribution (PRRD) | 7,080,587 | 10.5% |
| AEFE Licensing | 4,005,266 | 5.9% |
| Other Personnel | 2,799,542 | 4.1% |
| **Subtotal Personnel** | **35,513,489** | **52.6%** |
| Rent | 8,395,518 | 12.4% |
| Utilities | 1,000,000 | 1.5% |
| Maintenance | 4,723,852 | 7.0% |
| **Subtotal Occupancy** | **14,119,370** | **20.9%** |
| Educational Supplies | 1,856,057 | 2.7% |
| Administrative | 4,455,047 | 6.6% |
| Marketing | 30,000 | 0.0% |
| Depreciation | 5,093,865 | 7.5% |
| **Total Expenses** | **61,067,828** | **90.4%** |

### 11.6 Outputs

| Output | Consumers | Description |
|--------|-----------|-------------|
| `personnel_costs` | Budget Consolidation | Staff costs breakdown |
| `operating_costs` | Budget Consolidation | Non-personnel costs |
| `costs_by_account` | Financial Statements | Chart of accounts mapping |
| `costs_by_cost_center` | Reporting | Departmental breakdown |
| `costs_by_month` | Cash Flow | Monthly distribution |

---

## Module 12: CapEx Planning

### 12.1 Purpose
Manage capital investments, depreciation, and multi-year asset planning.

### 12.2 Inputs

| Input | Data Type | Description |
|-------|-----------|-------------|
| `project_name` | String | Investment project name |
| `asset_category` | Enum | Building / Equipment / IT / Vehicles / Furniture |
| `total_investment` | Decimal | Total project cost in SAR |
| `useful_life_years` | Integer | Depreciation period |
| `depreciation_method` | Enum | Straight-line / Declining balance |
| `disbursement_schedule` | JSON | Monthly cash outflow schedule |
| `in_service_date` | Date | When asset becomes operational |

### 12.3 Asset Categories

| Category | Useful Life | Depreciation Method |
|----------|-------------|---------------------|
| Building Improvements | 10-20 years | Straight-line |
| IT Equipment | 3-5 years | Straight-line |
| Furniture | 7-10 years | Straight-line |
| Educational Equipment | 5-7 years | Straight-line |
| Vehicles | 5 years | Straight-line |

### 12.4 Calculations

#### Straight-Line Depreciation
```python
def calculate_depreciation(
    asset_value: float,
    useful_life_years: int,
    in_service_date: date,
    calculation_year: int
) -> dict:
    """
    Calculate annual depreciation using straight-line method.
    
    Depreciation begins in month following in-service date.
    """
    annual_depreciation = asset_value / useful_life_years
    monthly_depreciation = annual_depreciation / 12
    
    # Calculate months of depreciation in calculation year
    if calculation_year < in_service_date.year:
        months_in_year = 0
    elif calculation_year == in_service_date.year:
        # Start month after in-service
        months_in_year = 12 - in_service_date.month
    else:
        months_in_year = 12
    
    depreciation_this_year = monthly_depreciation * months_in_year
    
    return {
        "annual_depreciation": annual_depreciation,
        "monthly_depreciation": monthly_depreciation,
        "depreciation_this_year": depreciation_this_year,
        "remaining_life_years": max(0, useful_life_years - 
            (calculation_year - in_service_date.year))
    }
```

### 12.5 Outputs

| Output | Consumers | Description |
|--------|-----------|-------------|
| `capex_by_category` | Financial Statements | Investment breakdown |
| `disbursement_schedule` | Cash Flow | Monthly cash requirements |
| `depreciation_schedule` | Cost Planning | Annual depreciation |
| `asset_register` | Balance Sheet | Asset inventory |

---

## Module 13: Budget Consolidation

### 13.1 Purpose
Bring together all budget components, manage versions, and support approval workflow.

### 13.2 Inputs

| Input | Source Module | Description |
|-------|---------------|-------------|
| `revenue_data` | Revenue Planning | All revenue lines |
| `cost_data` | Cost Planning | All cost lines |
| `capex_data` | CapEx Planning | Capital investments |
| `top_down_targets` | Board/Management | Target envelopes |

### 13.3 Consolidation Structure

```
Budget Version
├── Revenue
│   ├── Tuition
│   ├── Registration/DAI
│   ├── Other Income
│   └── Grants
├── Operating Costs
│   ├── Personnel
│   │   ├── Teaching (Local)
│   │   ├── Teaching (AEFE)
│   │   ├── Administrative
│   │   └── Support Staff
│   ├── Occupancy
│   │   ├── Rent
│   │   ├── Utilities
│   │   └── Maintenance
│   ├── Educational
│   └── Administrative
├── Depreciation
├── CapEx (Cash Flow)
└── Net Result
```

### 13.4 Calculations

#### Operating Surplus
```python
def calculate_operating_surplus(
    total_revenue: float,
    total_operating_costs: float,
    depreciation: float
) -> dict:
    """
    Calculate operating result and key margins.
    """
    ebitda = total_revenue - (total_operating_costs - depreciation)
    operating_result = total_revenue - total_operating_costs
    
    return {
        "total_revenue": total_revenue,
        "total_costs": total_operating_costs,
        "ebitda": ebitda,
        "ebitda_margin_pct": (ebitda / total_revenue) * 100,
        "operating_result": operating_result,
        "operating_margin_pct": (operating_result / total_revenue) * 100
    }
```

#### Top-Down vs Bottom-Up Variance
```python
def calculate_budget_variance(
    top_down_targets: dict,
    bottom_up_actuals: dict
) -> dict:
    """
    Compare top-down targets with bottom-up detailed budget.
    """
    variances = {}
    
    for category in top_down_targets.keys():
        target = top_down_targets[category]
        actual = bottom_up_actuals.get(category, 0)
        variance = actual - target
        variance_pct = (variance / target * 100) if target != 0 else 0
        
        variances[category] = {
            "target": target,
            "actual": actual,
            "variance": variance,
            "variance_pct": variance_pct,
            "status": "favorable" if variance <= 0 else "unfavorable"
        }
    
    return variances
```

### 13.5 Budget Versions

| Version Type | Description | Editable |
|--------------|-------------|----------|
| Working | Active development | Yes |
| Submitted | Pending approval | No |
| Approved | Board approved | No |
| Forecast | Revised projection | Yes |
| Superseded | Historical versions | No |

### 13.6 Outputs

| Output | Consumers | Description |
|--------|-----------|-------------|
| `consolidated_budget` | Financial Statements | Complete budget |
| `variance_report` | Reporting | Target vs actual |
| `approval_status` | Workflow | Approval progress |
| `version_history` | Audit | Historical versions |

---

## Module 14: Financial Statements

### 14.1 Purpose
Generate French PCG and IFRS-compliant financial projections.

### 14.2 Statement Types

| Statement | Format | Content |
|-----------|--------|---------|
| Income Statement (P&L) | Monthly/Annual | Revenue, Expenses, Net Result |
| Balance Sheet | Period End | Assets, Liabilities, Equity |
| Cash Flow Statement | Monthly | Operating, Investing, Financing |

### 14.3 Income Statement Structure (French PCG)

```
PRODUITS (REVENUE)
├── 70 - Ventes et prestations de services
│   ├── 70110 - Scolarité T1
│   ├── 70120 - Scolarité T2
│   ├── 70130 - Scolarité T3
│   └── 70140 - Droits d'inscription
├── 74 - Subventions
├── 77 - Produits financiers
└── TOTAL PRODUITS

CHARGES (EXPENSES)
├── 60 - Achats
├── 61 - Services extérieurs
│   ├── 61310 - Loyer
│   ├── 61510 - Maintenance
│   └── 606 - Utilities
├── 64 - Charges de personnel
│   ├── 64110 - Salaires enseignement
│   ├── 64140 - Administration
│   └── 64800 - AEFE contributions
├── 68 - Dotations amortissements
└── TOTAL CHARGES

RÉSULTAT NET
```

### 14.4 Calculations

#### Cash Flow - Indirect Method
```python
def calculate_cash_flow_operating(
    net_income: float,
    depreciation: float,
    working_capital_changes: dict
) -> float:
    """
    Calculate cash from operating activities using indirect method.
    """
    # Start with net income
    cash_from_operations = net_income
    
    # Add back non-cash expenses
    cash_from_operations += depreciation
    
    # Adjust for working capital changes
    # Increase in receivables = cash outflow
    cash_from_operations -= working_capital_changes.get("receivables_increase", 0)
    # Increase in payables = cash inflow
    cash_from_operations += working_capital_changes.get("payables_increase", 0)
    
    return cash_from_operations
```

### 14.5 Outputs

| Output | Format | Description |
|--------|--------|-------------|
| `income_statement` | PDF/Excel | P&L by month/year |
| `balance_sheet` | PDF/Excel | Period-end position |
| `cash_flow` | PDF/Excel | Cash movements |
| `ifrs_mapping` | Export | IFRS translation |

---

## Module 15: Statistical Analysis (KPIs)

### 15.1 Purpose
Provide key performance indicators for educational and financial management.

### 15.2 Educational KPIs

| KPI | Formula | Target | Unit |
|-----|---------|--------|------|
| Student/Teacher Ratio | Total Students ÷ Teaching FTE | 8-12 | ratio |
| Average Class Size | Total Students ÷ Total Classes | 20-26 | students |
| Teacher Utilization | Actual Hours ÷ Standard Hours | 85-95% | % |
| AEFE Teacher % | AEFE FTE ÷ Total Teaching FTE | varies | % |

### 15.3 Financial KPIs

| KPI | Formula | Target | Unit |
|-----|---------|--------|------|
| Staff Cost Ratio | Personnel Costs ÷ Revenue | 60-75% | % |
| Revenue per Student | Total Revenue ÷ Total Students | varies | SAR |
| Cost per Student | Total Costs ÷ Total Students | varies | SAR |
| Operating Margin | Operating Result ÷ Revenue | 5-10% | % |
| Rent Ratio | Rent ÷ Revenue | 8-15% | % |

### 15.4 Calculations

```python
def calculate_kpis(
    financial_data: dict,
    operational_data: dict
) -> dict:
    """
    Calculate all standard KPIs.
    """
    kpis = {}
    
    # Educational
    kpis["student_teacher_ratio"] = (
        operational_data["total_students"] / 
        operational_data["teaching_fte"]
    )
    
    kpis["avg_class_size"] = (
        operational_data["total_students"] / 
        operational_data["total_classes"]
    )
    
    # Financial
    kpis["staff_cost_ratio"] = (
        financial_data["total_personnel_costs"] / 
        financial_data["total_revenue"] * 100
    )
    
    kpis["revenue_per_student"] = (
        financial_data["total_revenue"] / 
        operational_data["total_students"]
    )
    
    kpis["operating_margin"] = (
        financial_data["operating_result"] / 
        financial_data["total_revenue"] * 100
    )
    
    return kpis
```

### 15.5 EFIR Reference KPIs (2024)

| Ratio | EFIR 2024 | AEFE Benchmark |
|-------|-----------|----------------|
| Staff Costs / Revenue | 52.6% | 60-75% |
| Teaching Staff / Total | 46.0% | 55-65% |
| Rent / Revenue | 12.4% | 8-15% |
| Operating Margin | 9.6% | 5-10% |
| Revenue per Student | ~42,500 SAR | Varies |
| Students per Teacher | ~7.6 | 8-12 |
| Average Class Size | 21-25 | 20-26 |

### 15.6 Outputs

| Output | Consumers | Description |
|--------|-----------|-------------|
| `kpi_dashboard` | Management | Real-time KPIs |
| `trend_analysis` | Reporting | Multi-year trends |
| `benchmark_comparison` | Strategy | vs. AEFE norms |
| `alerts` | Management | Threshold breaches |

---

## Module 16: Dashboards & Reporting

### 16.1 Purpose
Provide role-based views and reporting capabilities.

### 16.2 Dashboard Types

| Dashboard | Audience | Key Metrics |
|-----------|----------|-------------|
| Executive | Board | Net result, KPIs, approval status |
| Finance Manager | DAF/CFO | Detailed variance, cash flow |
| Department | Cost center heads | Budget vs actual by line |
| Operations | School Director | Enrollment, staffing |

### 16.3 Standard Reports

| Report | Frequency | Format |
|--------|-----------|--------|
| Monthly Budget Summary | Monthly | PDF/Excel |
| Variance Analysis | Monthly | PDF/Excel |
| Cash Flow Forecast | Weekly/Monthly | PDF/Excel |
| Board Pack | Quarterly | PDF/PowerPoint |
| AEFE Reporting | Per requirements | Specific format |

### 16.4 Export Capabilities

- PDF for formal reports
- Excel for data analysis
- PowerPoint for presentations
- CSV for data exchange

---

## Module 17: Budget vs Actual Analysis

### 17.1 Purpose
Monitor actual performance against budget and support forecast revisions.

### 17.2 Inputs

| Input | Source | Description |
|-------|--------|-------------|
| `budget_data` | Budget Consolidation | Approved budget |
| `actual_data` | Accounting System (Odoo) | GL transactions |
| `period` | System | Month/Year |

### 17.3 Variance Analysis

```python
def calculate_variance(
    budget: float,
    actual: float,
    is_expense: bool = True
) -> dict:
    """
    Calculate variance and determine favorability.
    
    For expenses: positive variance (under budget) = favorable
    For revenue: positive variance (over budget) = favorable
    """
    variance = budget - actual
    variance_pct = (variance / budget * 100) if budget != 0 else 0
    
    if is_expense:
        favorable = variance > 0  # Under budget
    else:
        favorable = variance < 0  # Over budget (more revenue)
    
    return {
        "budget": budget,
        "actual": actual,
        "variance": variance,
        "variance_pct": variance_pct,
        "status": "favorable" if favorable else "unfavorable"
    }
```

### 17.4 Forecast Revision

```python
def revise_forecast(
    original_budget: dict,
    ytd_actuals: dict,
    remaining_months: int,
    trend_factor: float = 1.0
) -> dict:
    """
    Create revised forecast based on YTD performance.
    
    Forecast = YTD Actual + (Remaining Budget × Trend Factor)
    """
    revised = {}
    
    for account, budget in original_budget.items():
        ytd_actual = ytd_actuals.get(account, 0)
        remaining_budget = budget - ytd_actual
        
        # Apply trend factor for remaining months
        revised_remaining = remaining_budget * trend_factor
        revised[account] = ytd_actual + revised_remaining
    
    return revised
```

### 17.5 Outputs

| Output | Consumers | Description |
|--------|-----------|-------------|
| `variance_report` | Management | MTD and YTD variances |
| `revised_forecast` | Budget Consolidation | Updated projections |
| `explanation_log` | Audit | Variance explanations |

---

## Module 18: 5-Year Strategic Plan

### 18.1 Purpose
Extend annual budgeting to multi-year strategic planning.

### 18.2 Inputs

| Input | Source | Description |
|-------|--------|-------------|
| `base_year_budget` | Budget Consolidation | Year 1 foundation |
| `enrollment_projections` | Strategic Planning | 5-year enrollment forecast |
| `fee_increase_rates` | Board Decisions | Annual fee adjustments |
| `salary_inflation` | HR Planning | Compensation growth |
| `capex_plan` | Strategic Planning | Multi-year investments |
| `strategic_initiatives` | Management | New programs, expansion |

### 18.3 Projection Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| Enrollment Growth | Annual % increase | 3-5% |
| Fee Increase | Annual tuition adjustment | 3-5% |
| Salary Inflation | Staff cost increase | 3-4% |
| Operating Cost Inflation | Non-personnel costs | 2-3% |
| Exchange Rate | SAR/EUR projection | Current |

### 18.4 Calculations

#### 5-Year Revenue Projection
```python
def project_revenue_5year(
    base_year_revenue: float,
    enrollment_growth_rates: list,  # [Y2, Y3, Y4, Y5]
    fee_increase_rates: list        # [Y2, Y3, Y4, Y5]
) -> list:
    """
    Project revenue for 5 years.
    
    Revenue_n = Revenue_(n-1) × (1 + enrollment_growth) × (1 + fee_increase)
    """
    projections = [base_year_revenue]
    
    for i in range(4):
        enrollment_factor = 1 + enrollment_growth_rates[i]
        fee_factor = 1 + fee_increase_rates[i]
        next_year = projections[-1] * enrollment_factor * fee_factor
        projections.append(next_year)
    
    return projections
```

#### 5-Year Cost Projection
```python
def project_costs_5year(
    base_year_costs: dict,
    salary_inflation: float,
    operating_inflation: float,
    workforce_changes: list  # FTE changes by year
) -> list:
    """
    Project costs for 5 years by category.
    """
    projections = [base_year_costs]
    
    for year in range(1, 5):
        year_costs = {}
        prior = projections[-1]
        
        # Personnel costs: salary inflation + workforce changes
        year_costs["personnel"] = (
            prior["personnel"] * (1 + salary_inflation) *
            (1 + workforce_changes[year-1])
        )
        
        # Operating costs: general inflation
        year_costs["operating"] = prior["operating"] * (1 + operating_inflation)
        
        # Depreciation: from CapEx plan
        year_costs["depreciation"] = calculate_depreciation_for_year(year)
        
        projections.append(year_costs)
    
    return projections
```

### 18.5 Strategic Scenarios

| Scenario | Description | Parameters |
|----------|-------------|------------|
| Base Case | Current trajectory | 3% growth, 4% fee increase |
| Conservative | Slower growth | 1% growth, 2% fee increase |
| Optimistic | Expansion | 5% growth, 5% fee increase |
| New Campus | Major investment | Includes new facility |

### 18.6 Outputs

| Output | Consumers | Description |
|--------|-----------|-------------|
| `5year_revenue_plan` | Board | Revenue trajectory |
| `5year_cost_plan` | Board | Cost projections |
| `5year_capex_plan` | Board | Investment schedule |
| `5year_cash_projection` | Finance | Funding requirements |
| `scenario_comparison` | Strategy | Multiple scenarios |

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CONFIGURATION LAYER                                │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │   System     │ │  Class Size  │ │Subject Hours │ │Teacher Costs │        │
│  │   Config     │ │  Parameters  │ │   Matrix     │ │  Parameters  │        │
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘        │
│  ┌──────────────┐ ┌──────────────┐                                          │
│  │     Fee      │ │  Timetable   │                                          │
│  │  Structure   │ │ Constraints  │                                          │
│  └──────────────┘ └──────────────┘                                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            PLANNING LAYER                                    │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                     ENROLLMENT PLANNING                               │   │
│  │  Students by Level/Nationality → Class Structure                      │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│           │                           │                          │          │
│           ▼                           ▼                          ▼          │
│  ┌────────────────┐          ┌────────────────┐         ┌────────────────┐  │
│  │    REVENUE     │          │   WORKFORCE    │         │   FACILITY     │  │
│  │   PLANNING     │          │   PLANNING     │         │   PLANNING     │  │
│  │                │          │    (DHG)       │         │                │  │
│  │ Tuition × Fees │          │ Hours → FTE    │         │ Classes → Rooms│  │
│  └────────────────┘          └────────────────┘         └────────────────┘  │
│           │                           │                          │          │
│           │                           ▼                          │          │
│           │                  ┌────────────────┐                  │          │
│           │                  │     COST       │◄─────────────────┘          │
│           │                  │   PLANNING     │                             │
│           │                  │                │                             │
│           │                  │ Personnel +    │                             │
│           │                  │ Operating +    │◄──── ┌────────────────┐     │
│           │                  │ Driver Costs   │      │    CAPEX       │     │
│           │                  └────────────────┘      │   PLANNING     │     │
│           │                           │              │ Depreciation   │     │
│           │                           │              └────────────────┘     │
└───────────┼───────────────────────────┼──────────────────────┼──────────────┘
            │                           │                      │
            ▼                           ▼                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          CONSOLIDATION LAYER                                 │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                    BUDGET CONSOLIDATION                               │   │
│  │  Revenue + Costs + CapEx → Consolidated Budget                        │   │
│  │  Version Management, Approval Workflow                                │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                      │                                       │
│                                      ▼                                       │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                    FINANCIAL STATEMENTS                               │   │
│  │  Income Statement (P&L) │ Balance Sheet │ Cash Flow                   │   │
│  │  French PCG + IFRS Formats                                            │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ANALYSIS LAYER                                     │
│                                                                              │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐           │
│  │    STATISTICAL   │  │   DASHBOARDS &   │  │  BUDGET VS       │           │
│  │    ANALYSIS      │  │   REPORTING      │  │  ACTUAL          │           │
│  │    (KPIs)        │  │                  │  │                  │           │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          STRATEGIC LAYER                                     │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                      5-YEAR STRATEGIC PLAN                            │   │
│  │  Multi-year projections, scenarios, strategic initiatives             │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Technology Stack

### Frontend
| Component | Technology | Purpose |
|-----------|------------|---------|
| Framework | React 18+ with TypeScript | UI components |
| Styling | Tailwind CSS | Responsive design |
| Components | Shadcn/ui | Pre-built components |
| Spreadsheet | Handsontable | Grid-based data entry |
| Charts | Recharts | Visualizations |

### Backend
| Component | Technology | Purpose |
|-----------|------------|---------|
| API | Python FastAPI | REST endpoints |
| Calculation Engine | Python | DHG, cost calculations |
| Validation | Pydantic | Data validation |

### Database
| Component | Technology | Purpose |
|-----------|------------|---------|
| Database | Supabase (PostgreSQL) | Data storage |
| Security | Row Level Security | Access control |
| Real-time | Supabase Realtime | Auto-save, collaboration |
| Auth | Supabase Auth | User authentication |

### Integration
| System | Method | Purpose |
|--------|--------|---------|
| Odoo (Accounting) | API | Actuals import |
| Skolengo | Export/Import | Enrollment data |
| AEFE | Manual/Export | Position data |

---

## Implementation Phases

### Phase 1: Foundation (Weeks 1-4)
- System Configuration
- Class Size Parameters
- Subject Hours Configuration
- Database schema

### Phase 2: Core Planning (Weeks 5-10)
- Enrollment Planning
- Workforce Planning (DHG)
- Fee Structure
- Teacher Cost Parameters

### Phase 3: Financial (Weeks 11-16)
- Revenue Planning
- Cost Planning
- CapEx Planning
- Budget Consolidation

### Phase 4: Reporting (Weeks 17-22)
- Financial Statements
- KPIs and Statistical Analysis
- Dashboards

### Phase 5: Advanced (Weeks 23-28)
- Budget vs Actual
- Forecast Revision
- 5-Year Planning

### Phase 6: Integration & Go-Live (Weeks 29-30)
- System integration
- User training
- Go-live

---

## Appendix: Glossary

| Term | Definition |
|------|------------|
| AEFE | Agence pour l'enseignement français à l'étranger |
| ATSEM | Agent Territorial Spécialisé des Écoles Maternelles |
| DAI | Droit Annuel d'Inscription |
| DHG | Dotation Horaire Globale |
| FTE | Full-Time Equivalent |
| H/E | Heures/Élève (Hours per Student) |
| HP | Heures Postes |
| HSA | Heures Supplémentaires Annuelles |
| ISVL | Indemnité Spécifique de Vie Locale |
| PCG | Plan Comptable Général |
| PRRD | Participation à la Rémunération des Résidents Détachés |
| TRMD | Tableau de Répartition des Moyens par Discipline |

---

*Document prepared for development team*  
*Version 1.0 - November 2025*
