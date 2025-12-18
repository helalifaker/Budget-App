# Module 16: Dashboard Configuration

## Overview

Module 16 provides the foundation for user-customizable dashboards and system-defined dashboard templates in the EFIR Budget Planning Application. This module enables users to create personalized views of budget data, KPIs, and financial metrics through flexible widget-based layouts.

**Layer**: Analysis Layer (Phase 4)
**Status**: Database Foundation Implemented (Phase 4)
**Future Phases**: Dashboard builder UI, widget rendering, real-time updates (Phase 5-6)

### Purpose

- Define system dashboard templates for different user roles (executive, finance manager, department, operations)
- Allow users to create custom dashboards with personalized layouts
- Support multiple widget types (KPI cards, charts, tables, gauges, heatmaps, etc.)
- Store user preferences for theme, default dashboard, notification settings
- Enable responsive 12×12 grid layout for flexible widget positioning

### Key Design Decisions

1. **Dual Dashboard Model**: Support both system-defined templates (public) and user-created dashboards (private)
2. **Ownership Pattern**: Dashboards can be owned by users (owner_user_id) or be system templates (dashboard_role)
3. **12×12 Grid Layout**: All widgets positioned on a 12-column grid system (like Bootstrap, Material UI)
4. **Widget Configuration**: JSONB fields allow flexible, widget-specific configuration without schema changes
5. **User Preferences**: Separate table for user-specific settings (theme, default dashboard, notifications)

## Database Schema

### Tables

#### 1. dashboard_configs

Dashboard definitions including both system templates and user-created dashboards.

**Columns:**
```sql
id                UUID PRIMARY KEY
name_en           VARCHAR(200) NOT NULL
name_fr           VARCHAR(200) NOT NULL
description_en    TEXT NULL
description_fr    TEXT NULL
dashboard_role    dashboardrole NULL         -- ENUM: executive, finance_manager, department, operations
                                             -- NULL for user-created dashboards
owner_user_id     UUID NULL                  -- FK to auth.users.id
                                             -- NULL for system templates
is_default        BOOLEAN NOT NULL DEFAULT false
layout_config     JSONB NOT NULL             -- Grid configuration, breakpoints, etc.
created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
created_by_id     UUID NULL FOREIGN KEY -> auth.users.id (SET NULL)
updated_by_id     UUID NULL FOREIGN KEY -> auth.users.id (SET NULL)
deleted_at        TIMESTAMPTZ NULL           -- Soft delete support
```

**Constraints:**
- Exactly one of (dashboard_role, owner_user_id) must be set (XOR constraint)
- If dashboard_role IS NOT NULL, owner_user_id must be NULL (system template)
- If owner_user_id IS NOT NULL, dashboard_role must be NULL (user dashboard)
- Bilingual names required for all dashboards

**RLS Policies:**
- Admin: Full access to all dashboards
- Manager: Full access to system templates, read-only to user dashboards
- Owner: Full access to own dashboards
- All users: Read system templates

**Dashboard Types:**

1. **System Templates** (dashboard_role IS NOT NULL, owner_user_id IS NULL):
   - Pre-configured by admins/managers
   - Visible to all users
   - Role-specific layouts (executive, finance manager, etc.)
   - Cannot be modified by regular users

2. **User Dashboards** (owner_user_id IS NOT NULL, dashboard_role IS NULL):
   - Created by individual users
   - Private to the owner
   - Fully customizable
   - Can clone system templates as starting point

#### 2. dashboard_widgets

Widget definitions within dashboards.

**Columns:**
```sql
id                UUID PRIMARY KEY
dashboard_id      UUID NOT NULL FOREIGN KEY -> dashboard_configs.id (CASCADE)
widget_type       widgettype NOT NULL        -- ENUM: kpi_card, chart, table, etc.
title_en          VARCHAR(200) NOT NULL
title_fr          VARCHAR(200) NOT NULL
position_x        INTEGER NOT NULL           -- Column position (0-11 in 12-col grid)
position_y        INTEGER NOT NULL           -- Row position (0-based)
width             INTEGER NOT NULL           -- Columns spanned (1-12)
height            INTEGER NOT NULL           -- Rows spanned (1-10)
display_order     INTEGER NOT NULL DEFAULT 0
widget_config     JSONB NOT NULL             -- Widget-specific configuration
created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
created_by_id     UUID NULL FOREIGN KEY -> auth.users.id (SET NULL)
updated_by_id     UUID NULL FOREIGN KEY -> auth.users.id (SET NULL)
deleted_at        TIMESTAMPTZ NULL           -- Soft delete support
```

