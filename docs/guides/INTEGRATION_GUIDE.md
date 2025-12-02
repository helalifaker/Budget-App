# EFIR Budget Planning Application - Integration Guide

**Version**: 1.0
**Last Updated**: December 2025

## Overview

The EFIR Budget Planning Application integrates with three external systems:
1. **Odoo**: Accounting system for actual financial data
2. **Skolengo**: Student Information System for enrollment data
3. **AEFE**: Position file for AEFE teacher allocations

---

## 1. Odoo Integration

### 1.1 Purpose

Import actual financial results from Odoo for budget vs actual variance analysis.

### 1.2 Prerequisites

- Odoo 17.0+ instance
- API access enabled
- Valid API key
- Account mapping configured

### 1.3 Setup Steps

**Step 1: Generate Odoo API Key**

1. Log in to Odoo as administrator
2. Navigate to Settings > Users & Companies > Users
3. Select your user
4. Click "New API Key"
5. Enter a descriptive name (e.g., "EFIR Budget App")
6. Click "Generate Key"
7. Copy and securely store the key (shown only once)

**Step 2: Configure Connection in EFIR App**

1. Navigate to Settings > Integrations > Odoo
2. Enter connection details:
   - **Odoo URL**: https://your-company.odoo.com
   - **Database**: Your database name
   - **API Key**: Generated key from Step 1
   - **Username**: Your Odoo username
3. Click "Test Connection"
4. If successful, click "Save Configuration"

**Step 3: Map Account Codes**

Map Odoo account codes to EFIR PCG account codes:

| Odoo Code | EFIR Code | Description |
|-----------|-----------|-------------|
| 600010 | 64110 | Teaching Salaries |
| 600020 | 64120 | Administrative Salaries |
| 610000 | 61110 | Educational Supplies |
| 410000 | 70110 | Tuition Revenue T1 |
| 410001 | 70120 | Tuition Revenue T2 |
| 410002 | 70130 | Tuition Revenue T3 |

To add mapping:
1. Navigate to "Mapping" tab
2. Click "Add Mapping"
3. Enter Odoo account code
4. Select EFIR account code from dropdown
5. Add description
6. Click "Save"

### 1.4 Importing Actuals

**Via UI**:
1. Navigate to Settings > Integrations > Odoo > Import
2. Select:
   - **Period**: T1, T2, or T3
   - **Fiscal Year**: 2025
   - **Budget Version**: Target version for comparison
3. Click "Import Actuals"
4. Wait for import to complete (progress bar shown)
5. Review import summary

**Via API**:
```bash
curl -X POST https://api.efir-budget.com/api/v1/integrations/odoo/import-actuals \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "version_id": "version-uuid",
    "period": "T1",
    "fiscal_year": 2025
  }'
```

**Response**:
```json
{
  "import_id": "import-uuid",
  "records_imported": 150,
  "status": "SUCCESS",
  "summary": {
    "revenue_records": 75,
    "expense_records": 75,
    "unmapped_accounts": []
  }
}
```

### 1.5 Import Schedule

Recommended import frequency:
- **Monthly**: For ongoing budget vs actual tracking
- **End of Period**: For formal variance analysis
- **Ad-hoc**: When investigating specific variances

### 1.6 Troubleshooting

**Issue**: Connection test fails with "Authentication error"

**Solution**:
- Verify API key is correct and not expired
- Check username has API access permissions in Odoo
- Ensure API access is enabled in Odoo settings

---

**Issue**: Import succeeds but shows "unmapped accounts"

**Solution**:
- Navigate to Mapping tab
- Review unmapped account list
- Add mappings for each unmapped account
- Re-run import

---

**Issue**: Import hangs or times out

**Solution**:
- Check Odoo server status
- Verify network connectivity
- Try importing smaller date range
- Contact IT support if issue persists

---

## 2. Skolengo Integration

### 2.1 Purpose

Sync enrollment data between Skolengo SIS and EFIR budget application for seamless planning.

### 2.2 Prerequisites

- Skolengo account with API access
- API credentials (provided by Skolengo)
- School ID

### 2.3 Setup Steps

**Step 1: Obtain Skolengo API Credentials**

