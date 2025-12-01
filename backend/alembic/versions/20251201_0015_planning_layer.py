"""Planning Layer migration (Modules 7-12)

Revision ID: 002_planning_layer
Revises: 001_initial_config
Create Date: 2025-12-01 00:15:00.000000

Creates Planning Layer tables:
- Module 7: Enrollment Planning (enrollment_plans)
- Module 8: Class Structure Planning (class_structures)
- Module 9: DHG Workforce Planning (dhg_subject_hours, dhg_teacher_requirements, teacher_allocations)
- Module 10: Revenue Planning (revenue_plans)
- Module 11: Cost Planning (personnel_cost_plans, operating_cost_plans)
- Module 12: CapEx Planning (capex_plans)
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_planning_layer'
down_revision = '001_initial_config'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create Planning Layer tables."""

    # =========================================================================
    # Module 7: Enrollment Planning
    # =========================================================================

    op.create_table(
        'enrollment_plans',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('budget_version_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('efir_budget.budget_versions.id', ondelete='CASCADE'),
                  nullable=False, index=True,
                  comment='Budget version this record belongs to'),
        sa.Column('level_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('efir_budget.academic_levels.id'), nullable=False, index=True,
                  comment='Academic level'),
        sa.Column('nationality_type_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('efir_budget.nationality_types.id'), nullable=False, index=True,
                  comment='Nationality type (French, Saudi, Other)'),
        sa.Column('student_count', sa.Integer(), nullable=False,
                  comment='Projected number of students'),
        sa.Column('notes', sa.Text(), nullable=True,
                  comment='Enrollment notes and assumptions'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('auth.users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('updated_by_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('auth.users.id', ondelete='SET NULL'), nullable=True),
        sa.UniqueConstraint('budget_version_id', 'level_id', 'nationality_type_id',
                            name='uk_enrollment_version_level_nat'),
        sa.CheckConstraint('student_count >= 0', name='ck_enrollment_non_negative'),
        schema='efir_budget',
        comment='Enrollment projections per level, nationality, and version'
    )

    # =========================================================================
    # Module 8: Class Structure Planning
    # =========================================================================

    op.create_table(
        'class_structures',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('budget_version_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('efir_budget.budget_versions.id', ondelete='CASCADE'),
                  nullable=False, index=True),
        sa.Column('level_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('efir_budget.academic_levels.id'), nullable=False, index=True,
                  comment='Academic level'),
        sa.Column('total_students', sa.Integer(), nullable=False,
                  comment='Total students at this level (sum of enrollment)'),
        sa.Column('number_of_classes', sa.Integer(), nullable=False,
                  comment='Number of classes formed'),
        sa.Column('avg_class_size', sa.Numeric(5, 2), nullable=False,
                  comment='Average class size (total_students / number_of_classes)'),
        sa.Column('requires_atsem', sa.Boolean(), nullable=False, server_default='false',
                  comment='Whether ATSEM (classroom assistant) is required'),
        sa.Column('atsem_count', sa.Integer(), nullable=False, server_default='0',
                  comment='Number of ATSEM needed (typically 1 per Maternelle class)'),
        sa.Column('calculation_method', sa.String(50), nullable=False, server_default='target',
                  comment='Method used (target, min, max, custom)'),
        sa.Column('notes', sa.Text(), nullable=True, comment='Class formation notes'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('auth.users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('updated_by_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('auth.users.id', ondelete='SET NULL'), nullable=True),
        sa.UniqueConstraint('budget_version_id', 'level_id',
                            name='uk_class_structure_version_level'),
        sa.CheckConstraint('total_students >= 0',
                           name='ck_class_structure_students_non_negative'),
        sa.CheckConstraint('number_of_classes > 0',
                           name='ck_class_structure_classes_positive'),
        sa.CheckConstraint('avg_class_size > 0 AND avg_class_size <= 35',
                           name='ck_class_structure_avg_size_realistic'),
        schema='efir_budget',
        comment='Calculated class formations based on enrollment'
    )

    # =========================================================================
    # Module 9: DHG Workforce Planning
    # =========================================================================

    # dhg_subject_hours table
    op.create_table(
        'dhg_subject_hours',
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
        sa.Column('number_of_classes', sa.Integer(), nullable=False,
                  comment='Number of classes at this level (from class_structures)'),
        sa.Column('hours_per_class_per_week', sa.Numeric(4, 2), nullable=False,
                  comment='Hours per class per week (from subject_hours_matrix)'),
        sa.Column('total_hours_per_week', sa.Numeric(6, 2), nullable=False,
                  comment='Total hours per week (classes × hours, ×2 if split)'),
        sa.Column('is_split', sa.Boolean(), nullable=False, server_default='false',
                  comment='Whether classes are split (counts as double hours)'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('auth.users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('updated_by_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('auth.users.id', ondelete='SET NULL'), nullable=True),
        sa.UniqueConstraint('budget_version_id', 'subject_id', 'level_id',
                            name='uk_dhg_hours_version_subject_level'),
        sa.CheckConstraint('number_of_classes > 0',
                           name='ck_dhg_hours_classes_positive'),
        sa.CheckConstraint('hours_per_class_per_week > 0 AND hours_per_class_per_week <= 12',
                           name='ck_dhg_hours_realistic_range'),
        schema='efir_budget',
        comment='DHG hours calculation per subject and level'
    )

    # dhg_teacher_requirements table
    op.create_table(
        'dhg_teacher_requirements',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('budget_version_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('efir_budget.budget_versions.id', ondelete='CASCADE'),
                  nullable=False, index=True),
        sa.Column('subject_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('efir_budget.subjects.id'), nullable=False, index=True,
                  comment='Subject'),
        sa.Column('total_hours_per_week', sa.Numeric(6, 2), nullable=False,
                  comment='Sum of DHG hours for this subject across all levels'),
        sa.Column('standard_teaching_hours', sa.Numeric(4, 2), nullable=False,
                  comment='Standard teaching hours (18h secondary, 24h primary)'),
        sa.Column('simple_fte', sa.Numeric(5, 2), nullable=False,
                  comment='Exact FTE (total_hours / standard_hours)'),
        sa.Column('rounded_fte', sa.Integer(), nullable=False,
                  comment='Rounded up FTE (ceiling of simple_fte)'),
        sa.Column('hsa_hours', sa.Numeric(5, 2), nullable=False, server_default='0.00',
                  comment='Overtime hours needed (or negative if underutilized)'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('auth.users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('updated_by_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('auth.users.id', ondelete='SET NULL'), nullable=True),
        sa.UniqueConstraint('budget_version_id', 'subject_id',
                            name='uk_dhg_teacher_req_version_subject'),
        sa.CheckConstraint('total_hours_per_week >= 0',
                           name='ck_dhg_req_hours_non_negative'),
        sa.CheckConstraint('simple_fte >= 0',
                           name='ck_dhg_req_fte_non_negative'),
        schema='efir_budget',
        comment='Teacher FTE requirements per subject (DHG calculation result)'
    )

    # teacher_allocations table
    op.create_table(
        'teacher_allocations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('budget_version_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('efir_budget.budget_versions.id', ondelete='CASCADE'),
                  nullable=False, index=True),
        sa.Column('subject_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('efir_budget.subjects.id'), nullable=False, index=True,
                  comment='Subject'),
        sa.Column('cycle_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('efir_budget.academic_cycles.id'), nullable=False, index=True,
                  comment='Academic cycle (primary grouping for allocations)'),
        sa.Column('category_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('efir_budget.teacher_categories.id'), nullable=False, index=True,
                  comment='Teacher category (AEFE Detached, AEFE Funded, Local)'),
        sa.Column('fte_count', sa.Numeric(5, 2), nullable=False,
                  comment='Number of FTE allocated'),
        sa.Column('notes', sa.Text(), nullable=True,
                  comment='Allocation notes (teacher names, constraints, etc.)'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('auth.users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('updated_by_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('auth.users.id', ondelete='SET NULL'), nullable=True),
        sa.CheckConstraint('fte_count > 0', name='ck_allocation_fte_positive'),
        schema='efir_budget',
        comment='Actual teacher assignments (TRMD - Gap Analysis)'
    )

    # =========================================================================
    # Module 10: Revenue Planning
    # =========================================================================

    op.create_table(
        'revenue_plans',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('budget_version_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('efir_budget.budget_versions.id', ondelete='CASCADE'),
                  nullable=False, index=True),
        sa.Column('account_code', sa.String(20), nullable=False, index=True,
                  comment='PCG revenue account (70xxx-77xxx)'),
        sa.Column('description', sa.Text(), nullable=False,
                  comment='Line item description'),
        sa.Column('category', sa.String(50), nullable=False, index=True,
                  comment='Category (tuition, fees, other)'),
        sa.Column('amount_sar', sa.Numeric(12, 2), nullable=False,
                  comment='Revenue amount in SAR'),
        sa.Column('is_calculated', sa.Boolean(), nullable=False, server_default='false',
                  comment='Whether auto-calculated from drivers'),
        sa.Column('calculation_driver', sa.String(100), nullable=True,
                  comment="Driver reference (e.g., 'enrollment', 'fee_structure')"),
        sa.Column('trimester', sa.Integer(), nullable=True,
                  comment='Trimester (1-3) for tuition, NULL for annual'),
        sa.Column('notes', sa.Text(), nullable=True,
                  comment='Revenue notes and assumptions'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('auth.users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('updated_by_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('auth.users.id', ondelete='SET NULL'), nullable=True),
        sa.CheckConstraint('amount_sar >= 0', name='ck_revenue_non_negative'),
        schema='efir_budget',
        comment='Revenue projections by account code'
    )

    # =========================================================================
    # Module 11: Cost Planning
    # =========================================================================

    # personnel_cost_plans table
    op.create_table(
        'personnel_cost_plans',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('budget_version_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('efir_budget.budget_versions.id', ondelete='CASCADE'),
                  nullable=False, index=True),
        sa.Column('account_code', sa.String(20), nullable=False, index=True,
                  comment='PCG expense account (64xxx)'),
        sa.Column('description', sa.Text(), nullable=False,
                  comment='Cost description'),
        sa.Column('category_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('efir_budget.teacher_categories.id'), nullable=True, index=True,
                  comment='Teacher category (NULL for non-teaching staff)'),
        sa.Column('cycle_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('efir_budget.academic_cycles.id'), nullable=True, index=True,
                  comment='Academic cycle (NULL for admin/support)'),
        sa.Column('fte_count', sa.Numeric(5, 2), nullable=False,
                  comment='Number of FTE'),
        sa.Column('unit_cost_sar', sa.Numeric(10, 2), nullable=False,
                  comment='Cost per FTE (SAR/year)'),
        sa.Column('total_cost_sar', sa.Numeric(12, 2), nullable=False,
                  comment='Total cost (FTE × unit_cost)'),
        sa.Column('is_calculated', sa.Boolean(), nullable=False, server_default='false',
                  comment='Whether auto-calculated from drivers'),
        sa.Column('calculation_driver', sa.String(100), nullable=True,
                  comment="Driver (e.g., 'dhg_allocation', 'class_structure')"),
        sa.Column('notes', sa.Text(), nullable=True, comment='Cost notes'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('auth.users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('updated_by_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('auth.users.id', ondelete='SET NULL'), nullable=True),
        sa.CheckConstraint('fte_count >= 0', name='ck_personnel_fte_non_negative'),
        sa.CheckConstraint('unit_cost_sar >= 0 AND total_cost_sar >= 0',
                           name='ck_personnel_costs_non_negative'),
        schema='efir_budget',
        comment='Personnel cost projections (salaries, benefits, social charges)'
    )

    # operating_cost_plans table
    op.create_table(
        'operating_cost_plans',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('budget_version_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('efir_budget.budget_versions.id', ondelete='CASCADE'),
                  nullable=False, index=True),
        sa.Column('account_code', sa.String(20), nullable=False, index=True,
                  comment='PCG expense account (60xxx-68xxx)'),
        sa.Column('description', sa.Text(), nullable=False,
                  comment='Expense description'),
        sa.Column('category', sa.String(50), nullable=False, index=True,
                  comment='Category (supplies, utilities, maintenance, insurance, etc.)'),
        sa.Column('amount_sar', sa.Numeric(12, 2), nullable=False,
                  comment='Expense amount in SAR'),
        sa.Column('is_calculated', sa.Boolean(), nullable=False, server_default='false',
                  comment='Whether auto-calculated from driver'),
        sa.Column('calculation_driver', sa.String(100), nullable=True,
                  comment="Driver (e.g., 'enrollment', 'square_meters', 'fixed')"),
        sa.Column('notes', sa.Text(), nullable=True, comment='Expense notes'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('auth.users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('updated_by_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('auth.users.id', ondelete='SET NULL'), nullable=True),
        sa.CheckConstraint('amount_sar >= 0', name='ck_operating_cost_non_negative'),
        schema='efir_budget',
        comment='Operating expense projections (non-personnel)'
    )

    # =========================================================================
    # Module 12: Capital Expenditure Planning
    # =========================================================================

    op.create_table(
        'capex_plans',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('budget_version_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('efir_budget.budget_versions.id', ondelete='CASCADE'),
                  nullable=False, index=True),
        sa.Column('account_code', sa.String(20), nullable=False, index=True,
                  comment='PCG account code (20xxx-21xxx assets)'),
        sa.Column('description', sa.Text(), nullable=False,
                  comment='Asset description'),
        sa.Column('category', sa.String(50), nullable=False, index=True,
                  comment='Category (equipment, IT, furniture, building, software)'),
        sa.Column('quantity', sa.Integer(), nullable=False,
                  comment='Number of units'),
        sa.Column('unit_cost_sar', sa.Numeric(10, 2), nullable=False,
                  comment='Cost per unit (SAR)'),
        sa.Column('total_cost_sar', sa.Numeric(12, 2), nullable=False,
                  comment='Total cost (quantity × unit_cost)'),
        sa.Column('acquisition_date', sa.Date(), nullable=False,
                  comment='Expected acquisition date'),
        sa.Column('useful_life_years', sa.Integer(), nullable=False,
                  comment='Depreciation life (years)'),
        sa.Column('notes', sa.Text(), nullable=True,
                  comment='CapEx notes and justification'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('auth.users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('updated_by_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('auth.users.id', ondelete='SET NULL'), nullable=True),
        sa.CheckConstraint('quantity > 0', name='ck_capex_quantity_positive'),
        sa.CheckConstraint('unit_cost_sar >= 0 AND total_cost_sar >= 0',
                           name='ck_capex_costs_non_negative'),
        sa.CheckConstraint('useful_life_years > 0 AND useful_life_years <= 50',
                           name='ck_capex_life_realistic'),
        schema='efir_budget',
        comment='Capital expenditure projections (asset purchases)'
    )

    # =========================================================================
    # Apply updated_at triggers to all new tables
    # =========================================================================

    planning_tables = [
        'enrollment_plans', 'class_structures', 'dhg_subject_hours',
        'dhg_teacher_requirements', 'teacher_allocations', 'revenue_plans',
        'personnel_cost_plans', 'operating_cost_plans', 'capex_plans'
    ]

    for table in planning_tables:
        op.execute(f"""
            CREATE TRIGGER set_updated_at
            BEFORE UPDATE ON efir_budget.{table}
            FOR EACH ROW
            EXECUTE FUNCTION efir_budget.update_updated_at();
        """)


def downgrade() -> None:
    """Drop all Planning Layer tables."""

    # Drop tables in reverse order (respecting foreign key dependencies)
    op.drop_table('capex_plans', schema='efir_budget')
    op.drop_table('operating_cost_plans', schema='efir_budget')
    op.drop_table('personnel_cost_plans', schema='efir_budget')
    op.drop_table('revenue_plans', schema='efir_budget')
    op.drop_table('teacher_allocations', schema='efir_budget')
    op.drop_table('dhg_teacher_requirements', schema='efir_budget')
    op.drop_table('dhg_subject_hours', schema='efir_budget')
    op.drop_table('class_structures', schema='efir_budget')
    op.drop_table('enrollment_plans', schema='efir_budget')