**Constraints:**
- position_x must be between 0 and 11 (12-column grid)
- width must be between 1 and 12
- position_x + width must be ≤ 12 (no overflow)
- height must be between 1 and 10
- Widget cannot overlap with other widgets in the same dashboard (enforced by application logic)

**RLS Policies:**
- Admin: Full access to all widgets
- Manager: Full access to system template widgets
- Owner: Full access to widgets in owned dashboards
- All users: Read widgets from accessible dashboards

**Widget Types (widgettype enum):**
- `kpi_card`: Single KPI value with trend indicator
- `chart`: Line, bar, pie, area charts (Recharts)
- `table`: Data table with sorting/filtering (AG Grid)
- `variance_table`: Budget vs Actual variance table
- `waterfall`: Waterfall chart for revenue/cost breakdown
- `gauge`: Gauge chart for KPI targets
- `timeline`: Timeline view for budget milestones
- `heatmap`: Heatmap for enrollment by level/nationality

#### 3. user_preferences

User-specific preferences and settings.

**Columns:**
```sql
id                       UUID PRIMARY KEY
user_id                  UUID NOT NULL UNIQUE FOREIGN KEY -> auth.users.id (CASCADE)
default_dashboard_id     UUID NULL FOREIGN KEY -> dashboard_configs.id (SET NULL)
theme                    VARCHAR(20) NOT NULL DEFAULT 'light'  -- 'light', 'dark', 'auto'
language                 VARCHAR(5) NOT NULL DEFAULT 'fr'      -- 'en', 'fr'
date_format              VARCHAR(20) NOT NULL DEFAULT 'DD/MM/YYYY'
number_format            VARCHAR(20) NOT NULL DEFAULT 'fr-FR'  -- Locale for number formatting
currency_display         VARCHAR(10) NOT NULL DEFAULT 'SAR'
notification_settings    JSONB NOT NULL DEFAULT '{}'::jsonb
display_preferences      JSONB NOT NULL DEFAULT '{}'::jsonb
created_at               TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at               TIMESTAMPTZ NOT NULL DEFAULT NOW()
created_by_id            UUID NULL FOREIGN KEY -> auth.users.id (SET NULL)
updated_by_id            UUID NULL FOREIGN KEY -> auth.users.id (SET NULL)
deleted_at               TIMESTAMPTZ NULL                     -- Soft delete support
```

**Constraints:**
- Unique user_id (one preference record per user)
- theme must be in ('light', 'dark', 'auto')
- language must be in ('en', 'fr')
- If default_dashboard_id is set, user must have access to that dashboard

**RLS Policies:**
- Admin: Full access to all user preferences
- Self: Full access to own preferences only

**Default Values:**
- Theme: light
- Language: fr (French default for EFIR)
- Date format: DD/MM/YYYY (European format)
- Number format: fr-FR (French locale: 1 234,56)
- Currency: SAR

### Enums

#### DashboardRole

```sql
CREATE TYPE efir_budget.dashboardrole AS ENUM (
    'executive',         -- CEO, CFO: High-level KPIs, strategic metrics
    'finance_manager',   -- Finance team: Detailed budget, actuals, variance
    'department',        -- Department heads: Department-specific metrics
    'operations'         -- Operations team: Enrollment, staffing, capacity
);
```

#### WidgetType

```sql
CREATE TYPE efir_budget.widgettype AS ENUM (
    'kpi_card',         -- Single KPI with trend
    'chart',            -- Chart widget (line, bar, pie, area)
    'table',            -- Data table (AG Grid)
    'variance_table',   -- Budget vs Actual table
    'waterfall',        -- Waterfall chart
    'gauge',            -- Gauge chart for targets
    'timeline',         -- Timeline/Gantt chart
    'heatmap'           -- Heatmap visualization
);
```

## Data Model

### Sample Dashboard Configuration

#### System Template: Executive Dashboard

