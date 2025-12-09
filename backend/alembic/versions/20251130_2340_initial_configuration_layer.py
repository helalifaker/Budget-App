"""Initial Configuration Layer migration (Modules 1-6)

Revision ID: 001_initial_config
Revises:
Create Date: 2025-11-30 23:40:00.000000

Creates efir_budget schema and all Configuration Layer tables:
- Module 1: System Configuration (system_configs, budget_versions)
- Module 2: Class Size Parameters (academic_cycles, academic_levels, class_size_params)
- Module 3: Subject Hours (subjects, subject_hours_matrix)
- Module 4: Teacher Costs (teacher_categories, teacher_cost_params)
- Module 5: Fee Structure (fee_categories, nationality_types, fee_structure)
- Module 6: Timetable Constraints (timetable_constraints)
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial_config'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create efir_budget schema and Configuration Layer tables."""

    # Create efir_budget schema
    op.execute('CREATE SCHEMA IF NOT EXISTS efir_budget')

    # Create BudgetVersionStatus enum
    # Note: create_type=False prevents auto-creation when used in Column,
    # so we explicitly call .create() below
    budget_version_status = postgresql.ENUM(
        'working', 'submitted', 'approved', 'forecast', 'superseded',
        name='budgetversionstatus',
        schema='efir_budget',
        create_type=False  # Prevent auto-creation when used in Column
    )
    budget_version_status.create(op.get_bind(), checkfirst=True)  # checkfirst to avoid duplicate error

    # =========================================================================
    # Module 1: System Configuration
    # =========================================================================

    # system_configs table
    op.create_table(
        'system_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('key', sa.String(100), nullable=False, unique=True, index=True,
                  comment='Configuration key (unique identifier)'),
        sa.Column('value', postgresql.JSONB(), nullable=False,
                  comment='Configuration value (flexible JSONB structure)'),
        sa.Column('category', sa.String(50), nullable=False, index=True,
                  comment='Configuration category (currency, locale, academic, etc.)'),
        sa.Column('description', sa.Text(), nullable=False,
                  comment='Human-readable description of configuration'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true',
                  comment='Whether configuration is active'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()'), comment='When the record was created'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()'), comment='When the record was last updated'),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('auth.users.id', ondelete='RESTRICT'), nullable=False,
                  comment='User who created the record'),
        sa.Column('updated_by_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('auth.users.id', ondelete='RESTRICT'), nullable=False,
                  comment='User who last updated the record'),
        schema='efir_budget',
        comment='Global system configuration parameters'
    )

    # budget_versions table
    op.create_table(
        'budget_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False,
                  comment="Version name (e.g., 'Budget 2025-2026')"),
        sa.Column('fiscal_year', sa.Integer(), nullable=False, index=True,
                  comment='Fiscal year (e.g., 2026 for 2025-2026)'),
        sa.Column('academic_year', sa.String(20), nullable=False,
                  comment="Academic year (e.g., '2025-2026')"),
        sa.Column('status', budget_version_status,  # Use the already-created enum object
                  nullable=False, server_default='working', index=True,
                  comment='Version status'),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True,
                  comment='When version was submitted for approval'),
        sa.Column('submitted_by_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('auth.users.id'), nullable=True,
                  comment='User who submitted version'),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True,
                  comment='When version was approved'),
        sa.Column('approved_by_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('auth.users.id'), nullable=True,
                  comment='User who approved version'),
        sa.Column('notes', sa.Text(), nullable=True,
                  comment='Version notes and comments'),
        sa.Column('is_baseline', sa.Boolean(), nullable=False, server_default='false',
                  comment='Whether this is the baseline version for comparison'),
        sa.Column('parent_version_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('efir_budget.budget_versions.id'), nullable=True,
                  comment='Parent version (for forecast revisions)'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('auth.users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('updated_by_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('auth.users.id', ondelete='SET NULL'), nullable=True),
        schema='efir_budget',
        comment='Budget version control'
    )

    # =========================================================================
    # Module 2: Class Size Parameters
    # =========================================================================

    # academic_cycles table
    op.create_table(
        'academic_cycles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('code', sa.String(20), nullable=False, unique=True, index=True,
                  comment='Cycle code (MAT, ELEM, COLL, LYC)'),
        sa.Column('name_fr', sa.String(100), nullable=False,
                  comment="French name (e.g., 'Maternelle')"),
        sa.Column('name_en', sa.String(100), nullable=False,
                  comment="English name (e.g., 'Preschool')"),
        sa.Column('sort_order', sa.Integer(), nullable=False,
                  comment='Display order (1=MAT, 2=ELEM, 3=COLL, 4=LYC)'),
        sa.Column('requires_atsem', sa.Boolean(), nullable=False, server_default='false',
                  comment='Whether ATSEM (classroom assistant) is required'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        schema='efir_budget',
        comment='Academic cycle definitions (Maternelle, Élémentaire, Collège, Lycée)'
    )

    # academic_levels table
    op.create_table(
        'academic_levels',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('cycle_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('efir_budget.academic_cycles.id'), nullable=False, index=True,
                  comment='Parent academic cycle'),
        sa.Column('code', sa.String(20), nullable=False, unique=True, index=True,
                  comment='Level code (PS, MS, GS, CP, CE1, etc.)'),
        sa.Column('name_fr', sa.String(100), nullable=False,
                  comment="French name (e.g., 'Petite Section')"),
        sa.Column('name_en', sa.String(100), nullable=False,
                  comment="English name (e.g., 'Preschool - Small Section')"),
        sa.Column('sort_order', sa.Integer(), nullable=False,
                  comment='Display order within cycle'),
        sa.Column('is_secondary', sa.Boolean(), nullable=False, server_default='false',
                  comment='Whether this is secondary level (DHG applicable)'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        schema='efir_budget',
        comment='Academic level definitions (PS, MS, GS, CP... Terminale)'
    )

    # class_size_params table
    op.create_table(
        'class_size_params',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('budget_version_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('efir_budget.budget_versions.id', ondelete='CASCADE'),
                  nullable=False, index=True, comment='Budget version this record belongs to'),
        sa.Column('level_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('efir_budget.academic_levels.id'), nullable=True, index=True,
                  comment='Specific academic level (NULL for cycle default)'),
        sa.Column('cycle_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('efir_budget.academic_cycles.id'), nullable=True, index=True,
                  comment='Academic cycle (NULL if level-specific)'),
        sa.Column('min_class_size', sa.Integer(), nullable=False,
                  comment='Minimum viable class size'),
        sa.Column('target_class_size', sa.Integer(), nullable=False,
                  comment='Target/optimal class size'),
        sa.Column('max_class_size', sa.Integer(), nullable=False,
                  comment='Maximum allowed class size'),
        sa.Column('notes', sa.Text(), nullable=True, comment='Parameter notes'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('auth.users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('updated_by_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('auth.users.id', ondelete='SET NULL'), nullable=True),
        sa.CheckConstraint(
            '(level_id IS NOT NULL AND cycle_id IS NULL) OR '
            '(level_id IS NULL AND cycle_id IS NOT NULL)',
            name='ck_class_size_params_level_or_cycle'
        ),
        sa.CheckConstraint(
            'min_class_size < target_class_size AND '
            'target_class_size <= max_class_size',
            name='ck_class_size_params_valid_range'
        ),
        schema='efir_budget',
        comment='Class size parameters per level and version'
    )

    # =========================================================================
    # Module 3: Subject Hours Configuration
    # =========================================================================

    # subjects table
    op.create_table(
        'subjects',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('code', sa.String(20), nullable=False, unique=True, index=True,
                  comment='Subject code (MATH, FRAN, ANGL, etc.)'),
        sa.Column('name_fr', sa.String(100), nullable=False,
                  comment="French name (e.g., 'Mathématiques')"),
        sa.Column('name_en', sa.String(100), nullable=False,
                  comment="English name (e.g., 'Mathematics')"),
        sa.Column('category', sa.String(50), nullable=False,
                  comment='Subject category (core, specialty, elective)'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true',
                  comment='Whether subject is currently active'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        schema='efir_budget',
        comment='Subject catalog for DHG calculations'
    )

    # subject_hours_matrix table
    op.create_table(
        'subject_hours_matrix',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('budget_version_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('efir_budget.budget_versions.id', ondelete='CASCADE'),
                  nullable=False, index=True),
        sa.Column('subject_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('efir_budget.subjects.id'), nullable=False, index=True,
                  comment='Subject being taught'),
        sa.Column('level_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('efir_budget.academic_levels.id'), nullable=False, index=True,
                  comment='Academic level'),
        sa.Column('hours_per_week', sa.Numeric(4, 2), nullable=False,
                  comment='Hours per week per class'),
        sa.Column('is_split', sa.Boolean(), nullable=False, server_default='false',
                  comment='Whether classes are split (half-size groups, counts as double hours)'),
        sa.Column('notes', sa.Text(), nullable=True, comment='Configuration notes'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('auth.users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('updated_by_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('auth.users.id', ondelete='SET NULL'), nullable=True),
        sa.UniqueConstraint('budget_version_id', 'subject_id', 'level_id',
                            name='uk_subject_hours_version_subject_level'),
        sa.CheckConstraint('hours_per_week > 0 AND hours_per_week <= 12',
                           name='ck_subject_hours_realistic_range'),
        schema='efir_budget',
        comment='Subject hours per level configuration (DHG matrix)'
    )

    # =========================================================================
    # Module 4: Teacher Costs Configuration
    # =========================================================================

    # teacher_categories table
    op.create_table(
        'teacher_categories',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('code', sa.String(20), nullable=False, unique=True, index=True,
                  comment='Category code'),
        sa.Column('name_fr', sa.String(100), nullable=False, comment='French name'),
        sa.Column('name_en', sa.String(100), nullable=False, comment='English name'),
        sa.Column('description', sa.Text(), nullable=True, comment='Category description'),
        sa.Column('is_aefe', sa.Boolean(), nullable=False, server_default='false',
                  comment='Whether AEFE-affiliated'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        schema='efir_budget',
        comment='Teacher employment categories (AEFE_DETACHED, AEFE_FUNDED, LOCAL)'
    )

    # teacher_cost_params table
    op.create_table(
        'teacher_cost_params',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('budget_version_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('efir_budget.budget_versions.id', ondelete='CASCADE'),
                  nullable=False, index=True),
        sa.Column('category_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('efir_budget.teacher_categories.id'), nullable=False, index=True,
                  comment='Teacher category'),
        sa.Column('cycle_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('efir_budget.academic_cycles.id'), nullable=True, index=True,
                  comment='Academic cycle (NULL for all cycles)'),
        sa.Column('prrd_contribution_eur', sa.Numeric(10, 2), nullable=True,
                  comment='PRRD contribution per teacher (EUR, for AEFE detached)'),
        sa.Column('avg_salary_sar', sa.Numeric(10, 2), nullable=True,
                  comment='Average salary for local teachers (SAR/year)'),
        sa.Column('social_charges_rate', sa.Numeric(5, 4), nullable=False,
                  server_default='0.21', comment='Social charges rate (e.g., 0.21 for 21%)'),
        sa.Column('benefits_allowance_sar', sa.Numeric(10, 2), nullable=False,
                  server_default='0.00', comment='Benefits/allowances per teacher (SAR/year)'),
        sa.Column('hsa_hourly_rate_sar', sa.Numeric(8, 2), nullable=False,
                  comment='HSA (overtime) hourly rate (SAR)'),
        sa.Column('max_hsa_hours', sa.Numeric(4, 2), nullable=False,
                  server_default='4.00', comment='Maximum HSA hours per teacher per week'),
        sa.Column('notes', sa.Text(), nullable=True, comment='Parameter notes'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('auth.users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('updated_by_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('auth.users.id', ondelete='SET NULL'), nullable=True),
        schema='efir_budget',
        comment='Teacher cost parameters per category and version'
    )

    # =========================================================================
    # Module 5: Fee Structure Configuration
    # =========================================================================

    # fee_categories table
    op.create_table(
        'fee_categories',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('code', sa.String(20), nullable=False, unique=True, index=True,
                  comment='Category code'),
        sa.Column('name_fr', sa.String(100), nullable=False, comment='French name'),
        sa.Column('name_en', sa.String(100), nullable=False, comment='English name'),
        sa.Column('account_code', sa.String(20), nullable=False,
                  comment='PCG account code (70xxx revenue)'),
        sa.Column('is_recurring', sa.Boolean(), nullable=False, server_default='true',
                  comment='Whether charged annually'),
        sa.Column('allows_sibling_discount', sa.Boolean(), nullable=False, server_default='false',
                  comment='Whether sibling discount applies (tuition only)'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        schema='efir_budget',
        comment='Fee category definitions (TUITION, DAI, REGISTRATION, etc.)'
    )

    # nationality_types table
    op.create_table(
        'nationality_types',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('code', sa.String(20), nullable=False, unique=True, index=True,
                  comment='Nationality code'),
        sa.Column('name_fr', sa.String(100), nullable=False, comment='French name'),
        sa.Column('name_en', sa.String(100), nullable=False, comment='English name'),
        sa.Column('vat_applicable', sa.Boolean(), nullable=False, server_default='true',
                  comment='Whether VAT applies (Saudi: no, Others: yes)'),
        sa.Column('sort_order', sa.Integer(), nullable=False, comment='Display order'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        schema='efir_budget',
        comment='Nationality-based fee tier definitions (FRENCH, SAUDI, OTHER)'
    )

    # fee_structure table
    op.create_table(
        'fee_structure',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('budget_version_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('efir_budget.budget_versions.id', ondelete='CASCADE'),
                  nullable=False, index=True),
        sa.Column('level_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('efir_budget.academic_levels.id'), nullable=False, index=True,
                  comment='Academic level'),
        sa.Column('nationality_type_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('efir_budget.nationality_types.id'), nullable=False, index=True,
                  comment='Nationality type (French, Saudi, Other)'),
        sa.Column('fee_category_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('efir_budget.fee_categories.id'), nullable=False, index=True,
                  comment='Fee category (tuition, DAI, etc.)'),
        sa.Column('amount_sar', sa.Numeric(10, 2), nullable=False, comment='Fee amount in SAR'),
        sa.Column('trimester', sa.Integer(), nullable=True,
                  comment='Trimester (1-3) for tuition, NULL for annual fees'),
        sa.Column('notes', sa.Text(), nullable=True, comment='Fee notes'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('auth.users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('updated_by_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('auth.users.id', ondelete='SET NULL'), nullable=True),
        sa.UniqueConstraint('budget_version_id', 'level_id', 'nationality_type_id',
                            'fee_category_id', 'trimester',
                            name='uk_fee_structure_version_level_nat_cat_trim'),
        schema='efir_budget',
        comment='Fee amounts per level, nationality, and category'
    )

    # =========================================================================
    # Module 6: Timetable Constraints
    # =========================================================================

    # timetable_constraints table
    op.create_table(
        'timetable_constraints',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('budget_version_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('efir_budget.budget_versions.id', ondelete='CASCADE'),
                  nullable=False, index=True),
        sa.Column('level_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('efir_budget.academic_levels.id'), nullable=False, index=True,
                  comment='Academic level'),
        sa.Column('total_hours_per_week', sa.Numeric(5, 2), nullable=False,
                  comment='Total student hours per week'),
        sa.Column('max_hours_per_day', sa.Numeric(4, 2), nullable=False,
                  comment='Maximum hours per day'),
        sa.Column('days_per_week', sa.Integer(), nullable=False, server_default='5',
                  comment='School days per week (typically 5)'),
        sa.Column('requires_lunch_break', sa.Boolean(), nullable=False, server_default='true',
                  comment='Whether lunch break is required'),
        sa.Column('min_break_duration_minutes', sa.Integer(), nullable=False, server_default='60',
                  comment='Minimum break duration (minutes)'),
        sa.Column('notes', sa.Text(), nullable=True, comment='Constraint notes'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('auth.users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('updated_by_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('auth.users.id', ondelete='SET NULL'), nullable=True),
        sa.UniqueConstraint('budget_version_id', 'level_id',
                            name='uk_timetable_constraint_version_level'),
        schema='efir_budget',
        comment='Timetable scheduling constraints per level'
    )

    # =========================================================================
    # Triggers for updated_at timestamp
    # =========================================================================

    op.execute("""
        CREATE OR REPLACE FUNCTION efir_budget.update_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Apply trigger to all tables with updated_at
    tables_with_updated_at = [
        'system_configs', 'budget_versions', 'academic_cycles', 'academic_levels',
        'class_size_params', 'subjects', 'subject_hours_matrix', 'teacher_categories',
        'teacher_cost_params', 'fee_categories', 'nationality_types', 'fee_structure',
        'timetable_constraints'
    ]

    for table in tables_with_updated_at:
        op.execute(f"""
            CREATE TRIGGER set_updated_at
            BEFORE UPDATE ON efir_budget.{table}
            FOR EACH ROW
            EXECUTE FUNCTION efir_budget.update_updated_at();
        """)


def downgrade() -> None:
    """Drop all Configuration Layer tables and schema."""

    # Drop tables in reverse order (respecting foreign key dependencies)
    op.drop_table('timetable_constraints', schema='efir_budget')
    op.drop_table('fee_structure', schema='efir_budget')
    op.drop_table('nationality_types', schema='efir_budget')
    op.drop_table('fee_categories', schema='efir_budget')
    op.drop_table('teacher_cost_params', schema='efir_budget')
    op.drop_table('teacher_categories', schema='efir_budget')
    op.drop_table('subject_hours_matrix', schema='efir_budget')
    op.drop_table('subjects', schema='efir_budget')
    op.drop_table('class_size_params', schema='efir_budget')
    op.drop_table('academic_levels', schema='efir_budget')
    op.drop_table('academic_cycles', schema='efir_budget')
    op.drop_table('budget_versions', schema='efir_budget')
    op.drop_table('system_configs', schema='efir_budget')

    # Drop function
    op.execute('DROP FUNCTION IF EXISTS efir_budget.update_updated_at()')

    # Drop enum
    op.execute('DROP TYPE IF EXISTS efir_budget.budgetversionstatus')

    # Drop schema (only if empty)
    op.execute('DROP SCHEMA IF EXISTS efir_budget CASCADE')
