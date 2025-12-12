# EFIR Budget Planning Model - Formula Logic Documentation

## Executive Summary

This document provides comprehensive technical documentation of the AEFE (Agence pour l'enseignement français à l'étranger) financial projection model for EFIR (École Française Internationale de Riyad). The model is a **driver-based planning system** where enrollment projections cascade through class structure calculations, workforce planning, revenue planning, and cost planning.

**Key Characteristics:**
- **Dual-Period Budgeting**: Fiscal year spans two academic years (Sept-Aug school year vs Jan-Dec fiscal year)
- **Four Educational Levels**: Maternelle (Kindergarten), Élémentaire (Elementary), Collège (Middle School), Lycée (High School)
- **Mixed Staffing Model**: Expatriate teachers (Détachés) paid by AEFE + Local hire teachers (PDL)
- **Currency**: Saudi Riyal (SAR) with EUR conversion capability

---

## Table of Contents

1. [Model Architecture Overview](#1-model-architecture-overview)
2. [Enrollment Projections](#2-enrollment-projections)
3. [Class Division Calculations](#3-class-division-calculations)
4. [Workforce Planning - Primary](#4-workforce-planning---primary)
5. [Workforce Planning - Secondary (H/E Method)](#5-workforce-planning---secondary-he-method)
6. [Salary Mass Calculations](#6-salary-mass-calculations)
7. [Revenue Calculations](#7-revenue-calculations)
8. [Operating Expense Calculations](#8-operating-expense-calculations)
9. [Income Statement Consolidation](#9-income-statement-consolidation)
10. [Lookup Tables and Reference Data](#10-lookup-tables-and-reference-data)
11. [Implementation Guidelines](#11-implementation-guidelines)

---

## 1. Model Architecture Overview

### 1.1 Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CONFIGURATION LAYER                                │
├─────────────────────────────────────────────────────────────────────────────┤
│  Hypothèses Sheet:                                                          │
│  • Base Year (C8)                                                           │
│  • School Year Mapping (C10)                                                │
│  • Tuition Rates by Level (D22-D26)                                        │
│  • Salary Rates by Position (B106-E126)                                    │
│  • Students per Class Targets (D49-D52)                                    │
│  • Annual Increase Rates (Row 32, 35, 36)                                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PROJECTION LAYER                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│  Projection Effectifs Sheet:                                                │
│  • Historical Enrollment (Cols F-G)                                         │
│  • Cohort Growth Rates (Col B)                                             │
│  • Projected Enrollment by Grade (Cols H-M)                                │
│  • Level Aggregations (Rows 32-38)                                         │
│  • Distribution Keys (Rows 38-43)                                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           STRUCTURE LAYER                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│  Nbre de divisions Sheet + Hypothèses Rows 42-52:                          │
│  • Number of Classes per Grade                                              │
│  • Students per Class                                                       │
│  • Class Structure by Level                                                │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                       ┌──────────────┴──────────────┐
                       ▼                              ▼
┌────────────────────────────────┐    ┌────────────────────────────────┐
│     WORKFORCE PLANNING         │    │     REVENUE PLANNING           │
├────────────────────────────────┤    ├────────────────────────────────┤
│  Calcul MS Personnels:         │    │  Compte Résultat ML:           │
│  • Teachers per Level          │    │  • Tuition Revenue             │
│  • Staff Allocation            │    │  • DPI (Registration Fees)     │
│  • H/E Ratio Calculations      │    │  • Re-enrollment Fees          │
│  • ASEM (Assistants)          │    │  • Discounts/Abatements        │
└────────────────────────────────┘    └────────────────────────────────┘
                       │                              │
                       └──────────────┬──────────────┘
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           COST CALCULATION LAYER                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  Calcul MS Personnels + Calcul Cout Détaché:                               │
│  • PDL (Local Hire) Salary Costs                                           │
│  • Expatriate (AEFE) Costs                                                 │
│  • PRRD Contribution Calculations                                          │
│  • Variable Costs (per student)                                            │
│  • Fixed Operating Costs                                                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CONSOLIDATION LAYER                                │
├─────────────────────────────────────────────────────────────────────────────┤
│  Compte Résultat ML / Euro:                                                │
│  • Operating Result = Revenue - Expenses                                   │
│  • By Level (Maternelle, Élémentaire, Collège, Lycée)                     │
│  • Global Consolidation                                                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Key Temporal Concepts

The model handles the mismatch between **academic years** (September-August) and **fiscal years** (January-December):

```
Fiscal Year 2025:
├── Jan-Aug 2025: School Year 2024/2025 (8 months = 8/12)
└── Sep-Dec 2025: School Year 2025/2026 (4 months = 4/12)
```

**Critical Formula Pattern for Fiscal Year Proration:**
```
Fiscal_Year_Value = (SchoolYear_N-1_Value × 8/12) + (SchoolYear_N_Value × 4/12)
```

---

## 2. Enrollment Projections

### 2.1 Grade Structure

| Level | French Grades | Age Range |
|-------|--------------|-----------|
| Maternelle | PS, MS, GS | 3-5 |
| Élémentaire | CP, CE1, CE2, CM1, CM2 | 6-10 |
| Collège | 6ème, 5ème, 4ème, 3ème | 11-14 |
| Lycée | Seconde, Première, Terminale | 15-17 |

### 2.2 Cohort Progression Model

**Formula: Average Growth Rate Calculation**
```typescript
// Location: Projection Effectifs!B16:B29
// Purpose: Calculate compound annual growth rate from historical data

averageGrowthRate = IFERROR((lastYearEnrollment / firstYearEnrollment)^(1/numberOfYears) - 1, 0)

// Example for MS (Moyenne Section):
// B16 = IFERROR((M16/E16)^(1/8)-1, 0)
```

**Formula: Cohort Progression (Grade N → Grade N+1)**
```typescript
// Location: Projection Effectifs!H16:M29 (for non-entry grades)
// Purpose: Students in grade N this year become grade N+1 next year

projected_enrollment_grade_N_year_Y = previous_year_grade_N-1_enrollment

// Example: CE1 enrollment 2025/2026 = CP enrollment 2024/2025
// H19 = G18  (CE1 = previous year's CP)
```

**Formula: Entry Grade (Petite Section) - Manual Input**
```typescript
// Location: Projection Effectifs!F15:M15
// Purpose: Entry cohort size must be manually specified (no predecessor grade)

// PS enrollment is user input - typically based on:
// - Waiting list data
// - Market analysis
// - Facility capacity
```

### 2.3 Level Aggregations

**Formula: Enrollment by Educational Level**
```typescript
// Location: Projection Effectifs!C32:M38

maternelle_enrollment = SUM(PS, MS, GS)
// C32 = SUM(C14:C17)

elementaire_enrollment = SUM(CP, CE1, CE2, CM1, CM2)
// C33 = SUM(C18:C22)

primaire_enrollment = maternelle_enrollment + elementaire_enrollment
// C34 = C33 + C32

college_enrollment = SUM(6ème, 5ème, 4ème, 3ème)
// C35 = SUM(C23:C26)

lycee_enrollment = SUM(Seconde, Première, Terminale)
// C36 = SUM(C27:C29)

secondaire_enrollment = college_enrollment + lycee_enrollment
// C37 = C36 + C35

total_enrollment = primaire_enrollment + secondaire_enrollment
// C38 = C37 + C34
```

### 2.4 Distribution Keys

**Formula: Calculate Distribution Ratios for Cost Allocation**
```typescript
// Location: Projection Effectifs!S38:AC43
// Purpose: Allocate shared costs across levels

// Maternelle as % of Primaire
maternelle_primaire_ratio = maternelle_enrollment / primaire_enrollment
// S38 = IFERROR(C32/C$34, 0)

// Élémentaire as % of Primaire
elementaire_primaire_ratio = elementaire_enrollment / primaire_enrollment
// S39 = IFERROR(C33/C$34, 0)

// Collège as % of Secondaire
college_secondaire_ratio = college_enrollment / secondaire_enrollment
// S41 = IFERROR(C35/C$37, 0)

// Lycée as % of Secondaire
lycee_secondaire_ratio = lycee_enrollment / secondaire_enrollment
// S42 = IFERROR(C36/C$37, 0)
```

---

## 3. Class Division Calculations

### 3.1 Number of Classes per Grade

**Formula: Calculate Required Divisions**
```typescript
// Location: Hypothèses!D43:K46
// Purpose: Determine number of classes needed based on enrollment and max class size

// For Primary (Maternelle/Élémentaire) - uses CEILING
divisions_maternelle = IFERROR(
  CEILING(
    HLOOKUP(school_year, enrollment_projection_range, maternelle_row, FALSE) / 
    max_students_per_class_maternelle
  ), 
  0
)

// For Secondary (Collège/Lycée) - uses ROUNDUP
divisions_college = IFERROR(
  ROUNDUP(
    HLOOKUP(school_year, enrollment_projection_range, college_row, FALSE) / 
    max_students_per_class_college
  ),
  0
)
```

### 3.2 Students per Class Calculation

**Formula: Average Class Size**
```typescript
// Location: Nbre de divisions!D4:M18
// Purpose: Calculate actual students per class

students_per_class = enrollment / number_of_divisions

// Example: D4 = B4/C4
```

### 3.3 Level Aggregation for Divisions

**Formula: Total Divisions by Level**
```typescript
// Location: Nbre de divisions!C21:M27

divisions_maternelle = divisions_PS + divisions_MS + divisions_GS
// C21 = C4 + C5 + C6

divisions_elementaire = divisions_CP + divisions_CE1 + divisions_CE2 + divisions_CM1 + divisions_CM2
// C22 = C7 + C8 + C9 + C10 + C11

divisions_college = divisions_6eme + divisions_5eme + divisions_4eme + divisions_3eme
// C24 = C12 + C13 + C14 + C15

divisions_lycee = divisions_Seconde + divisions_Premiere + divisions_Terminale
// C25 = C16 + C17 + C18
```

---

## 4. Workforce Planning - Primary

### 4.1 Primary Teacher Model (Class-Based)

For Primary education (Maternelle + Élémentaire), teacher count is **directly based on number of classes**:

```
1 Class = 1 Main Teacher + Language/Specialist Teachers
```

**Formula: Primary Teachers**
```typescript
// Location: Calcul MS Personnels!C60:K65 (Maternelle), C112:K116 (Élémentaire)

// Expatriate Teachers (Détachés) - from Hypothèses
teachers_detaches = IFERROR(
  HLOOKUP(school_year, hypotheses_detaches_range, level_row, FALSE),
  0
)

// Local Hire Teachers (PDL) = Total Needed - Detaches
teachers_PDL_class = number_of_divisions - teachers_detaches

// Language/Specialist Teachers (based on International Section indicator)
teachers_languages = IF(
  international_section_indicator = 1,
  VLOOKUP(divisions, language_teacher_table, rate_column, FALSE),
  VLOOKUP(divisions, language_teacher_table_SI, rate_column, FALSE)
)

// Total Primary Teachers
total_primary_teachers = teachers_detaches + teachers_PDL_class + teachers_languages
```

### 4.2 ASEM (Teaching Assistants for Maternelle)

**Formula: ASEM Count**
```typescript
// Location: Calcul MS Personnels!C65:K65
// Rule: 1 ASEM per Maternelle class

asem_count = number_of_maternelle_divisions
```

### 4.3 Language Teacher Rates

**Reference Table: Tables Enseignants!C7:C8**

| International Section Index | Rate |
|-----------------------------|------|
| 1 (Without SI) | 0.3 |
| 2 (With SI) | 0.4 |

```typescript
// Formula: Additional language teachers
additional_language_teachers = number_of_primary_divisions × rate
```

---

## 5. Workforce Planning - Secondary (H/E Method)

### 5.1 The H/E Ratio Concept

For Secondary education (Collège + Lycée), teacher count uses the **H/E (Heures/Élèves)** ratio - a statistical relationship between class size and teaching hours needed per student.

```
H/E = Teaching Hours per Student per Week
Teacher FTE = H/E × Total Students / 18 (standard teaching hours per week)
```

### 5.2 H/E Lookup Tables

**Collège H/E Table (Tables Enseignants!B19:G36)**

| Students/Class | H/E Mean | H/E Max | Extrapolated Mean |
|----------------|----------|---------|-------------------|
| 16 | 2.07 | 2.11 | y = -0.0536x + 2.798 |
| 20 | 1.71 | 1.97 | = -0.0536 × 20 + 2.798 |
| 25 | 1.44 | 1.66 | = 1.726 |
| 30 | 1.31 | 1.39 | = 1.19 |

**Lycée H/E Table (Tables Enseignants!B43:G57)**

| Students/Class | H/E Mean | H/E Max | Extrapolated Mean |
|----------------|----------|---------|-------------------|
| 16 | 2.46 | 2.54 | y = -0.0809x + 3.805 |
| 20 | 2.12 | 2.70 | = -0.0809 × 20 + 3.805 |
| 25 | 1.98 | 2.26 | = 2.187 |
| 30 | 1.74 | 2.02 | = 1.378 |

### 5.3 H/E Calculation Formulas

**Formula: Lookup H/E Based on Class Size**
```typescript
// Location: Calcul MS Personnels!C169 (Collège), C223 (Lycée)

// Get average students per class
avg_students_per_class = HLOOKUP(school_year, hypotheses_class_size_range, level_row, FALSE)

// Lookup H/E from table (with/without International Section)
he_ratio = IF(
  international_section_indicator = 1,
  // Without SI - use Mean H/E
  VLOOKUP(avg_students_per_class, he_table, mean_column, FALSE),
  // With SI - use Max H/E
  VLOOKUP(avg_students_per_class, he_table, max_column, FALSE)
)
```

**Formula: Secondary Teachers from H/E**
```typescript
// Location: Calcul MS Personnels!C167 (Collège), C221 (Lycée)

// Total secondary teachers needed (excluding expatriates)
teachers_PDL_secondary = IFERROR(
  he_ratio × level_enrollment / 18 - teachers_detaches,
  0
)

// Breakdown:
// he_ratio: Hours needed per student
// level_enrollment: Total students in Collège or Lycée
// 18: Standard teaching hours per week per teacher
// teachers_detaches: Already allocated expatriate teachers
```

### 5.4 Expatriate Teacher Allocation for Secondary

**Formula: Distribute Expatriates Across Secondary Levels**
```typescript
// Location: Calcul MS Personnels!C166, C220

// Expatriate teachers for Collège
teachers_detaches_college = total_detaches_secondary × college_secondaire_ratio

// Expatriate teachers for Lycée  
teachers_detaches_lycee = total_detaches_secondary × lycee_secondaire_ratio
```

---

## 6. Salary Mass Calculations

### 6.1 Fiscal Year Proration Pattern

**Critical Formula: Academic-to-Fiscal Year Conversion**
```typescript
// All salary calculations use this pattern
// Location: Throughout Calcul MS Personnels!D69:K247

fiscal_year_cost = (
  (schoolYear_N-1_FTE × 8/12) + 
  (schoolYear_N_FTE × 4/12)
) × annual_salary_rate

// Example for a position:
// D69 = (C42*8/12 + D42*4/12) × VLOOKUP($B69, salary_table, 3, FALSE)
```

### 6.2 Non-Teaching Staff Cost Allocation

Non-teaching staff costs are allocated to educational levels using distribution keys:

**Formula: Staff Allocation by Level**
```typescript
// Location: Calcul MS Personnels!C42:K49 (Maternelle common staff)

// Step 1: Get total common staff count
common_staff_count = VLOOKUP(position_name, staff_hypotheses_range, year_column, FALSE)

// Step 2: Apply distribution key
level_allocated_staff = common_staff_count × distribution_key

// Example for Maternelle:
// C42 = VLOOKUP($B42, $B$6:$K$13, C$3, FALSE) × C$41
// Where C$41 = maternelle share of total students
```

### 6.3 PDL (Local Hire) Salary Costs

**Formula: Local Teacher Salary**
```typescript
// Location: Calcul MS Personnels!D87, D138 (Primary), D193, D247 (Secondary)

pdl_teacher_cost = (
  (previous_year_teachers × 8/12) + 
  (current_year_teachers × 4/12)
) × annual_salary_rate_PDL

// Where annual_salary_rate_PDL comes from Hypothèses!B106:E126
// D87 = ((C63+C64)*8/12 + (D64+D63)*4/12) × VLOOKUP($B87, salary_table, 3, FALSE)
```

### 6.4 Expatriate (Détaché) Salary Costs

Expatriate costs involve the PRRD (Participation aux Rémunérations des Résidents et Détachés) mechanism:

**Formula: Expatriate Cost Calculation**
```typescript
// Location: Calcul Cout Détaché sheet + Calcul MS Personnels!D86, D137, D192, D246

// From Calcul Cout Détaché:
global_remuneration_cost = 1646054.89  // Total AEFE costs
prrd_rate = 0.62  // PRRD contribution rate
isvl_allowance = 290060  // Expatriation allowance

theoretical_contribution = global_remuneration_cost × prrd_rate
actual_contribution = 1041174.94  // Actual amount paid
final_contribution_per_expatriate = (actual_contribution + isvl_allowance) / expatriate_count

// In salary calculations:
expatriate_cost = teacher_FTE × (
  (average_cost_per_expatriate × prrd_rate) + 
  (average_cost_per_expatriate × correction_factor)
)

// D86 = ((C62*8/12+D62*4/12) × (
//   ('Calcul Cout Détaché'!$B$12 × D$36) + 
//   ('Calcul Cout Détaché'!$B$12 × 'Calcul Cout Détaché'!$G$11)
// ))
```

### 6.5 Salary Increase Application

**Formula: Apply Annual Salary Increases**
```typescript
// Location: Implicit in salary lookups

// Salary rates in Hypothèses are stored by year
// Each year column applies the cumulative increase

year_N_salary = year_N-1_salary × (1 + annual_increase_rate)

// annual_increase_rate from Hypothèses!C35:K35
```

---

## 7. Revenue Calculations

### 7.1 Tuition Fee Revenue

**Formula: Annual Tuition Revenue with Proration**
```typescript
// Location: Compte Résultat ML!C29, C37, C45, C53 (by level)

// Step 1: Get enrollment for both school years in fiscal year
enrollment_yearN-1 = HLOOKUP(fiscal_year_to_school_year_N-1, enrollment_table, level_row, FALSE)
enrollment_yearN = HLOOKUP(fiscal_year_to_school_year_N, enrollment_table, level_row, FALSE)

// Step 2: Get tuition rates for both school years
tuition_yearN-1 = HLOOKUP(fiscal_year_to_school_year_N-1, tuition_table, level_row, FALSE)
tuition_yearN = HLOOKUP(fiscal_year_to_school_year_N, tuition_table, level_row, FALSE)

// Step 3: Calculate weighted revenue with abatement
tuition_revenue = (
  (enrollment_yearN-1 × tuition_yearN-1 × 6/10) +  // Sept-Feb of fiscal year
  (enrollment_yearN × tuition_yearN × 4/10)         // Mar-Aug of fiscal year
) × (1 - abatement_rate)

// Note: 6/10 and 4/10 used instead of 8/12 and 4/12 because tuition
// is typically billed over 10 months (Sept-June)

// C29 = IFERROR(((C25*C27/10*6)+(C26*C28/10*4))*(1-C$17), 0)
```

### 7.2 First Enrollment Fees (DPI)

**Formula: Registration Fee Revenue**
```typescript
// Location: Compte Résultat ML!C30, C38, C46, C54

// Only new students pay DPI
dpi_revenue = (
  (enrollment_yearN-1 × 6/10) + 
  (enrollment_yearN × 4/10)
) × dpi_rate × new_student_rate

// C30 = IFERROR((C25/10*6 + C26/10*4) × C$18 × C$16, 0)
```

### 7.3 Re-enrollment Fees

**Formula: Annual Re-enrollment Revenue**
```typescript
// Location: Compte Résultat ML!C31, C39, C47, C55

// All returning students pay re-enrollment
reenrollment_revenue = enrollment_yearN × reenrollment_fee

// C31 = C26 × C$19
```

### 7.4 Tuition Rate Increases

**Formula: Year-over-Year Tuition Increase**
```typescript
// Location: Hypothèses!E22:K26

// Each level's tuition increases by the global rate
tuition_yearN = tuition_yearN-1 × (1 + tuition_increase_rate)

// E22 = D22 × (1 + E$32)
// Where E$32 is the tuition increase rate for that year
```

---

## 8. Operating Expense Calculations

### 8.1 Variable Costs (Per-Student)

**Formula: Per-Student Variable Costs**
```typescript
// Location: Hypothèses!D133:D136, Compte Résultat ML!C89:C93

// Variable costs scale with enrollment
variable_cost_item = cost_per_student × enrollment

// Cost categories:
// - Crédits disciplinaires (Teaching materials)
// - Manuels scolaires (Textbooks)
// - Equipements individuels (Individual equipment - tablets, etc.)
// - Autres charges variables (Other variable costs)

// D133 = C133 × HLOOKUP(school_year, enrollment_projection, total_row, FALSE)
```

### 8.2 Fixed Costs

**Formula: Fixed Operating Costs**
```typescript
// Location: Hypothèses!D138:D146, Compte Résultat ML!C94:C103

// Fixed costs are entered directly, may increase with inflation
fixed_cost_yearN = fixed_cost_yearN-1 × (1 + inflation_rate)

// Cost categories:
// - Loyer (Rent)
// - Viabilisation (Utilities - water, energy)
// - Maintenance courante (Routine maintenance)
// - Aménagements (Improvements)
// - Informatique/Licences (IT/Software licenses)
// - Sécurité (Security)
// - Communication
// - Administratif (Administrative)
// - Autres dépenses (Other expenses)
```

### 8.3 Cost Allocation to Levels

**Formula: Allocate Costs to Educational Levels**
```typescript
// Location: Compte Résultat ML!C89:C103 (repeated for each level section)

// Fixed and variable costs are allocated using distribution keys
level_cost = total_cost × level_distribution_key

// Example: Maternelle share of utilities
// C96 = total_utilities × maternelle_ratio
```

---

## 9. Income Statement Consolidation

### 9.1 Operating Result by Level

**Formula: Level Operating Result**
```typescript
// Location: Compte Résultat ML!C7:J10

// Operating Result = Revenue - Expenses
operating_result_maternelle = revenue_maternelle - expenses_maternelle
// C7 = C24 - C84

operating_result_elementaire = revenue_elementaire - expenses_elementaire
// C8 = C32 - C110

operating_result_college = revenue_college - expenses_college
// C9 = C40 - C136

operating_result_lycee = revenue_lycee - expenses_lycee
// C10 = C48 - C162
```

### 9.2 Global Operating Result

**Formula: Total School Operating Result**
```typescript
// Location: Compte Résultat ML!C6

// Global = Sum of all revenues - Sum of all expenses
operating_result_global = total_revenue - total_expenses
// C6 = C15 - C60

// Where:
// C15 = SUM(C20:C23)  // Total revenues
// C60 = C61 + C65 + C70 + C80  // Total expenses
```

### 9.3 Expense Breakdown Structure

```typescript
// Expense hierarchy:
total_expenses = salary_mass + variable_costs + fixed_costs + network_costs

salary_mass = pdl_teacher_salaries + expatriate_salaries + non_teaching_salaries
// C61 = C85 + C111 + C137 + C163

variable_costs = teaching_materials + textbooks + equipment + other_variable
// C65 = C89 + C115 + C141 + C167

fixed_costs = rent + utilities + maintenance + IT + security + admin + other
// C70 = C94 + C120 + C146 + C172

network_costs = pfc + partnership_fees + training_contribution  // AEFE-specific
// C80 = (AEFE network charges - varies by school status)
```

---

## 10. Lookup Tables and Reference Data

### 10.1 School Year Mapping Table

**Location: table années scolaires!C17:E27**

| Calendar Year | School Year N-1 | School Year N |
|---------------|-----------------|---------------|
| 2025 | 2024/2025 | 2025/2026 |
| 2026 | 2025/2026 | 2026/2027 |
| 2027 | 2026/2027 | 2027/2028 |

**Usage:**
```typescript
// Convert fiscal year to school years for lookups
school_year_N-1 = VLOOKUP(fiscal_year, year_mapping_table, 2, FALSE)
school_year_N = VLOOKUP(fiscal_year, year_mapping_table, 3, FALSE)
```

### 10.2 Salary Rate Table

**Location: Hypothèses!B106:E126**

| Position | 2024 Rate | 2025 Rate | ... |
|----------|-----------|-----------|-----|
| Chef d'Etablissement D1 | [rate] | [rate] | ... |
| DAF PDL | [rate] | [rate] | ... |
| Enseignant PDL | [rate] | [rate] | ... |
| ASEM | [rate] | [rate] | ... |

### 10.3 H/E Reference Tables

**Location: Tables Enseignants!B19:H36 (Collège), B43:H57 (Lycée)**

See Section 5.2 for detailed table structure.

### 10.4 Key Hypotheses Parameters

**Location: Hypothèses sheet**

| Parameter | Row | Description |
|-----------|-----|-------------|
| Base Year | C8 | First projection year (e.g., 2025) |
| School Year | C10 | Initial academic year |
| Tuition by Level | D22:D26 | Annual tuition rates |
| New Student Rate | D28 | % of students that are new |
| Abatement Rate | D29 | Discount rate (scholarships, sibling, staff) |
| Tuition Increase | Row 32 | Annual tuition increase rate |
| Salary Increase | Row 35 | Annual salary increase rate |
| Inflation | Row 36 | Annual inflation rate |
| Exchange Rate | Row 38 | SAR/EUR exchange rate |
| PRRD Rate | Row 40 | Expatriate contribution rate |
| Max Students/Class | D49:D52 | Target class sizes by level |
| Staff Counts | Rows 59-83 | Non-teaching staff by position |

---

## 11. Implementation Guidelines

### 11.1 Calculation Order (Dependencies)

The formulas must be calculated in this specific order to resolve dependencies:

```
1. Configuration Loading
   └── Load all Hypothèses parameters
   
2. Time Period Mapping
   └── Calculate school year mappings for each fiscal year
   
3. Enrollment Projections
   ├── Calculate cohort growth rates
   ├── Project grade-level enrollments
   └── Aggregate to level totals
   
4. Class Structure
   ├── Calculate divisions per grade
   ├── Calculate students per class
   └── Calculate distribution keys
   
5. Workforce Planning
   ├── Calculate primary teachers (class-based)
   ├── Calculate secondary teachers (H/E method)
   ├── Calculate non-teaching staff allocations
   └── Calculate ASEM requirements
   
6. Cost Calculations
   ├── Calculate PDL salary costs
   ├── Calculate expatriate costs
   ├── Calculate variable costs
   └── Calculate fixed costs
   
7. Revenue Calculations
   ├── Calculate tuition revenue
   ├── Calculate DPI revenue
   └── Calculate re-enrollment revenue
   
8. Consolidation
   ├── Aggregate by level
   └── Calculate operating results
```

### 11.2 TypeScript Interface Definitions

```typescript
// Core domain types
interface SchoolYear {
  label: string;           // "2024/2025"
  startYear: number;       // 2024
  endYear: number;         // 2025
}

interface FiscalYear {
  year: number;            // 2025
  schoolYearPrevious: SchoolYear;  // 2024/2025
  schoolYearCurrent: SchoolYear;   // 2025/2026
}

interface EducationalLevel {
  id: 'MATERNELLE' | 'ELEMENTAIRE' | 'COLLEGE' | 'LYCEE';
  name: string;
  grades: Grade[];
}

interface Grade {
  id: string;              // "PS", "MS", "6EME", etc.
  levelId: string;
  sequence: number;        // Order within level
  enrollment: Map<string, number>;  // School year -> count
}

interface EnrollmentProjection {
  schoolYear: SchoolYear;
  byGrade: Map<string, number>;
  byLevel: Map<string, number>;
  total: number;
}

interface ClassStructure {
  schoolYear: SchoolYear;
  gradeId: string;
  divisions: number;
  studentsPerClass: number;
}

interface StaffPosition {
  id: string;
  name: string;
  category: 'TEACHING' | 'NON_TEACHING' | 'ASEM';
  contractType: 'PDL' | 'DETACHE';
  annualSalary: Map<number, number>;  // Year -> salary
}

interface WorkforceAllocation {
  fiscalYear: number;
  positionId: string;
  levelId: string;
  fte: number;
  annualCost: number;
}

interface HeRatioTable {
  level: 'COLLEGE' | 'LYCEE';
  studentsPerClass: number;
  heMean: number;
  heMax: number;
  coeffDirecteur: number;  // Slope
  ordoOrigine: number;     // Y-intercept
}

interface RevenueCalculation {
  fiscalYear: number;
  levelId: string;
  tuitionRevenue: number;
  dpiRevenue: number;
  reenrollmentRevenue: number;
  totalRevenue: number;
}

interface ExpenseCalculation {
  fiscalYear: number;
  levelId: string;
  salaryMass: number;
  variableCosts: number;
  fixedCosts: number;
  networkCosts: number;
  totalExpenses: number;
}

interface OperatingResult {
  fiscalYear: number;
  levelId: string | 'GLOBAL';
  revenue: number;
  expenses: number;
  operatingResult: number;
}
```

### 11.3 Key Calculation Functions

```typescript
// Academic-Fiscal Year Proration
function calculateFiscalYearValue(
  schoolYearPreviousValue: number,
  schoolYearCurrentValue: number,
  previousMonths: number = 8,
  currentMonths: number = 4
): number {
  const totalMonths = previousMonths + currentMonths;
  return (schoolYearPreviousValue * previousMonths / totalMonths) +
         (schoolYearCurrentValue * currentMonths / totalMonths);
}

// H/E Ratio Lookup with Linear Extrapolation
function getHeRatio(
  level: 'COLLEGE' | 'LYCEE',
  studentsPerClass: number,
  hasInternationalSection: boolean,
  heTable: HeRatioTable[]
): number {
  const levelTable = heTable.filter(t => t.level === level);
  
  // Direct lookup
  const exactMatch = levelTable.find(t => t.studentsPerClass === Math.round(studentsPerClass));
  if (exactMatch) {
    return hasInternationalSection ? exactMatch.heMax : exactMatch.heMean;
  }
  
  // Linear extrapolation: y = mx + b
  const coefficients = levelTable[0];  // All rows have same coefficients
  return coefficients.coeffDirecteur * studentsPerClass + coefficients.ordoOrigine;
}

// Primary Teacher Calculation
function calculatePrimaryTeachers(
  divisions: number,
  expatriateCount: number,
  hasInternationalSection: boolean,
  languageTeacherRate: number
): { detaches: number; pdl: number; languages: number; total: number } {
  const languageTeachers = divisions * languageTeacherRate;
  const pdlTeachers = divisions - expatriateCount;
  
  return {
    detaches: expatriateCount,
    pdl: pdlTeachers,
    languages: languageTeachers,
    total: expatriateCount + pdlTeachers + languageTeachers
  };
}

// Secondary Teacher Calculation
function calculateSecondaryTeachers(
  enrollment: number,
  heRatio: number,
  expatriateCount: number,
  standardTeachingHours: number = 18
): { detaches: number; pdl: number; total: number } {
  const totalTeachersNeeded = (heRatio * enrollment) / standardTeachingHours;
  const pdlTeachers = Math.max(0, totalTeachersNeeded - expatriateCount);
  
  return {
    detaches: expatriateCount,
    pdl: pdlTeachers,
    total: totalTeachersNeeded
  };
}

// Tuition Revenue Calculation
function calculateTuitionRevenue(
  enrollmentPrevYear: number,
  enrollmentCurrYear: number,
  tuitionPrevYear: number,
  tuitionCurrYear: number,
  abatementRate: number,
  billingMonths: number = 10
): number {
  const prevYearRevenue = enrollmentPrevYear * tuitionPrevYear * (6 / billingMonths);
  const currYearRevenue = enrollmentCurrYear * tuitionCurrYear * (4 / billingMonths);
  return (prevYearRevenue + currYearRevenue) * (1 - abatementRate);
}
```

### 11.4 Data Validation Rules

```typescript
// Validation rules for input data
const validationRules = {
  // Enrollment must be non-negative integer
  enrollment: (value: number) => Number.isInteger(value) && value >= 0,
  
  // Class size must be between 1 and 35
  studentsPerClass: (value: number) => value >= 1 && value <= 35,
  
  // H/E ratio must be between 0.8 and 4.0
  heRatio: (value: number) => value >= 0.8 && value <= 4.0,
  
  // Rates must be between 0 and 1
  rate: (value: number) => value >= 0 && value <= 1,
  
  // Currency amounts must be non-negative
  amount: (value: number) => value >= 0,
  
  // FTE must be non-negative
  fte: (value: number) => value >= 0
};
```

### 11.5 Error Handling Patterns

```typescript
// Pattern used throughout the Excel model
function safeCalculation<T>(
  calculation: () => T,
  defaultValue: T,
  errorHandler?: (error: Error) => void
): T {
  try {
    const result = calculation();
    if (result === null || result === undefined || Number.isNaN(result)) {
      return defaultValue;
    }
    return result;
  } catch (error) {
    if (errorHandler) {
      errorHandler(error as Error);
    }
    return defaultValue;
  }
}

// Usage example (equivalent to IFERROR in Excel)
const enrollment = safeCalculation(
  () => lookupEnrollment(schoolYear, level),
  0
);
```

---

## Appendix A: Formula Reference Summary

| Formula Type | Excel Pattern | Location |
|-------------|---------------|----------|
| Cohort Growth | `IFERROR((M/E)^(1/8)-1, 0)` | Projection Effectifs!B16:B29 |
| Division Count | `CEILING(enrollment/maxClass)` | Hypothèses!D43:K46 |
| H/E Lookup | `VLOOKUP(classSize, table, col, FALSE)` | Calcul MS Personnels!C169, C223 |
| Fiscal Proration | `(prev*8/12 + curr*4/12) × rate` | Throughout salary calcs |
| Distribution Key | `IFERROR(level/total, 0)` | Projection Effectifs!S38:AC43 |
| School Year Map | `VLOOKUP(year, yearTable, col, FALSE)` | Multiple sheets |
| Tuition Revenue | `((eff_prev*tarif_prev*6/10)+(eff_curr*tarif_curr*4/10))*(1-abat)` | Compte Résultat!C29+ |

---

## Appendix B: Sheet Dependency Matrix

| Sheet | Depends On | Provides To |
|-------|-----------|-------------|
| Hypothèses | table années scolaires | All other sheets |
| Projection Effectifs | Hypothèses | Nbre divisions, Calcul MS |
| Nbre de divisions | Projection Effectifs | Reference only |
| Tables Enseignants | None | Calcul MS Personnels |
| Calcul Cout Détaché | Hypothèses | Calcul MS Personnels |
| Calcul MS Personnels | Hypothèses, Projection Effectifs, Tables Enseignants, Calcul Cout Détaché | Compte Résultat ML |
| Compte Résultat ML | Hypothèses, Calcul MS Personnels | Compte Résultat Euro |
| Compte Résultat Euro | Compte Résultat ML, Hypothèses | Final output |

---

## Appendix C: Glossary

| French Term | English | Description |
|-------------|---------|-------------|
| AEFE | Agency for French Education Abroad | French government agency managing overseas French schools |
| ASEM | Maternelle Teaching Assistant | Classroom assistant for kindergarten |
| Collège | Middle School | Grades 6ème-3ème (ages 11-14) |
| CPE | Principal Education Advisor | Student life coordinator |
| DAF | Administrative and Financial Director | CFO equivalent |
| Détaché | Expatriate | Teacher seconded from French national education |
| DPI | First Registration Fee | One-time enrollment fee |
| Élémentaire | Elementary | Grades CP-CM2 (ages 6-10) |
| H/E | Hours per Student | Teacher workload ratio |
| ISVL | Cost of Living Allowance | Expatriate location bonus |
| Lycée | High School | Grades Seconde-Terminale (ages 15-17) |
| Maternelle | Kindergarten | Grades PS-GS (ages 3-5) |
| PDL | Local Hire | Locally recruited staff |
| PFC | Network Contribution | AEFE membership fee |
| PRRD | Resident Remuneration Participation | Expatriate cost-sharing mechanism |
| SI | International Section | Enhanced language program |

---

*Document Version: 1.0*
*Generated for: EFIR Budget Planning Application*
*Based on: AEFE Financial Projection Model*
