# EFIR Workforce Planning Logic
## Analysis of DHG (Dotation Horaire Globale) and Effectifs Prévisionnels Models

**Document Date:** November 2025  
**Source Files:** DHG_2025.xlsx, Effectifs_prévisionnels_EFIR.xlsx  
**Purpose:** Document the current workforce planning methodology for the Budget Planning Application

---

## 1. EXECUTIVE SUMMARY

EFIR uses two complementary spreadsheet models for workforce planning:

1. **DHG (Dotation Horaire Globale)** - Detailed hours-based planning for secondary education (Collège + Lycée)
2. **Effectifs Prévisionnels** - Long-term enrollment projection and staff planning (AEFE standard model)

These models work together to:
- Calculate teaching hours required by subject and level
- Determine teacher FTE requirements
- Distinguish between AEFE-assigned teachers and locally recruited staff
- Project financial impact of staffing decisions

---

## 2. DHG MODEL - SECONDARY TEACHER PLANNING

### 2.1 Purpose
The DHG (Dotation Horaire Globale / Global Hours Allocation) is the **standard French Education methodology** for calculating secondary teacher requirements. It works on the principle that teaching needs are driven by:
- Number of classes (divisions) per level
- Regulatory hours per subject per level
- Additional hours for special needs (language groups, labs, projects)

### 2.2 Model Structure

The DHG workbook contains 8 sheets:

| Sheet | Purpose |
|-------|---------|
| **Horaires réglementaires** | Official curriculum hours by subject and level |
| **Effectifs** | Enrollment projections and class structure |
| **Collège** | Detailed hours calculation for Collège (6ème-3ème) |
| **Lycée** | Detailed hours calculation for Lycée (2nde-Terminale) |
| **Groupes Langue** | Language group configuration (splitting classes) |
| **DHG** | Summary of total hours needed by subject |
| **Moyens** | Teacher allocation by name and hours |
| **TRMD** | Gap analysis (needs vs available staff) |

### 2.3 Regulatory Hours (Horaires Réglementaires)

The French national curriculum defines hours per week for each subject:

**Collège Hours:**

| Subject | 6ème | 5ème | 4ème | 3ème |
|---------|------|------|------|------|
| Français | 4.5 | 4.5 | 4.5 | 4 |
| Mathématiques | 4.5 | 3.5 | 3.5 | 3.5 |
| Histoire-Géo | 3 | 3 | 3 | 3.5 |
| LV1 (Anglais) | 4 | 3 | 3 | 3 |
| LV2 (Espagnol) | - | 2.5 | 2.5 | 2.5 |
| SVT | 3 | 1.5 | 1.5 | 1.5 |
| Physique-Chimie | - | 1.5 | 1.5 | 1.5 |
| Technologie | - | 1.5 | 1.5 | 1.5 |
| Education Musicale | 1 | 1 | 1 | 1 |
| Arts Plastiques | 1 | 1 | 1 | 1 |
| EPS | 4 | 3 | 3 | 3 |

**Lycée Hours:**

| Subject | 2nde | 1ère | Terminale |
|---------|------|------|-----------|
| Français | 4 | 4 | - |
| Philosophie | - | - | 4 |
| Mathématiques | 4 | 1.5 | varies |
| Anglais | 3 | 2.5 | 2 |
| Histoire-Géo | 3 | 3 | 3 |
| EPS | 2 | 2 | 2 |
| + Specialization subjects | varies | 4h each | 6h each |

### 2.4 Hours Calculation Formula

**Basic Formula:**
```
Total Hours per Subject = Classes × Hours per Week
```

**Example for Français 6ème:**
- 6 classes (divisions)
- 4.5 hours/week per class
- **Total = 6 × 4.5 = 27 hours/week**

**With "Choc des Savoirs" (Remediation Groups):**
- Extra hours added for splitting classes into smaller groups
- Typically for core subjects (French, Math)
- Calculation: Additional hours based on group configuration