```json
{
  "id": "exec-001",
  "name_en": "Executive Dashboard",
  "name_fr": "Tableau de Bord Exécutif",
  "description_en": "High-level KPIs and strategic metrics for C-suite",
  "description_fr": "KPIs de haut niveau et métriques stratégiques pour la direction",
  "dashboard_role": "executive",
  "owner_user_id": null,
  "is_default": true,
  "layout_config": {
    "columns": 12,
    "row_height": 80,
    "breakpoints": {
      "lg": 1200,
      "md": 996,
      "sm": 768,
      "xs": 480
    },
    "cols": {
      "lg": 12,
      "md": 10,
      "sm": 6,
      "xs": 4
    }
  }
}
```

#### User Dashboard: Custom Budget Analysis

```json
{
  "id": "user-001",
  "name_en": "My Budget Analysis",
  "name_fr": "Mon Analyse Budgétaire",
  "description_en": "Custom dashboard for detailed budget review",
  "description_fr": "Tableau de bord personnalisé pour l'analyse budgétaire",
  "dashboard_role": null,
  "owner_user_id": "550e8400-e29b-41d4-a716-446655440000",
  "is_default": false,
  "layout_config": {
    "columns": 12,
    "row_height": 80
  }
}
```

### Sample Widget Configurations

#### KPI Card Widget

```json
{
  "id": "widget-001",
  "dashboard_id": "exec-001",
  "widget_type": "kpi_card",
  "title_en": "Total Enrollment",
  "title_fr": "Effectif Total",
  "position_x": 0,
  "position_y": 0,
  "width": 3,
  "height": 2,
  "widget_config": {
    "kpi_definition_code": "total_enrollment",
    "show_trend": true,
    "trend_period": "YoY",
    "color_scheme": "blue",
    "icon": "users",
    "comparison": {
      "enabled": true,
      "compare_to": "previous_version",
      "show_percentage": true
    }
  }
}
```

#### Chart Widget

```json
{
  "id": "widget-002",
  "dashboard_id": "exec-001",
  "widget_type": "chart",
  "title_en": "Revenue Breakdown by Category",
  "title_fr": "Répartition des Recettes par Catégorie",
  "position_x": 3,
  "position_y": 0,
  "width": 6,
  "height": 4,
  "widget_config": {
    "chart_type": "pie",
    "data_source": "revenue_plans",
    "group_by": "category",
    "aggregate": "sum",
    "field": "amount_sar",
    "filters": {
      "version_id": "current"
    },
    "colors": ["#0088FE", "#00C49F", "#FFBB28", "#FF8042"],
    "show_legend": true,
    "show_labels": true,
    "format": {
      "number": "fr-FR",
      "currency": "SAR"
    }
  }
}
```

#### Variance Table Widget

```json
{
  "id": "widget-003",
  "dashboard_id": "finance-001",
  "widget_type": "variance_table",
  "title_en": "Budget vs Actual Variance",
  "title_fr": "Écart Budget vs Réel",
  "position_x": 0,
  "position_y": 2,
  "width": 12,
  "height": 5,
  "widget_config": {
    "data_source": "budget_vs_actual",
    "columns": [
      "account_code",
      "account_name",
      "budget_amount_sar",
      "actual_amount_sar",
      "variance_sar",
      "variance_percent"
    ],
    "filters": {
      "version_id": "current",
      "period": "YTD"
    },
    "conditional_formatting": {
      "variance_status": {
        "favorable": "#00C49F",
        "unfavorable": "#FF8042",
        "neutral": "#808080"
      }
    },
    "sorting": {
      "column": "variance_sar",
      "direction": "desc"
    },
    "pagination": {
      "page_size": 20
    }
  }
}
```

#### Gauge Widget

```json
{
  "id": "widget-004",
  "dashboard_id": "exec-001",
  "widget_type": "gauge",
  "title_en": "Capacity Utilization",
  "title_fr": "Taux d'Occupation",
  "position_x": 9,
  "position_y": 0,
  "width": 3,
  "height": 2,
  "widget_config": {
    "kpi_definition_code": "capacity_utilization",
    "min_value": 0,
    "max_value": 100,
    "target_value": 90,
    "ranges": [
      {"min": 0, "max": 60, "color": "#FF8042", "label": "Low"},
      {"min": 60, "max": 80, "color": "#FFBB28", "label": "Medium"},
      {"min": 80, "max": 90, "color": "#00C49F", "label": "Good"},
      {"min": 90, "max": 100, "color": "#0088FE", "label": "Excellent"}
    ],
    "show_percentage": true,
    "needle_color": "#333"
  }
}
```

