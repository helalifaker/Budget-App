# Integration Guide - EFIR Budget App

This guide provides setup instructions for integrating the EFIR Budget App with external systems: Odoo, Skolengo, and AEFE.

## Table of Contents

1. [Overview](#overview)
2. [Odoo Integration](#odoo-integration)
3. [Skolengo Integration](#skolengo-integration)
4. [AEFE Integration](#aefe-integration)
5. [Security Considerations](#security-considerations)
6. [Troubleshooting](#troubleshooting)

---

## Overview

The EFIR Budget App integrates with three external systems:

- **Odoo**: Import actual financial data (revenue and costs) for budget vs actual analysis
- **Skolengo**: Import/export enrollment data for variance analysis
- **AEFE**: Import teacher position data and PRRD contribution rates

### Integration Architecture

```
EFIR Budget App
    ├── Odoo Integration (XML-RPC API)
    │   └── Import actuals by period (T1, T2, T3)
    ├── Skolengo Integration (REST API + File Import)
    │   ├── Export enrollment to CSV
    │   └── Import actual enrollment
    └── AEFE Integration (File Import)
        └── Import position data from Excel
```

### Key Features

- **Automated Data Import**: Schedule automatic syncs from external systems
- **Data Mapping**: Automatic mapping of external account codes to EFIR codes
- **Audit Logging**: Complete audit trail of all import/export operations
- **Error Handling**: Graceful error handling with detailed error messages
- **Batch Processing**: Support for importing large datasets in batches

---

## Odoo Integration

### Overview

Odoo integration allows importing actual financial data (revenue and costs) for budget variance analysis. The system uses Odoo's XML-RPC API to fetch account move lines.

### Prerequisites

- Odoo 14.0+ instance (tested with 14.0-16.0)
- Database name
- Username with accounting read permissions
- Password or API key

### Configuration Steps

#### 1. Configure Connection Settings

Navigate to: **Settings > Integrations > Odoo**

**Required Fields:**
- **URL**: Odoo server URL (e.g., `https://odoo.example.com`)
- **Database**: Odoo database name
- **Username**: Odoo username
- **Password**: User password (encrypted before storage)

**Optional Fields:**
- **Auto-sync enabled**: Enable automatic syncing
- **Auto-sync interval**: Sync frequency in minutes (minimum 5)

#### 2. Test Connection

Click **Test Connection** to verify credentials and connectivity.

**Success Response:**
```json
{
  "success": true,
  "message": "Successfully connected to Odoo as user ID 123",
  "user_id": 123
}
```

#### 3. Configure Account Mapping

The system uses predefined account mappings to convert Odoo account codes to EFIR codes:

**Revenue Accounts:**
| Odoo Code | EFIR Code | Description |
|-----------|-----------|-------------|
| 70001 | 70110 | Tuition T1 |
| 70002 | 70120 | Tuition T2 |
| 70003 | 70130 | Tuition T3 |
| 70011 | 70210 | Registration fees T1 |
| 70021 | 70310 | DAI fees T1 |

**Cost Accounts:**
| Odoo Code | EFIR Code | Description |
|-----------|-----------|-------------|
| 60001 | 64110 | Teaching salaries |
| 60002 | 64120 | Administrative salaries |
| 61001 | 61110 | Facility rent |
| 62001 | 62110 | Office supplies |

**Note:** To customize mappings, edit `backend/app/services/odoo_integration.py` and update the `ODOO_TO_EFIR_ACCOUNTS` dictionary.

### Import Workflow

#### Manual Import

1. Navigate to: **Settings > Integrations > Odoo**
2. Select **Import Actuals**
3. Choose:
   - Budget Version
   - Period (T1, T2, or T3)
   - Fiscal Year
4. Click **Import**

**API Endpoint:**
```bash
POST /api/v1/integrations/odoo/import-actuals
{
  "budget_version_id": "uuid",
  "period": "T1",
  "fiscal_year": 2025
}
```

#### Auto-Sync (All Periods)

Click **Sync All Periods** to import T1, T2, and T3 in one operation.

**API Endpoint:**
```bash
POST /api/v1/integrations/odoo/sync
{
  "budget_version_id": "uuid",
  "fiscal_year": 2025
}
```

### Period Date Ranges

- **T1** (Period 1): January 1 - June 30
- **T2** (Summer): July 1 - August 31
- **T3** (Period 2): September 1 - December 31

### Data Processing

The integration:

1. **Connects** to Odoo via XML-RPC
2. **Searches** for account move lines in date range
3. **Filters** to posted entries only (`move_id.state = 'posted'`)
4. **Maps** Odoo account codes to EFIR codes
5. **Aggregates** amounts by EFIR account
6. **Imports** into `budget_actuals` table
7. **Logs** operation in `integration_logs` table

### Troubleshooting

**Connection Failed:**
- Verify Odoo URL is accessible
- Check database name is correct
- Confirm user has XML-RPC API access enabled

**Authentication Failed:**
- Verify username and password
- Check user is not locked
- Confirm user has accounting read permissions

**No Data Imported:**
- Verify account move lines exist in date range
- Check account codes match mapping
- Ensure moves are posted (not draft)

---

## Skolengo Integration

### Overview

Skolengo integration enables importing actual enrollment data and comparing against budget projections to identify variances.

### Prerequisites

- Skolengo API access (for API sync)
- API URL and API key
- Or: CSV/Excel file with enrollment data

### Configuration Steps

#### 1. Configure API Settings (Optional)

Navigate to: **Settings > Integrations > Skolengo**

**Required Fields:**
- **API URL**: Skolengo API endpoint
- **API Key**: Authentication key

#### 2. Level Mapping

The system uses predefined level mappings:

| Skolengo Level | EFIR Code | Cycle |
|----------------|-----------|-------|
| Maternelle-PS | PS | Maternelle |
| Maternelle-MS | MS | Maternelle |
| Maternelle-GS | GS | Maternelle |
| Elementaire-CP | CP | Élémentaire |
| Elementaire-CE1 | CE1 | Élémentaire |
| College-6eme | 6ème | Collège |
| Lycee-Terminale | Terminale | Lycée |

**Note:** To customize mappings, edit `backend/app/services/skolengo_integration.py` and update the `SKOLENGO_TO_EFIR_LEVELS` dictionary.

### Import/Export Workflow

#### Export Enrollment

1. Navigate to: **Settings > Integrations > Skolengo**
2. Select Budget Version
3. Click **Export to CSV**
4. Download generated CSV file

**CSV Format:**
```csv
Level,Nationality,Count
Maternelle-PS,French,15
Maternelle-MS,French,18
Elementaire-CP,Saudi,10
```

**API Endpoint:**
```bash
GET /api/v1/integrations/skolengo/export/{version_id}
```

#### Import Enrollment (File)

1. Prepare CSV or Excel file with columns:
   - **Level**: Skolengo level name
   - **Nationality**: French, Saudi, or Other
   - **Count**: Number of students (integer ≥ 0)
2. Navigate to: **Settings > Integrations > Skolengo**
3. Click **Import File**
4. Select file
5. Click **Upload**

**API Endpoint:**
```bash
POST /api/v1/integrations/skolengo/import?budget_version_id={uuid}
Content-Type: multipart/form-data
file: (binary)
```

#### Sync via API

Click **Sync via API** to fetch enrollment data directly from Skolengo API.

**API Endpoint:**
```bash
POST /api/v1/integrations/skolengo/sync/{version_id}
```

### Variance Analysis

Navigate to: **Settings > Integrations > Skolengo > Variance Report**

**Report Columns:**
- **Level**: Academic level
- **Nationality**: Nationality category
- **Budget**: Budgeted enrollment
- **Actual**: Actual enrollment (from import/sync)
- **Variance**: Difference (actual - budget)
- **Variance %**: Percentage variance

**Color Coding:**
- **Green**: Within ±5% of budget
- **Yellow**: ±5-10% variance
- **Red**: >10% variance

**API Endpoint:**
```bash
GET /api/v1/integrations/skolengo/compare/{version_id}
```

### Troubleshooting

**Invalid File Format:**
- Ensure file is CSV or Excel (.xlsx, .xls)
- Verify all required columns are present
- Check column names match exactly (case-sensitive)

**Invalid Level Name:**
- Verify level names match Skolengo format
- Check for typos or extra spaces
- Refer to level mapping table above

**Negative Counts:**
- Ensure all Count values are ≥ 0
- Check for formula errors in Excel

---

## AEFE Integration

### Overview

AEFE integration imports teacher position data including PRRD (Participation à la Rémunération des Résidents Détachés) contribution rates.

### Prerequisites

- Excel file (.xlsx or .xls) with AEFE position data

### File Format

**Required Columns:**
- **Teacher Name**: Full name (optional for summary positions)
- **Category**: Position category (Detached, Funded, or Resident)
- **Cycle**: Educational cycle (Maternelle, Elementaire, or Secondary)
- **PRRD Rate**: PRRD contribution in EUR (0 for AEFE-funded positions)

**Example:**
```
| Teacher Name    | Category  | Cycle       | PRRD Rate |
|-----------------|-----------|-------------|-----------|
| Marie Dupont    | Detached  | Maternelle  | 41863.0   |
| Jean Martin     | Detached  | Elementaire | 41863.0   |
| Sophie Bernard  | Funded    | Secondary   | 0.0       |
```

### Import Workflow

#### 1. Download Template

1. Navigate to: **Settings > Integrations > AEFE**
2. Click **Download Template**
3. Fill in position data
4. Save as .xlsx

**API Endpoint:**
```bash
GET /api/v1/integrations/aefe/template
```

#### 2. Import Positions

1. Navigate to: **Settings > Integrations > AEFE**
2. Click **Import Positions**
3. Select Excel file
4. Click **Upload**

**API Endpoint:**
```bash
POST /api/v1/integrations/aefe/import
Content-Type: multipart/form-data
file: (binary)
```

### Position Categories

**Detached:**
- AEFE detached teachers (French nationals)
- School pays PRRD contribution (~€41,863 per teacher)
- Full benefits from AEFE

**Funded:**
- Fully AEFE-funded positions
- No cost to school (PRRD = 0)
- Usually department heads or special positions

**Resident:**
- Resident teachers with special status
- Variable PRRD rates
- Partial school contribution

### Position Summary

View position summary at: **Settings > Integrations > AEFE > Summary**

**Summary Cards:**
- **Total AEFE Positions**: Count of all positions
- **AEFE-Funded Positions**: Count of funded positions (no school cost)
- **Total PRRD Contribution**: Sum of PRRD rates in EUR

**Position Breakdown Table:**
| Category | Cycle | Count | PRRD Rate | Total Cost |
|----------|-------|-------|-----------|------------|
| Detached | Maternelle | 5 | €41,863 | €209,315 |
| Detached | Elementaire | 8 | €41,863 | €334,904 |
| Funded | Secondary | 3 | €0 | €0 |

**API Endpoint:**
```bash
GET /api/v1/integrations/aefe/summary
```

### Troubleshooting

**Invalid File Format:**
- Ensure file is Excel format (.xlsx or .xls)
- Verify all required columns are present
- Check column names match exactly

**Invalid Category:**
- Must be: Detached, Funded, or Resident
- Check for typos or extra spaces
- Case-sensitive

**Invalid Cycle:**
- Must be: Maternelle, Elementaire, or Secondary
- Check spelling (note: French accents in Élémentaire)

**Negative PRRD Rate:**
- PRRD rate cannot be negative
- Use 0 for AEFE-funded positions

---

## Security Considerations

### Credential Storage

**Passwords and API Keys:**
- Encrypted using Fernet (symmetric encryption)
- Stored encrypted in `integration_settings.config` (JSONB)
- Decrypted only when needed for API calls
- Never logged or returned in API responses

**Production Recommendation:**
- Store encryption key in environment variable
- Use separate keys per environment (dev, staging, prod)
- Rotate keys periodically
- Use Supabase Vault for additional security

### File Upload Security

**Validation:**
- File type validation (.csv, .xlsx, .xls only)
- File size limit: 10MB maximum
- Content scanning for malicious files (basic checks)

**Storage:**
- Files stored temporarily during processing
- Deleted immediately after import
- No persistent file storage

### API Rate Limiting

**Skolengo API:**
- Respects Skolengo rate limits
- Implements exponential backoff on failures
- Queues requests if rate limit exceeded

**Odoo API:**
- No built-in rate limit (XML-RPC)
- Recommend limiting manual imports to avoid overload

### Audit Logging

All integration operations are logged in `integration_logs`:

- **Integration Type**: odoo, skolengo, aefe
- **Action**: import_actuals, export_enrollment, etc.
- **Status**: success, failed, partial
- **Records Processed/Failed**: Count
- **Error Message**: If failed
- **User**: Who initiated the operation
- **Timestamp**: When operation occurred

**View Logs:**
```bash
GET /api/v1/integrations/logs?integration_type=odoo&status_filter=failed
```

---

## Troubleshooting

### Common Issues

#### Connection Timeout

**Symptoms:**
- API calls hang or timeout
- Error: "Connection timeout"

**Solutions:**
- Check network connectivity
- Verify firewall rules allow outbound connections
- Increase timeout in Nginx/proxy if behind firewall
- Check external system is online

#### Authentication Failed

**Symptoms:**
- Error: "Authentication failed"
- Error: "Invalid credentials"

**Solutions:**
- Verify username and password are correct
- Check API key has not expired
- Confirm user has required permissions
- Check for special characters in password (may need escaping)

#### Data Not Imported

**Symptoms:**
- Import succeeds but 0 records imported
- No error message

**Solutions:**
- Verify date range contains data
- Check account codes match mapping
- Ensure data meets validation rules
- Review integration log for details

#### Partial Import

**Symptoms:**
- Some records imported, some failed
- Status: "partial"

**Solutions:**
- Review error messages in integration log
- Check failed records for validation issues
- Fix data and re-import
- May need to delete previous batch before re-importing

### Debug Mode

Enable SQL logging to debug database issues:

```bash
# In .env
SQL_ECHO=True
```

This will log all SQL queries to console for debugging.

### Support

For additional support:

1. Check integration logs: `/api/v1/integrations/logs`
2. Review error messages
3. Consult API documentation: `/docs`
4. Contact EFIR IT support

---

## API Reference

### Base URL

```
{API_BASE_URL}/api/v1/integrations
```

### Authentication

All endpoints require JWT authentication:

```
Authorization: Bearer {token}
```

### Endpoints Summary

**Odoo:**
- `POST /odoo/connect` - Test connection
- `POST /odoo/import-actuals` - Import actuals
- `POST /odoo/sync` - Sync all periods
- `GET /odoo/actuals/{version_id}` - Get actuals

**Skolengo:**
- `GET /skolengo/export/{version_id}` - Export enrollment
- `POST /skolengo/import` - Import enrollment
- `POST /skolengo/sync/{version_id}` - Sync via API
- `GET /skolengo/compare/{version_id}` - Variance report

**AEFE:**
- `POST /aefe/import` - Import positions
- `GET /aefe/positions` - List positions
- `GET /aefe/summary` - Position summary
- `GET /aefe/template` - Download template

**Settings:**
- `POST /settings` - Create/update settings
- `GET /settings/{type}` - Get settings
- `PATCH /settings/{type}` - Update settings

**Logs:**
- `GET /logs` - List logs (with filters)
- `GET /logs/{log_id}` - Get specific log

### Full API documentation available at: `/docs` (Swagger UI)

---

## Change Log

**Version 1.0** (December 2025)
- Initial release
- Odoo integration (XML-RPC)
- Skolengo integration (file-based)
- AEFE integration (Excel import)
- Integration settings and logging
- Audit trail

**Future Enhancements:**
- Skolengo REST API integration (currently file-based)
- Automated sync scheduling (cron jobs)
- Real-time sync with webhooks
- Advanced data validation rules
- Custom mapping configuration UI
- Integration dashboard with metrics
