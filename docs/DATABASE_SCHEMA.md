# EFIR Budget Database Schema

> **Schema**: `efir_budget`
> **Last Updated**: 2025-12-11
> **Total Tables**: 44

This document describes all tables in the EFIR Budget Planning Application database.

---

## Table of Contents

1. [Configuration Layer (Reference Data)](#1-configuration-layer-reference-data)
2. [Version-Controlled Configuration](#2-version-controlled-configuration)
3. [Planning Layer (Modules 7-12)](#3-planning-layer-modules-7-12)
4. [Consolidation Layer (Modules 13-14)](#4-consolidation-layer-modules-13-14)
5. [Analysis Layer (Modules 15-17)](#5-analysis-layer-modules-15-17)
6. [Strategic Layer (Module 18)](#6-strategic-layer-module-18)
7. [System Tables](#7-system-tables)
8. [Entity Relationship Diagram](#8-entity-relationship-diagram)
9. [Enums Reference](#9-enums-reference)

---

## 1. Configuration Layer (Reference Data)

These tables contain reference data that rarely changes and is shared across all budget versions.

### 1.1 `academic_cycles`

Academic cycle definitions for the French education system.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | uuid | NO | gen_random_uuid() | Primary key |
| `code` | varchar | NO | - | Cycle code (MAT, ELEM, COLL, LYC) |
| `name_fr` | varchar | NO | - | French name (e.g., 'Maternelle') |
| `name_en` | varchar | NO | - | English name (e.g., 'Preschool') |
| `sort_order` | integer | NO | - | Display order (1=MAT, 2=ELEM, 3=COLL, 4=LYC) |
| `requires_atsem` | boolean | NO | false | Whether ATSEM (classroom assistant) is required |
| `created_at` | timestamptz | NO | now() | Record creation timestamp |
| `updated_at` | timestamptz | NO | now() | Last update timestamp |
| `deleted_at` | timestamptz | YES | NULL | Soft delete timestamp |

**Sample Data**:
| code | name_fr | name_en | requires_atsem |
|------|---------|---------|----------------|
| MAT | Maternelle | Preschool | true |
| ELEM | Élémentaire | Elementary | false |
| COLL | Collège | Middle School | false |
| LYC | Lycée | High School | false |

---

### 1.2 `academic_levels`

Academic level definitions within each cycle.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | uuid | NO | gen_random_uuid() | Primary key |
| `cycle_id` | uuid | NO | - | FK to academic_cycles |
| `code` | varchar | NO | - | Level code (PS, MS, GS, CP, CE1, etc.) |
| `name_fr` | varchar | NO | - | French name (e.g., 'Petite Section') |
| `name_en` | varchar | NO | - | English name |
| `sort_order` | integer | NO | - | Display order within cycle |
| `is_secondary` | boolean | NO | false | Whether DHG applies (Collège/Lycée) |
| `created_at` | timestamptz | NO | now() | Record creation timestamp |
| `updated_at` | timestamptz | NO | now() | Last update timestamp |
| `deleted_at` | timestamptz | YES | NULL | Soft delete timestamp |

**Sample Data** (15 levels):
| cycle | code | name_fr | is_secondary |
|-------|------|---------|--------------|
| MAT | PS | Petite Section | false |
| MAT | MS | Moyenne Section | false |
| MAT | GS | Grande Section | false |
| ELEM | CP | Cours Préparatoire | false |
| ELEM | CE1 | Cours Élémentaire 1 | false |
| ELEM | CE2 | Cours Élémentaire 2 | false |
| ELEM | CM1 | Cours Moyen 1 | false |
| ELEM | CM2 | Cours Moyen 2 | false |
| COLL | 6ème | Sixième | true |
| COLL | 5ème | Cinquième | true |
| COLL | 4ème | Quatrième | true |
| COLL | 3ème | Troisième | true |
| LYC | 2nde | Seconde | true |
| LYC | 1ère | Première | true |
| LYC | Term | Terminale | true |

---

### 1.3 `subjects`

Subject catalog for DHG (Dotation Horaire Globale) calculations.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | uuid | NO | gen_random_uuid() | Primary key |
| `code` | varchar | NO | - | Subject code (MATH, FRAN, ANGL, etc.) |
| `name_fr` | varchar | NO | - | French name (e.g., 'Mathématiques') |
| `name_en` | varchar | NO | - | English name (e.g., 'Mathematics') |
| `category` | varchar | NO | - | Category (core, specialty, elective) |
| `is_active` | boolean | NO | true | Whether subject is currently active |
| `created_at` | timestamptz | NO | now() | Record creation timestamp |
| `updated_at` | timestamptz | NO | now() | Last update timestamp |
| `deleted_at` | timestamptz | YES | NULL | Soft delete timestamp |

**Sample Data** (20 subjects):
| code | name_fr | name_en | category |
|------|---------|---------|----------|
| MATH | Mathématiques | Mathematics | core |
| FRAN | Français | French | core |
| ANGL | Anglais | English | core |
| ARAB | Arabe | Arabic | core |
| HIST | Histoire-Géographie | History-Geography | core |
| SVT | Sciences de la Vie et de la Terre | Life Sciences | core |
| PHYS | Physique-Chimie | Physics-Chemistry | core |
| EPS | Éducation Physique et Sportive | Physical Education | core |
| ARTS | Arts Plastiques | Visual Arts | elective |
| MUSI | Éducation Musicale | Music | elective |

---

### 1.4 `nationality_types`

Nationality-based fee tier definitions.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | uuid | NO | gen_random_uuid() | Primary key |
| `code` | varchar | NO | - | Nationality code |
| `name_fr` | varchar | NO | - | French name |
| `name_en` | varchar | NO | - | English name |
| `vat_applicable` | boolean | NO | true | Whether VAT applies (Saudi: no) |
| `sort_order` | integer | NO | - | Display order |
| `created_at` | timestamptz | NO | now() | Record creation timestamp |
| `updated_at` | timestamptz | NO | now() | Last update timestamp |
| `deleted_at` | timestamptz | YES | NULL | Soft delete timestamp |

**Sample Data**:
| code | name_en | vat_applicable |
|------|---------|----------------|
| FR | French | true |
| SA | Saudi | false |
| OT | Other | true |

---

### 1.5 `fee_categories`

Fee category definitions for revenue planning.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | uuid | NO | gen_random_uuid() | Primary key |
| `code` | varchar | NO | - | Category code |
| `name_fr` | varchar | NO | - | French name |
| `name_en` | varchar | NO | - | English name |
| `account_code` | varchar | NO | - | PCG account code (70xxx revenue) |
| `is_recurring` | boolean | NO | true | Whether charged annually |
| `allows_sibling_discount` | boolean | NO | false | Whether sibling discount applies |
| `created_at` | timestamptz | NO | now() | Record creation timestamp |
| `updated_at` | timestamptz | NO | now() | Last update timestamp |
| `deleted_at` | timestamptz | YES | NULL | Soft delete timestamp |

**Expected Categories**:
| code | name_en | account_code | allows_sibling_discount |
|------|---------|--------------|------------------------|
| TUITION | Tuition | 70110 | true |
| DAI | Annual Registration Fee | 70120 | false |
| REGISTRATION | First Registration | 70130 | false |
| TRANSPORT | Transport | 70140 | false |
| CANTEEN | Canteen | 70150 | false |

---

### 1.6 `teacher_categories`

Teacher employment categories for cost planning.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | uuid | NO | gen_random_uuid() | Primary key |
| `code` | varchar | NO | - | Category code |
| `name_fr` | varchar | NO | - | French name |
| `name_en` | varchar | NO | - | English name |
| `description` | text | YES | NULL | Category description |
| `is_aefe` | boolean | NO | false | Whether AEFE-affiliated |
| `created_at` | timestamptz | NO | now() | Record creation timestamp |
| `updated_at` | timestamptz | NO | now() | Last update timestamp |
| `deleted_at` | timestamptz | YES | NULL | Soft delete timestamp |

**Expected Categories**:
| code | name_en | is_aefe | description |
|------|---------|---------|-------------|
| AEFE_DET | AEFE Detached | true | French nationals, school pays PRRD |
| AEFE_FND | AEFE Funded | true | Fully funded by AEFE (no school cost) |
| LOCAL | Local Contract | false | Locally recruited teachers |

---

### 1.7 `system_configs`

Global system configuration parameters.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | uuid | NO | gen_random_uuid() | Primary key |
| `key` | varchar | NO | - | Configuration key (unique) |
| `value` | jsonb | NO | - | Configuration value (flexible JSONB) |
| `category` | varchar | NO | - | Category (currency, locale, academic, etc.) |
| `description` | text | NO | - | Human-readable description |
| `is_active` | boolean | NO | true | Whether configuration is active |
| `created_at` | timestamptz | NO | now() | Record creation timestamp |
| `updated_at` | timestamptz | NO | now() | Last update timestamp |
| `created_by_id` | uuid | NO | - | FK to auth.users |
| `updated_by_id` | uuid | NO | - | FK to auth.users |
| `deleted_at` | timestamptz | YES | NULL | Soft delete timestamp |

**Expected Configurations**:
| key | category | description |
|-----|----------|-------------|
| currency_primary | currency | Primary currency (SAR) |
| currency_secondary | currency | Secondary currency (EUR for AEFE) |
| exchange_rate_eur_sar | currency | EUR to SAR exchange rate |
| academic_year_start | academic | Academic year start month (September) |
| sibling_discount_rate | fees | Sibling discount percentage (25%) |

---

## 2. Version-Controlled Configuration

These tables contain configuration that can vary by budget version.

### 2.1 `budget_versions`

Budget version control - the central table for version management.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | uuid | NO | gen_random_uuid() | Primary key |
| `name` | varchar | NO | - | Version name (e.g., 'Budget 2025-2026') |
| `fiscal_year` | integer | NO | - | Fiscal year (e.g., 2026 for 2025-2026) |
| `academic_year` | varchar | NO | - | Academic year (e.g., '2025-2026') |
| `status` | budgetversionstatus | NO | 'working' | Version status enum |
| `submitted_at` | timestamptz | YES | NULL | When version was submitted |
| `submitted_by_id` | uuid | YES | NULL | FK to auth.users |
| `approved_at` | timestamptz | YES | NULL | When version was approved |
| `approved_by_id` | uuid | YES | NULL | FK to auth.users |
| `notes` | text | YES | NULL | Version notes and comments |
| `is_baseline` | boolean | NO | false | Whether this is the baseline version |
| `parent_version_id` | uuid | YES | NULL | FK to budget_versions (for forecasts) |
| `created_at` | timestamptz | NO | now() | Record creation timestamp |
| `updated_at` | timestamptz | NO | now() | Last update timestamp |
| `created_by_id` | uuid | YES | NULL | FK to auth.users |
| `updated_by_id` | uuid | YES | NULL | FK to auth.users |
| `deleted_at` | timestamptz | YES | NULL | Soft delete timestamp |

**Status Workflow**:
```
working → submitted → approved → forecast → superseded
```

---

### 2.2 `class_size_params`

Class size parameters per level and budget version.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | uuid | NO | gen_random_uuid() | Primary key |
| `budget_version_id` | uuid | NO | - | FK to budget_versions |
| `level_id` | uuid | YES | NULL | FK to academic_levels (NULL for cycle default) |
| `cycle_id` | uuid | YES | NULL | FK to academic_cycles (NULL if level-specific) |
| `min_class_size` | integer | NO | - | Minimum viable class size |
| `target_class_size` | integer | NO | - | Target/optimal class size |
| `max_class_size` | integer | NO | - | Maximum allowed class size |
| `notes` | text | YES | NULL | Parameter notes |
| `created_at` | timestamptz | NO | now() | Record creation timestamp |
| `updated_at` | timestamptz | NO | now() | Last update timestamp |
| `created_by_id` | uuid | YES | NULL | FK to auth.users |
| `updated_by_id` | uuid | YES | NULL | FK to auth.users |
| `deleted_at` | timestamptz | YES | NULL | Soft delete timestamp |

**Typical Values**:
| cycle | min | target | max |
|-------|-----|--------|-----|
| Maternelle | 15 | 24 | 28 |
| Élémentaire | 18 | 25 | 30 |
| Collège | 20 | 28 | 32 |
| Lycée | 20 | 30 | 35 |

---

### 2.3 `subject_hours_matrix`

Hours per week per subject per level - the DHG configuration matrix.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | uuid | NO | gen_random_uuid() | Primary key |
| `budget_version_id` | uuid | NO | - | FK to budget_versions |
| `subject_id` | uuid | NO | - | FK to subjects |
| `level_id` | uuid | NO | - | FK to academic_levels |
| `hours_per_week` | numeric | NO | - | Hours per week per class (0-12) |
| `is_split` | boolean | NO | false | Whether classes are split (doubles hours) |
| `notes` | text | YES | NULL | Configuration notes |
| `created_at` | timestamptz | NO | now() | Record creation timestamp |
| `updated_at` | timestamptz | NO | now() | Last update timestamp |
| `created_by_id` | uuid | YES | NULL | FK to auth.users |
| `updated_by_id` | uuid | YES | NULL | FK to auth.users |
| `deleted_at` | timestamptz | YES | NULL | Soft delete timestamp |

**Constraint**: `hours_per_week > 0 AND hours_per_week <= 12`

---

### 2.4 `teacher_cost_params`

Teacher cost parameters per category and budget version.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | uuid | NO | gen_random_uuid() | Primary key |
| `budget_version_id` | uuid | NO | - | FK to budget_versions |
| `category_id` | uuid | NO | - | FK to teacher_categories |
| `cycle_id` | uuid | YES | NULL | FK to academic_cycles (NULL for all) |
| `prrd_contribution_eur` | numeric | YES | NULL | PRRD per teacher (EUR, AEFE detached) |
| `avg_salary_sar` | numeric | YES | NULL | Average salary for local (SAR/year) |
| `social_charges_rate` | numeric | NO | 0.21 | Social charges rate (21% = GOSI) |
| `benefits_allowance_sar` | numeric | NO | 0.00 | Benefits/allowances per teacher |
| `hsa_hourly_rate_sar` | numeric | NO | - | HSA (overtime) hourly rate |
| `max_hsa_hours` | numeric | NO | 4.00 | Max HSA hours per teacher per week |
| `notes` | text | YES | NULL | Parameter notes |
| `created_at` | timestamptz | NO | now() | Record creation timestamp |
| `updated_at` | timestamptz | NO | now() | Last update timestamp |
| `created_by_id` | uuid | YES | NULL | FK to auth.users |
| `updated_by_id` | uuid | YES | NULL | FK to auth.users |
| `deleted_at` | timestamptz | YES | NULL | Soft delete timestamp |

---

### 2.5 `fee_structure`

Fee amounts per level, nationality, and category.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | uuid | NO | gen_random_uuid() | Primary key |
| `budget_version_id` | uuid | NO | - | FK to budget_versions |
| `level_id` | uuid | NO | - | FK to academic_levels |
| `nationality_type_id` | uuid | NO | - | FK to nationality_types |
| `fee_category_id` | uuid | NO | - | FK to fee_categories |
| `amount_sar` | numeric | NO | - | Fee amount in SAR |
| `trimester` | integer | YES | NULL | Trimester (1-3) for tuition, NULL for annual |
| `notes` | text | YES | NULL | Fee notes |
| `created_at` | timestamptz | NO | now() | Record creation timestamp |
| `updated_at` | timestamptz | NO | now() | Last update timestamp |
| `created_by_id` | uuid | YES | NULL | FK to auth.users |
| `updated_by_id` | uuid | YES | NULL | FK to auth.users |
| `deleted_at` | timestamptz | YES | NULL | Soft delete timestamp |

---

### 2.6 `timetable_constraints`

Scheduling constraints per level.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | uuid | NO | gen_random_uuid() | Primary key |
| `budget_version_id` | uuid | NO | - | FK to budget_versions |
| `level_id` | uuid | NO | - | FK to academic_levels |
| `total_hours_per_week` | numeric | NO | - | Total student hours per week |
| `max_hours_per_day` | numeric | NO | - | Maximum hours per day |
| `days_per_week` | integer | NO | 5 | School days per week |
| `requires_lunch_break` | boolean | NO | true | Whether lunch break is required |
| `min_break_duration_minutes` | integer | NO | 60 | Minimum break duration |
| `notes` | text | YES | NULL | Constraint notes |
| `created_at` | timestamptz | NO | now() | Record creation timestamp |
| `updated_at` | timestamptz | NO | now() | Last update timestamp |
| `created_by_id` | uuid | YES | NULL | FK to auth.users |
| `updated_by_id` | uuid | YES | NULL | FK to auth.users |
| `deleted_at` | timestamptz | YES | NULL | Soft delete timestamp |

---

## 3. Planning Layer (Modules 7-12)

These tables contain the core planning data that drives budget calculations.

### 3.1 `enrollment_plans`

Student enrollment projections by level and nationality.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | uuid | NO | gen_random_uuid() | Primary key |
| `budget_version_id` | uuid | NO | - | FK to budget_versions |
| `level_id` | uuid | NO | - | FK to academic_levels |
| `nationality_type_id` | uuid | NO | - | FK to nationality_types |
| `student_count` | integer | NO | - | Projected number of students |
| `notes` | text | YES | NULL | Enrollment notes and assumptions |
| `created_at` | timestamptz | NO | now() | Record creation timestamp |
| `updated_at` | timestamptz | NO | now() | Last update timestamp |
| `created_by_id` | uuid | YES | NULL | FK to auth.users |
| `updated_by_id` | uuid | YES | NULL | FK to auth.users |
| `deleted_at` | timestamptz | YES | NULL | Soft delete timestamp |

**Constraint**: `student_count >= 0`

---

### 3.2 `nationality_distributions`

Nationality distribution percentages by level.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | uuid | NO | gen_random_uuid() | Primary key |
| `budget_version_id` | uuid | NO | - | FK to budget_versions |
| `level_id` | uuid | NO | - | FK to academic_levels |
| `french_percent` | numeric | NO | - | French students percentage |
| `saudi_percent` | numeric | NO | - | Saudi students percentage |
| `other_percent` | numeric | NO | - | Other nationalities percentage |
| `created_at` | timestamptz | NO | now() | Record creation timestamp |
| `updated_at` | timestamptz | NO | now() | Last update timestamp |
| `deleted_at` | timestamptz | YES | NULL | Soft delete timestamp |

**Constraint**: `french_percent + saudi_percent + other_percent = 100`

---

### 3.3 `class_structures`

Calculated class formations based on enrollment.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | uuid | NO | gen_random_uuid() | Primary key |
| `budget_version_id` | uuid | NO | - | FK to budget_versions |
| `level_id` | uuid | NO | - | FK to academic_levels |
| `total_students` | integer | NO | - | Total students at this level |
| `number_of_classes` | integer | NO | - | Number of classes formed |
| `avg_class_size` | numeric | NO | - | Average class size |
| `requires_atsem` | boolean | NO | false | Whether ATSEM is required |
| `atsem_count` | integer | NO | 0 | Number of ATSEM needed |
| `calculation_method` | varchar | NO | 'target' | Method used (target, min, max, custom) |
| `notes` | text | YES | NULL | Class formation notes |
| `created_at` | timestamptz | NO | now() | Record creation timestamp |
| `updated_at` | timestamptz | NO | now() | Last update timestamp |
| `created_by_id` | uuid | YES | NULL | FK to auth.users |
| `updated_by_id` | uuid | YES | NULL | FK to auth.users |
| `deleted_at` | timestamptz | YES | NULL | Soft delete timestamp |

**Constraints**:
- `total_students >= 0`
- `number_of_classes > 0`
- `avg_class_size > 0 AND avg_class_size <= 35`

---

### 3.4 `dhg_subject_hours`

DHG hours calculation per subject and level.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | uuid | NO | gen_random_uuid() | Primary key |
| `budget_version_id` | uuid | NO | - | FK to budget_versions |
| `subject_id` | uuid | NO | - | FK to subjects |
| `level_id` | uuid | NO | - | FK to academic_levels |
| `number_of_classes` | integer | NO | - | Classes at this level (from class_structures) |
| `hours_per_class_per_week` | numeric | NO | - | Hours per class (from subject_hours_matrix) |
| `total_hours_per_week` | numeric | NO | - | Total hours (classes × hours, ×2 if split) |
| `is_split` | boolean | NO | false | Whether classes are split |
| `created_at` | timestamptz | NO | now() | Record creation timestamp |
| `updated_at` | timestamptz | NO | now() | Last update timestamp |
| `created_by_id` | uuid | YES | NULL | FK to auth.users |
| `updated_by_id` | uuid | YES | NULL | FK to auth.users |
| `deleted_at` | timestamptz | YES | NULL | Soft delete timestamp |

**Calculation**:
```
total_hours_per_week = number_of_classes × hours_per_class_per_week × (2 if is_split else 1)
```

---

### 3.5 `dhg_teacher_requirements`

Teacher FTE requirements per subject (DHG calculation result).

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | uuid | NO | gen_random_uuid() | Primary key |
| `budget_version_id` | uuid | NO | - | FK to budget_versions |
| `subject_id` | uuid | NO | - | FK to subjects |
| `total_hours_per_week` | numeric | NO | - | Sum of DHG hours for this subject |
| `standard_teaching_hours` | numeric | NO | - | Standard hours (18h secondary, 24h primary) |
| `simple_fte` | numeric | NO | - | Exact FTE (total_hours / standard_hours) |
| `rounded_fte` | integer | NO | - | Rounded up FTE (ceiling) |
| `hsa_hours` | numeric | NO | 0.00 | Overtime hours needed |
| `created_at` | timestamptz | NO | now() | Record creation timestamp |
| `updated_at` | timestamptz | NO | now() | Last update timestamp |
| `created_by_id` | uuid | YES | NULL | FK to auth.users |
| `updated_by_id` | uuid | YES | NULL | FK to auth.users |
| `deleted_at` | timestamptz | YES | NULL | Soft delete timestamp |

**Calculation**:
```
simple_fte = total_hours_per_week / standard_teaching_hours
rounded_fte = CEILING(simple_fte)
hsa_hours = (rounded_fte × standard_teaching_hours) - total_hours_per_week
```

---

### 3.6 `teacher_allocations`

Actual teacher assignments (TRMD - Gap Analysis).

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | uuid | NO | gen_random_uuid() | Primary key |
| `budget_version_id` | uuid | NO | - | FK to budget_versions |
| `subject_id` | uuid | NO | - | FK to subjects |
| `cycle_id` | uuid | NO | - | FK to academic_cycles |
| `category_id` | uuid | NO | - | FK to teacher_categories |
| `fte_count` | numeric | NO | - | Number of FTE allocated |
| `notes` | text | YES | NULL | Allocation notes (teacher names, etc.) |
| `created_at` | timestamptz | NO | now() | Record creation timestamp |
| `updated_at` | timestamptz | NO | now() | Last update timestamp |
| `created_by_id` | uuid | YES | NULL | FK to auth.users |
| `updated_by_id` | uuid | YES | NULL | FK to auth.users |
| `deleted_at` | timestamptz | YES | NULL | Soft delete timestamp |

**Constraint**: `fte_count > 0`

---

### 3.7 `revenue_plans`

Revenue projections by account code.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | uuid | NO | gen_random_uuid() | Primary key |
| `budget_version_id` | uuid | NO | - | FK to budget_versions |
| `account_code` | varchar | NO | - | PCG revenue account (70xxx-77xxx) |
| `description` | text | NO | - | Line item description |
| `category` | varchar | NO | - | Category (tuition, fees, other) |
| `amount_sar` | numeric | NO | - | Revenue amount in SAR |
| `is_calculated` | boolean | NO | false | Whether auto-calculated |
| `calculation_driver` | varchar | YES | NULL | Driver reference |
| `trimester` | integer | YES | NULL | Trimester (1-3) or NULL for annual |
| `notes` | text | YES | NULL | Revenue notes |
| `created_at` | timestamptz | NO | now() | Record creation timestamp |
| `updated_at` | timestamptz | NO | now() | Last update timestamp |
| `created_by_id` | uuid | YES | NULL | FK to auth.users |
| `updated_by_id` | uuid | YES | NULL | FK to auth.users |
| `deleted_at` | timestamptz | YES | NULL | Soft delete timestamp |

**Constraint**: `amount_sar >= 0`

---

### 3.8 `personnel_cost_plans`

Personnel cost projections (salaries, benefits, social charges).

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | uuid | NO | gen_random_uuid() | Primary key |
| `budget_version_id` | uuid | NO | - | FK to budget_versions |
| `account_code` | varchar | NO | - | PCG expense account (64xxx) |
| `description` | text | NO | - | Cost description |
| `category_id` | uuid | YES | NULL | FK to teacher_categories |
| `cycle_id` | uuid | YES | NULL | FK to academic_cycles |
| `fte_count` | numeric | NO | - | Number of FTE |
| `unit_cost_sar` | numeric | NO | - | Cost per FTE (SAR/year) |
| `total_cost_sar` | numeric | NO | - | Total cost (FTE × unit_cost) |
| `is_calculated` | boolean | NO | false | Whether auto-calculated |
| `calculation_driver` | varchar | YES | NULL | Driver reference |
| `notes` | text | YES | NULL | Cost notes |
| `created_at` | timestamptz | NO | now() | Record creation timestamp |
| `updated_at` | timestamptz | NO | now() | Last update timestamp |
| `created_by_id` | uuid | YES | NULL | FK to auth.users |
| `updated_by_id` | uuid | YES | NULL | FK to auth.users |
| `deleted_at` | timestamptz | YES | NULL | Soft delete timestamp |

**Constraint**: `fte_count >= 0`

---

### 3.9 `operating_cost_plans`

Operating expense projections (non-personnel).

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | uuid | NO | gen_random_uuid() | Primary key |
| `budget_version_id` | uuid | NO | - | FK to budget_versions |
| `account_code` | varchar | NO | - | PCG expense account (60xxx-68xxx) |
| `description` | text | NO | - | Expense description |
| `category` | varchar | NO | - | Category (supplies, utilities, etc.) |
| `amount_sar` | numeric | NO | - | Expense amount in SAR |
| `is_calculated` | boolean | NO | false | Whether auto-calculated |
| `calculation_driver` | varchar | YES | NULL | Driver reference |
| `notes` | text | YES | NULL | Expense notes |
| `created_at` | timestamptz | NO | now() | Record creation timestamp |
| `updated_at` | timestamptz | NO | now() | Last update timestamp |
| `created_by_id` | uuid | YES | NULL | FK to auth.users |
| `updated_by_id` | uuid | YES | NULL | FK to auth.users |
| `deleted_at` | timestamptz | YES | NULL | Soft delete timestamp |

**Constraint**: `amount_sar >= 0`

---

### 3.10 `capex_plans`

Capital expenditure projections (asset purchases).

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | uuid | NO | gen_random_uuid() | Primary key |
| `budget_version_id` | uuid | NO | - | FK to budget_versions |
| `account_code` | varchar | NO | - | PCG account code (20xxx-21xxx) |
| `description` | text | NO | - | Asset description |
| `category` | varchar | NO | - | Category (equipment, IT, furniture, etc.) |
| `quantity` | integer | NO | - | Number of units |
| `unit_cost_sar` | numeric | NO | - | Cost per unit (SAR) |
| `total_cost_sar` | numeric | NO | - | Total cost |
| `acquisition_date` | date | NO | - | Expected acquisition date |
| `useful_life_years` | integer | NO | - | Depreciation life (years) |
| `notes` | text | YES | NULL | CapEx notes and justification |
| `created_at` | timestamptz | NO | now() | Record creation timestamp |
| `updated_at` | timestamptz | NO | now() | Last update timestamp |
| `created_by_id` | uuid | YES | NULL | FK to auth.users |
| `updated_by_id` | uuid | YES | NULL | FK to auth.users |
| `deleted_at` | timestamptz | YES | NULL | Soft delete timestamp |

**Constraints**:
- `quantity > 0`
- `useful_life_years > 0 AND useful_life_years <= 50`

---

### 3.11 `planning_cells`

Cell-level planning data for AG Grid writeback.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | uuid | NO | gen_random_uuid() | Primary key |
| `budget_version_id` | uuid | NO | - | FK to budget_versions |
| `module` | varchar | NO | - | Module identifier |
| `row_key` | varchar | NO | - | Row identifier |
| `column_key` | varchar | NO | - | Column identifier |
| `value` | jsonb | NO | - | Cell value |
| `created_at` | timestamptz | NO | now() | Record creation timestamp |
| `updated_at` | timestamptz | NO | now() | Last update timestamp |
| `created_by_id` | uuid | YES | NULL | FK to auth.users |
| `updated_by_id` | uuid | YES | NULL | FK to auth.users |
| `deleted_at` | timestamptz | YES | NULL | Soft delete timestamp |

---

### 3.12 `cell_changes`

Audit trail for cell changes.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | uuid | NO | gen_random_uuid() | Primary key |
| `budget_version_id` | uuid | NO | - | FK to budget_versions |
| `module` | varchar | NO | - | Module identifier |
| `row_key` | varchar | NO | - | Row identifier |
| `column_key` | varchar | NO | - | Column identifier |
| `old_value` | jsonb | YES | NULL | Previous value |
| `new_value` | jsonb | NO | - | New value |
| `changed_at` | timestamptz | NO | now() | When change occurred |
| `changed_by_id` | uuid | NO | - | FK to auth.users |

---

## 4. Consolidation Layer (Modules 13-14)

### 4.1 `budget_consolidations`

Aggregated revenues and costs by account code.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | uuid | NO | gen_random_uuid() | Primary key |
| `budget_version_id` | uuid | NO | - | FK to budget_versions |
| `account_code` | varchar | NO | - | French PCG account code |
| `account_name` | varchar | NO | - | Account name |
| `consolidation_category` | consolidationcategory | NO | - | Grouping category enum |
| `is_revenue` | boolean | NO | false | True if revenue (70xxx-77xxx) |
| `amount_sar` | numeric | NO | 0.00 | Total amount in SAR |
| `source_table` | varchar | NO | - | Source table name |
| `source_count` | integer | NO | 0 | Number of source records |
| `is_calculated` | boolean | NO | true | True if auto-calculated |
| `notes` | text | YES | NULL | Notes or explanations |
| `created_at` | timestamptz | NO | now() | Record creation timestamp |
| `created_by_id` | uuid | YES | NULL | FK to auth.users |
| `updated_at` | timestamptz | NO | now() | Last update timestamp |
| `updated_by_id` | uuid | YES | NULL | FK to auth.users |
| `deleted_at` | timestamptz | YES | NULL | Soft delete timestamp |

---

### 4.2 `financial_statements`

Financial statement headers.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | uuid | NO | gen_random_uuid() | Primary key |
| `budget_version_id` | uuid | NO | - | FK to budget_versions |
| `statement_type` | statementtype | NO | - | Type enum |
| `statement_format` | statementformat | NO | - | Format enum (french_pcg, ifrs) |
| `statement_name` | varchar | NO | - | Statement name |
| `fiscal_year` | integer | NO | - | Fiscal year |
| `total_amount_sar` | numeric | NO | 0.00 | Total statement amount |
| `is_calculated` | boolean | NO | true | True if auto-calculated |
| `notes` | text | YES | NULL | Notes |
| `created_at` | timestamptz | NO | now() | Record creation timestamp |
| `created_by_id` | uuid | YES | NULL | FK to auth.users |
| `updated_at` | timestamptz | NO | now() | Last update timestamp |
| `updated_by_id` | uuid | YES | NULL | FK to auth.users |
| `deleted_at` | timestamptz | YES | NULL | Soft delete timestamp |

---

### 4.3 `financial_statement_lines`

Individual line items in financial statements.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | uuid | NO | gen_random_uuid() | Primary key |
| `statement_id` | uuid | NO | - | FK to financial_statements |
| `line_number` | integer | NO | - | Sequential line number |
| `line_type` | linetype | NO | - | Type enum |
| `indent_level` | integer | NO | 0 | Indentation (0-3) |
| `line_code` | varchar | YES | NULL | Account or section code |
| `line_description` | varchar | NO | - | Line description |
| `amount_sar` | numeric | YES | NULL | Amount (null for headers) |
| `is_bold` | boolean | NO | false | Display in bold |
| `is_underlined` | boolean | NO | false | Underlined (for totals) |
| `source_consolidation_category` | varchar | YES | NULL | Source category |
| `created_at` | timestamptz | NO | now() | Record creation timestamp |
| `created_by_id` | uuid | YES | NULL | FK to auth.users |
| `updated_at` | timestamptz | NO | now() | Last update timestamp |
| `updated_by_id` | uuid | YES | NULL | FK to auth.users |
| `deleted_at` | timestamptz | YES | NULL | Soft delete timestamp |

**Constraints**:
- `line_number > 0`
- `indent_level >= 0 AND indent_level <= 3`

---

## 5. Analysis Layer (Modules 15-17)

### 5.1 `kpi_definitions`

KPI metadata catalog with formulas and targets.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | uuid | NO | gen_random_uuid() | Primary key |
| `code` | varchar | NO | - | Unique KPI code (e.g., 'H_E_RATIO') |
| `name_en` | varchar | NO | - | KPI name in English |
| `name_fr` | varchar | NO | - | KPI name in French |
| `category` | kpicategory | NO | - | Category enum |
| `formula_text` | text | NO | - | Human-readable formula |
| `unit` | varchar | NO | - | Unit of measure |
| `target_value` | numeric | YES | NULL | Target benchmark |
| `min_acceptable` | numeric | YES | NULL | Minimum acceptable |
| `max_acceptable` | numeric | YES | NULL | Maximum acceptable |
| `is_active` | boolean | NO | true | Whether actively calculated |
| `description` | text | YES | NULL | Detailed description |
| `created_at` | timestamptz | NO | now() | Record creation timestamp |
| `updated_at` | timestamptz | NO | now() | Last update timestamp |
| `created_by_id` | uuid | YES | NULL | FK to auth.users |
| `updated_by_id` | uuid | YES | NULL | FK to auth.users |
| `deleted_at` | timestamptz | YES | NULL | Soft delete timestamp |

**Constraint**: `target_value >= 0`

**Key KPIs**:
| code | name_en | formula | target |
|------|---------|---------|--------|
| H_E_RATIO | Hours per Student | Total Teaching Hours / Total Students | 1.2-1.5 |
| E_D_RATIO | Students per Class | Total Students / Total Classes | 25-28 |
| STAFF_COST_PCT | Staff Cost Ratio | Personnel Costs / Total Revenue | 65-75% |
| OPER_MARGIN | Operating Margin | Operating Result / Total Revenue | 5-10% |

---

### 5.2 `kpi_values`

Calculated KPI values per budget version.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | uuid | NO | gen_random_uuid() | Primary key |
| `budget_version_id` | uuid | NO | - | FK to budget_versions |
| `kpi_definition_id` | uuid | NO | - | FK to kpi_definitions |
| `calculated_value` | numeric | NO | - | Calculated KPI value |
| `variance_from_target` | numeric | YES | NULL | Variance (calculated - target) |
| `variance_percent` | numeric | YES | NULL | Variance as percentage |
| `calculation_inputs` | jsonb | NO | - | Inputs used (audit trail) |
| `calculated_at` | timestamptz | NO | now() | When calculated |
| `notes` | text | YES | NULL | Notes or interpretation |
| `created_at` | timestamptz | NO | now() | Record creation timestamp |
| `updated_at` | timestamptz | NO | now() | Last update timestamp |
| `created_by_id` | uuid | YES | NULL | FK to auth.users |
| `updated_by_id` | uuid | YES | NULL | FK to auth.users |
| `deleted_at` | timestamptz | YES | NULL | Soft delete timestamp |

---

### 5.3 `dashboard_configs`

Dashboard definitions (system templates + user custom).

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | uuid | NO | gen_random_uuid() | Primary key |
| `name` | varchar | NO | - | Dashboard name |
| `description` | text | YES | NULL | Purpose and contents |
| `dashboard_role` | dashboardrole | YES | NULL | Role for system templates |
| `is_system_template` | boolean | NO | false | True for pre-defined |
| `owner_user_id` | uuid | YES | NULL | FK to auth.users |
| `is_public` | boolean | NO | false | Visible to others |
| `is_default` | boolean | NO | false | Default for role/user |
| `layout_config` | jsonb | NO | - | Grid layout configuration |
| `created_at` | timestamptz | NO | now() | Record creation timestamp |
| `updated_at` | timestamptz | NO | now() | Last update timestamp |
| `created_by_id` | uuid | YES | NULL | FK to auth.users |
| `updated_by_id` | uuid | YES | NULL | FK to auth.users |
| `deleted_at` | timestamptz | YES | NULL | Soft delete timestamp |

---

### 5.4 `dashboard_widgets`

Widget definitions within dashboards.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | uuid | NO | gen_random_uuid() | Primary key |
| `dashboard_config_id` | uuid | NO | - | FK to dashboard_configs |
| `widget_type` | widgettype | NO | - | Type enum |
| `title` | varchar | NO | - | Widget title |
| `data_source_query` | text | NO | - | Query identifier or API endpoint |
| `widget_config` | jsonb | NO | - | Widget-specific configuration |
| `position_x` | integer | NO | - | Grid position X (0-11) |
| `position_y` | integer | NO | - | Grid position Y (0+) |
| `width` | integer | NO | - | Width in grid columns (1-12) |
| `height` | integer | NO | - | Height in grid rows (1-10) |
| `sort_order` | integer | NO | 0 | Display order |
| `refresh_interval_seconds` | integer | YES | NULL | Auto-refresh interval |
| `created_at` | timestamptz | NO | now() | Record creation timestamp |
| `updated_at` | timestamptz | NO | now() | Last update timestamp |
| `created_by_id` | uuid | YES | NULL | FK to auth.users |
| `updated_by_id` | uuid | YES | NULL | FK to auth.users |
| `deleted_at` | timestamptz | YES | NULL | Soft delete timestamp |

**Constraints**:
- `position_x >= 0 AND position_x < 12`
- `position_y >= 0`
- `width > 0 AND width <= 12`
- `height > 0 AND height <= 10`

---

### 5.5 `actual_data`

Actual financial data imported from Odoo GL.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | uuid | NO | gen_random_uuid() | Primary key |
| `fiscal_year` | integer | NO | - | Fiscal year (2020-2099) |
| `period` | integer | NO | - | Month (0-12, 0 = annual total) |
| `account_code` | varchar | NO | - | French PCG account code |
| `account_name` | varchar | YES | NULL | Account name from Odoo |
| `amount_sar` | numeric | NO | - | Actual amount in SAR |
| `currency` | varchar | NO | 'SAR' | Original currency code |
| `import_batch_id` | uuid | NO | - | Batch import identifier |
| `import_date` | timestamptz | NO | now() | When imported |
| `source` | actualdatasource | NO | 'odoo_import' | Source enum |
| `transaction_date` | date | YES | NULL | Original transaction date |
| `description` | text | YES | NULL | Transaction description |
| `is_reconciled` | boolean | NO | false | Whether validated |
| `created_at` | timestamptz | NO | now() | Record creation timestamp |
| `updated_at` | timestamptz | NO | now() | Last update timestamp |
| `created_by_id` | uuid | YES | NULL | FK to auth.users |
| `updated_by_id` | uuid | YES | NULL | FK to auth.users |
| `deleted_at` | timestamptz | YES | NULL | Soft delete timestamp |

**Constraints**:
- `fiscal_year >= 2020 AND fiscal_year <= 2099`
- `period >= 0 AND period <= 12`

---

### 5.6 `budget_vs_actual`

Variance analysis comparing budget to actual.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | uuid | NO | gen_random_uuid() | Primary key |
| `budget_version_id` | uuid | NO | - | FK to budget_versions |
| `account_code` | varchar | NO | - | French PCG account code |
| `period` | integer | NO | - | Month (1-12) |
| `budget_amount_sar` | numeric | NO | - | Budgeted amount |
| `actual_amount_sar` | numeric | NO | - | Actual amount |
| `variance_sar` | numeric | NO | - | Variance |
| `variance_percent` | numeric | NO | - | Variance percentage |
| `variance_status` | variancestatus | NO | - | Favorability enum |
| `ytd_budget_sar` | numeric | NO | - | Year-to-date budget |
| `ytd_actual_sar` | numeric | NO | - | Year-to-date actual |
| `ytd_variance_sar` | numeric | NO | - | Year-to-date variance |
| `is_material` | boolean | NO | false | Exceeds materiality threshold |
| `created_at` | timestamptz | NO | now() | Record creation timestamp |
| `updated_at` | timestamptz | NO | now() | Last update timestamp |
| `created_by_id` | uuid | YES | NULL | FK to auth.users |
| `updated_by_id` | uuid | YES | NULL | FK to auth.users |
| `deleted_at` | timestamptz | YES | NULL | Soft delete timestamp |

**Constraint**: `period >= 1 AND period <= 12`

---

### 5.7 `variance_explanations`

User-provided explanations for variances.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | uuid | NO | gen_random_uuid() | Primary key |
| `budget_vs_actual_id` | uuid | NO | - | FK to budget_vs_actual |
| `explanation_text` | text | NO | - | Detailed explanation (min 10 chars) |
| `root_cause` | varchar | NO | - | Root cause category |
| `corrective_action` | text | YES | NULL | Planned corrective action |
| `action_deadline` | date | YES | NULL | Deadline for action |
| `is_resolved` | boolean | NO | false | Whether resolved |
| `created_at` | timestamptz | NO | now() | Record creation timestamp |
| `updated_at` | timestamptz | NO | now() | Last update timestamp |
| `created_by_id` | uuid | YES | NULL | FK to auth.users |
| `updated_by_id` | uuid | YES | NULL | FK to auth.users |
| `deleted_at` | timestamptz | YES | NULL | Soft delete timestamp |

**Constraint**: `length(explanation_text) > 10`

---

### 5.8 `user_preferences`

User-specific preferences and settings.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | uuid | NO | gen_random_uuid() | Primary key |
| `user_id` | uuid | NO | - | FK to auth.users (unique) |
| `default_dashboard_id` | uuid | YES | NULL | FK to dashboard_configs |
| `theme` | varchar | NO | 'light' | UI theme (light, dark, auto) |
| `default_fiscal_year` | integer | YES | NULL | Default fiscal year filter |
| `display_preferences` | jsonb | NO | '{}' | Number format, language, etc. |
| `notification_settings` | jsonb | NO | '{}' | Email alerts, notifications |
| `created_at` | timestamptz | NO | now() | Record creation timestamp |
| `updated_at` | timestamptz | NO | now() | Last update timestamp |
| `created_by_id` | uuid | YES | NULL | FK to auth.users |
| `updated_by_id` | uuid | YES | NULL | FK to auth.users |
| `deleted_at` | timestamptz | YES | NULL | Soft delete timestamp |

---

## 6. Strategic Layer (Module 18)

### 6.1 `strategic_plans`

5-year strategic plan headers.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | uuid | NO | gen_random_uuid() | Primary key |
| `name` | varchar | NO | - | Unique plan name |
| `description` | text | YES | NULL | Description and objectives |
| `base_year` | integer | NO | - | Starting year (2000-2100) |
| `status` | varchar | NO | 'draft' | Plan status |
| `created_at` | timestamptz | NO | now() | Record creation timestamp |
| `updated_at` | timestamptz | NO | now() | Last update timestamp |
| `created_by_id` | uuid | YES | NULL | FK to auth.users |
| `updated_by_id` | uuid | YES | NULL | FK to auth.users |
| `deleted_at` | timestamptz | YES | NULL | Soft delete timestamp |

**Constraint**: `base_year >= 2000 AND base_year <= 2100`

---

### 6.2 `strategic_plan_scenarios`

Scenarios within strategic plans.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | uuid | NO | gen_random_uuid() | Primary key |
| `strategic_plan_id` | uuid | NO | - | FK to strategic_plans |
| `scenario_type` | scenariotype | NO | - | Type enum |
| `name` | varchar | NO | - | User-friendly name |
| `description` | text | YES | NULL | Description and assumptions |
| `enrollment_growth_rate` | numeric | NO | - | Annual enrollment growth (-50% to +100%) |
| `fee_increase_rate` | numeric | NO | - | Annual fee increase (-20% to +50%) |
| `salary_inflation_rate` | numeric | NO | - | Annual salary inflation (-20% to +50%) |
| `operating_inflation_rate` | numeric | NO | - | Annual operating inflation (-20% to +50%) |
| `additional_assumptions` | jsonb | YES | NULL | Additional assumptions |
| `created_at` | timestamptz | NO | now() | Record creation timestamp |
| `updated_at` | timestamptz | NO | now() | Last update timestamp |
| `created_by_id` | uuid | YES | NULL | FK to auth.users |
| `updated_by_id` | uuid | YES | NULL | FK to auth.users |
| `deleted_at` | timestamptz | YES | NULL | Soft delete timestamp |

---

### 6.3 `strategic_plan_projections`

Year-by-year projections per scenario.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | uuid | NO | gen_random_uuid() | Primary key |
| `strategic_plan_scenario_id` | uuid | NO | - | FK to strategic_plan_scenarios |
| `year` | integer | NO | - | Year in plan (1-5) |
| `category` | projectioncategory | NO | - | Category enum |
| `amount_sar` | numeric | NO | - | Projected amount |
| `calculation_inputs` | jsonb | YES | NULL | Calculation inputs |
| `created_at` | timestamptz | NO | now() | Record creation timestamp |
| `updated_at` | timestamptz | NO | now() | Last update timestamp |
| `created_by_id` | uuid | YES | NULL | FK to auth.users |
| `updated_by_id` | uuid | YES | NULL | FK to auth.users |
| `deleted_at` | timestamptz | YES | NULL | Soft delete timestamp |

**Constraints**:
- `year >= 1 AND year <= 5`
- `amount_sar >= 0`

---

### 6.4 `strategic_initiatives`

Strategic initiatives with budgets.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | uuid | NO | gen_random_uuid() | Primary key |
| `strategic_plan_id` | uuid | NO | - | FK to strategic_plans |
| `name` | varchar | NO | - | Initiative name |
| `description` | text | YES | NULL | Description and deliverables |
| `planned_year` | integer | NO | - | Year in plan (1-5) |
| `budget_sar` | numeric | NO | - | Initiative budget |
| `priority` | varchar | NO | 'medium' | Priority level |
| `status` | varchar | NO | 'planned' | Initiative status |
| `created_at` | timestamptz | NO | now() | Record creation timestamp |
| `updated_at` | timestamptz | NO | now() | Last update timestamp |
| `created_by_id` | uuid | YES | NULL | FK to auth.users |
| `updated_by_id` | uuid | YES | NULL | FK to auth.users |
| `deleted_at` | timestamptz | YES | NULL | Soft delete timestamp |

**Constraints**:
- `planned_year >= 1 AND planned_year <= 5`
- `budget_sar >= 0`

---

## 7. System Tables

### 7.1 `alembic_version`

Alembic migration version tracking.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `version_num` | varchar | NO | - | Migration version number |

---

## 8. Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CONFIGURATION LAYER                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  academic_cycles ──┬──> academic_levels                                     │
│                    │                                                        │
│  subjects          │    nationality_types    fee_categories                 │
│                    │                                                        │
│  teacher_categories│    system_configs                                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          VERSION CONTROL                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                         budget_versions                                      │
│                              │                                              │
│    ┌─────────────────────────┼─────────────────────────┐                    │
│    │                         │                         │                    │
│    ▼                         ▼                         ▼                    │
│ class_size_params    subject_hours_matrix    teacher_cost_params            │
│                                                                             │
│ fee_structure        timetable_constraints                                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PLANNING LAYER                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  enrollment_plans ──> class_structures ──> dhg_subject_hours                │
│         │                                        │                          │
│         │                                        ▼                          │
│         │                              dhg_teacher_requirements              │
│         │                                        │                          │
│         │                                        ▼                          │
│         │                              teacher_allocations                   │
│         │                                        │                          │
│         ▼                                        ▼                          │
│  revenue_plans ◄────────────────────── personnel_cost_plans                 │
│         │                                        │                          │
│         │            operating_cost_plans        │                          │
│         │                   │                    │                          │
│         │            capex_plans                 │                          │
│         │                   │                    │                          │
│         └───────────────────┴────────────────────┘                          │
│                             │                                               │
└─────────────────────────────┼───────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        CONSOLIDATION LAYER                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                    budget_consolidations                                     │
│                             │                                               │
│                             ▼                                               │
│                    financial_statements                                      │
│                             │                                               │
│                             ▼                                               │
│                 financial_statement_lines                                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          ANALYSIS LAYER                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  kpi_definitions ──> kpi_values                                             │
│                                                                             │
│  dashboard_configs ──> dashboard_widgets                                    │
│                                                                             │
│  actual_data ──> budget_vs_actual ──> variance_explanations                 │
│                                                                             │
│  user_preferences                                                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         STRATEGIC LAYER                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  strategic_plans ──┬──> strategic_plan_scenarios ──> strategic_plan_projections
│                    │                                                        │
│                    └──> strategic_initiatives                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 9. Enums Reference

### `budgetversionstatus`
```sql
'working' | 'submitted' | 'approved' | 'forecast' | 'superseded'
```

### `consolidationcategory`
```sql
'revenue_tuition' | 'revenue_fees' | 'revenue_other' |
'personnel_teaching' | 'personnel_admin' | 'personnel_support' | 'personnel_social' |
'operating_supplies' | 'operating_utilities' | 'operating_maintenance' | 'operating_insurance' | 'operating_other' |
'capex_equipment' | 'capex_it' | 'capex_furniture' | 'capex_building' | 'capex_software'
```

### `statementtype`
```sql
'income_statement' | 'balance_sheet_assets' | 'balance_sheet_liabilities' | 'cash_flow'
```

### `statementformat`
```sql
'french_pcg' | 'ifrs'
```

### `linetype`
```sql
'section_header' | 'account_group' | 'account_line' | 'subtotal' | 'total'
```

### `kpicategory`
```sql
'educational' | 'financial' | 'operational' | 'strategic'
```

### `dashboardrole`
```sql
'executive' | 'finance_manager' | 'department' | 'operations'
```

### `widgettype`
```sql
'kpi_card' | 'chart' | 'table' | 'variance_table' | 'waterfall' | 'gauge' | 'timeline' | 'heatmap'
```

### `actualdatasource`
```sql
'odoo_import' | 'manual_entry' | 'system_calc'
```

### `variancestatus`
```sql
'favorable' | 'unfavorable' | 'neutral' | 'not_applicable'
```

### `scenariotype`
```sql
'base_case' | 'conservative' | 'optimistic' | 'new_campus'
```

### `projectioncategory`
```sql
'revenue' | 'personnel_costs' | 'operating_costs' | 'capex' | 'depreciation'
```

---

## Appendix: Common Audit Columns

Most tables include these standard audit columns:

| Column | Type | Description |
|--------|------|-------------|
| `created_at` | timestamptz | Record creation timestamp (default: now()) |
| `updated_at` | timestamptz | Last update timestamp (default: now()) |
| `created_by_id` | uuid | FK to auth.users who created the record |
| `updated_by_id` | uuid | FK to auth.users who last updated |
| `deleted_at` | timestamptz | Soft delete timestamp (NULL if active) |

All user foreign keys reference `auth.users.id` (Supabase Auth).
