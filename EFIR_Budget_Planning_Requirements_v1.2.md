# EFIR School Budget Planning Application
## Functional Requirements Specification - Version 1.2
**November 2025**

| Field | Value |
|-------|-------|
| Document Status | Draft |
| Prepared For | École Française Internationale de Riyad (EFIR) |
| Document Type | Functional Requirements Specification (FRS) |
| AEFE Status | Conventionné |
| Primary Currency | SAR (Saudi Riyal) |
| Confidentiality | Internal Use Only |

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Key Objectives](#key-objectives)
3. [School Profile - EFIR](#school-profile---efir)
4. [Fee Structure (2025-2026)](#fee-structure-2025-2026)
5. [Personnel Structure](#personnel-structure)
6. [Curriculum & Teaching Hours](#curriculum--teaching-hours)
7. [Budget Overview](#budget-overview)
8. [Chart of Accounts](#chart-of-accounts)
9. [System Architecture](#system-architecture)
10. [Workforce Planning Model](#workforce-planning-model)
11. [Application Modules](#application-modules)
12. [Key Ratios & Benchmarks](#key-ratios--benchmarks)
13. [Glossary of Terms](#glossary-of-terms)

---

## Executive Summary

This document defines the functional requirements for a comprehensive School Budget Planning Application designed specifically for École Française Internationale de Riyad (EFIR), operating under AEFE (Agence pour l'enseignement français à l'étranger) guidelines as a Conventionné school.

The application addresses the unique challenges of planning and managing school budgets that span two distinct periods within a calendar year:
- The continuation of the current academic year (January-June)
- The start of the new academic year (September-December)

The system uses SAR (Saudi Riyal) as its primary currency while supporting EUR conversion for AEFE reporting.

The system provides driver-based budgeting capabilities, where costs are automatically calculated based on key operational drivers such as enrollment, class structures, teacher requirements, and facility utilization. This approach ensures accuracy, consistency, and enables powerful what-if scenario analysis for management decision-making.

---

## Key Objectives

- **Accurate Enrollment-Driven Revenue**: Provide accurate enrollment-driven revenue projections by grade level and nationality category (French, Saudi, Other)

- **Comprehensive Teacher Workforce Planning**: Enable comprehensive teacher workforce planning considering AEFE allocations (24 school-paid + 4 AEFE-funded positions), local recruitment, and timetable constraints

- **Dual-Period Budget Planning**: Support dual-period budget planning (Academic Year continuation January-June + New Academic Year start September-December)

- **Driver-Based Cost Planning**: Deliver driver-based cost planning with automatic calculations using DHG (Dotation Horaire Globale) methodology

- **Financial Reporting Standards**: Generate both French GAP (Plan Comptable Général) and IFRS-compliant financial statements

- **Robust Approval Workflows**: Implement robust approval workflows aligned with governance requirements

- **Real-Time Dashboards**: Provide real-time dashboards and variance analysis capabilities

---

## School Profile - EFIR

### Overview

| Attribute | Value |
|-----------|-------|
| School Name | École Française Internationale de Riyad (EFIR) |
| Location | Riyadh, Saudi Arabia |
| AEFE Status | Conventionné |
| Academic Year | September to June |
| Weekend | Friday - Saturday (Saudi calendar) |
| Primary Currency | SAR (Saudi Riyal) |
| Maximum Capacity | ~1,875 students |
| Current Enrollment (2024-25) | ~1,796 students |
| Total Classes | 73 classes |
| Total Staff | ~210 (182 local + 28 AEFE) |

### Enrollment History

| Academic Year | Students | Classes | Growth |
|---------------|----------|---------|--------|
| 2021-2022 | 1,430 | 71 | -6.4% |
| 2022-2023 | 1,499 | 67 | +4.8% |
| 2023-2024 | 1,587 | 75 | +5.9% |
| 2024-2025 | 1,796 | 73 | +13.2% |
| 2025-2026 (proj) | 1,825 | 75 | +1.6% |

### Enrollment by Level (2023-2024)

| Cycle | Levels | Students | Classes | Avg Size |
|-------|--------|----------|---------|----------|
| Maternelle | PS, MS, GS | 249 | 11 | 22.6 |
| Élémentaire | CP, CE1, CE2, CM1, CM2 | 607 | 25 | 24.3 |
| Collège | 6ème, 5ème, 4ème, 3ème | 450 | 18 | 25.0 |
| Lycée | 2nde, 1ère, Terminale | 281 | 11 | 25.5 |
| **TOTAL** | — | **1,587** | **75** | **21.2** |

### Nationality Distribution (2023-2024)

| Category | Students | Percentage | Fee Basis |
|----------|----------|------------|-----------|
| French (Français) | 503 | 31.7% | TTC (VAT inclusive) |
| Saudi Nationals | 60 | 3.8% | HT (VAT exempt) |
| Other Nationalities | 1,024 | 64.5% | TTC (VAT inclusive) |
| **TOTAL** | **1,587** | **100%** | — |

---

## Fee Structure (2025-2026)

### Annual Tuition Fees (SAR)

| Level | French (TTC) | Saudi (HT) | Other (TTC) | DAI |
|-------|--------------|------------|-------------|-----|
| Maternelle PS | 30,000 | 34,783 | 40,000 | 5,000 |
| Maternelle MS-GS | 34,500 | 35,650 | 41,000 | 5,000 |
| Élémentaire (CP-CM2) | 34,500 | 35,650 | 41,000 | 5,000 |
| Collège (6ème-3ème) | 34,500 | 35,650 | 41,000 | 5,000 |
| Lycée (2nde-Term) | 38,500 | 40,000 | 46,000 | 5,000 |

**DAI = Droit Annuel d'Inscription (Annual Enrollment Fee)**

### Payment Schedule

| Trimester | Period | Due Date | % of Total |
|-----------|--------|----------|------------|
| T1 | September - December | August 20 | 40% |
| T2 | January - March | January 1 | 30% |
| T3 | April - June | April 1 | 30% |

### Discount Policies

- **Sibling Discount**: 25% reduction on tuition for 3rd child and beyond
- **Staff Discount**: Applicable (tracked separately in budget)
- **Note**: Discounts NOT applicable on registration fees or DAI

---

## Personnel Structure

### Staff Categories

| Category | Count | Notes |
|----------|-------|-------|
| Teachers (Enseignants) | 122 | Local contract |
| AEFE Teachers (Detached) | 24 | School pays PRRD contribution |
| AEFE Teachers (Funded) | 4 | Fully AEFE-funded |
| ASEM (Classroom Assistants) | 14 | Maternelle support |
| Administration | 22 | Office & support |
| Direction | 5 | Management team |
| Vie Scolaire | 14 | Student life |
| Other | 5 | Inclusion, training, etc. |
| **TOTAL** | **~210** | — |

### AEFE Teacher Structure

EFIR has 28 AEFE-assigned teachers, structured as follows:

| Category | Count | Cost Bearer | School Contribution |
|----------|-------|-------------|---------------------|
| Détachés (Residents) | 24 | School (PRRD) | ~41,863 EUR/teacher |
| Funded by AEFE | 4 | AEFE | None |
| **TOTAL** | **28** | — | — |

*PRRD = Participation à la Rémunération des Résidents Détachés*

### Local Staff Salary Structure (SAR/month)

| Position | Count | Base Range | Avg Net |
|----------|-------|------------|---------|
| Professeur des écoles (Primary) | 30 | 8,000-12,750 | 12,500 |
| Enseignant second degré (Secondary) | 43 | 4,000-12,000 | 12,613 |
| Enseignant langue étrangère | 24 | 3,700-14,250 | 13,500 |
| Professeur EPS | 4 | 8,500-12,250 | 13,062 |
| Assistante maternelle (ASEM) | 13 | 5,800-8,500 | 9,900 |
| Assistant d'éducation | 12 | 7,000-9,000 | 10,575 |
| Administrative Staff | ~20 | 7,000-13,750 | 12,000-17,000 |

### Salary Components

- **Base Salary**: Variable by position and experience
- **Housing Allowance (IL)**: 2,500 SAR/month (standard)
- **Transport Allowance (IT)**: 500 SAR/month (standard)
- **Responsibility Premium**: 1,000+ SAR (for management roles)
- **HSA (Overtime)**: Variable, paid over 10 months

---

## Curriculum & Teaching Hours

### Standard Teaching Hours

| Category | Hours/Week | Notes |
|----------|------------|-------|
| Primary Teachers (Professeur des écoles) | 24 | Class-based model |
| Secondary Teachers (Certifiés) | 18 | Subject specialist model |
| Maximum Overtime (HSA) | 2-4 | Additional hours allowed |

### Collège Curriculum Hours (per week)

| Subject | 6ème | 5ème | 4ème | 3ème |
|---------|------|------|------|------|
| Français | 4.5 | 4.5 | 4.5 | 4 |
| Mathématiques | 4.5 | 3.5 | 3.5 | 3.5 |
| Histoire-Géographie | 3 | 3 | 3 | 3.5 |
| Anglais (LV1) | 4 | 3 | 3 | 3 |
| Espagnol (LV2) | — | 2.5 | 2.5 | 2.5 |
| Arabic (LVB) | 2.5 | 2.5 | 2.5 | 2.5 |
| SVT | 3 | 1.5 | 1.5 | 1.5 |
| Physique-Chimie | — | 1.5 | 1.5 | 1.5 |
| EPS | 4 | 3 | 3 | 3 |

*Note: Arabic is a core local subject (LVB - Langue Vivante B) required by Saudi regulations*

### DHG Summary - Secondary Teacher Hours (2025)

| Subject | Total Hours | FTE Needed |
|---------|-------------|------------|
| Mathématiques | 193 | 10.7 |
| Français | 179 | 9.9 |
| Physique-Chimie | 148 | 8.2 |
| EPS | 121 | 6.7 |
| Histoire-Géographie | 119.5 | 6.6 |
| Anglais | 118 | 6.6 |
| SVT | 117.5 | 6.5 |
| Arabic (LVB) | 101.5 | 5.6 |
| Espagnol | 59 | 3.3 |
| Other subjects | ~100 | ~5.5 |

*DHG = Dotation Horaire Globale (Global Hours Allocation). FTE calculated as Total Hours ÷ 18.*

---

## Budget Overview

### Revenue Trend (SAR)

| Year | Revenue | Growth |
|------|---------|--------|
| 2018 | 39,817,724 | — |
| 2019 | 40,583,852 | +1.9% |
| 2020 | 42,164,721 | +3.9% |
| 2021 | 42,460,380 | +0.7% |
| 2022 | 44,622,546 | +5.1% |
| 2023 | 65,477,206 | +46.7% |
| 2024 | 67,516,928 | +3.1% |

### Budget 2024 Summary

| Category | Amount (SAR) | % of Revenue |
|----------|--------------|--------------|
| **REVENUE** | 67,516,928 | 100% |
| **PERSONNEL COSTS** | | |
| Teaching Staff (Local) | 16,355,839 | 24.2% |
| Administrative Staff | 5,272,255 | 7.8% |
| AEFE Contribution (PRRD) | 7,080,587 | 10.5% |
| AEFE Licensing | 4,005,266 | 5.9% |
| Other Personnel | 2,799,542 | 4.1% |
| **Subtotal Personnel** | **35,513,489** | **52.6%** |
| **OCCUPANCY** | | |
| Rent | 8,395,518 | 12.4% |
| Utilities | 1,000,000 | 1.5% |
| Maintenance | 4,723,852 | 7.0% |
| **Subtotal Occupancy** | **14,119,370** | **20.9%** |
| **OTHER COSTS** | | |
| Educational Supplies | 1,856,057 | 2.7% |
| Administrative | 4,455,047 | 6.6% |
| Marketing | 30,000 | 0.0% |
| Depreciation | 5,093,865 | 7.5% |
| **TOTAL EXPENSES** | **61,067,828** | **90.4%** |
| **OPERATING SURPLUS** | **6,449,100** | **9.6%** |

---

## Chart of Accounts

### Accounting Standards

EFIR maintains accounts using the French Plan Comptable Général (PCG). The system will support dual reporting in both French GAP and IFRS formats.

### French PCG Account Classes

| Class | French Description | English | IFRS Mapping |
|-------|-------------------|---------|--------------|
| 1 | Comptes de capitaux | Equity | Equity |
| 2 | Comptes d'immobilisations | Fixed Assets | Non-current Assets |
| 3 | Comptes de stocks | Inventory | Inventories |
| 4 | Comptes de tiers | Receivables/Payables | Trade & Other |
| 5 | Comptes financiers | Cash | Cash & Equivalents |
| 6 | Comptes de charges | Expenses | Operating Expenses |
| 7 | Comptes de produits | Revenue | Revenue |

### Key Revenue Accounts (Class 7)

| Account | Description | IFRS Line |
|---------|-------------|-----------|
| 70110 | Scolarité 1er trimestre | Tuition - T1 |
| 70120 | Scolarité 2ème trimestre | Tuition - T2 |
| 70130 | Scolarité 3ème trimestre | Tuition - T3 |
| 70140 | Droits d'inscription | Enrollment Fees |
| 60900-60902 | Réductions scolarité | Contra-Revenue |
| 73000 | Tests | Examination Fees |
| 77000 | Intérêts bancaires | Finance Income |

### Key Expense Accounts (Class 6)

| Account | Description | Category |
|---------|-------------|----------|
| 64110/64130 | Salaires enseignement | Personnel - Teaching |
| 64140 | Administration | Personnel - Admin |
| 64800 | AEFE - salaires résidents | Personnel - AEFE |
| 64801 | Cotisations AEFE | AEFE Licensing |
| 61310 | Loyer établissement | Occupancy - Rent |
| 61510 | Contrats maintenance | Maintenance |
| 60610-60620 | Électricité, Eau | Utilities |
| 68110 | Dotation amortissements | Depreciation |
| 68175 | Provision fin service | Personnel - Provision |

---

## System Architecture

### Technology Stack

| Component | Technology |
|-----------|------------|
| Frontend | React 18+ with TypeScript, Tailwind CSS, Shadcn/ui |
| Spreadsheet UI | Handsontable (free for non-commercial use) |
| Backend | Python FastAPI for calculation engine |
| Database | Supabase (PostgreSQL) with Row Level Security |
| Authentication | Supabase Auth with role-based access control |
| Charts | Recharts for dashboards and visualizations |
| Real-time | Supabase Realtime for auto-save |

### Budget Period Structure

The application manages budget planning across calendar years while respecting academic year boundaries:

- **Calendar Year Budget**: January to December (financial reporting period)
- **Period 1**: January to June (current academic year continuation)
- **Period 2**: September to December (new academic year start)
- **Summer Period**: July and August (minimal operations)

### Academic Calendar (2025-2026)

| Event | Date |
|-------|------|
| Staff Return (Pré-rentrée) | September 1-2, 2025 |
| Students Return | September 3, 2025 |
| National Day Holiday | September 23, 2025 |
| End of Trimester 1 | December 31, 2025 |
| Eid Al-Fitr | ~March 19, 2026 |
| End of Trimester 2 | March 31, 2026 |
| Eid Al-Adha | ~May 26, 2026 |
| End of Academic Year | June 30, 2026 |

**Working Days**: Sunday to Thursday  
**Weekend**: Friday-Saturday

---

## Workforce Planning Model

### DHG (Dotation Horaire Globale) Methodology

The DHG is the standard French methodology for calculating secondary teacher requirements based on teaching hours. EFIR uses this approach in their current Excel-based planning.

#### Core Calculation Formula

- **Total Hours** = Number of Classes × Hours per Subject per Week
- **Simple FTE** = Total Hours ÷ Standard Teaching Hours (18 for secondary)
- **Constraint-Adjusted FTE** = Simple FTE adjusted for timetable constraints

### H/E Ratio Reference (Hours per Student)

AEFE provides standard H/E ratios for staffing projections based on class size:

| Students/Class | H/E Collège | H/E Lycée |
|----------------|-------------|-----------|
| 20 | 1.71 | 1.97 |
| 24 | 1.46 | 1.68 |
| 26 | 1.27 | 1.40 |
| 28 | 1.38 | 1.46 |

*Interpretation: With 24 students/class, plan for ~1.46 teaching hours per student in Collège.*

### Primary vs Secondary Model

| Aspect | Primary (1er Degré) | Secondary (2nd Degré) |
|--------|-------------------|----------------------|
| Model | Class-based | Hours-based |
| Teacher Type | Generalist | Subject Specialist |
| Standard Hours | 24h/week | 18h/week |
| Calculation | 1 teacher per class | DHG hours ÷ 18 |
| Additional Staff | +30-40% for languages/specialists | Per subject requirement |

### Gap Analysis (TRMD)

The TRMD (Tableau de Répartition des Moyens par Discipline) compares staffing needs against available resources:

- **Besoins (Needs)**: Hours required from DHG calculation
- **HP (Heures Postes)**: Available teacher hours
- **Déficit**: Gap to fill with recruitment or overtime
- **HSA (Heures Supplémentaires)**: Overtime allocation

---

## Application Modules

The application consists of 17 integrated modules, each addressing a specific aspect of budget planning:

| # | Module | Purpose |
|---|--------|---------|
| 1 | System Configuration | School structure, calendar, chart of accounts, users |
| 2 | Class Size Parameters | Min/target/max class sizes, ATSEM rules |
| 3 | Subject Hours Configuration | Curriculum hours matrix, local subjects (Arabic) |
| 4 | Teacher Cost Parameters | AEFE & local salary scales, benefits, overtime |
| 5 | Fee Structure Configuration | Tuition by level/nationality, discounts |
| 6 | Timetable Constraints | Scheduling rules, parallel class requirements |
| 7 | Enrollment Planning | Student projections by level and nationality |
| 8 | Teacher Workforce Planning | DHG calculations, AEFE tracking, optimization |
| 9 | Facility Planning | Classroom inventory, utilization analysis |
| 10 | Revenue Planning | Tuition revenue, fees, grants |
| 11 | Cost Planning | Personnel, operating, driver-based costs |
| 12 | CapEx Planning | Capital investments, depreciation |
| 13 | Budget Consolidation | Top-down/bottom-up, version management |
| 14 | Financial Statements | French GAP & IFRS P&L, Balance Sheet, Cash Flow |
| 15 | Statistical Analysis | KPIs, ratios, benchmarks |
| 16 | Dashboards & Reporting | Role-based views, exports |
| 17 | Budget vs Actual | Variance tracking, forecast revision |

### Key Integration Points

The modules are interconnected through driver-based calculations:

- Enrollment → Class Structure → DHG Hours → Teacher FTE → Personnel Costs
- Enrollment × Fees → Revenue Planning
- All costs → Budget Consolidation → Financial Statements
- AEFE positions tracked separately with EUR/SAR conversion

---

## Key Ratios & Benchmarks

| Ratio | EFIR 2024 | AEFE Benchmark | Notes |
|-------|-----------|----------------|-------|
| Staff Costs / Revenue | 52.6% | 60-75% | Below benchmark - efficient |
| Teaching Staff / Total Personnel | 46.0% | 55-65% | Room for optimization |
| Rent / Revenue | 12.4% | 8-15% | Within range |
| Operating Margin | 9.6% | 5-10% | Healthy surplus |
| Revenue per Student | ~42,500 SAR | Varies | School-specific |
| Students per Teacher | ~7.6 | 8-12 | Good ratio |
| Average Class Size | 21-25 | 20-26 | Within target |

---

## Glossary of Terms

| Term | Definition |
|------|------------|
| AEFE | Agence pour l'enseignement français à l'étranger - French agency managing French schools abroad |
| ATSEM | Agent Territorial Spécialisé des Écoles Maternelles - Classroom assistant for early years |
| Conventionné | AEFE school status with partial funding and staff allocation |
| DAI | Droit Annuel d'Inscription - Annual enrollment fee |
| DHG | Dotation Horaire Globale - Global hours allocation for teacher planning |
| FTE | Full-Time Equivalent - Standard measure of workforce |
| H/E | Heures/Élève - Hours per student ratio for staffing |
| HP | Heures Postes - Standard teaching hours allocated to positions |
| HSA | Heures Supplémentaires Annuelles - Annual overtime hours |
| IFRS | International Financial Reporting Standards |
| ISVL | Indemnité Spécifique de Vie Locale - Local living allowance for AEFE staff |
| LVB | Langue Vivante B - Second foreign language (Arabic at EFIR) |
| PCG | Plan Comptable Général - French chart of accounts standard |
| PRRD | Participation à la Rémunération des Résidents - School contribution to AEFE teacher costs |
| TTC/HT | Toutes Taxes Comprises / Hors Taxes - With/without VAT |
| TRMD | Tableau de Répartition des Moyens par Discipline - Staffing allocation by subject |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | November 2025 | Planning Team | Initial document creation |
| 1.1 | November 2025 | Planning Team | Added SAR currency, updated terminology |
| 1.2 | November 2025 | Planning Team | Added EFIR-specific data: enrollment, fees, personnel, curriculum, budget, chart of accounts, workforce planning model |

---

**Confidentiality**: Internal Use Only  
**Document Status**: Draft