### Sample User Preferences

```json
{
  "id": "pref-001",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "default_dashboard_id": "exec-001",
  "theme": "light",
  "language": "fr",
  "date_format": "DD/MM/YYYY",
  "number_format": "fr-FR",
  "currency_display": "SAR",
  "notification_settings": {
    "email_enabled": true,
    "browser_enabled": true,
    "budget_approval": true,
    "variance_alerts": true,
    "variance_threshold_percent": 10,
    "kpi_alerts": true,
    "kpi_out_of_range": true
  },
  "display_preferences": {
    "compact_mode": false,
    "show_tooltips": true,
    "animation_enabled": true,
    "grid_density": "comfortable",
    "sidebar_collapsed": false,
    "default_view": "dashboard"
  }
}
```

## Business Rules

### Dashboard Configuration Rules

1. **XOR Constraint**: Dashboard must be either a system template (dashboard_role set) OR user-owned (owner_user_id set), not both
2. **Bilingual Names**: All dashboards must have both English and French names
3. **Default Dashboard**: Only one dashboard per user can be marked as default
4. **System Template Access**: All authenticated users can read system templates
5. **User Dashboard Privacy**: User dashboards are private and visible only to owner and admins
6. **Soft Delete**: Deleted dashboards are soft-deleted (deleted_at set) for audit compliance

### Dashboard Widget Rules

1. **Grid Constraints**:
   - position_x: 0-11 (12-column grid)
   - width: 1-12
   - position_x + width ≤ 12 (no horizontal overflow)
   - height: 1-10
2. **No Overlap**: Widgets cannot overlap (enforced by application logic during save)
3. **Parent Access**: Widget access inherits from parent dashboard access control
4. **Bilingual Titles**: All widgets must have both English and French titles
5. **Widget Config Validation**: Each widget type has a specific config schema (validated by application)
6. **Cascade Delete**: If dashboard is deleted, all widgets are cascade deleted

### User Preferences Rules

1. **One Per User**: Each user has exactly one preferences record (unique user_id)
2. **Default Dashboard Validation**: If set, user must have access to the specified dashboard
3. **Theme Options**: light, dark, auto (system preference)
4. **Language Options**: en (English), fr (French)
5. **Number Format**: Must be valid locale identifier (e.g., fr-FR, en-US)
6. **Notification Settings**: JSONB allows flexible addition of new notification types
7. **Auto-Create**: User preferences created automatically on first login with defaults

## 12×12 Grid Layout System

### Grid Specifications

- **Total Columns**: 12
- **Row Height**: Configurable per dashboard (default: 80px)
- **Gutter Width**: 16px between widgets
- **Responsive Breakpoints**:
  - lg (large): ≥1200px → 12 columns
  - md (medium): ≥996px → 10 columns
  - sm (small): ≥768px → 6 columns
  - xs (extra small): ≥480px → 4 columns

### Widget Sizing Examples

| Widget Size | Columns | Example Use Case |
|-------------|---------|------------------|
| Small | 3 (25%) | KPI card, gauge |
| Medium | 6 (50%) | Chart, table |
| Large | 9 (75%) | Detailed table, multi-series chart |
| Full Width | 12 (100%) | Variance table, timeline |

### Layout Example: Executive Dashboard

```
+---+---+---+---+---+---+---+---+---+---+---+---+
| Enrollment| Revenue   | Surplus   | Capacity  | <- Row 0-1 (4x KPI cards)
| KPI (3)   | KPI (3)   | KPI (3)   | Gauge (3) |
+---+---+---+---+---+---+---+---+---+---+---+---+
| Revenue Breakdown Chart (6)   | Cost Breakdown| <- Row 2-5 (2x charts)
|                               | Chart (6)     |
+---+---+---+---+---+---+---+---+---+---+---+---+
| Enrollment Trend Line Chart (12)             | <- Row 6-9 (full-width chart)
|                                               |
+---+---+---+---+---+---+---+---+---+---+---+---+
```

## Integration Points

### Upstream Dependencies