Contact Skolengo support to request:
- API URL (e.g., https://api.skolengo.com)
- API Key
- School ID

**Step 2: Configure Connection in EFIR App**

1. Navigate to Settings > Integrations > Skolengo
2. Enter credentials:
   - **API URL**: Provided by Skolengo
   - **API Key**: Your authentication key
   - **School ID**: Your institution ID
3. Click "Test Connection"
4. If successful, click "Save Configuration"

### 2.4 Importing Enrollment

**Import Current Year Enrollment** (as baseline):

1. Navigate to Settings > Integrations > Skolengo > Import
2. Select:
   - **Academic Year**: 2024-2025
   - **Target Budget Version**: Budget 2025-2026
3. Click "Preview" to see data before importing
4. Review student counts by level
5. Click "Import Enrollment"
6. Data is imported into Planning > Enrollment module

**Example Import Result**:
```
Imported 1,450 students:
- Maternelle: 250 students
- Élémentaire: 500 students
- Collège: 400 students
- Lycée: 300 students

By Nationality:
- French: 870 students (60%)
- Saudi: 435 students (30%)
- Other: 145 students (10%)
```

### 2.5 Exporting Projections

**Export Budget Projections to Skolengo**:

1. Navigate to Settings > Integrations > Skolengo > Export
2. Select budget version to export
3. Click "Export to Skolengo"
4. System sends projected enrollment for next year
5. Admissions team can view projections in Skolengo

**Use Cases**:
- Share finalized budget projections with admissions
- Coordinate recruitment targets
- Align capacity planning

### 2.6 Data Format

**Import Format** (from Skolengo):
```json
{
  "academic_year": "2024-2025",
  "students": [
    {
      "student_id": "stu-12345",
      "level": "6ème",
      "nationality": "French",
      "enrollment_date": "2024-09-01"
    }
  ]
}
```

**Export Format** (to Skolengo):
```json
{
  "academic_year": "2025-2026",
  "projections": [
    {
      "level": "6ème",
      "projected_students": 125,
      "nationality_breakdown": {
        "French": 75,
        "Saudi": 38,
        "Other": 12
      }
    }
  ]
}
```

### 2.7 Troubleshooting

**Issue**: Import shows 0 students

**Solution**:
- Verify academic year selection matches data in Skolengo
- Check API key has read permissions
- Ensure school ID is correct
- Contact Skolengo support

---

**Issue**: Duplicate enrollment records

**Solution**:
- System automatically deduplicates by student ID
- If issue persists, delete existing enrollments and re-import
- Contact support if duplicates remain

---

## 3. AEFE Integration

### 3.1 Purpose

Import AEFE teacher position allocations to accurately calculate PRRD costs.

### 3.2 Prerequisites

- AEFE position file (Excel format)
- PRRD rate for fiscal year
- EUR to SAR exchange rate

### 3.3 Position File Format

AEFE provides an Excel file with this structure:

| Column | Description | Example |
|--------|-------------|---------|
| Position_ID | Unique identifier | POS-2025-001 |
| Teacher_Name | Name (optional) | Jean Dupont |
| Position_Type | Funded or Detached | Détaché |
| Subject | Subject taught | Mathématiques |
| Level | Academic level | Collège |
| FTE | Full-time equivalent | 1.0 |
| Start_Date | Position start date | 2025-09-01 |
| End_Date | Position end date | 2026-06-30 |

**Position Types**:
- **Enseignant Titulaire** (Funded): Fully funded by AEFE, zero cost to school
- **Résident Détaché** (Detached): School pays PRRD contribution (~41,863 EUR/year)

### 3.4 Importing Position File

**Via UI**:
1. Navigate to Settings > Integrations > AEFE
2. Click "Upload File"
3. Select AEFE position Excel file
4. Select target budget version
5. Click "Import"
6. Review import summary:
   - Total positions imported
   - Funded positions (zero cost)
   - Detached positions (PRRD cost)
   - Total PRRD cost in EUR and SAR

**Example Import Summary**:
```
Positions Imported: 45
- Funded (Titulaires): 20 positions (Zero cost)
- Detached (Détachés): 25 positions

PRRD Costs:
- Per Teacher: 41,863 EUR
- Total: 1,046,575 EUR
- In SAR (@ 4.2 rate): 4,395,615 SAR
```

### 3.5 PRRD Rate Configuration

**Update PRRD Rate**:
1. Navigate to Settings > Integrations > AEFE > PRRD Configuration
2. Enter:
   - **PRRD Rate (EUR)**: 41,863 (for 2025)
   - **EUR to SAR Exchange Rate**: 4.2
3. Click "Save"
4. System recalculates all AEFE costs automatically

**Historical PRRD Rates**:
- 2023: 40,500 EUR
- 2024: 41,200 EUR
- 2025: 41,863 EUR

### 3.6 Viewing Positions

1. Navigate to Settings > Integrations > AEFE > Positions
2. View table of all positions:
   - Filter by Funded/Detached
   - Search by subject or level
   - View associated costs
3. Export to Excel for reporting

### 3.7 Integration with DHG Module

AEFE positions automatically flow to DHG module:
- Funded positions: Available FTE (zero cost)
- Detached positions: Available FTE (with PRRD cost)
- Local positions: Filled by recruitment to meet gap

**TRMD (Gap Analysis)**:
```
Subject: Mathématiques - Collège
DHG Hours Required: 68h/week
Required FTE: 3.78 → 4 teachers

Available Positions:
- AEFE Funded: 1 FTE (Zero cost)
- AEFE Detached: 1 FTE (41,863 EUR = 175,824 SAR)
- Gap: 2 FTE

Local Recruitment Needed:
- 2 teachers @ 20,000 SAR/month × 12 months = 480,000 SAR

Total Mathématiques Cost:
- AEFE: 175,824 SAR
- Local: 480,000 SAR
- Total: 655,824 SAR
```

### 3.8 Troubleshooting

**Issue**: Import fails with "Invalid file format"

**Solution**:
- Verify file is Excel format (.xlsx)
- Check column headers match expected format
- Ensure Position_Type values are "Titulaire" or "Détaché"
- Remove any merged cells or formatting

---

**Issue**: PRRD costs don't update after changing exchange rate

**Solution**:
- Click "Recalculate Costs" button
- Navigate to DHG module to see updated costs
- If issue persists, re-import position file

---

## 4. Integration Testing

### 4.1 Test Data

Use test credentials for integration testing:

**Odoo Test Instance**:
- URL: https://test.odoo.com
- Database: efir_test
- API Key: test_key_12345
- Account: test@efir.local

**Skolengo Sandbox**:
- URL: https://sandbox.skolengo.com
- API Key: sandbox_key_67890
- School ID: TEST_SCHOOL

### 4.2 Test Scenarios

**Odoo Integration Test**:
1. Configure test connection
2. Import actuals for test period
3. Verify 10+ records imported
4. Check budget vs actual shows variance
5. Disconnect test connection

**Skolengo Integration Test**:
1. Configure sandbox connection
2. Import test enrollment (100 students)
3. Verify data in Planning > Enrollment
4. Export projections back to sandbox
5. Verify export successful

**AEFE Integration Test**:
1. Upload sample position file (5-10 positions)
2. Verify funded vs detached split
3. Check PRRD calculation accuracy
4. Verify costs flow to DHG module
5. Delete test data

### 4.3 Integration Monitoring

**Health Checks**:
- Odoo: Daily connection test
- Skolengo: Weekly sync check
- AEFE: Manual file imports (as received)

**Error Alerting**:
- Failed imports trigger email notification
- Connection failures logged
- Weekly integration health report

---

## 5. Security Considerations

### 5.1 API Keys

- Store API keys securely (environment variables)
- Never commit keys to Git
- Rotate keys annually
- Use separate keys for dev/production

### 5.2 Data Privacy

- Import only necessary fields
- Anonymize student data if possible (use IDs, not names)
- Comply with GDPR and local data protection laws
- Audit integration logs regularly

### 5.3 Access Control

- Restrict integration configuration to admin role
- Log all import/export operations
- Review access logs monthly

---

## 6. Support Contacts

**Odoo Support**:
- Email: support@odoo.com
- Phone: +1-xxx-xxx-xxxx

**Skolengo Support**:
- Email: support@skolengo.com
- Phone: +33-x-xx-xx-xx-xx

**AEFE Contact**:
- Email: positions@aefe.fr
- Website: https://www.aefe.fr

**EFIR IT Support**:
- Email: it@efir-school.com
- Internal: Ext. 1234

---

**End of Integration Guide**