### 2.5 Language Group Configuration

Languages require special handling because:
- Students are grouped by proficiency level, not by class
- One level might have more groups than classes

**EFIR Language Configuration (2025):**

| Level | Students | Classes | Arabic Groups | English Groups | Spanish Groups |
|-------|----------|---------|---------------|----------------|----------------|
| 6ème | 145 | 6 | 8 | 6 | - |
| 5ème | 146 | 6 | 8 | 6 | 5 |
| 4ème | 121 | 5 | 7 | 5 | 4 |
| 3ème | 104 | 4 | 6 | 4 | 4 |

**Impact:** More groups = More teacher hours needed

### 2.6 DHG Summary (Total Hours by Subject)

The DHG sheet aggregates all hours across Collège and Lycée:

| Subject | Total Hours (2025) |
|---------|-------------------|
| Mathématiques | 193 |
| Français | 179 |
| Physique-Chimie | 148 |
| EPS | 121 |
| Histoire-Géo | 119.5 |
| Anglais | 118 |
| SVT | 117.5 |
| Arabe (LVB) | 101.5 |
| Espagnol | 59 |
| Technologie | 45 |
| SES | 43 |
| SNT/ENS | 30.5 |
| Arts | 24 |
| Musique | 24 |
| Philosophie | 18.5 |
| Allemand | 18 |
| Latin | 3 |

### 2.7 TRMD - Gap Analysis

The TRMD (Tableau de Répartition des Moyens par Discipline) compares:
- **Needs (Besoins)**: Total hours required from DHG
- **Apport Initial**: Teachers currently assigned (FTE × 18h)
- **Excedent/Deficit**: Gap between needs and available staff
- **HSA**: Overtime hours to fill gaps

**Example TRMD Analysis:**

| Subject | Hours Needed | HP Available | Gap | HSA |
|---------|-------------|--------------|-----|-----|
| Maths | 110 | 108 | -2 | 20 |
| Français | 127 | 106 | -21 | 21 |
| Histoire-Géo | 65 | 69 | +4 | -4 |
| SVT | 54 | 34 | -20 | 9 |
| Physique | 54 | 36 | -18 | 18 |

**Key Insight:** Where HP (Heures Postes) is insufficient, HSA (Heures Supplémentaires Annuelles) fills the gap up to the regulatory maximum per teacher.

### 2.8 Moyens - Teacher Assignment

The Moyens sheet tracks individual teacher allocations:

| Teacher | Standard Hours | Subject | Notes |
|---------|---------------|---------|-------|
| Teacher A | 18 | Maths | Full-time |
| Teacher B | 18 | Maths | Full-time |
| Teacher C | 18 | Français | Full-time |
| Teacher D | 21 | Français | Latin/HLP combo |
| X BMP | 18 | Various | To be recruited |

**Key Concepts:**
- **Standard Hours:** 18h/week for secondary teachers
- **BMP (Besoins en Moyens Provisoires):** Positions to be filled
- **HSA Column:** Overtime assigned per teacher

---

## 3. EFFECTIFS PRÉVISIONNELS MODEL

### 3.1 Purpose
The Effectifs Prévisionnels is an **AEFE standard financial planning tool** that:
- Projects enrollment up to 7 years ahead
- Calculates staffing needs based on enrollment
- Projects financial results (P&L)
- Enables scenario analysis

### 3.2 Model Structure

| Sheet | Purpose |
|-------|---------|
| **Méthodo** | Methodology documentation |
| **Projection Effectifs** | Multi-year enrollment projection |
| **Nbre de divisions** | Class structure calculation |
| **Hypothèses** | Input parameters and assumptions |
| **Calcul MS Personnels** | Staff cost calculations |
| **Compte Résultat ML** | P&L in local currency (SAR) |
| **Compte Résultat Euro** | P&L in EUR (for AEFE reporting) |
| **Calcul Cout Détaché** | AEFE teacher cost calculation |
| **Tables Enseignants** | H/E ratio reference tables |