1. **auth.users**: User ownership and preferences
2. **kpi_values**: Data source for KPI widgets
3. **budget_vs_actual**: Data source for variance widgets
4. **revenue_plans, personnel_cost_plans, etc.**: Data sources for charts/tables

### Downstream Dependencies

1. **Frontend Dashboard Renderer**: Reads dashboard configs and renders widgets
2. **Real-time Updates**: Supabase Realtime subscriptions for live data updates
3. **Export System**: Export dashboard views to PDF/PNG for reports

### External Systems

- **Export to PDF**: Dashboard snapshots for executive reports
- **Email Digests**: Send dashboard summaries via email (notification settings)

## API Endpoints (Future Implementation)

### Planned Endpoints (Phase 5-6)

```
# Dashboard Configs
GET    /api/v1/dashboards                      # List dashboards (system + own)
GET    /api/v1/dashboards/templates            # List system templates
GET    /api/v1/dashboards/:id                  # Get dashboard by ID
POST   /api/v1/dashboards                      # Create user dashboard
PUT    /api/v1/dashboards/:id                  # Update dashboard
DELETE /api/v1/dashboards/:id                  # Soft delete dashboard
POST   /api/v1/dashboards/:id/clone            # Clone dashboard (system template → user dashboard)
POST   /api/v1/dashboards/:id/set-default      # Set as default dashboard

# Dashboard Widgets
GET    /api/v1/dashboards/:id/widgets          # List widgets in dashboard
POST   /api/v1/dashboards/:id/widgets          # Add widget to dashboard
PUT    /api/v1/widgets/:id                     # Update widget
DELETE /api/v1/widgets/:id                     # Delete widget
PUT    /api/v1/dashboards/:id/layout           # Update widget layout (bulk)

# User Preferences
GET    /api/v1/users/preferences                # Get current user preferences
PUT    /api/v1/users/preferences                # Update user preferences
POST   /api/v1/users/preferences/reset          # Reset to defaults
```

## Testing Strategy

### Unit Tests

1. **Model Tests**: Verify SQLAlchemy model definitions and relationships
2. **Constraint Tests**: Test XOR constraint on dashboard_configs, grid constraints on widgets
3. **Enum Tests**: Verify DashboardRole and WidgetType enum values

### Integration Tests

1. **RLS Policy Tests**: Verify row-level security for all user roles
2. **Cascade Delete Tests**: Ensure widgets are deleted when dashboard is deleted
3. **Soft Delete Tests**: Verify soft delete functionality
4. **Grid Layout Tests**: Validate widget positioning and overlap detection

### Test Scenarios

#### Scenario 1: Create System Template Dashboard

```python
def test_create_system_template():
    """Test creating a system template dashboard."""
    dashboard = DashboardConfig(
        name_en="Executive Dashboard",
        name_fr="Tableau de Bord Exécutif",
        dashboard_role=DashboardRole.EXECUTIVE,
        owner_user_id=None,  # System template
        is_default=True,
        layout_config={"columns": 12, "row_height": 80}
    )
    db.session.add(dashboard)
    db.session.commit()

    assert dashboard.id is not None
    assert dashboard.dashboard_role == DashboardRole.EXECUTIVE
    assert dashboard.owner_user_id is None
```

#### Scenario 2: Create User Dashboard

```python
def test_create_user_dashboard():
    """Test creating a user-owned dashboard."""
    user = create_test_user()

    dashboard = DashboardConfig(
        name_en="My Custom Dashboard",
        name_fr="Mon Tableau de Bord",
        dashboard_role=None,  # User dashboard
        owner_user_id=user.id,
        is_default=False,
        layout_config={"columns": 12, "row_height": 80}
    )
    db.session.add(dashboard)
    db.session.commit()

    assert dashboard.id is not None
    assert dashboard.owner_user_id == user.id
    assert dashboard.dashboard_role is None
```

#### Scenario 3: XOR Constraint Violation

```python
def test_xor_constraint_violation():
    """Test that dashboard cannot have both role and owner."""
    user = create_test_user()

    # Attempt to create dashboard with both role and owner
    dashboard = DashboardConfig(
        name_en="Invalid Dashboard",
        name_fr="Tableau Invalide",
        dashboard_role=DashboardRole.EXECUTIVE,  # Both set
        owner_user_id=user.id,                   # Both set
        layout_config={}
    )
    db.session.add(dashboard)

    with pytest.raises(CheckConstraintError):
        db.session.commit()
```

