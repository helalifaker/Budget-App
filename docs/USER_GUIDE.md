# EFIR Budget Planning Application - User Guide

**Version**: 1.0
**Last Updated**: December 2025
**Target Audience**: Budget planners, financial managers, administrators

## Table of Contents

1. [Getting Started](#1-getting-started)
2. [Configuration Module](#2-configuration-module)
3. [Planning Module](#3-planning-module)
4. [Consolidation Module](#4-consolidation-module)
5. [Analysis Module](#5-analysis-module)
6. [Strategic Planning](#6-strategic-planning)
7. [Integrations](#7-integrations)
8. [Troubleshooting](#8-troubleshooting)

---

## 1. Getting Started

### 1.1 Logging In

1. Navigate to the application URL (e.g., `https://budget.efir-school.com`)
2. Enter your email and password
3. Click "Sign In"
4. You will be redirected to the Dashboard

**First-time login**: Use the credentials provided by your IT administrator. You will be prompted to change your password.

### 1.2 Dashboard Overview

The Dashboard provides a high-level overview of:
- **Active Budget Versions**: Current working, submitted, and approved budgets
- **Quick Stats**: Total revenue, expenses, net result
- **Recent Activity**: Latest changes and updates
- **Alerts**: Validation warnings or required actions

### 1.3 Navigation

Use the sidebar menu to access different modules:

**Configuration**
- System Configuration
- Class Size Parameters
- Subject Hours Matrix
- Teacher Costs
- Fee Structure
- Budget Versions

**Planning**
- Enrollment Planning
- Class Structure
- DHG Workforce Planning
- Revenue Planning
- Cost Planning
- CapEx Planning

**Consolidation**
- Budget Consolidation
- Financial Statements

**Analysis**
- Statistical Analysis
- Dashboards
- Budget vs Actual

**Strategic**
- 5-Year Strategic Plan

**Settings**
- Integrations (Odoo, Skolengo, AEFE)
- User Management
- System Settings

### 1.4 Understanding Budget Workflow

Budgets progress through the following statuses:

1. **WORKING**: Draft mode, all changes allowed
2. **SUBMITTED**: Submitted for approval, limited edits
3. **APPROVED**: Finalized budget, read-only
4. **BASELINE**: Approved budget used for variance analysis
5. **FORECAST**: Mid-year revised forecast

---

## 2. Configuration Module

### 2.1 Creating Your First Budget Version

**Prerequisites**: Administrator or Budget Manager role

**Steps**:
1. Navigate to **Configuration > Budget Versions**
2. Click **"New Version"** button
3. Fill in the form:
   - **Name**: e.g., "Budget 2025-2026"
   - **Fiscal Year**: 2025
   - **Academic Year**: 2024-2025
   - **Start Date**: January 1, 2025
   - **End Date**: December 31, 2025
   - **Description**: Optional notes
4. Click **"Create"**
5. The new version will appear in the list with status **WORKING**

**Best Practices**:
- Use consistent naming conventions (e.g., "Budget YYYY-YYYY")
- Create new versions by copying previous year's approved budget
- Document major assumptions in the description field

### 2.2 Setting Up Class Size Parameters

Class size parameters control how enrollment is converted into classes.

**Navigation**: Configuration > Class Size Parameters

**Parameters by Cycle**:
- **Min Class Size**: Minimum students to form a class (e.g., 15)
- **Target Class Size**: Optimal class size (e.g., 25)
- **Max Class Size**: Maximum allowed students per class (e.g., 30)

**Example**:
```
Level: 6ème (Collège)
Min: 20 students
Target: 25 students
Max: 28 students

Enrollment: 76 students
Calculation: 76 ÷ 25 = 3.04 → 3 classes
Verification: 76 ÷ 3 = 25.3 students/class ✓ (within 20-28 range)
```

**To Edit Parameters**:
1. Select the budget version
2. Choose the cycle (Maternelle, Élémentaire, Collège, Lycée)
3. Click "Edit" on the level you want to modify
4. Update min, target, or max values
5. Click "Save"
6. The system will automatically recalculate affected classes

### 2.3 Configuring Subject Hours Matrix

The Subject Hours Matrix defines teaching hours per subject per level, which drives DHG calculations.

**Navigation**: Configuration > Subject Hours

**Standard Hours** (French National Curriculum):

**Collège** (Middle School):
| Subject | 6ème | 5ème | 4ème | 3ème |
|---------|------|------|------|------|
| Français | 4.5h | 4.5h | 4.5h | 4h |
| Mathématiques | 4.5h | 3.5h | 3.5h | 3.5h |
| Histoire-Géo | 3h | 3h | 3h | 3.5h |
| Anglais LV1 | 4h | 3h | 3h | 3h |
| Sciences | 4h | 4.5h | 4.5h | 4.5h |

**To Update Hours**:
1. Select level (e.g., 6ème)
2. Click "Edit" for a subject
3. Enter new hours per week
4. Click "Save"
5. Navigate to Planning > DHG to see updated FTE requirements

### 2.4 Configuring Teacher Costs

**Navigation**: Configuration > Teacher Costs

**Teacher Categories**:

**AEFE Detached Teachers** (Résident Détachés):
- Paid by French government
- School pays PRRD contribution: ~41,863 EUR/teacher/year
- Converted to SAR at configured exchange rate

**AEFE Funded Teachers** (Enseignants Titulaires):
- Fully funded by AEFE
- Zero cost to school

**Local Teachers** (Recrutés Locaux):
- Hired and paid by school in SAR
- Monthly salary: 15,000 - 25,000 SAR depending on experience
- Benefits: Housing allowance, transportation, health insurance

**Configuration Fields**:
- **PRRD Rate (EUR)**: Annual contribution per AEFE teacher
- **EUR to SAR Exchange Rate**: Current conversion rate (e.g., 4.2)
- **Local Teacher Base Salary (SAR)**: Monthly gross salary
- **Benefits Percentage**: % of salary for benefits (e.g., 30%)
- **Employer Contributions**: Social charges and taxes (e.g., 15%)

### 2.5 Fee Structure Configuration

**Navigation**: Configuration > Fee Structure

**Fee Categories**:
1. **Tuition** (Frais de Scolarité): Main annual fee
2. **Registration** (Inscription): One-time or annual enrollment fee
3. **DAI** (Droit Annuel d'Inscription): Annual right of enrollment
4. **Cafeteria** (Cantine): Meal plan fees
5. **Transportation** (Transport): Bus service fees
6. **Activities** (Activités): Extra-curricular activities

**Tuition Pricing Structure**:
- **By Level**: Different fees for Maternelle, Élémentaire, Collège, Lycée
- **By Nationality**: French (TTC with VAT), Saudi (HT without VAT), Other (TTC)
- **By Period**: T1 (40%), T2 (30%), T3 (30%)

**Example Tuition Configuration**:
```
Level: Collège (6ème-3ème)
French Nationality (TTC): 35,000 SAR/year
Saudi Nationality (HT): 29,000 SAR/year
Other Nationality (TTC): 40,000 SAR/year

Period Distribution:
T1 (Jan-Apr): 14,000 SAR (40%)
T2 (May-Aug): 10,500 SAR (30%)
T3 (Sep-Dec): 10,500 SAR (30%)
```

**Sibling Discounts**:
- **1st child**: Full price (100%)
- **2nd child**: Full price (100%)
- **3rd+ child**: 25% discount on tuition only (not on DAI or registration)

---

## 3. Planning Module

### 3.1 Enrollment Planning

**Navigation**: Planning > Enrollment

**Purpose**: Project student enrollment by level and nationality for the fiscal year.

**Steps to Add Enrollment**:
1. Select your budget version
2. Click **"Add Enrollment"**
3. Fill in:
   - **Level**: Academic level (e.g., 6ème)
   - **Nationality**: French, Saudi, Other
   - **Student Count**: Number of projected students
   - **Period**: P1 (Jan-Jun) or P2 (Sep-Dec)
4. Click **"Save"**

**Best Practices**:
- Start with historical data from previous year
- Apply growth rate assumptions (e.g., 5% increase)
- Consider capacity constraints (~1,875 total students)
- Review enrollment by nationality for revenue planning
- Update P2 projections as recruitment progresses

**Example Enrollment Entry**:
```
Budget Version: 2025
Level: 6ème
Nationality: French
Period: P2 (Sep-Dec)
Student Count: 120 students
```

### 3.2 Class Structure Calculation

**Navigation**: Planning > Class Structure

**Purpose**: Convert enrollment into number of classes based on class size parameters.

**Automatic Calculation**:
1. Select budget version
2. Click **"Calculate from Enrollment"**
3. System calculates classes using algorithm:
   ```
   Number of Classes = CEILING(Enrollment ÷ Target Class Size)
   Verify: Min ≤ (Enrollment ÷ Classes) ≤ Max
   ```
4. Review calculated classes
5. Override manually if needed (e.g., for pedagogical reasons)

**Example**:
```
Level: 6ème
Enrollment: 120 students
Target Class Size: 25
Calculation: 120 ÷ 25 = 4.8 → 5 classes
Actual: 120 ÷ 5 = 24 students/class ✓
```

**Manual Overrides**:
- Click "Edit" next to any level
- Enter desired number of classes
- System will show average class size
- Click "Save"

**Additional Considerations**:
- **Maternelle**: Each class requires 1 ATSEM (classroom assistant)
- **Split Classes**: For mixed-level classes (e.g., CP-CE1)
- **Specialty Classes**: For ESL, special education

### 3.3 DHG Workforce Planning

**Navigation**: Planning > DHG

**Purpose**: Calculate teacher requirements using DHG (Dotation Horaire Globale) methodology.

**Understanding DHG**:
DHG is the French education system's method for calculating teacher needs based on hours:

**Formula**:
```
Total Subject Hours = Σ (Classes × Hours per Subject per Level)
Teacher FTE = Total Subject Hours ÷ Standard Teaching Hours

Standard Teaching Hours:
- Primary: 24 hours/week
- Secondary: 18 hours/week
```

**Example Calculation - Mathématiques in Collège**:
```
Classes:
- 6ème: 5 classes × 4.5h = 22.5h
- 5ème: 5 classes × 3.5h = 17.5h
- 4ème: 4 classes × 3.5h = 14.0h
- 3ème: 4 classes × 3.5h = 14.0h

Total Hours: 68 hours/week
FTE: 68 ÷ 18 = 3.78 → 4 teachers needed

HSA (Overtime): 68 - (3 × 18) = 14 hours
Distribution: 3 teachers × 18h + 1 teacher × 14h
```

**DHG Workflow**:
1. Select budget version
2. System auto-calculates based on:
   - Class Structure (from Module 8)
   - Subject Hours Matrix (from Module 3)
3. Review by cycle and subject
4. View detailed breakdown:
   - Total hours required
   - Simple FTE (hours ÷ 18)
   - Recommended teachers
   - HSA (overtime hours)
5. Assign teacher types:
   - AEFE Detached
   - AEFE Funded
   - Local Recruited
6. System calculates costs automatically

**TRMD (Gap Analysis)**:
The TRMD table shows:
- **Besoins** (Needs): Hours required from DHG
- **Moyens Disponibles** (Available): AEFE + Local positions
- **Déficit**: Gap to be filled

**H/E Ratio Validation**:
The system displays H/E (Hours per Student) ratio for validation:
```
Collège Target: 1.35 - 1.45 H/E
Example: 600 students, 840 hours → 1.40 H/E ✓
```

### 3.4 Revenue Planning

**Navigation**: Planning > Revenue

**Revenue Streams**:
1. **Tuition Revenue**: Calculated from enrollment × fee structure
2. **Registration Fees**: New student registration
3. **DAI**: Annual enrollment rights
4. **Cafeteria**: Meal plan subscriptions
5. **Transportation**: Bus service
6. **Activities**: Extra-curricular programs
7. **Other Revenue**: Grants, subsidies, donations

**Automatic Calculation**:
Revenue is automatically calculated based on:
- Enrollment by level and nationality
- Fee structure configuration
- Period distribution (T1: 40%, T2: 30%, T3: 30%)
- Sibling discounts

**Example**:
```
Level: Collège 6ème
Enrollment: 120 students
  - French: 80 students
  - Saudi: 30 students
  - Other: 10 students

Tuition Revenue:
  - French: 80 × 35,000 = 2,800,000 SAR
  - Saudi: 30 × 29,000 = 870,000 SAR
  - Other: 10 × 40,000 = 400,000 SAR
Total: 4,070,000 SAR

Period Distribution:
  - T1: 1,628,000 SAR (40%)
  - T2: 1,221,000 SAR (30%)
  - T3: 1,221,000 SAR (30%)
```

**Manual Adjustments**:
- Click "Edit" next to any revenue line
- Adjust amount or assumptions
- Add notes for justification
- System will flag manual overrides

### 3.5 Cost Planning

**Navigation**: Planning > Cost Planning

**Cost Categories** (French PCG Account Codes):

**61 - Purchases & Supplies**:
- 61110: Educational supplies
- 61120: Administrative supplies
- 61130: Maintenance supplies

**62 - External Services**:
- 62110: Facility maintenance
- 62120: Utilities (electricity, water)
- 62130: Insurance
- 62140: Professional services

**63 - Taxes & Fees**:
- 63110: Business taxes
- 63120: Government fees

**64 - Personnel Costs**:
- 64110: Teaching salaries (auto-calculated from DHG)
- 64120: Administrative salaries
- 64130: Support staff salaries
- 64140: Benefits and contributions

**65 - Other Operating Costs**:
- 65110: Staff training
- 65120: Travel and conferences

**66 - Financial Charges**:
- 66110: Interest expenses
- 66120: Bank fees

**67 - Exceptional Costs**:
- 67110: Write-offs
- 67120: Non-recurring expenses

**Driver-Based Costs**:
Many costs are automatically calculated:
- **Teaching Salaries**: From DHG workforce planning
- **ATSEM**: From Maternelle class count
- **Utilities**: From square meters × rate
- **Supplies**: From student count × rate

**Manual Cost Entry**:
1. Select budget version
2. Choose account code
3. Enter amount by period (P1, P2)
4. Add description/justification
5. Click "Save"

### 3.6 CapEx Planning

**Navigation**: Planning > CapEx Planning

**Capital Expenditure Categories**:

**20 - Intangible Assets**:
- 20110: Software licenses
- 20120: Development costs

**21 - Property & Buildings**:
- 21110: Land
- 21120: Building construction
- 21130: Building improvements

**22 - Equipment**:
- 22110: IT equipment (computers, servers)
- 22120: Educational equipment (labs, libraries)
- 22130: Furniture
- 22140: Vehicles

**CapEx Workflow**:
1. Click "Add CapEx Item"
2. Fill in:
   - **Description**: Equipment or project name
   - **Account Code**: From chart above
   - **Amount**: Total investment in SAR
   - **Period**: When purchase will occur
   - **Useful Life**: Years (for depreciation)
3. System calculates annual depreciation
4. Depreciation flows to cost planning automatically

**Example**:
```
Item: New Computer Lab
Account: 22110 - IT Equipment
Amount: 500,000 SAR
Period: P2 (Sep-Dec)
Useful Life: 5 years
Annual Depreciation: 500,000 ÷ 5 = 100,000 SAR/year
```

---

## 4. Consolidation Module

### 4.1 Budget Consolidation

**Navigation**: Consolidation > Budget

**Purpose**: Aggregate all revenue and cost planning into a consolidated budget.

**Consolidation Steps**:
1. Select budget version (must have completed all planning modules)
2. Click **"Consolidate Budget"**
3. System performs:
   - Revenue aggregation (all streams)
   - Cost aggregation (all accounts)
   - CapEx and depreciation calculation
   - Period distribution (P1 / P2 split)
   - Account code validation
4. View consolidated results:
   - **Total Revenue**
   - **Total Operating Costs**
   - **EBITDA** (Earnings Before Interest, Tax, Depreciation, Amortization)
   - **Net Result** (Profit/Loss)
5. Export to Excel for detailed review

**Validation Checks**:
- All required modules completed
- Account codes valid per PCG
- Period totals match annual totals
- No missing data

**Period Breakdown**:
```
Period 1 (Jan-Jun):
- Includes: 40% tuition (T1) + 50% operating costs
- Academic year continuation

Period 2 (Sep-Dec):
- Includes: 30% tuition (T2) + 50% operating costs
- New academic year start
```

### 4.2 Financial Statements

**Navigation**: Consolidation > Financial Statements

**Available Statements**:

**1. Income Statement** (Compte de Résultat):
```
REVENUE (Produits)
70xxx - Operating Revenue
  70110: Tuition T1
  70120: Tuition T2
  70130: Tuition T3
  70210: Registration fees
  70220: Cafeteria
76xxx - Financial Revenue
77xxx - Exceptional Revenue

TOTAL REVENUE: X,XXX,XXX SAR

EXPENSES (Charges)
60xxx - Purchases & Supplies
61xxx - External Services
62xxx - Taxes & Fees
63xxx - Personnel Costs
  64110: Teaching salaries
  64120: Administrative salaries
65xxx - Other Operating
66xxx - Financial Charges
67xxx - Exceptional Costs

TOTAL EXPENSES: X,XXX,XXX SAR

NET RESULT: X,XXX,XXX SAR (Profit/Loss)
```

**2. Balance Sheet** (Bilan):
```
ASSETS (Actif)
Fixed Assets (Immobilisations):
- Intangible assets
- Property & buildings
- Equipment
Less: Accumulated depreciation

Current Assets (Actif Circulant):
- Accounts receivable (tuition)
- Inventory
- Cash and equivalents

TOTAL ASSETS: X,XXX,XXX SAR

LIABILITIES & EQUITY (Passif)
Equity (Capitaux Propres):
- Capital
- Retained earnings
- Current year result

Long-term Liabilities:
- Long-term debt

Current Liabilities (Passif Circulant):
- Accounts payable
- Accrued expenses
- Short-term debt

TOTAL LIABILITIES & EQUITY: X,XXX,XXX SAR
```

**3. Cash Flow Statement** (Tableau de Flux):
```
Operating Activities:
+ Net income
+ Depreciation
+/- Working capital changes
= Operating Cash Flow

Investing Activities:
- CapEx purchases
= Investing Cash Flow

Financing Activities:
+ New borrowing
- Debt repayment
= Financing Cash Flow

NET CHANGE IN CASH: X,XXX,XXX SAR
```

**Export Options**:
- **PDF**: For printing and presentations
- **Excel**: For detailed analysis
- **PCG Format**: French accounting standard
- **IFRS Format**: International standard

---

## 5. Analysis Module

### 5.1 Statistical Analysis & KPIs

**Navigation**: Analysis > Statistical Analysis

**Key Performance Indicators**:

**Enrollment KPIs**:
- Total enrollment (by cycle, level, nationality)
- Growth rate year-over-year
- Capacity utilization (enrollment / 1,875 max)
- Average class size
- French vs Saudi vs Other nationality mix

**Financial KPIs**:
- Revenue per student
- Cost per student
- Operating margin %
- EBITDA margin %
- Net profit margin %

**Workforce KPIs**:
- Student-teacher ratio (overall)
- H/E ratio (hours per student) for secondary
- % AEFE teachers vs local teachers
- Average teacher cost (SAR per FTE)
- HSA hours as % of total hours

**Operational KPIs**:
- Fee collection rate %
- Tuition discount rate %
- Operating expense ratio
- CapEx as % of revenue
- Administrative cost ratio

**KPI Dashboard**:
- Visual charts and graphs
- Trend analysis (multi-year comparison)
- Alerts for out-of-range values
- Export to Excel or PDF

### 5.2 Budget vs Actual Analysis

**Navigation**: Analysis > Budget vs Actual

**Purpose**: Compare actual financial results (imported from Odoo) against budget projections.

**Workflow**:
1. Import actuals from Odoo (see Integrations section)
2. Select:
   - Budget Version (baseline)
   - Period (T1, T2, T3)
   - Account Category (Revenue, Costs, or All)
3. View variance report:
   - **Budget**: Original projection
   - **Actual**: Real results from accounting
   - **Variance**: Actual - Budget
   - **Variance %**: (Variance / Budget) × 100%

**Variance Analysis**:
```
Example - Tuition Revenue:
Budget: 25,000,000 SAR
Actual: 23,500,000 SAR
Variance: -1,500,000 SAR (6% unfavorable)

Potential Causes:
- Lower enrollment than projected
- Higher discounts/scholarships
- Fee collection delays
```

**Favorable vs Unfavorable**:
- **Revenue**: Actual > Budget = Favorable ✓
- **Costs**: Actual < Budget = Favorable ✓

**Action Items**:
- Investigate significant variances (>10%)
- Update forecast if trends continue
- Adjust future budget assumptions

---

## 6. Strategic Planning

### 6.1 5-Year Strategic Plan

**Navigation**: Strategic > 5-Year Plan

**Purpose**: Create multi-year enrollment and financial projections for long-term planning.

**Setup**:
1. Click "Create New Strategic Plan"
2. Enter:
   - **Plan Name**: e.g., "Strategic Plan 2025-2030"
   - **Start Year**: 2025
   - **End Year**: 2030
   - **Base Year**: 2024 (reference for projections)
3. Click "Create"

**Scenarios**:
Create multiple scenarios for sensitivity analysis:
- **Conservative**: Low growth (2% enrollment increase)
- **Base**: Moderate growth (5% enrollment increase)
- **Optimistic**: High growth (8% enrollment increase)

**Projection Methods**:
1. **Enrollment Growth**:
   - Apply annual growth rate
   - Constrain by capacity limit
   - Adjust by nationality mix

2. **Revenue Growth**:
   - Enrollment growth × fee structure
   - Add inflation factor (e.g., 3% annual fee increase)

3. **Cost Growth**:
   - Personnel: Based on FTE growth
   - Operating: Apply inflation (e.g., 4% annual)
   - CapEx: Enter major projects manually

**Strategic KPIs** (5-year horizon):
- Cumulative enrollment growth
- Average annual revenue growth
- Operating margin trend
- Cumulative CapEx investment
- Net cash flow projection

**Example 5-Year Projection**:
```
Year    Enrollment  Revenue (M SAR)  Costs (M SAR)  Net Result (M SAR)
2025    1,500       75.0             68.5           6.5
2026    1,575       81.0             72.0           9.0
2027    1,654       87.5             76.0          11.5
2028    1,737       94.5             80.0          14.5
2029    1,824      102.0             84.5          17.5

Total 5-Year Net Result: 59.0M SAR
```

**Export & Presentation**:
- Generate PDF report with charts
- Export to Excel for board presentations
- Compare scenarios side-by-side

---

## 7. Integrations

### 7.1 Odoo Integration (Accounting System)

**Navigation**: Settings > Integrations > Odoo

**Purpose**: Import actual financial data from Odoo accounting system for budget vs actual analysis.

**Configuration**:
1. Navigate to Odoo settings
2. Enter connection details:
   - **Odoo URL**: https://your-company.odoo.com
   - **Database**: Your database name
   - **API Key**: Generated in Odoo (Settings > Users > API Keys)
3. Click "Test Connection"
4. If successful, click "Save"

**Account Mapping**:
Map Odoo account codes to EFIR PCG account codes:

```
Odoo Account  → EFIR Account  → Description
600010       → 64110         → Teaching salaries
600020       → 64120         → Administrative salaries
410000       → 70110         → Tuition revenue
```

**To Create Mapping**:
1. Click "Add Mapping"
2. Enter Odoo account code
3. Select EFIR account code from dropdown
4. Click "Save"

**Import Actuals**:
1. Navigate to "Import" tab
2. Select:
   - **Period**: T1, T2, or T3
   - **Fiscal Year**: 2025
3. Click "Import Actuals"
4. System will:
   - Fetch data from Odoo via API
   - Map accounts using configuration
   - Import to budget vs actual module
5. Review import summary (X records imported)

**Import History**:
View past imports with:
- Import date/time
- Period and year
- Records imported
- Status (Success/Failed)
- Ability to retry failed imports

### 7.2 Skolengo Integration (Student Information System)

**Navigation**: Settings > Integrations > Skolengo

**Purpose**: Sync enrollment data between Skolengo SIS and EFIR budget application.

**Configuration**:
1. Enter Skolengo API details:
   - **API URL**: Provided by Skolengo
   - **API Key**: Your authentication key
   - **School ID**: Your institution ID
2. Click "Test Connection"
3. Click "Save"

**Import Enrollment**:
1. Navigate to "Import" tab
2. Select:
   - **Academic Year**: 2024-2025
   - **Target Budget Version**: Where to import data
3. Click "Preview" to see data before importing
4. Review student counts by level and nationality
5. Click "Import Enrollment"
6. Data is imported into Planning > Enrollment

**Export Projections**:
Send budget projections back to Skolengo:
1. Navigate to "Export" tab
2. Select budget version to export
3. Click "Export to Skolengo"
4. System sends projected enrollment for next year

**Use Cases**:
- Import current year actuals as base for next year
- Sync mid-year enrollment changes
- Share finalized budget projections with admissions team

### 7.3 AEFE Integration (Teacher Positions)

**Navigation**: Settings > Integrations > AEFE

**Purpose**: Import AEFE teacher position allocations and manage PRRD costs.

**Import Position File**:
1. Obtain position file from AEFE (Excel format)
2. Click "Upload File"
3. Select file from computer
4. Click "Import"
5. System will:
   - Parse position data
   - Identify Detached vs Funded positions
   - Calculate PRRD costs for Detached positions

**Position Types**:
- **Enseignants Titulaires** (Funded): Zero cost to school
- **Résidents Détachés** (Detached): School pays PRRD (~41,863 EUR/year)

**PRRD Rate Configuration**:
1. Navigate to "PRRD" tab
2. Enter current PRRD rate (EUR)
3. Enter EUR to SAR exchange rate
4. Click "Save"
5. System recalculates all AEFE teacher costs

**View Positions**:
- See list of all AEFE positions
- Filter by Funded vs Detached
- View associated costs
- Export to Excel

---

## 8. Troubleshooting

### 8.1 Common Issues

**Issue**: "Cannot submit budget version - validation errors"

**Cause**: Incomplete planning data

**Solution**:
1. Navigate to Configuration > Budget Versions
2. Click on the version showing errors
3. Review error messages (e.g., "Enrollment missing for Collège")
4. Complete missing modules
5. Retry submission

---

**Issue**: "Class calculation results in oversized classes"

**Cause**: Enrollment exceeds max class size × calculated classes

**Solution**:
1. Check class size parameters (Configuration > Class Size)
2. Verify max class size is reasonable
3. Consider manual override:
   - Planning > Class Structure
   - Click "Edit" for affected level
   - Increase number of classes manually

---

**Issue**: "DHG shows unrealistic FTE requirements"

**Cause**: Incorrect subject hours configuration or class structure

**Solution**:
1. Verify subject hours (Configuration > Subject Hours)
2. Check class structure accuracy (Planning > Class Structure)
3. Review DHG calculation breakdown
4. If needed, adjust subject hours to match curriculum

---

**Issue**: "Odoo import failed - connection timeout"

**Cause**: Odoo server unreachable or incorrect credentials

**Solution**:
1. Verify Odoo URL is correct and accessible
2. Test API key in Odoo (Settings > Users > API Keys)
3. Check firewall/network settings
4. Contact IT administrator if issue persists

---

**Issue**: "Financial statements don't balance"

**Cause**: Missing account mappings or calculation errors

**Solution**:
1. Run budget consolidation again
2. Check for validation errors
3. Verify all account codes are valid (60xxx-79xxx)
4. Contact support if issue persists

---

**Issue**: "Export to Excel fails or produces corrupted file"

**Cause**: Browser download settings or data size issues

**Solution**:
1. Try different browser (Chrome recommended)
2. Clear browser cache
3. Disable popup blockers
4. For large datasets, filter to specific period first

---

### 8.2 Getting Help

**Documentation**:
- User Guide (this document)
- Developer Guide (technical reference)
- API Documentation (for integrations)
- Video Tutorials (link in application)

**Support Contacts**:
- **Technical Issues**: IT Helpdesk (helpdesk@efir-school.com)
- **Budget Questions**: Finance Department (finance@efir-school.com)
- **Training Requests**: Training Coordinator (training@efir-school.com)

**Reporting Bugs**:
1. Note exact error message and screenshot
2. Document steps to reproduce
3. Email to: budget-app-support@efir-school.com
4. Include your user ID and budget version

---

## Appendix A: Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl + S` | Save current form |
| `Ctrl + N` | Create new entry (on list pages) |
| `Ctrl + F` | Focus search box |
| `Ctrl + E` | Edit selected item |
| `Esc` | Close modal/dialog |
| `Ctrl + /` | Show keyboard shortcuts |

---

## Appendix B: Glossary

**AEFE**: Agence pour l'enseignement français à l'étranger (Agency for French Education Abroad)

**DAI**: Droit Annuel d'Inscription (Annual Enrollment Right)

**DHG**: Dotation Horaire Globale (Global Hours Allocation) - method for calculating teacher requirements

**FTE**: Full-Time Equivalent

**H/E**: Heures/Élève (Hours per Student ratio)

**HSA**: Heures Supplémentaires Annuelles (Annual Overtime Hours)

**PCG**: Plan Comptable Général (French Chart of Accounts)

**PRRD**: Participation à la Rémunération des Résidents Détachés (Contribution to AEFE Detached Teacher Compensation)

**TRMD**: Tableau de Répartition des Moyens par Discipline (Discipline-wise Resource Allocation Table)

---

**End of User Guide**
