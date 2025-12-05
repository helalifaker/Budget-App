# EFIR Budget Application
## Quick Start Planning Guide: Creating Your First Budget

**Version**: 1.0
**Target Users**: Finance Directors + Academic Directors
**Time Required**: 6-8 hours (recommended spread over 3-5 days)
**Prerequisite**: Administrator or Budget Manager role access

---

## Introduction

### What You'll Accomplish

This guide will walk you through creating a complete budget for the upcoming school year, from initial configuration through final consolidation. By following these steps, you will:

- ✅ Set up all configuration parameters (class sizes, fees, teacher costs)
- ✅ Plan enrollment by academic level and nationality
- ✅ Calculate class structure and workforce requirements (DHG)
- ✅ Project revenue from tuition, fees, and other sources
- ✅ Plan operating costs and capital expenditures
- ✅ Consolidate into a complete budget with financial statements

### Who Does What

| Step | Finance Director | Academic Director | Both Together |
|------|------------------|-------------------|---------------|
| Configuration (1-5) | Teacher Costs, Fees | Class Sizes, Subject Hours | System Config |
| Planning (6-11) | Revenue, Costs, CapEx | Enrollment, Classes, DHG | Budget Review |
| Consolidation (12-13) | Statements & Export | - | Budget Approval |

### Key Success Factors

- **Start with accurate historical data**: Use previous 3 years' enrollment and financial data
- **Use conservative assumptions**: Apply 2-5% growth rates to avoid over-optimism
- **Validate DHG calculations**: Ensure H/E ratio meets or exceeds AEFE benchmarks
- **Review consolidated budget**: Verify operating margin 5-15% before submission

### How This Guide Works

- **Sequential steps**: Follow steps in order (Step 0 through Step 13)
- **Step structure**: Each step shows Purpose, Time, Role, Actions, Output, and Validation
- **Time estimates**: Realistic time estimates help you plan your work sessions
- **Callout boxes**: ⚠️ highlights critical dependencies, 💡 provides helpful tips

**Important**: Enrollment (Step 6) is THE primary driver for the entire budget. All other modules cascade from enrollment projections.

---

## Step 0: Prerequisites & Setup

**Time Required**: 30 minutes
**Role**: Both (Finance + Academic)

### Purpose

Gather historical data and create your budget version in the system.

### Before You Begin - Checklist

Gather the following documents before starting:

- [ ] **Historical enrollment data**: Previous 3 years by level and nationality
- [ ] **Current fee structure**: Tuition rates by level and nationality
- [ ] **AEFE position allocation**: Current teacher roster (Detached vs Funded)
- [ ] **Teacher cost data**: PRRD rate, local teacher salaries
- [ ] **Historical financials**: Previous year revenue and cost data (if available)

### Actions

#### 1. Create New Budget Version (5 minutes)

1. Navigate to: **Configuration > Budget Versions**
2. Click **"New Version"** button
3. Fill in the form:
   - **Fiscal Year**: `2026` (or your target year)
   - **Version Name**: `"Budget 2025-2026"` (use your academic year)
   - **Scenario**: Select `"base"` (start with base case scenario)
   - **Description**: `"Official budget for AY 2025-2026"`
4. Click **"Create"**

#### 2. Verify Budget Created (2 minutes)

- Budget version should appear in the list
- Status should show: **WORKING** (draft mode, editable)
- Note the budget version ID for reference

#### 3. Gather Historical Data (23 minutes)

Export or compile the following data:

| Data Type | Source | Format | Example |
|-----------|--------|--------|---------|
| Enrollment history | Skolengo or Excel | By level, nationality, year | 6ème: 145 students (46 French, 99 Other) |
| Class structure | School records | Classes per level | 6ème: 6 classes, avg 24 students |
| AEFE positions | HR department | Subject allocation | Français: 6 AEFE teachers |
| Fee structure | Finance records | By level, nationality | Collège French: 11,000 SAR |

### Expected Output

- ✅ New budget version visible in system (Status: WORKING)
- ✅ Historical data spreadsheet ready as reference
- ✅ Can navigate to Configuration module

### Validation

- [ ] Budget version created successfully
- [ ] Budget status = WORKING (editable)
- [ ] Historical data accessible for reference

---

## Step 1: System Configuration - Academic Structure

**Time Required**: 15 minutes
**Role**: Academic Director (with Finance review)
**Dependency**: Step 0 complete

### Purpose

Define academic levels and set school capacity limits.

### Navigate To

**Configuration > System Configuration**

### Actions

#### 1. Verify Academic Levels (10 minutes)

Review the pre-loaded academic structure:

**Maternelle** (Preschool):
- PS (Petite Section)
- MS (Moyenne Section)
- GS (Grande Section)

**Élémentaire** (Elementary):
- CP, CE1, CE2, CM1, CM2

**Collège** (Middle School):
- 6ème, 5ème, 4ème, 3ème

**Lycée** (High School):
- 2nde, 1ère, Terminale

✅ Confirm all 14 levels match your school structure. Add any specialized programs if needed.

#### 2. Set School Capacity (5 minutes)

Enter maximum enrollment capacity:

- **Maximum Enrollment**: `1,875` students (or your school's physical capacity)
- This limit enforces capacity constraints during enrollment planning

### Expected Output

- ✅ Academic structure verified (PS through Terminale)
- ✅ Capacity limit configured

### Validation

- [ ] All 14 academic levels present for your school
- [ ] Maximum capacity reflects facility constraints
- [ ] Academic cycles properly organized (4 cycles)

---

## Step 2: Configure Class Size Parameters

**Time Required**: 30 minutes
**Role**: Academic Director
**Dependency**: Step 1 complete

### Purpose

Set class size parameters that determine how many classes form from enrollment.

### Navigate To

**Configuration > Class Size Parameters**

### Critical Concept

These parameters drive class formation using this formula:

```
Number of Classes = CEILING(Enrollment ÷ Target Class Size)

Constraint: Min ≤ (Enrollment ÷ Classes) ≤ Max
```

### Actions

#### 1. Configure Maternelle (8 minutes)

| Parameter | Value | Notes |
|-----------|-------|-------|
| **Minimum** | 18 students | Minimum viable class size |
| **Target** | 22 students | Ideal pedagogical size |
| **Maximum** | 25 students | Absolute capacity limit |

💡 **Tip**: Each Maternelle class requires 1 ATSEM (classroom assistant) - this is auto-calculated.

#### 2. Configure Élémentaire (8 minutes)

| Parameter | Value | Notes |
|-----------|-------|-------|
| **Minimum** | 20 students | Minimum viable class size |
| **Target** | 25 students | Ideal pedagogical size |
| **Maximum** | 28 students | Absolute capacity limit |

#### 3. Configure Collège (8 minutes)

| Parameter | Value | Notes |
|-----------|-------|-------|
| **Minimum** | 22 students | Minimum viable class size |
| **Target** | 26 students | Ideal pedagogical size |
| **Maximum** | 30 students | Absolute capacity limit |

#### 4. Configure Lycée (6 minutes)

| Parameter | Value | Notes |
|-----------|-------|-------|
| **Minimum** | 22 students | Minimum viable class size |
| **Target** | 26 students | Ideal pedagogical size |
| **Maximum** | 30 students | Absolute capacity limit |

### Example Calculation

```
Level: 6ème
Enrollment: 145 students
Target: 26 students/class

Calculation:
Classes = CEILING(145 ÷ 26) = CEILING(5.58) = 6 classes
Average size = 145 ÷ 6 = 24.17 students/class ✓

Validation:
Is 24.17 within range [22, 30]? YES ✓
```

### Expected Output

- ✅ Class size parameters set for all 4 cycles
- ✅ Parameters saved in budget version
- ✅ System ready to calculate class structure

### Validation

- [ ] Target class size realistic for pedagogy (22-26 typical)
- [ ] Max class size respects facility constraints
- [ ] Min class size ensures financial viability
- [ ] All parameters entered for Maternelle, Élémentaire, Collège, Lycée

⚠️ **Important**: Use conservative targets (slightly smaller classes) to avoid overcrowding risk when enrollment exceeds projections.

---

## Step 3: Configure Subject Hours Matrix

**Time Required**: 45 minutes
**Role**: Academic Director
**Dependency**: Step 2 complete

### Purpose

Define curriculum hours that drive DHG (workforce) calculations.

### Navigate To

**Configuration > Subject Hours**

### Critical Concept

Subject hours are THE driver for teacher requirements:

```
Total Subject Hours = Σ(Classes × Hours per Subject per Level)
Teacher FTE Required = Total Subject Hours ÷ 18 (for secondary)
```

⚠️ **Why This Matters**: Subject hours determine workforce costs (50-60% of total budget).

### Actions

#### A. Configure Secondary Subject Hours (30 minutes)

Enter hours per week for each subject and level:

| Subject | 6ème | 5ème | 4ème | 3ème | 2nde | 1ère | Term |
|---------|------|------|------|------|------|------|------|
| **Français** | 4.5h | 4.5h | 4.5h | 4.0h | 4.0h | 4.0h | 4.0h |
| **Mathématiques** | 4.5h | 3.5h | 3.5h | 3.5h | 4.0h | 4.0h | 4.0h |
| **Histoire-Géo** | 3.0h | 3.0h | 3.0h | 3.5h | 3.0h | 3.5h | 3.5h |
| **Anglais LV1** | 4.0h | 3.0h | 3.0h | 3.0h | 2.5h | 2.0h | 2.0h |
| **Sciences (SVT/PC)** | 4.0h | 4.5h | 4.5h | 4.5h | - | - | - |
| **SVT** | - | - | - | - | 1.5h | 2.0h | 2.0h |
| **Physique-Chimie** | - | - | - | - | 3.0h | 4.0h | 4.0h |
| **EPS** | 3.0h | 3.0h | 3.0h | 3.0h | 2.0h | 2.0h | 2.0h |
| **Arts** | 1.0h | 1.0h | 1.0h | 1.0h | 1.0h | 1.0h | 1.0h |

**Entry Method**:
1. Select level (e.g., **6ème**)
2. For each subject, click **"Edit"** and enter hours/week
3. Click **"Save"** after each subject
4. Repeat for all 7 secondary levels (6ème through Terminale)

#### B. Configure Primary Structure (15 minutes)

Primary education uses a different model:

| Parameter | Value | Notes |
|-----------|-------|-------|
| **Generalist Teachers** | 1 per class | One teacher per primary class (automatic) |
| **Specialist Ratio** | 35% | Additional for languages, PE, arts, music |
| **Standard Hours** | 24 hours/week | Primary teachers work 24h/week (vs 18h secondary) |

💡 **Example**: 36 primary classes = 36 generalist + 13 specialist (35% of 36) = 49 total teaching FTE

### Expected Output

- ✅ Complete subject hours matrix for secondary (6ème-Terminale)
- ✅ Primary structure parameters configured
- ✅ System ready to calculate DHG

### Validation

- [ ] Hours match French National Curriculum standards
- [ ] Total weekly hours realistic (26-30 hours per level typical)
- [ ] Specialty subjects included (LV2, LV3, optional courses)
- [ ] Primary specialist ratio set to 35%

⚠️ **Important**: These hours directly calculate teacher FTE in Step 8 (DHG). Errors here cascade to personnel costs.

---

## Step 4: Configure Teacher Costs

**Time Required**: 30 minutes
**Role**: Finance Director
**Dependency**: Step 3 complete

### Purpose

Set unit costs for teacher salaries (drives 50-60% of total budget).

### Navigate To

**Configuration > Teacher Costs**

### Teacher Categories

#### A. AEFE Detached Teachers (Résidents Détachés)

School pays PRRD contribution to AEFE:

| Parameter | Value | Notes |
|-----------|-------|-------|
| **PRRD Rate** | 41,863 EUR/year | Current AEFE rate per detached teacher |
| **EUR to SAR** | 4.2 | Current exchange rate |
| **Cost in SAR** | 175,825 SAR/year | Auto-calculated: 41,863 × 4.2 |

**Actions**:
1. Enter **PRRD rate**: `41,863` EUR
2. Enter **Exchange rate**: `4.2` (update quarterly)
3. System calculates: **175,825 SAR/year** per teacher

#### B. AEFE Funded Teachers (Enseignants Titulaires)

Fully funded by AEFE:

- **Cost to school**: `0 SAR` (no payment required)
- No configuration needed

#### C. Local Teachers (Recrutés Locaux)

Hired and paid by school:

| Parameter | Value | Calculation |
|-----------|-------|-------------|
| **Base Salary** | 18,000 SAR/month | Market competitive rate |
| **Benefits %** | 30% | Housing, transport, health |
| **Employer Charges** | 15% | Social contributions (GOSI) |
| **Annual Cost** | 313,200 SAR/year | 18,000 × 12 × (1 + 0.30) × (1 + 0.15) |

**Calculation**:
```
Monthly total = 18,000 base + 30% benefits = 23,400 SAR/month
Annual total = 23,400 × 12 months = 280,800 SAR
With charges = 280,800 × 1.15 = 313,200 SAR/year per FTE
```

**Actions**:
1. Enter **base salary**: `18,000` SAR/month
2. Enter **benefits**: `30%`
3. Enter **employer charges**: `15%`
4. System calculates: **313,200 SAR/year** per FTE

#### D. ATSEM (Classroom Assistants - Maternelle only)

| Parameter | Value | Calculation |
|-----------|-------|-------------|
| **Salary** | 8,000 SAR/month | ATSEM salary scale |
| **Benefits** | 20% | Housing, transport |
| **Annual Cost** | 115,200 SAR/year | 8,000 × 12 × (1 + 0.20) |

### Expected Output

- ✅ Teacher unit costs configured for all categories
- ✅ Costs will auto-calculate in DHG and Cost Planning modules
- ✅ Exchange rate current for AEFE PRRD

### Validation

- [ ] PRRD rate matches current AEFE communication (check annually)
- [ ] Local salaries competitive for Saudi market
- [ ] Exchange rate current (EUR to SAR updated quarterly)
- [ ] ATSEM costs separate from teacher costs

💡 **Tip**: These costs are per FTE - partial FTE calculated proportionally (e.g., 0.5 FTE = 50% of annual cost).

---

## Step 5: Configure Fee Structure

**Time Required**: 45 minutes
**Role**: Finance Director
**Dependency**: Step 4 complete

### Purpose

Set fee rates that drive revenue projections (94% of total revenue).

### Navigate To

**Configuration > Fee Structure**

### Fee Types

#### A. Tuition (Frais de Scolarité) - Primary Revenue Source

**Fee Matrix by Level and Nationality**:

| Level | French TTC (SAR) | Saudi HT (SAR) | Other TTC (SAR) |
|-------|------------------|----------------|-----------------|
| **Maternelle** (PS-GS) | 8,800 | 14,520 | 14,520 |
| **Élémentaire** (CP-CM2) | 9,900 | 16,335 | 16,335 |
| **Collège** (6ème-3ème) | 11,000 | 18,150 | 18,500 |
| **Lycée** (2nde-Terminale) | 12,100 | 19,965 | 22,275 |

**Notes**:
- **TTC** = Toutes Taxes Comprises (includes VAT)
- **HT** = Hors Taxes (tax-exempt for Saudi nationals)
- **French** = Lowest tier (AEFE subsidized families)
- **Saudi** = Middle tier (no VAT)
- **Other** = Highest tier (full cost recovery)

**Entry Method**:
1. Select "**Tuition**" category
2. For each level:
   - Enter French nationality TTC rate
   - Enter Saudi nationality HT rate
   - Enter Other nationality TTC rate
3. Click **"Save"** after each level

#### B. Trimester Distribution

Set revenue recognition split:

| Trimester | Percentage | Period |
|-----------|------------|--------|
| **T1** | 40% | September-December |
| **T2** | 30% | January-March |
| **T3** | 30% | April-June |

**Total**: 100% (must equal 100%)

#### C. DAI (Droit Annuel d'Inscription) - Annual Registration Fee

| Parameter | Value | Notes |
|-----------|-------|-------|
| **DAI Rate** | 500 SAR | Per student, all nationalities |
| **Applies to** | All students | New AND returning students |
| **Sibling discount** | No | Discount does NOT apply to DAI |

#### D. Enrollment Fee (Frais d'Inscription) - New Students Only

| Parameter | Value | Notes |
|-----------|-------|-------|
| **Enrollment Fee** | 1,500 SAR | One-time fee per new student |
| **Applies to** | New students only | NOT returning students |
| **Sibling discount** | No | Discount does NOT apply |

#### E. Sibling Discount

| Parameter | Value | Notes |
|-----------|-------|-------|
| **Discount** | 25% | On tuition for 3rd child and beyond |
| **Applies to** | Tuition only | NOT DAI, NOT enrollment fees |
| **Average rate** | 5% | Weighted average across all families |

💡 **How it works**: 25% discount on tuition for 3rd+ child in same family, but most families have 1-2 children, so weighted average is ~5%.

#### F. Other Revenue (Optional)

| Revenue Source | Driver | Rate | Notes |
|----------------|--------|------|-------|
| **Cafeteria** | Per student/month | 150 SAR | ~30% participation rate |
| **Extracurricular** | Per activity | 500-2,000 SAR | Sports, music, art programs |
| **Facility rentals** | Fixed | Varies | Renting facilities to external groups |

### Expected Output

- ✅ Complete fee structure by level and nationality
- ✅ Sibling discount parameters configured (25% discount, ~5% average)
- ✅ DAI and enrollment fees configured
- ✅ Trimester distribution set (40/30/30)
- ✅ System ready to calculate revenue in Step 9

### Validation

- [ ] Fees competitive with local market
- [ ] French/Saudi/Other pricing differential matches strategy
- [ ] Sibling discount realistic (5-8% average typical)
- [ ] Trimester split totals 100%
- [ ] DAI and enrollment fees exclude sibling discount

---

## Step 6: Enrollment Planning ⚠️ PRIMARY DRIVER

**Time Required**: 60 minutes
**Role**: Academic Director (with Finance validation)
**Dependency**: Steps 0-5 complete

### Purpose

Project student enrollment by level and nationality.

### Navigate To

**Planning > Enrollment**

### ⚠️ Critical Concept

**Enrollment drives EVERYTHING downstream**:

```
Enrollment → Classes → Teachers → Personnel Costs (50-60% of budget)
           → Revenue (Enrollment × Fees = 94% of revenue)
```

**Errors here cascade through ALL modules**. Validate carefully!

### Preparation: Analyze Historical Data

| Academic Year | Maternelle | Élémentaire | Collège | Lycée | Total | Growth |
|---------------|------------|-------------|---------|-------|-------|--------|
| 2021-2022 | 251 | 556 | 389 | 238 | 1,434 | -6.4% |
| 2022-2023 | 267 | 574 | 413 | 245 | 1,499 | +4.8% |
| 2023-2024 | 249 | 607 | 450 | 281 | 1,587 | +5.9% |
| 2024-2025 | 280 | 650 | 510 | 356 | 1,796 | +13.2% |
| **2025-2026 (Target)** | **?** | **?** | **?** | **?** | **?** | **?** |

### Growth Assumptions

| Scenario | Growth Rate | Use Case |
|----------|-------------|----------|
| **Conservative** | +2% | Low recruitment, market saturation |
| **Base** | +5% | Moderate growth (recommended) |
| **Optimistic** | +8% | Strong demand, new programs |

💡 **Recommendation**: Start with **Base scenario** (+5% growth).

### Actions

#### A. Calculate Projected Enrollment (20 minutes)

Starting from 2024-2025 baseline (1,796 students), apply 5% growth:

```
Projected 2025-2026 = 1,796 × 1.05 = 1,886 students

Capacity check: 1,886 ≤ 1,875 max capacity? NO - EXCEEDS

Adjusted projection: 1,875 students (capped at capacity)
```

⚠️ **Alert**: Projection exceeds capacity by 11 students. Need to adjust distribution.

#### B. Distribute by Cycle (40 minutes)

Apply historical proportions with level progression:

**Maternelle** (295 students projected, +5% from 280):

| Level | Enrollment | Notes |
|-------|------------|-------|
| PS (Petite) | 85 | New entries, youngest |
| MS (Moyenne) | 100 | From PS progression |
| GS (Grande) | 110 | From MS progression |
| **Total** | **295** | |

**Élémentaire** (680 students, +5% from 650):

| Level | Enrollment | Notes |
|-------|------------|-------|
| CP | 135 | From GS + new entries |
| CE1 | 135 | From CP progression |
| CE2 | 138 | From CE1 progression |
| CM1 | 136 | From CE2 progression |
| CM2 | 136 | From CM1 progression |
| **Total** | **680** | |

**Collège** (540 students, +6% from 510):

| Level | Enrollment | Notes |
|-------|------------|-------|
| 6ème | 145 | From CM2 + new entries |
| 5ème | 138 | From 6ème progression |
| 4ème | 132 | From 5ème progression |
| 3ème | 125 | From 4ème progression |
| **Total** | **540** | |

**Lycée** (385 students, +8% from 356):

| Level | Enrollment | Notes |
|-------|------------|-------|
| 2nde | 135 | From 3ème + new entries |
| 1ère | 130 | From 2nde progression |
| Terminale | 120 | From 1ère progression |
| **Total** | **385** | |

**Grand Total**: 295 + 680 + 540 + 385 = **1,900 students**

⚠️ **Capacity Issue**: 1,900 > 1,875 capacity. **Reduce by 25 students** across levels.

#### C. Enter Enrollment by Level (40 minutes)

For each level, enter data in the system:

**Example: 6ème (Collège)**

1. Click **"Add Enrollment"** button
2. Select level: **6ème**
3. Enter by nationality:
   - **French**: `46` students (32% of 145)
   - **Saudi**: `0` students (rare in secondary)
   - **Other**: `99` students (68% of 145)
4. Enter new vs returning:
   - **New students**: `20` (14% of 145)
   - **Returning students**: `125` (86% of 145)
5. Click **"Save"**
6. **Repeat for all 14 levels** (PS through Terminale)

💡 **Tip**: Use nationality distribution from historical data (French ~32%, Saudi ~4%, Other ~64%).

### Expected Output

- ✅ Enrollment entered for all 14 levels
- ✅ Total enrollment: ≤ 1,875 students (capacity constraint)
- ✅ Breakdown by nationality and new/returning status complete
- ✅ Level progression makes sense (students flow 6ème → 5ème → 4ème → 3ème)

### Validation Checks

- [ ] **Capacity constraint**: Total enrollment ≤ 1,875 students ✓
- [ ] **Level progression**: Logical flow between levels (6ème → 5ème → 4ème → 3ème)
- [ ] **New students**: ~10-15% of total (realistic recruitment rate)
- [ ] **Nationality mix**: Consistent with historical (French ~32%, Other ~64%)
- [ ] **Re-enrollment rate**: ~85-90% (typical for stable school)

### Quick Validation Formula

```
Total = Maternelle + Élémentaire + Collège + Lycée
      = 295 + 680 + 540 + 385
      = 1,900 students

Capacity check: 1,900 ≤ 1,875? NO
Action required: Reduce 25 students (adjust across levels)

Final adjusted total: 1,875 students ✓
```

⚠️ **CRITICAL WARNING**: Errors in enrollment cascade to:
- Class structure (Step 7)
- DHG workforce requirements (Step 8) → 50-60% of budget
- Revenue projections (Step 9) → 94% of revenue

**Double-check all numbers before proceeding!**

---

## Step 7: Class Structure Calculation

**Time Required**: 15 minutes
**Role**: Academic Director
**Dependency**: Step 6 complete (Enrollment)

### Purpose

Convert enrollment into number of classes using class size parameters from Step 2.

### Navigate To

**Planning > Class Structure**

### Actions

#### 1. Trigger Auto-Calculation (5 minutes)

1. Click **"Calculate from Enrollment"** button
2. System uses this algorithm:

```
For each level:
  Classes = CEILING(Enrollment ÷ Target Class Size)

Validation:
  Average = Enrollment ÷ Classes
  Check: Min ≤ Average ≤ Max
```

3. Review calculated classes for each level

#### 2. Review Results (10 minutes)

System displays calculated class structure:

**Example Output:**

| Level | Enrollment | Target | Classes | Avg Size | Status |
|-------|------------|--------|---------|----------|--------|
| 6ème | 145 | 26 | 6 | 24.2 | ✓ Good |
| 5ème | 138 | 26 | 6 | 23.0 | ✓ Good |
| 4ème | 132 | 26 | 5 | 26.4 | ✓ Good |
| 3ème | 125 | 26 | 5 | 25.0 | ✓ Good |
| ... | ... | ... | ... | ... | ... |

**Actions**:
- Review each level's class calculation
- Check that average size is within [Min, Max] range
- Click **"Edit"** next to any level to manually override if needed

💡 **Manual Override**: Only override if there's a specific pedagogical or facility reason. Auto-calculation is usually optimal.

### Expected Output

- ✅ Class structure calculated for all 14 levels
- ✅ ATSEM count for Maternelle (1 per class) - auto-calculated
- ✅ Total classes calculated across all levels
- ✅ System ready for DHG calculation (Step 8)

### Validation

- [ ] **No overcrowding**: No classes exceed max class size
- [ ] **Target alignment**: Average class sizes near target (within ±3 students)
- [ ] **ATSEM allocation**: ATSEM count = Number of Maternelle classes
- [ ] **Total classes realistic**: Total ~65-75 classes typical for 1,875 students

**Example: Maternelle ATSEM Calculation**
```
Maternelle classes:
  PS: 4 classes (85 ÷ 22 = 3.86 → 4)
  MS: 5 classes (100 ÷ 22 = 4.55 → 5)
  GS: 5 classes (110 ÷ 22 = 5.0 → 5)
  Total: 14 classes

ATSEM required: 14 (1 per Maternelle class)
```

---

## Step 8: DHG Workforce Planning ⚠️ MOST COMPLEX

**Time Required**: 90 minutes
**Role**: Academic Director (with Finance review)
**Dependency**: Steps 6-7 complete
**Complexity**: ⚠️ HIGHEST - Drives 50-60% of total budget

### Purpose

Calculate teacher FTE requirements using DHG (Dotation Horaire Globale) methodology.

### Navigate To

**Planning > DHG (Teacher Workforce Planning)**

### Critical Concept - DHG Methodology

```
Step 1: Calculate Total Subject Hours
  Total Hours = Σ(Classes × Hours per Subject per Level)

Step 2: Calculate Teacher FTE
  FTE Required = Total Hours ÷ 18 (standard teaching hours/week for secondary)

Step 3: Perform Gap Analysis (TRMD)
  Deficit = Required FTE - (AEFE Positions + Local Staff)

Step 4: Fill Gap
  If Deficit small (< 2 FTE): Use HSA (overtime, max 4h/teacher)
  If Deficit large (≥ 2 FTE): Recruit new teachers
```

### Actions

#### Part A: Review Auto-Calculated DHG (30 minutes)

System automatically calculates based on:
- Class Structure (from Step 7)
- Subject Hours Matrix (from Step 3)

**Example: Mathématiques in Collège**

```
Level-by-Level Calculation:
  6ème: 6 classes × 4.5h = 27.0 hours/week
  5ème: 6 classes × 3.5h = 21.0 hours/week
  4ème: 5 classes × 3.5h = 17.5 hours/week
  3ème: 5 classes × 3.5h = 17.5 hours/week
  ───────────────────────────────────────────
  Total hours/week: 83.0 hours

FTE Calculation:
  Simple FTE = 83.0 ÷ 18 = 4.61 FTE
  Adjusted FTE = CEILING(4.61) = 5 FTE

Result: Need 5 Mathématiques teachers for Collège
```

**Review calculated FTE for all subjects:**

| Subject | Total Hours | Simple FTE | Adjusted FTE | Teachers Needed |
|---------|-------------|------------|--------------|-----------------|
| Français | 178.9 | 9.94 | 10 | 10 |
| Mathématiques | 83.0 | 4.61 | 5 | 5 |
| Histoire-Géo | 84.0 | 4.67 | 5 | 5 |
| Anglais LV1 | 77.0 | 4.28 | 5 | 5 |
| Sciences | 123.0 | 6.83 | 7 | 7 |
| EPS | 63.0 | 3.50 | 4 | 4 |
| Arts | 21.0 | 1.17 | 2 | 2 |
| ... | ... | ... | ... | ... |

#### Part B: TRMD Gap Analysis (40 minutes)

**TRMD** = Tableau de Répartition des Moyens par Discipline (Staffing Gap Analysis)

For each subject, complete the TRMD table:

**Example: Français (French Language)**

```
Step 1: Identify Required FTE (from DHG)
  Besoins (Required): 9.94 FTE

Step 2: Count Available Positions
  HP AEFE: 6.0 FTE (6 AEFE teachers assigned)
  HP Local: 3.0 FTE (3 local teachers assigned)
  HP Disponible (Available): 9.0 FTE total

Step 3: Calculate Deficit
  Deficit = Besoins - HP Disponible
         = 9.94 - 9.0
         = 0.94 FTE

Step 4: HSA Strategy (Overtime)
  Deficit hours = 0.94 FTE × 18 hours = 16.92 hours/week needed
  Available teachers = 6 + 3 = 9 teachers
  HSA per teacher = 16.92 ÷ 9 = 1.88 hours/teacher/week

  Is 1.88h < 4h cap? YES ✓

Decision: Fill gap with HSA (no recruitment needed)
```

**Complete TRMD Table for All Subjects:**

| Subject | Besoins (FTE) | AEFE | Local | HP Dispo | Déficit | HSA Hours | Recruitment |
|---------|---------------|------|-------|----------|---------|-----------|-------------|
| Français | 9.94 | 6.0 | 3.0 | 9.0 | +0.94 | 16.92 | 0 |
| Math | 4.61 | 3.0 | 2.0 | 5.0 | -0.39 | 0 | 0 (surplus) |
| Histoire | 4.67 | 3.0 | 2.0 | 5.0 | -0.33 | 0 | 0 (surplus) |
| Anglais | 4.28 | 2.0 | 2.0 | 4.0 | +0.28 | 5.04 | 0 |
| Sciences | 6.83 | 4.0 | 3.0 | 7.0 | -0.17 | 0 | 0 (surplus) |
| EPS | 3.50 | 2.0 | 2.0 | 4.0 | -0.50 | 0 | 0 (surplus) |
| ... | ... | ... | ... | ... | ... | ... | ... |

💡 **Surplus (negative deficit)** means you have more teachers than needed - some capacity for HSA distribution.

#### Part C: Calculate Primary Workforce (20 minutes)

Primary uses class-based model (not hours-based like secondary):

```
Total Primary Classes:
  Maternelle: 14 classes
  Élémentaire: 27 classes
  Total: 41 primary classes

Generalist Teachers = 41 FTE (1 per class)

Specialist Teachers = CEILING(41 × 0.35) = CEILING(14.35) = 15 FTE
  (For languages, PE, arts, music across all primary)

ATSEM = 14 FTE (1 per Maternelle class only)

Total Primary Staff:
  Teaching FTE = 41 + 15 = 56 FTE
  Support FTE = 14 ATSEM
  Total Staff = 70 FTE
```

#### Part D: Validate H/E Ratio (10 minutes)

**H/E Ratio** = Hours per Student (AEFE quality benchmark)

**Collège Example:**
```
Total Collège Students: 540 students
Total DHG Hours (all subjects): 719.5 hours/week

H/E Ratio = Total Hours ÷ Total Students
         = 719.5 ÷ 540
         = 1.33 hours per student

AEFE Benchmark (class size 26): 1.27 H/E

Comparison:
  EFIR actual: 1.33
  AEFE benchmark: 1.27
  Variance: +0.06 (+4.7% above benchmark) ✓ GOOD

Status: EFIR exceeds AEFE quality benchmark
```

💡 **Interpretation**: Higher H/E ratio = more teaching hours per student = better pedagogical quality.

### Expected Output

- ✅ Complete DHG calculation for all subjects
- ✅ TRMD gap analysis showing deficits/surpluses by subject
- ✅ HSA allocation plan (overtime hours distributed)
- ✅ Recruitment needs identified (if any large deficits)
- ✅ Primary workforce calculated (generalist + specialist + ATSEM)
- ✅ H/E ratio validated against AEFE benchmarks

### Validation

- [ ] **H/E ratio**: Meets or exceeds AEFE benchmarks (Collège: ≥1.27, Lycée: ≥1.40)
- [ ] **HSA within cap**: No teacher assigned > 4 hours HSA per week
- [ ] **AEFE quota**: Total AEFE positions ≤ 28 (EFIR's allocation: 24 detached + 4 funded)
- [ ] **Recruitment realistic**: 0-5 new hires typical (large deficits > 5 may need fee increase)
- [ ] **Primary staffing**: Generalist = 1 per class, Specialist ~35%, ATSEM = Maternelle classes

⚠️ **CRITICAL**: This step drives **50-60% of total budget** (personnel costs). Validate thoroughly!

**Cost Impact**:
```
AEFE teachers: 24 × 175,825 SAR = 4,219,800 SAR
Local teachers: 45 × 313,200 SAR = 14,094,000 SAR
ATSEM: 14 × 115,200 SAR = 1,612,800 SAR
Administrative: 15 × 240,000 SAR = 3,600,000 SAR

Total Personnel: ~23,500,000 SAR (~60% of 30M SAR budget)
```

---

## Step 9: Revenue Planning

**Time Required**: 30 minutes
**Role**: Finance Director
**Dependency**: Step 6 complete (Enrollment)

### Purpose

Calculate revenue projections from enrollment and fee structure.

### Navigate To

**Planning > Revenue**

### Critical Concept

Revenue **AUTO-CALCULATES** from:

```
Revenue = Enrollment (Step 6) × Fee Structure (Step 5)
```

System handles all calculations - you review and validate.

### Actions

#### 1. Click "Calculate Revenue" (5 minutes)

System automatically computes:
- ✅ Tuition by level and nationality
- ✅ Sibling discounts (25% for 3rd+ child)
- ✅ Trimester distribution (40%/30%/30%)
- ✅ DAI (500 SAR × all students)
- ✅ Enrollment fees (1,500 SAR × new students only)

#### 2. Review Revenue Summary (25 minutes)

**Example Output:**

| Revenue Stream | Amount (SAR) | % of Total |
|----------------|--------------|------------|
| **Tuition Revenue (Gross)** | 28,500,000 | 94.2% |
| Less: Sibling Discount (5% avg) | (1,425,000) | -4.7% |
| **Net Tuition Revenue** | 27,075,000 | 89.5% |
| DAI (Annual Registration) | 950,000 | 3.1% |
| Enrollment Fees (New Students) | 225,000 | 0.7% |
| Other Revenue | 570,000 | 1.9% |
| **Total Revenue** | **30,245,000** | **100.0%** |

**Tuition by Trimester:**

| Trimester | Amount (SAR) | % of Annual |
|-----------|--------------|-------------|
| T1 (Sep-Dec) | 10,830,000 | 40% |
| T2 (Jan-Mar) | 8,122,500 | 30% |
| T3 (Apr-Jun) | 8,122,500 | 30% |
| **Total** | **27,075,000** | **100%** |

**Revenue by Nationality:**

| Nationality | Students | Avg Fee | Gross Revenue | Discount | Net Revenue |
|-------------|----------|---------|---------------|----------|-------------|
| French | 603 | 10,200 | 6,150,600 | (307,530) | 5,843,070 |
| Saudi | 76 | 16,500 | 1,254,000 | (50,160) | 1,203,840 |
| Other | 1,221 | 17,800 | 21,733,800 | (1,067,310) | 20,666,490 |
| **Total** | **1,900** | **15,000** | **28,500,000** | **(1,425,000)** | **27,075,000** |

### Expected Output

- ✅ Complete revenue projections by category (tuition, DAI, enrollment, other)
- ✅ Trimester distribution calculated (40/30/30 split)
- ✅ Sibling discount applied (~5% average)
- ✅ System ready for cost planning (Step 10)

### Validation

- [ ] **Revenue per student**: 30,245,000 ÷ 1,900 = 15,918 SAR/student (reasonable: 15-17K typical)
- [ ] **Sibling discount**: 4-5% of gross tuition (1.4M SAR typical)
- [ ] **Tuition dominance**: Tuition = 89-94% of total revenue ✓ (expected for private school)
- [ ] **Trimester split**: T1 (40%) + T2 (30%) + T3 (30%) = 100% ✓
- [ ] **DAI calculation**: 1,900 students × 500 SAR = 950,000 SAR ✓
- [ ] **Enrollment fees**: ~150 new students × 1,500 SAR = 225,000 SAR ✓

💡 **Tip**: Revenue is fully automated based on enrollment accuracy. If revenue looks wrong, check enrollment data in Step 6.

---

## Step 10: Cost Planning

**Time Required**: 60 minutes
**Role**: Finance Director (with Academic input on personnel)
**Dependency**: Steps 8-9 complete

### Purpose

Project all operating costs for the budget year.

### Navigate To

**Planning > Costs**

### Cost Categories (French PCG Account Codes)

#### A. Personnel Costs (64xxx) - AUTO-CALCULATED (10 minutes review)

System automatically calculates from DHG (Step 8):

**Teaching Salaries (Account 64110)**:
```
AEFE Detached: 24 teachers × 175,825 SAR = 4,219,800 SAR
AEFE Funded: 4 teachers × 0 SAR = 0 SAR (AEFE pays)
Local Teachers: 45 teachers × 313,200 SAR = 14,094,000 SAR

Total Teaching Salaries: 18,313,800 SAR
```

**ATSEM (Account 64115)**:
```
ATSEM: 14 × 115,200 SAR = 1,612,800 SAR
```

**Administrative Staff (Account 64120)** - MANUAL ENTRY:
```
Administrative: 15 staff × 240,000 SAR = 3,600,000 SAR
(Enter manually based on org chart)
```

**Total Personnel Costs**: 23,526,600 SAR (~60% of budget)

**Actions**: Review auto-calculated teaching costs, add administrative staff manually.

#### B. Facility & Utilities (62xxx) - MANUAL ENTRY (15 minutes)

| Account | Description | Driver | Amount (SAR) |
|---------|-------------|--------|--------------|
| 62110 | Facility Maintenance | Fixed | 800,000 |
| 62120 | Electricity | kWh usage | 1,200,000 |
| 62130 | Water | Fixed | 180,000 |
| 62140 | Insurance | Fixed | 320,000 |
| 62150 | Security Services | Contract | 480,000 |
| | **Subtotal** | | **2,980,000** |

**Actions**: Enter each amount in the system based on historical data and contracts.

#### C. Supplies & Materials (61xxx) - MANUAL ENTRY (10 minutes)

| Account | Description | Driver | Calculation | Amount (SAR) |
|---------|-------------|--------|-------------|--------------|
| 61110 | Educational Supplies | Per student | 1,900 × 200 SAR | 380,000 |
| 61120 | Office Supplies | Fixed | - | 120,000 |
| 61130 | IT Supplies | Fixed | - | 240,000 |
| | **Subtotal** | | | **740,000** |

#### D. External Services (62xxx continued) - MANUAL ENTRY (10 minutes)

| Account | Description | Amount (SAR) |
|---------|-------------|--------------|
| 62210 | IT Support Services | 420,000 |
| 62220 | Cleaning Services | 680,000 |
| 62230 | Professional Fees | 280,000 |
| | **Subtotal** | **1,380,000** |

#### E. Other Operating Costs (65xxx) - MANUAL ENTRY (10 minutes)

| Account | Description | Amount (SAR) |
|---------|-------------|--------------|
| 65110 | Staff Training | 240,000 |
| 65120 | Travel & Conferences | 180,000 |
| 65130 | Marketing & Recruitment | 320,000 |
| | **Subtotal** | **740,000** |

#### F. Depreciation (68xxx) - AUTO-CALCULATED (5 minutes)

System calculates from CapEx (Step 11):

```
Depreciation = Σ(CapEx ÷ Useful Life)

Example: 1,480,000 SAR CapEx with avg 5-year life
       = 1,480,000 ÷ 5 = 296,000 SAR/year depreciation

Actual depreciation (system calculated): 225,500 SAR
```

### Expected Output

- ✅ **Total Operating Costs**: ~28,500,000 SAR
- ✅ Breakdown by account code and category
- ✅ Personnel costs (64xxx) = largest category (60-65%)
- ✅ System ready for CapEx planning (Step 11)

### Cost Summary

| Category | Account Codes | Amount (SAR) | % of Total |
|----------|---------------|--------------|------------|
| **Personnel** | 64xxx | 23,526,600 | 82.5% |
| **Facility & Utilities** | 62xxx | 2,980,000 | 10.5% |
| **Supplies** | 61xxx | 740,000 | 2.6% |
| **Services** | 62xxx | 1,380,000 | 4.8% |
| **Other Operating** | 65xxx | 740,000 | 2.6% |
| **Depreciation** | 68xxx | 225,500 | 0.8% |
| **Total** | | **28,592,100** | **100.0%** |

### Validation

- [ ] **Personnel dominance**: 60-65% of total costs ✓ (typical for schools)
- [ ] **Facility costs**: 8-12% of total costs
- [ ] **Supplies**: 2-4% of total costs
- [ ] **Total costs align with revenue**: Costs < Revenue for positive surplus
- [ ] **All account codes valid**: 60xxx-68xxx series for expenses

💡 **Tip**: Personnel costs auto-calculate from DHG (Step 8). Focus manual entry on facility, supplies, and services.

---

## Step 11: CapEx Planning

**Time Required**: 20 minutes
**Role**: Finance Director (with Academic input on needs)
**Dependency**: Step 10 complete

### Purpose

Plan capital expenditures and calculate depreciation.

### Navigate To

**Planning > CapEx (Capital Expenditures)**

### Actions

#### 1. Add Major CapEx Items (15 minutes)

Enter planned capital investments:

| Description | Account | Amount (SAR) | Useful Life | Annual Depreciation |
|-------------|---------|--------------|-------------|---------------------|
| Computer Lab Upgrade | 22110 | 500,000 | 5 years | 100,000 |
| Library Furniture | 22130 | 180,000 | 10 years | 18,000 |
| Science Lab Equipment | 22120 | 420,000 | 7 years | 60,000 |
| School Buses (2 units) | 22140 | 380,000 | 8 years | 47,500 |
| **Total CapEx** | | **1,480,000** | | **225,500** |

**Entry Method**:
1. Click **"Add CapEx Item"**
2. Fill in:
   - Description: "Computer Lab Upgrade"
   - Account code: 22110
   - Amount: 500,000 SAR
   - Useful life: 5 years
   - Depreciation method: Straight-line
3. Click **"Save"**
4. Repeat for all items

#### 2. Review Depreciation (5 minutes)

System auto-calculates annual depreciation:
- Computer Lab: 500,000 ÷ 5 = 100,000 SAR/year
- Library: 180,000 ÷ 10 = 18,000 SAR/year
- Science Lab: 420,000 ÷ 7 = 60,000 SAR/year
- School Buses: 380,000 ÷ 8 = 47,500 SAR/year

**Total Annual Depreciation**: 225,500 SAR

💡 Depreciation flows to **Cost Planning** (Account 68110 - Depreciation expense).

### Expected Output

- ✅ Total CapEx: 1,480,000 SAR
- ✅ Annual depreciation: 225,500 SAR (impacts operating costs)
- ✅ CapEx as % of revenue: 4.9% (reasonable, < 10% target)
- ✅ System ready for budget consolidation (Step 12)

### Validation

- [ ] **CapEx sustainability**: CapEx < 10% of revenue (financially sustainable)
- [ ] **Useful lives realistic**: IT 3-5 years, Furniture 10 years, Vehicles 8 years
- [ ] **Major purchases justified**: All items necessary and approved
- [ ] **Depreciation calculated**: System auto-calculated depreciation correctly

💡 **Useful Life Guidelines**:
- IT Equipment: 3-5 years
- Furniture: 10-15 years
- Vehicles: 8-10 years
- Buildings/Infrastructure: 20-50 years

---

## Step 12: Budget Consolidation & Review

**Time Required**: 45 minutes
**Role**: Both (Finance + Academic together)
**Dependency**: All prior steps complete (0-11)

### Purpose

Consolidate all modules into unified budget and validate financial metrics.

### Navigate To

**Consolidation > Budget**

### Actions

#### A. Trigger Consolidation (5 minutes)

1. Click **"Consolidate Budget"** button
2. System aggregates:
   - All revenue (Step 9)
   - All costs (Steps 10 + 11)
   - Calculates financial metrics automatically

#### B. Review Consolidated Results (30 minutes)

**Budget Summary:**

```
═══════════════════════════════════════════════════════
                    BUDGET SUMMARY
                   AY 2025-2026 (Base Scenario)
═══════════════════════════════════════════════════════

REVENUE
───────────────────────────────────────────────────────
Total Revenue                              30,245,000 SAR

  Tuition (Net of Sibling Discount)        27,075,000 SAR
  DAI (Annual Registration)                   950,000 SAR
  Enrollment Fees (New Students)              225,000 SAR
  Other Revenue                               570,000 SAR


OPERATING COSTS
───────────────────────────────────────────────────────
Total Operating Costs                      28,592,100 SAR

  Personnel Costs                          23,526,600 SAR (82.3%)
    - Teaching Staff                       18,313,800 SAR
    - ATSEM                                 1,612,800 SAR
    - Administrative                        3,600,000 SAR

  Facility & Utilities                      2,980,000 SAR (10.4%)
  Supplies & Materials                        740,000 SAR (2.6%)
  External Services                         1,380,000 SAR (4.8%)
  Other Operating                             740,000 SAR (2.6%)
  Depreciation                                225,500 SAR (0.8%)


CAPITAL EXPENDITURES
───────────────────────────────────────────────────────
Total CapEx                                 1,480,000 SAR


FINANCIAL RESULTS
───────────────────────────────────────────────────────
Operating Surplus                           1,652,900 SAR
  (Revenue - Operating Costs)

Net Surplus                                   172,900 SAR
  (Revenue - Operating Costs - CapEx)

EBITDA                                      1,878,400 SAR
  (Operating Surplus + Depreciation)


FINANCIAL METRICS
───────────────────────────────────────────────────────
Operating Margin                                  5.5%
Net Margin                                        0.6%
EBITDA Margin                                     6.2%

Revenue per Student                        15,918 SAR
Cost per Student                           15,048 SAR
Personnel Cost Ratio                          77.8%

═══════════════════════════════════════════════════════
```

#### C. Validation Checklist (10 minutes)

**Financial Integrity Checks:**

- [ ] **Revenue = Enrollment × Fees** ✓
  ```
  Verification: 1,900 students × ~15,900 avg = ~30.2M SAR ✓
  ```

- [ ] **Personnel Costs = DHG FTE × Unit Costs** ✓
  ```
  Verification: Teaching + ATSEM + Admin = 23.5M SAR ✓
  ```

- [ ] **Operating Surplus > 0** ✓
  ```
  Operating Surplus = 1,652,900 SAR (positive) ✓
  ```

- [ ] **Operating Margin: 5-15%** ⚠️
  ```
  Operating Margin = 5.5% (at lower bound - consider optimization)
  ```

- [ ] **All Modules Complete** ✓
  ```
  ✓ Enrollment (Step 6)
  ✓ Classes (Step 7)
  ✓ DHG (Step 8)
  ✓ Revenue (Step 9)
  ✓ Costs (Step 10)
  ✓ CapEx (Step 11)
  ```

- [ ] **No Validation Errors** ✓
  ```
  System shows: "All validations passed"
  ```

### Expected Output

- ✅ Consolidated budget summary displayed
- ✅ Financial metrics calculated (margins, ratios)
- ✅ All validation checks passed
- ✅ Ready for financial statements (Step 13)

### Validation

- [ ] **Operating surplus positive**: Indicates financial sustainability
- [ ] **Personnel costs 60-80%**: Within typical range for schools
- [ ] **CapEx reasonable**: < 10% of revenue
- [ ] **Net margin positive**: Profitable after CapEx

⚠️ **Warning**: If Operating Margin < 5%, consider:
- Reviewing and reducing operating costs
- Considering fee increase for next year
- Optimizing staffing levels (review TRMD for surpluses)

💡 **Target Ranges**:
- Operating Margin: 10-15% (healthy)
- Personnel Cost Ratio: 60-70% (optimal)
- Revenue per Student: 15,000-17,000 SAR (market competitive)

---

## Step 13: Financial Statements & Export

**Time Required**: 15 minutes
**Role**: Finance Director
**Dependency**: Step 12 complete

### Purpose

Generate formal financial statements for board presentation and export data.

### Navigate To

**Consolidation > Financial Statements**

### Actions

#### 1. Generate Statements (5 minutes)

1. Click **"Generate Statements"** button
2. System creates three statements:
   - **Income Statement** (Compte de Résultat) - French PCG format
   - **Balance Sheet** (Bilan) - Assets and liabilities
   - **Cash Flow Statement** - Operating, investing, financing activities

#### 2. Review Income Statement (5 minutes)

**Example Income Statement (Simplified)**:

```
INCOME STATEMENT (Compte de Résultat)
Budget 2025-2026 (Base Scenario)
═══════════════════════════════════════════════════════

REVENUE (Produits)
  70110  Tuition T1                          10,830,000 SAR
  70120  Tuition T2                           8,122,500 SAR
  70130  Tuition T3                           8,122,500 SAR
  70210  DAI                                    950,000 SAR
  70220  Enrollment Fees                        225,000 SAR
  70xxx  Other Revenue                          570,000 SAR
         ─────────────────────────────────────────────
         TOTAL REVENUE                      30,245,000 SAR


OPERATING COSTS (Charges)
  64110  Teaching Salaries                  18,313,800 SAR
  64115  ATSEM Salaries                      1,612,800 SAR
  64120  Administrative Salaries             3,600,000 SAR
  61xxx  Supplies & Materials                  740,000 SAR
  62xxx  Facility, Utilities, Services       4,360,000 SAR
  65xxx  Other Operating Costs                 740,000 SAR
  68110  Depreciation                          225,500 SAR
         ─────────────────────────────────────────────
         TOTAL OPERATING COSTS              28,592,100 SAR


OPERATING SURPLUS                            1,652,900 SAR

NON-OPERATING ITEMS
  Capital Expenditures (CapEx)              (1,480,000) SAR

NET SURPLUS                                    172,900 SAR

═══════════════════════════════════════════════════════
```

#### 3. Export to PDF and Excel (5 minutes)

1. Select export format:
   - **PDF**: For board presentation (click "Export to PDF")
   - **Excel**: For detailed analysis (click "Export to Excel")

2. Excel export includes:
   - Multiple worksheets (Income Statement, Balance Sheet, Cash Flow)
   - Line item detail with account codes
   - Budget vs Actual comparison template

### Expected Output

- ✅ Income Statement generated (PCG-compliant)
- ✅ Balance Sheet generated
- ✅ Cash Flow Statement generated
- ✅ PDF export for board presentation
- ✅ Excel export with all detail
- ✅ Budget ready for submission/approval

### Validation

- [ ] **Income statement balances**: Total Revenue - Total Costs = Surplus
- [ ] **All account codes present**: Revenue 70xxx-77xxx, Expenses 60xxx-68xxx
- [ ] **Export files created**: PDF and Excel downloads successful
- [ ] **Statements readable**: Format clear for board presentation

---

## What to Do Next

**Congratulations!** You've created a complete budget for the school year.

### Next Steps

#### 1. Submit for Approval (5 minutes)

1. Navigate to: **Configuration > Budget Versions**
2. Select your budget version
3. Click **"Submit for Approval"** button
4. Status changes from **WORKING** to **SUBMITTED**
5. Budget is now **locked** (read-only, no further edits)

#### 2. Approval Process (1-3 days)

- **Finance Committee** reviews budget
- Questions/revisions may be requested
- If revisions needed, budget status returns to **WORKING**
- Once approved, status changes to **APPROVED**

#### 3. Create Alternative Scenarios (Optional, 2-3 hours each)

Create additional scenarios for risk planning:

**Conservative Scenario** (2% enrollment growth):
- Repeat Steps 6-13 with 1,800 students
- Compare to base scenario
- Identify downside risk

**Optimistic Scenario** (8% enrollment growth):
- Repeat Steps 6-13 with 2,000 students (capped at capacity)
- Compare to base scenario
- Identify upside opportunity

#### 4. Monitor Actuals (Ongoing throughout year)

- Import actual enrollment monthly (from Skolengo)
- Import actual financials quarterly (from Odoo)
- Run **Budget vs Actual** analysis (Module 17)
- Update forecast if significant variances occur

---

## Quick Reference Checklist

Use this checklist to track your progress:

### Configuration Setup (2 hours)

- [ ] **Step 0**: Create budget version (30 min)
- [ ] **Step 1**: Configure academic structure (15 min)
- [ ] **Step 2**: Set class size parameters (30 min)
- [ ] **Step 3**: Configure subject hours matrix (45 min)
- [ ] **Step 4**: Set teacher unit costs (30 min)
- [ ] **Step 5**: Configure fee structure (45 min)

**Subtotal**: ~2 hours 45 minutes

### Planning (4 hours)

- [ ] **Step 6**: Enter enrollment projections ⚠️ PRIMARY DRIVER (60 min)
- [ ] **Step 7**: Calculate class structure (15 min)
- [ ] **Step 8**: Complete DHG workforce planning ⚠️ MOST COMPLEX (90 min)
- [ ] **Step 9**: Review auto-calculated revenue (30 min)
- [ ] **Step 10**: Enter operating costs (60 min)
- [ ] **Step 11**: Plan capital expenditures (20 min)

**Subtotal**: ~4 hours 35 minutes

### Consolidation (1 hour)

- [ ] **Step 12**: Consolidate budget and review metrics (45 min)
- [ ] **Step 13**: Generate financial statements and export (15 min)

**Subtotal**: ~1 hour

**Total Time**: ~6-8 hours (spread over 3-5 days recommended)

### Key Validation Points

After completing all steps, verify:

- [ ] **Total enrollment ≤ capacity** (1,875 students max)
- [ ] **H/E ratio meets AEFE benchmarks** (Collège ≥1.27, Lycée ≥1.40)
- [ ] **Operating margin 5-15%** (healthy financial position)
- [ ] **Personnel costs 60-80% of revenue** (typical for schools)
- [ ] **Net surplus positive** (financially sustainable)
- [ ] **All validation checks passed** (no system errors)

---

## Glossary of Key Terms

### French Education System

**AEFE**: Agence pour l'enseignement français à l'étranger - French education agency managing schools abroad. EFIR has 28 AEFE teacher positions.

**ATSEM**: Agent Territorial Spécialisé des Écoles Maternelles - Classroom assistant required for Maternelle classes (1 per class).

**Cycle**: French education is organized in cycles:
- Cycle 1: Maternelle (PS, MS, GS)
- Cycle 2: Élémentaire early (CP, CE1, CE2)
- Cycle 3: Élémentaire late + Collège early (CM1, CM2, 6ème)
- Cycle 4: Collège late (5ème, 4ème, 3ème)
- Lycée: High school (2nde, 1ère, Terminale)

### Workforce Planning

**DHG**: Dotation Horaire Globale - Global hours allocation, French methodology for calculating teacher requirements.
- Formula: `Total Hours ÷ 18 = FTE required` (for secondary)

**FTE**: Full-Time Equivalent - Standard measure of teacher workload.
- Secondary: 18 hours/week teaching
- Primary: 24 hours/week teaching

**H/E Ratio**: Heures/Élève - Hours per student, AEFE quality benchmark.
- Collège target: 1.27-1.71 H/E
- Lycée target: 1.40-1.97 H/E
- Higher = better quality (more teaching hours per student)

**HSA**: Heures Supplémentaires Annuelles - Annual overtime hours.
- Cap: 4 hours/week maximum per teacher
- Used to fill small staffing gaps (< 2 FTE deficit)

**PRRD**: Participation à la Rémunération des Résidents Détachés - AEFE teacher contribution paid by school.
- Current rate: 41,863 EUR/year (~175,825 SAR)

**TRMD**: Tableau de Répartition des Moyens par Discipline - Staffing gap analysis table.
- Shows: Required FTE - Available FTE = Deficit
- Determines HSA allocation or recruitment needs

### Financial Terms

**DAI**: Droit Annuel d'Inscription - Annual registration fee.
- Rate: 500 SAR per student (all nationalities)
- Charged to ALL students (new and returning)

**Enrollment Fee**: Frais d'inscription - One-time fee for new students.
- Rate: 1,500 SAR per new student
- NOT charged to returning students

**Sibling Discount**: Discount on tuition for families with 3+ children.
- Rate: 25% on tuition only
- Does NOT apply to DAI or enrollment fees

**TTC**: Toutes Taxes Comprises - Includes VAT (French and Other nationalities)

**HT**: Hors Taxes - Exempt from VAT (Saudi nationals only)

**Trimester**: French schools recognize revenue in 3 periods:
- T1: September-December (40% of annual tuition)
- T2: January-March (30% of annual tuition)
- T3: April-June (30% of annual tuition)

### Financial Metrics

**Operating Surplus**: Revenue - Operating Costs (excludes CapEx)
- Target: Positive surplus indicates financial health
- Operating Margin = Operating Surplus ÷ Revenue × 100

**Net Surplus**: Revenue - Operating Costs - CapEx (includes CapEx)
- Target: Positive net surplus indicates sustainability
- Net Margin = Net Surplus ÷ Revenue × 100

**EBITDA**: Earnings Before Interest, Taxes, Depreciation, Amortization
- Calculation: Operating Surplus + Depreciation
- Indicates cash-generating capability

**Personnel Cost Ratio**: Personnel Costs ÷ Revenue × 100
- Target: 60-70% (optimal for schools)
- Higher ratios indicate staffing intensity

---

## Troubleshooting Common Issues

### Issue 1: "Class size exceeds maximum"

**Symptom**: Calculated class has 32 students, but max is 30

**Cause**: Enrollment too high for configured class size parameters

**Solution**:
- Option 1: Increase max class size parameter in Step 2
- Option 2: Manually override to add another class (e.g., 6 → 7 classes)
- Option 3: Reduce enrollment projection in Step 6

**Example**:
```
Level: 6ème
Enrollment: 180 students
Target: 26, Max: 30

Auto-calculated: CEILING(180 ÷ 26) = 7 classes
Average: 180 ÷ 7 = 25.7 students/class ✓ (within range)
```

---

### Issue 2: "DHG shows unrealistic FTE requirements"

**Symptom**: System calculates 15 Math teachers needed, seems too high

**Cause**: Incorrect subject hours configuration OR incorrect class structure

**Solution**:
1. **Verify subject hours** (Step 3): Check hours match curriculum
   - 6ème Math should be 4.5h, not 45h (decimal error)
2. **Verify class structure** (Step 7): Ensure class counts are correct
   - 6 classes for 6ème, not 60 classes (data entry error)

**Example of Error**:
```
WRONG:
  6ème: 6 classes × 45h (error!) = 270 hours
  FTE = 270 ÷ 18 = 15 teachers (unrealistic!)

CORRECT:
  6ème: 6 classes × 4.5h = 27 hours
  FTE = 27 ÷ 18 = 1.5 → 2 teachers (realistic)
```

---

### Issue 3: "Operating margin negative"

**Symptom**: Budget shows -2% operating margin (costs exceed revenue)

**Cause**: Costs too high relative to revenue

**Solution**:

**A. Review Personnel Costs** (largest category, ~60-65%):
- Check TRMD for surpluses (can reduce staff)
- Review administrative staffing levels
- Consider local teachers vs AEFE (local = 313K, AEFE = 176K)

**B. Review Fee Structure** (Step 5):
- Consider fee increase (e.g., +5% can add 1.5M SAR revenue)
- Benchmark against competitor schools

**C. Reduce Non-Essential Costs**:
- Defer non-critical CapEx projects
- Optimize facility costs (energy efficiency)
- Reduce discretionary spending (travel, training)

**Example**:
```
Current:
  Revenue: 30,245,000 SAR
  Costs: 31,000,000 SAR
  Operating Margin: -2.5% (negative)

After 5% fee increase:
  Revenue: 31,757,000 SAR (+1.5M from tuition)
  Costs: 31,000,000 SAR (unchanged)
  Operating Margin: +2.4% (positive) ✓
```

---

### Issue 4: "H/E ratio below AEFE benchmark"

**Symptom**: Collège H/E = 1.15, but AEFE benchmark is 1.27

**Cause**: Understaffed relative to student count (too few teaching hours)

**Solution**:

**Option 1**: Increase teaching hours (modify subject hours in Step 3)
- Review curriculum - can any subjects increase hours?

**Option 2**: Reduce class sizes (creates more classes, more teachers)
- Lower target class size in Step 2 (e.g., 26 → 24)
- More classes = more DHG hours = higher H/E ratio

**Example**:
```
Current (understaffed):
  Total hours: 620 hours/week
  Students: 540
  H/E = 620 ÷ 540 = 1.15 (below 1.27 benchmark)

After reducing class size (26 → 24):
  Classes increase: 21 → 23 classes (+2)
  Hours increase: 620 → 680 hours/week
  H/E = 680 ÷ 540 = 1.26 (meets benchmark) ✓
```

💡 **Note**: Increasing H/E ratio increases personnel costs. Balance quality vs budget constraints.

---

### Issue 5: "Cannot submit budget - validation errors"

**Symptom**: Submit button grayed out, error message "Please complete all required modules"

**Cause**: Incomplete data OR data inconsistencies

**Solution**:

**Step-by-Step Validation**:

1. **Check Enrollment** (Step 6):
   - [ ] All 14 levels have enrollment data entered
   - [ ] New + Returning = Total for each level
   - [ ] Total ≤ 1,875 (capacity)

2. **Check Class Structure** (Step 7):
   - [ ] All levels have classes calculated
   - [ ] No classes exceed max size

3. **Check DHG** (Step 8):
   - [ ] All subjects have FTE calculated
   - [ ] TRMD gap analysis complete
   - [ ] Primary workforce calculated

4. **Check Revenue** (Step 9):
   - [ ] Revenue calculated (> 0)
   - [ ] Trimester split = 100%

5. **Check Costs** (Step 10):
   - [ ] Personnel costs calculated
   - [ ] All cost categories entered

6. **Check CapEx** (Step 11):
   - [ ] CapEx items entered (or 0 if no CapEx)

7. **Check Consolidation** (Step 12):
   - [ ] Budget consolidated
   - [ ] No validation errors

**System Error Messages**:
- "Enrollment missing for level X" → Go to Step 6, add enrollment for level X
- "Class structure not calculated" → Go to Step 7, click "Calculate from Enrollment"
- "DHG not complete" → Go to Step 8, complete TRMD analysis

---

## Support & Resources

### Need Help?

**Technical Support**:
- Email: helpdesk@efir-school.com
- Response time: 24-48 hours
- Include: Budget version ID, step number, error message

**Budget Questions**:
- Finance Director: finance@efir-school.com
- Academic Director: academic@efir-school.com

**Training Videos**:
- Available in application: **Help menu > Video Tutorials**
- Topics: Enrollment Planning, DHG Calculation, Budget Consolidation

### Additional Documentation

**Comprehensive User Guide**:
- Location: [docs/user-guides/USER_GUIDE.md](USER_GUIDE.md)
- ~100 pages with screenshots and detailed explanations

**Module Specifications** (Technical Details):
- [MODULE_07_ENROLLMENT_PLANNING.md](../MODULES/MODULE_07_ENROLLMENT_PLANNING.md)
- [MODULE_08_TEACHER_WORKFORCE_PLANNING_DHG.md](../MODULES/MODULE_08_TEACHER_WORKFORCE_PLANNING_DHG.md)
- [MODULE_10_REVENUE_PLANNING.md](../MODULES/MODULE_10_REVENUE_PLANNING.md)
- [MODULE_13_BUDGET_CONSOLIDATION.md](../MODULES/MODULE_13_BUDGET_CONSOLIDATION.md)

**Developer Documentation**:
- API Documentation: [docs/developer-guides/API_DOCUMENTATION.md](../developer-guides/API_DOCUMENTATION.md)
- Database Schema: [docs/database/SCHEMA.md](../database/SCHEMA.md)

---

## Document Information

**Version**: 1.0
**Last Updated**: December 5, 2025
**Audience**: Finance Directors + Academic Directors
**Format**: Quick Start Guide (12-15 pages)
**Estimated Completion Time**: 6-8 hours
**Related Documents**:
- [USER_GUIDE.md](USER_GUIDE.md) - Comprehensive user manual
- [DEVELOPER_GUIDE.md](../developer-guides/DEVELOPER_GUIDE.md) - Developer setup
- [MODULE Specifications](../MODULES/) - Business rules and formulas

---

**End of Quick Start Planning Guide**

*For additional help or questions, contact: helpdesk@efir-school.com*