#### Scenario 4: Widget Grid Validation

```python
def test_widget_grid_overflow():
    """Test that widget cannot overflow 12-column grid."""
    dashboard = create_test_dashboard()

    # Widget at position 10 with width 4 = overflow (10 + 4 > 12)
    widget = DashboardWidget(
        dashboard_id=dashboard.id,
        widget_type=WidgetType.KPI_CARD,
        title_en="Test Widget",
        title_fr="Widget Test",
        position_x=10,
        width=4,  # Would overflow
        height=2,
        widget_config={}
    )
    db.session.add(widget)

    with pytest.raises(CheckConstraintError):
        db.session.commit()
```

#### Scenario 5: RLS - User Can Access Own Dashboard

```python
def test_rls_user_dashboard_access():
    """Test that user can access their own dashboard."""
    user = create_test_user()
    dashboard = create_user_dashboard(owner_user_id=user.id)

    # Simulate user login
    set_current_user(user.id)

    # User can read own dashboard
    result = db.session.query(DashboardConfig).filter_by(id=dashboard.id).first()
    assert result is not None

    # User can update own dashboard
    result.name_en = "Updated Name"
    db.session.commit()

    refreshed = db.session.query(DashboardConfig).filter_by(id=dashboard.id).first()
    assert refreshed.name_en == "Updated Name"
```

#### Scenario 6: RLS - User Cannot Access Other User Dashboard

```python
def test_rls_cannot_access_other_dashboard():
    """Test that user cannot access another user's dashboard."""
    user1 = create_test_user("user1@efir.sa")
    user2 = create_test_user("user2@efir.sa")

    dashboard_user1 = create_user_dashboard(owner_user_id=user1.id)

    # Simulate user2 login
    set_current_user(user2.id)

    # User2 cannot see user1's dashboard
    result = db.session.query(DashboardConfig).filter_by(id=dashboard_user1.id).first()
    assert result is None
```

#### Scenario 7: User Preferences Auto-Create

```python
def test_user_preferences_auto_create():
    """Test that user preferences are auto-created on first access."""
    user = create_test_user()

    # Check no preferences exist
    prefs = db.session.query(UserPreferences).filter_by(user_id=user.id).first()
    assert prefs is None

    # Auto-create with defaults
    prefs = UserPreferences(
        user_id=user.id,
        theme="light",
        language="fr",
        notification_settings={},
        display_preferences={}
    )
    db.session.add(prefs)
    db.session.commit()

    # Verify defaults
    assert prefs.theme == "light"
    assert prefs.language == "fr"
    assert prefs.date_format == "DD/MM/YYYY"
```

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-01 | Claude (Phase 4) | Initial database schema implementation: dashboard_configs, dashboard_widgets, user_preferences tables, RLS policies, migration scripts |

## Future Enhancements (Phase 5-6)

1. **Dashboard Builder UI**: Drag-and-drop interface for creating/editing dashboards
2. **Widget Library**: Pre-built widget templates for common use cases
3. **Real-time Updates**: Supabase Realtime subscriptions for live data refresh
4. **Responsive Layouts**: Automatic layout adjustment for mobile/tablet
5. **Dashboard Sharing**: Share dashboards with specific users or teams
6. **Export to PDF/PNG**: Export dashboard snapshots for reports
7. **Dashboard Versioning**: Save dashboard versions for rollback
8. **Collaborative Editing**: Multiple users editing dashboards simultaneously
9. **Widget Marketplace**: Share widget configurations across users
10. **AI-Powered Suggestions**: Suggest widgets based on user role and data

## Notes

- **Phase 4 Scope**: This module currently implements only the database foundation (tables, constraints, RLS policies, migration)
- **Business Logic**: Dashboard rendering, widget data fetching, and UI will be implemented in Phases 5-6
- **12×12 Grid**: Standard responsive grid system (like Bootstrap) for familiar UX
- **JSONB Flexibility**: widget_config and user preferences use JSONB to allow future additions without migrations
- **Bilingual Support**: All dashboard and widget titles support both English and French
- **Ownership Model**: Clear distinction between system templates (public) and user dashboards (private)