### 3.3 Enrollment Projection Methodology

**Growth Calculation:**
- Uses **cohort progression rates** from historical data
- Formula: Next year enrollment = Current year × Cohort growth rate
- Example: 50 CP students × 110% rate = 55 CE1 students next year

**Current EFIR Projections:**

| Level | 2024/25 | 2025/26 | 2026/27 | 2027/28 |
|-------|---------|---------|---------|---------|
| PS | 61 | 70 | 60 | 60 |
| MS | 109 | 72 | 70 | 60 |
| GS | 123 | 130 | 72 | 70 |
| CP | 116 | 134 | 130 | 72 |
| CE1 | 140 | 124 | 134 | 130 |
| ... | ... | ... | ... | ... |
| **Total** | **1,796** | **1,825** | **1,775** | **1,709** |

**Capacity Limits:**
- Maximum potential: 1,875 students
- Maximum per level: 125 students (5 classes × 25)

### 3.4 Class Structure Calculation

**Formula:**
```
Number of Classes = ROUNDUP(Enrollment ÷ Target Class Size)
```

**EFIR Class Size Parameters (observed):**

| Cycle | Average E/D | Target | Max |
|-------|-------------|--------|-----|
| Maternelle | 22-24 | 24 | 25 |
| Élémentaire | 23-25 | 25 | 26 |
| Collège | 24-26 | 25 | 26 |
| Lycée | 26-28 | 26 | 28 |

**E/D = Élèves par Division (Students per Class)**

### 3.5 H/E Ratio Tables (Secondary)

The model uses **H/E (Heures/Élève) ratio tables** to calculate secondary teacher needs:

**H/E Calculation:**
```
H/E = Total Teaching Hours ÷ Total Students
```

**Reference Table - Collège:**

| E/D (Students/Class) | H/E Theoretical | H/E Observed Avg | H/E Max |
|---------------------|-----------------|------------------|---------|
| 16 | 1.625 | 2.07 | 2.11 |
| 18 | 1.43 | 1.88 | 2.01 |
| 20 | 1.30 | 1.71 | 1.97 |
| 22 | 1.18 | 1.58 | 1.80 |
| 24 | 1.08 | 1.46 | 1.68 |
| 25 | 1.04 | 1.44 | 1.66 |
| 26 | 1.00 | 1.27 | 1.40 |
| 28 | 0.93 | 1.38 | 1.46 |

**Interpretation:** With 25 students per class, expect ~1.44 teaching hours per student, which translates to staff requirements.

### 3.6 Staff Calculation Logic

**Primary (1er Degré) - Simple Model:**
```
Teachers Needed = Number of Classes × 1.0
+ Language/Specialist Teachers (30-40% additional)
```

**Secondary (2nd Degré) - Hours-Based Model:**
```
Total Hours = Students × H/E Ratio
Teacher FTE = Total Hours ÷ 18
```

### 3.7 AEFE Detached Teacher Costs

The model calculates AEFE teacher costs separately:

| Component | Value |
|-----------|-------|
| Global AEFE Cost | 1,646,055 EUR |
| School Contribution (PRRD) | ~63% |
| ISVL (Housing Allowance) | 290,060 EUR |
| **Total School Cost** | 1,331,235 EUR |
| **Cost per Detached** | ~41,863 EUR |
| **Number of Detached (annualized)** | 31.8 FTE |

---

## 4. KEY PLANNING PARAMETERS

### 4.1 Standard Teaching Hours

| Category | Hours/Week |
|----------|-----------|
| Primary Teachers (Professeur des écoles) | 24 |
| Secondary Teachers (Certifiés/Agrégés) | 18 |
| Maximum Overtime (HSA) | 2-4 additional |

### 4.2 Staff Ratios (AEFE Reference)

**By School Size - Primary:**

