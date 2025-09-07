"""Add APP functionality tables

Revision ID: 013_add_app_functionality_tables
Revises: 012_org_branding
Create Date: 2025-05-30 05:10:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '013_add_app_functionality_tables'
down_revision = '000_base_tables_pg'
branch_labels = None
depends_on = None

# Following the multi-step migration approach as documented in the system
def upgrade() -> None:
    # Step 0: Enable uuid-ossp extension if using PostgreSQL
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    
    # Check if we're using PostgreSQL and enable uuid-ossp extension
    if inspector.dialect.name == 'postgresql':
        try:
            connection.execute(sa.text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
        except Exception as e:
            print(f"Warning: Could not create uuid-ossp extension: {e}")
    
    # Step 1: Check if dependency tables exist
    # This is handled by Alembic dependency chain, but we'll add a safeguard
    tables = inspector.get_table_names()
    
    # Check for required tables - warn but don't fail if missing
    required_tables = ['organizations', 'certificates', 'users', 'submission_records']
    missing_tables = []
    for table in required_tables:
        if table not in tables:
            missing_tables.append(table)
            print(f"Warning: Dependency table {table} not found. Some foreign keys will be skipped.")
    
    # Log missing tables but continue migration
    if missing_tables:
        print(f"Missing tables: {missing_tables}. Migration will continue with available tables.")
    
    # Step 2: Create tables without foreign key constraints initially
    
    # 1. Certificate requests table (for storing CSR data and request status)
    op.create_table(
        'certificate_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('request_type', sa.String(50), nullable=False),
        sa.Column('csr_data', sa.Text),
        sa.Column('is_encrypted', sa.Boolean, server_default=sa.text('true')),
        sa.Column('encryption_key_id', sa.String(100)),
        sa.Column('status', sa.String(50), server_default=sa.text("'pending'")),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
        sa.Column('request_metadata', postgresql.JSONB)
    )
    
    # 2. Transmission records table (for secure APP transmissions)
    op.create_table(
        'transmission_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('certificate_id', postgresql.UUID(as_uuid=True)),
        sa.Column('submission_id', postgresql.UUID(as_uuid=True)),
        sa.Column('transmission_time', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('status', sa.String(50), server_default=sa.text("'pending'")),
        sa.Column('encrypted_payload', sa.Text),
        sa.Column('encryption_metadata', postgresql.JSONB),
        sa.Column('response_data', postgresql.JSONB),
        sa.Column('retry_count', sa.Integer, server_default=sa.text('0')),
        sa.Column('last_retry_time', sa.DateTime(timezone=True)),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
        sa.Column('transmission_metadata', postgresql.JSONB)
    )
    
    # 3. CSID registry table (for storing CSIDs associated with certificates)
    op.create_table(
        'csid_registry',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('csid', sa.String(100), nullable=False),
        sa.Column('certificate_id', postgresql.UUID(as_uuid=True)),
        sa.Column('creation_time', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('expiration_time', sa.DateTime(timezone=True)),
        sa.Column('is_active', sa.Boolean, server_default=sa.text('true')),
        sa.Column('revocation_time', sa.DateTime(timezone=True)),
        sa.Column('revocation_reason', sa.String(255)),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
        sa.Column('metadata', postgresql.JSONB)
    )
    
    # Create unique constraint on CSID
    op.create_unique_constraint('uq_csid_registry_csid', 'csid_registry', ['csid'])
    
    # Create indexes for faster lookups
    op.create_index('ix_certificate_requests_organization_id', 'certificate_requests', ['organization_id'])
    op.create_index('ix_certificate_requests_status', 'certificate_requests', ['status'])
    
    op.create_index('ix_transmission_records_organization_id', 'transmission_records', ['organization_id'])
    op.create_index('ix_transmission_records_certificate_id', 'transmission_records', ['certificate_id'])
    op.create_index('ix_transmission_records_submission_id', 'transmission_records', ['submission_id'])
    op.create_index('ix_transmission_records_status', 'transmission_records', ['status'])
    
    op.create_index('ix_csid_registry_organization_id', 'csid_registry', ['organization_id'])
    op.create_index('ix_csid_registry_certificate_id', 'csid_registry', ['certificate_id'])
    op.create_index('ix_csid_registry_is_active', 'csid_registry', ['is_active'])
    
    # Step 3: Add foreign key constraints separately
    # First check which tables actually exist
    constraints = [
        # Certificate request constraints
        ('fk_certificate_requests_organization_id', 'certificate_requests', 'organization_id', 'organizations', 'id'),
        ('fk_certificate_requests_created_by', 'certificate_requests', 'created_by', 'users', 'id'),
        
        # Transmission records constraints
        ('fk_transmission_records_organization_id', 'transmission_records', 'organization_id', 'organizations', 'id'),
        ('fk_transmission_records_certificate_id', 'transmission_records', 'certificate_id', 'certificates', 'id'),
        ('fk_transmission_records_submission_id', 'transmission_records', 'submission_id', 'submission_records', 'id'),
        ('fk_transmission_records_created_by', 'transmission_records', 'created_by', 'users', 'id'),
        
        # CSID registry constraints
        ('fk_csid_registry_organization_id', 'csid_registry', 'organization_id', 'organizations', 'id'),
        ('fk_csid_registry_certificate_id', 'csid_registry', 'certificate_id', 'certificates', 'id'),
        ('fk_csid_registry_created_by', 'csid_registry', 'created_by', 'users', 'id')
    ]
    
    # Optional constraint for encryption_keys if it exists
    if 'encryption_keys' in tables:
        constraints.append(
            ('fk_certificate_requests_encryption_key_id', 'certificate_requests', 'encryption_key_id', 'encryption_keys', 'id')
        )
    
    for constraint_name, table, column, ref_table, ref_column in constraints:
        try:
            # Check if the referenced table exists
            if ref_table in tables:
                op.create_foreign_key(
                    constraint_name, table, ref_table,
                    [column], [ref_column]
                )
            else:
                print(f"Skipping constraint {constraint_name}: referenced table {ref_table} does not exist")
        except Exception as e:
            print(f"Warning: Could not create constraint {constraint_name}: {e}")
            # Continue with other constraints


def downgrade() -> None:
    # Drop tables and indexes in reverse order to avoid dependency issues
    
    # Check which tables exist before dropping constraints
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    tables = inspector.get_table_names()
    
    # Drop foreign key constraints first
    constraints = [
        # CSID registry constraints
        ('fk_csid_registry_created_by', 'csid_registry'),
        ('fk_csid_registry_certificate_id', 'csid_registry'),
        ('fk_csid_registry_organization_id', 'csid_registry'),
        
        # Transmission records constraints
        ('fk_transmission_records_created_by', 'transmission_records'),
        ('fk_transmission_records_submission_id', 'transmission_records'),
        ('fk_transmission_records_certificate_id', 'transmission_records'),
        ('fk_transmission_records_organization_id', 'transmission_records'),
        
        # Certificate request constraints
        ('fk_certificate_requests_created_by', 'certificate_requests'),
        ('fk_certificate_requests_organization_id', 'certificate_requests')
    ]
    
    # Add optional encryption key constraint if it was created
    if 'encryption_keys' in tables:
        constraints.append(('fk_certificate_requests_encryption_key_id', 'certificate_requests'))
    
    for constraint_name, table in constraints:
        try:
            if table in tables:
                op.drop_constraint(constraint_name, table)
        except Exception as e:
            print(f"Warning: Could not drop constraint {constraint_name}: {e}")
    
    # Drop indexes only if tables exist
    if 'csid_registry' in tables:
        try:
            op.drop_index('ix_csid_registry_is_active', table_name='csid_registry')
            op.drop_index('ix_csid_registry_certificate_id', table_name='csid_registry')
            op.drop_index('ix_csid_registry_organization_id', table_name='csid_registry')
            op.drop_constraint('uq_csid_registry_csid', 'csid_registry')
        except Exception as e:
            print(f"Warning: Could not drop csid_registry indexes/constraints: {e}")
    
    if 'transmission_records' in tables:
        try:
            op.drop_index('ix_transmission_records_status', table_name='transmission_records')
            op.drop_index('ix_transmission_records_submission_id', table_name='transmission_records')
            op.drop_index('ix_transmission_records_certificate_id', table_name='transmission_records')
            op.drop_index('ix_transmission_records_organization_id', table_name='transmission_records')
        except Exception as e:
            print(f"Warning: Could not drop transmission_records indexes: {e}")
    
    if 'certificate_requests' in tables:
        try:
            op.drop_index('ix_certificate_requests_status', table_name='certificate_requests')
            op.drop_index('ix_certificate_requests_organization_id', table_name='certificate_requests')
        except Exception as e:
            print(f"Warning: Could not drop certificate_requests indexes: {e}")
    
    # Drop tables only if they exist
    for table_name in ['csid_registry', 'transmission_records', 'certificate_requests']:
        if table_name in tables:
            try:
                op.drop_table(table_name)
            except Exception as e:
                print(f"Warning: Could not drop table {table_name}: {e}")
