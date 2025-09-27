"""Add SDK Management Models

Revision ID: add_sdk_management_models
Revises: 920b8e791d92
Create Date: 2024-12-31 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_sdk_management_models'
down_revision = '920b8e791d92'
branch_labels = None
depends_on = None


SDK_LANGUAGES = (
    'python',
    'javascript',
    'java',
    'csharp',
    'php',
    'go',
    'ruby',
    'swift',
    'kotlin',
    'rust',
)

SDK_STATUSES = (
    'draft',
    'beta',
    'stable',
    'deprecated',
    'archived',
)

FEEDBACK_TYPES = (
    'general',
    'bug_report',
    'feature_request',
    'documentation',
    'performance',
    'integration',
)

TEST_STATUSES = (
    'pending',
    'running',
    'success',
    'failed',
    'timeout',
)

sdk_language_enum = postgresql.ENUM(*SDK_LANGUAGES, name='sdklanguage', create_type=False)
sdk_status_enum = postgresql.ENUM(*SDK_STATUSES, name='sdkstatus', create_type=False)
feedback_type_enum = postgresql.ENUM(*FEEDBACK_TYPES, name='feedbacktype', create_type=False)
test_status_enum = postgresql.ENUM(*TEST_STATUSES, name='teststatus', create_type=False)

sdk_language_enum_type = postgresql.ENUM(*SDK_LANGUAGES, name='sdklanguage')
sdk_status_enum_type = postgresql.ENUM(*SDK_STATUSES, name='sdkstatus')
feedback_type_enum_type = postgresql.ENUM(*FEEDBACK_TYPES, name='feedbacktype')
test_status_enum_type = postgresql.ENUM(*TEST_STATUSES, name='teststatus')


def upgrade():
    # Create enums
    bind = op.get_bind()
    sdk_language_enum_type.create(bind, checkfirst=True)
    sdk_status_enum_type.create(bind, checkfirst=True)
    feedback_type_enum_type.create(bind, checkfirst=True)
    test_status_enum_type.create(bind, checkfirst=True)
    
    # Create sdks table
    op.create_table('sdks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('language', sdk_language_enum, nullable=False),
        sa.Column('version', sa.String(length=20), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('features', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('requirements', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('compatibility', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('examples', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('download_count', sa.Integer(), nullable=True),
        sa.Column('rating', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('status', sdk_status_enum, nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sdks_download_count'), 'sdks', ['download_count'], unique=False)
    op.create_index(op.f('ix_sdks_is_active'), 'sdks', ['is_active'], unique=False)
    op.create_index(op.f('ix_sdks_language'), 'sdks', ['language'], unique=False)
    op.create_index(op.f('ix_sdks_name'), 'sdks', ['name'], unique=False)
    
    # Create sdk_versions table
    op.create_table('sdk_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sdk_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('version', sa.String(length=20), nullable=False),
        sa.Column('release_notes', sa.Text(), nullable=True),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('file_size', sa.BigInteger(), nullable=False),
        sa.Column('checksum', sa.String(length=64), nullable=False),
        sa.Column('is_stable', sa.Boolean(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['sdk_id'], ['sdks.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sdk_versions_is_active'), 'sdk_versions', ['is_active'], unique=False)
    op.create_index(op.f('ix_sdk_versions_is_stable'), 'sdk_versions', ['is_stable'], unique=False)
    op.create_index(op.f('ix_sdk_versions_sdk_id'), 'sdk_versions', ['sdk_id'], unique=False)
    op.create_index(op.f('ix_sdk_versions_version'), 'sdk_versions', ['version'], unique=False)
    
    # Create sdk_downloads table
    op.create_table('sdk_downloads',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sdk_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('version_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('download_method', sa.String(length=50), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['sdk_id'], ['sdks.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['version_id'], ['sdk_versions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sdk_downloads_organization_id'), 'sdk_downloads', ['organization_id'], unique=False)
    op.create_index(op.f('ix_sdk_downloads_sdk_id'), 'sdk_downloads', ['sdk_id'], unique=False)
    op.create_index(op.f('ix_sdk_downloads_user_id'), 'sdk_downloads', ['user_id'], unique=False)
    op.create_index(op.f('ix_sdk_downloads_version_id'), 'sdk_downloads', ['version_id'], unique=False)
    
    # Create sdk_usage_logs table
    op.create_table('sdk_usage_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sdk_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('endpoint', sa.String(length=200), nullable=False),
        sa.Column('method', sa.String(length=10), nullable=False),
        sa.Column('response_time', sa.Integer(), nullable=False),
        sa.Column('status_code', sa.Integer(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('request_size', sa.Integer(), nullable=True),
        sa.Column('response_size', sa.Integer(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['sdk_id'], ['sdks.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sdk_usage_logs_endpoint'), 'sdk_usage_logs', ['endpoint'], unique=False)
    op.create_index(op.f('ix_sdk_usage_logs_organization_id'), 'sdk_usage_logs', ['organization_id'], unique=False)
    op.create_index(op.f('ix_sdk_usage_logs_sdk_id'), 'sdk_usage_logs', ['sdk_id'], unique=False)
    op.create_index(op.f('ix_sdk_usage_logs_status_code'), 'sdk_usage_logs', ['status_code'], unique=False)
    op.create_index(op.f('ix_sdk_usage_logs_user_id'), 'sdk_usage_logs', ['user_id'], unique=False)
    
    # Create sandbox_scenarios table
    op.create_table('sandbox_scenarios',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('endpoint', sa.String(length=200), nullable=False),
        sa.Column('method', sa.String(length=10), nullable=False),
        sa.Column('headers', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('body', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('expected_response', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('difficulty', sa.String(length=20), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sandbox_scenarios_category'), 'sandbox_scenarios', ['category'], unique=False)
    op.create_index(op.f('ix_sandbox_scenarios_is_active'), 'sandbox_scenarios', ['is_active'], unique=False)
    op.create_index(op.f('ix_sandbox_scenarios_name'), 'sandbox_scenarios', ['name'], unique=False)
    
    # Create sandbox_test_results table
    op.create_table('sandbox_test_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('scenario_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', test_status_enum, nullable=False),
        sa.Column('response_time', sa.Integer(), nullable=False),
        sa.Column('status_code', sa.Integer(), nullable=True),
        sa.Column('response_body', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('headers_sent', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('body_sent', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['scenario_id'], ['sandbox_scenarios.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sandbox_test_results_organization_id'), 'sandbox_test_results', ['organization_id'], unique=False)
    op.create_index(op.f('ix_sandbox_test_results_scenario_id'), 'sandbox_test_results', ['scenario_id'], unique=False)
    op.create_index(op.f('ix_sandbox_test_results_status'), 'sandbox_test_results', ['status'], unique=False)
    op.create_index(op.f('ix_sandbox_test_results_user_id'), 'sandbox_test_results', ['user_id'], unique=False)
    
    # Create sdk_documentation table
    op.create_table('sdk_documentation',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sdk_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('language', sa.String(length=10), nullable=False),
        sa.Column('content_type', sa.String(length=50), nullable=False),
        sa.Column('content', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('version', sa.String(length=20), nullable=False),
        sa.Column('is_published', sa.Boolean(), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['sdk_id'], ['sdks.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sdk_documentation_content_type'), 'sdk_documentation', ['content_type'], unique=False)
    op.create_index(op.f('ix_sdk_documentation_is_published'), 'sdk_documentation', ['is_published'], unique=False)
    op.create_index(op.f('ix_sdk_documentation_language'), 'sdk_documentation', ['language'], unique=False)
    op.create_index(op.f('ix_sdk_documentation_sdk_id'), 'sdk_documentation', ['sdk_id'], unique=False)
    
    # Create sdk_feedback table
    op.create_table('sdk_feedback',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sdk_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('feedback_type', feedback_type_enum, nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('comments', sa.Text(), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=True),
        sa.Column('is_resolved', sa.Boolean(), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['sdk_id'], ['sdks.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sdk_feedback_feedback_type'), 'sdk_feedback', ['feedback_type'], unique=False)
    op.create_index(op.f('ix_sdk_feedback_is_public'), 'sdk_feedback', ['is_public'], unique=False)
    op.create_index(op.f('ix_sdk_feedback_is_resolved'), 'sdk_feedback', ['is_resolved'], unique=False)
    op.create_index(op.f('ix_sdk_feedback_organization_id'), 'sdk_feedback', ['organization_id'], unique=False)
    op.create_index(op.f('ix_sdk_feedback_sdk_id'), 'sdk_feedback', ['sdk_id'], unique=False)
    op.create_index(op.f('ix_sdk_feedback_user_id'), 'sdk_feedback', ['user_id'], unique=False)
    
    # Create sdk_analytics table
    op.create_table('sdk_analytics',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sdk_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('period', sa.String(length=10), nullable=False),
        sa.Column('downloads', sa.Integer(), nullable=True),
        sa.Column('active_users', sa.Integer(), nullable=True),
        sa.Column('api_calls', sa.Integer(), nullable=True),
        sa.Column('avg_response_time', sa.Integer(), nullable=True),
        sa.Column('error_rate', sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column('top_features', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('top_organizations', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['sdk_id'], ['sdks.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sdk_analytics_date'), 'sdk_analytics', ['date'], unique=False)
    op.create_index(op.f('ix_sdk_analytics_period'), 'sdk_analytics', ['period'], unique=False)
    op.create_index(op.f('ix_sdk_analytics_sdk_id'), 'sdk_analytics', ['sdk_id'], unique=False)


def downgrade():
    # Drop tables
    op.drop_index(op.f('ix_sdk_analytics_sdk_id'), table_name='sdk_analytics')
    op.drop_index(op.f('ix_sdk_analytics_period'), table_name='sdk_analytics')
    op.drop_index(op.f('ix_sdk_analytics_date'), table_name='sdk_analytics')
    op.drop_table('sdk_analytics')
    
    op.drop_index(op.f('ix_sdk_feedback_user_id'), table_name='sdk_feedback')
    op.drop_index(op.f('ix_sdk_feedback_sdk_id'), table_name='sdk_feedback')
    op.drop_index(op.f('ix_sdk_feedback_organization_id'), table_name='sdk_feedback')
    op.drop_index(op.f('ix_sdk_feedback_is_resolved'), table_name='sdk_feedback')
    op.drop_index(op.f('ix_sdk_feedback_is_public'), table_name='sdk_feedback')
    op.drop_index(op.f('ix_sdk_feedback_feedback_type'), table_name='sdk_feedback')
    op.drop_table('sdk_feedback')
    
    op.drop_index(op.f('ix_sdk_documentation_sdk_id'), table_name='sdk_documentation')
    op.drop_index(op.f('ix_sdk_documentation_language'), table_name='sdk_documentation')
    op.drop_index(op.f('ix_sdk_documentation_is_published'), table_name='sdk_documentation')
    op.drop_index(op.f('ix_sdk_documentation_content_type'), table_name='sdk_documentation')
    op.drop_table('sdk_documentation')
    
    op.drop_index(op.f('ix_sandbox_test_results_user_id'), table_name='sandbox_test_results')
    op.drop_index(op.f('ix_sandbox_test_results_status'), table_name='sandbox_test_results')
    op.drop_index(op.f('ix_sandbox_test_results_scenario_id'), table_name='sandbox_test_results')
    op.drop_index(op.f('ix_sandbox_test_results_organization_id'), table_name='sandbox_test_results')
    op.drop_table('sandbox_test_results')
    
    op.drop_index(op.f('ix_sandbox_scenarios_name'), table_name='sandbox_scenarios')
    op.drop_index(op.f('ix_sandbox_scenarios_is_active'), table_name='sandbox_scenarios')
    op.drop_index(op.f('ix_sandbox_scenarios_category'), table_name='sandbox_scenarios')
    op.drop_table('sandbox_scenarios')
    
    op.drop_index(op.f('ix_sdk_usage_logs_user_id'), table_name='sdk_usage_logs')
    op.drop_index(op.f('ix_sdk_usage_logs_status_code'), table_name='sdk_usage_logs')
    op.drop_index(op.f('ix_sdk_usage_logs_sdk_id'), table_name='sdk_usage_logs')
    op.drop_index(op.f('ix_sdk_usage_logs_organization_id'), table_name='sdk_usage_logs')
    op.drop_index(op.f('ix_sdk_usage_logs_endpoint'), table_name='sdk_usage_logs')
    op.drop_table('sdk_usage_logs')
    
    op.drop_index(op.f('ix_sdk_downloads_version_id'), table_name='sdk_downloads')
    op.drop_index(op.f('ix_sdk_downloads_user_id'), table_name='sdk_downloads')
    op.drop_index(op.f('ix_sdk_downloads_sdk_id'), table_name='sdk_downloads')
    op.drop_index(op.f('ix_sdk_downloads_organization_id'), table_name='sdk_downloads')
    op.drop_table('sdk_downloads')
    
    op.drop_index(op.f('ix_sdk_versions_version'), table_name='sdk_versions')
    op.drop_index(op.f('ix_sdk_versions_sdk_id'), table_name='sdk_versions')
    op.drop_index(op.f('ix_sdk_versions_is_stable'), table_name='sdk_versions')
    op.drop_index(op.f('ix_sdk_versions_is_active'), table_name='sdk_versions')
    op.drop_table('sdk_versions')
    
    op.drop_index(op.f('ix_sdks_name'), table_name='sdks')
    op.drop_index(op.f('ix_sdks_language'), table_name='sdks')
    op.drop_index(op.f('ix_sdks_is_active'), table_name='sdks')
    op.drop_index(op.f('ix_sdks_download_count'), table_name='sdks')
    op.drop_table('sdks')
    
    # Drop enums
    bind = op.get_bind()
    test_status_enum_type.drop(bind, checkfirst=True)
    feedback_type_enum_type.drop(bind, checkfirst=True)
    sdk_status_enum_type.drop(bind, checkfirst=True)
    sdk_language_enum_type.drop(bind, checkfirst=True)