| Students | Director | Adjoint | CPE/Educators | Documentalist | Nurse |
|----------|----------|---------|---------------|---------------|-------|
| <100 | 1 | 0 | 0 | 0 | 0.5 |
| 100-200 | 1 | 0 | 0.5 | 0.5 | 1 |
| 200-500 | 1 | 0 | 1 | 1 | 1.5 |
| 500-1000 | 1 | 1 | 2 | 1.5 | 2 |
| 1000-1500 | 1 | 1 | 3 | 2 | 2.5 |

### 4.3 Financial Parameters

| Parameter | Value |
|-----------|-------|
| New Student Rate | 10% |
| Family Discount Rate | 6% |
| Exchange Rate (EUR/SAR) | 0.25 |
| PRRD Rate | 0% (conventionné) |

---

## 5. WORKFLOW: ANNUAL BUDGET PLANNING

### 5.1 Timeline

1. **June-July**: Receive final enrollment projections
2. **September**: Confirm actual enrollment, adjust classes
3. **October-November**: Build DHG based on confirmed structure
4. **December**: Calculate teacher needs vs available
5. **January-February**: Recruitment decisions
6. **March-April**: Budget finalization

### 5.2 Planning Sequence

```
Enrollment Projection
        ↓
Class Structure Calculation
        ↓
DHG Hours Calculation (Secondary)
        ↓
Teacher FTE Requirement
        ↓
Gap Analysis (TRMD)
        ↓
Staffing Decisions:
  - Confirm AEFE positions
  - Local recruitment
  - Overtime allocation
        ↓
Cost Calculation
        ↓
Budget Integration
```

---

## 6. GAPS IN CURRENT MODEL

### 6.1 What Works Well
- ✅ Standard French methodology (DHG)
- ✅ H/E ratio-based projections
- ✅ Multi-year enrollment projection
- ✅ AEFE cost calculation

### 6.2 Limitations to Address in New System

| Gap | Impact | Proposed Solution |
|-----|--------|-------------------|
| Spreadsheet-based (error prone) | Data integrity risk | Database-driven application |
| No timetable constraint modeling | Peak demand not calculated | Constraint-aware staffing |
| Manual nationality fee calculation | Revenue errors | Automatic fee matrix |
| No scenario comparison | Limited decision support | Side-by-side scenarios |
| No approval workflow | Governance gaps | Multi-level approvals |
| No real-time updates | Stale data | Auto-save, live calculations |

---

## 7. RECOMMENDATIONS FOR NEW SYSTEM

### 7.1 Preserve Existing Logic
- Keep DHG hours calculation methodology
- Maintain H/E ratio tables
- Use AEFE staff ratio references
- Preserve PRRD cost structure

### 7.2 Enhance With
- **Timetable constraint modeling** - Calculate peak demand
- **Optimization engine** - Suggest staffing scenarios
- **Automatic calculations** - Driver-based budgeting
- **Version control** - Track changes, compare scenarios
- **Workflow automation** - Approval routing
- **Dashboard analytics** - Real-time KPIs

### 7.3 Data Migration
- Import historical DHG data
- Transfer H/E tables as reference data
- Load current staff roster
- Pre-populate enrollment projections

---

## 8. APPENDIX: ACRONYMS

| Term | French | English |
|------|--------|---------|
| DHG | Dotation Horaire Globale | Global Hours Allocation |
| TRMD | Tableau de Répartition des Moyens par Discipline | Staffing Allocation by Subject |
| HSA | Heures Supplémentaires Annuelles | Annual Overtime Hours |
| HP | Heures Postes | Position Hours (standard allocation) |
| BMP | Besoins en Moyens Provisoires | Temporary Staffing Needs |
| H/E | Heures/Élève | Hours per Student ratio |
| E/D | Élèves/Division | Students per Class |
| PRRD | Participation à la Rémunération des Résidents | School contribution to AEFE teacher costs |
| ISVL | Indemnité Spécifique de Vie Locale | Local living allowance |

---

*Document prepared for School Budget Planning Application development*
*Based on analysis of actual EFIR planning tools*
