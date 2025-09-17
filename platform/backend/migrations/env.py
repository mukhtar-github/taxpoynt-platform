import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Add the project root to Python path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Import configuration system first (minimal imports to avoid dependency issues)
try:
    from core_platform.config.environment import get_config
    config_manager = get_config()
    database_url = config_manager.get_database_url()
except ImportError as e:
    # Fallback to environment variable if config system isn't available
    print(f"Warning: Could not import config system, using fallback: {e}")
    database_url = os.getenv("DATABASE_URL")

# Import models with error handling
try:
    from core_platform.data_management.models.base import Base
    from core_platform.data_management.models.user import User, UserServiceAccess
    from core_platform.data_management.models.organization import Organization, OrganizationUser  
    from core_platform.data_management.models.integration import Integration, IntegrationCredentials
    from core_platform.data_management.models.firs_submission import FIRSSubmission
    
    # Import banking models if available
    try:
        from core_platform.data_management.models.banking import (
            BankingConnection, BankAccount, BankTransaction, 
            BankingWebhook, BankingSyncLog, BankingCredentials
        )
    except ImportError:
        print("Warning: Banking models not available for migration")
    
    # Import business system models if available
    try:
        from core_platform.data_management.models.business_systems import (
            ERPConnection, ERPSyncLog, CRMConnection, CRMSyncLog,
            POSConnection, POSTransactionLog, Certificate,
            DocumentTemplate, DocumentGenerationLog, IRNGeneration,
            Taxpayer, WebhookEvent, AnalyticsReport, AuditLog, ComplianceCheck
        )
    except ImportError:
        print("Warning: Business system models not available for migration")
    # Import RBAC models if available
    try:
        from core_platform.data_management.models.rbac import (
            Role as RBACRole,
            Permission as RBACPermission,
            RolePermission as RBACRolePermission,
            PermissionHierarchy as RBACPermissionHierarchy,
            RoleInheritance as RBACRoleInheritance,
        )
    except ImportError:
        print("Warning: RBAC models not available for migration")
    # Import payment + reconciliation models if available
    try:
        from core_platform.data_management.models.payment import (
            PaymentConnection, PaymentWebhook
        )
        from core_platform.data_management.models.reconciliation import (
            ReconciliationConfig,
        )
    except ImportError:
        print("Warning: Payment/Reconciliation models not available for migration")
        
except ImportError as e:
    print(f"Error importing models for migration: {e}")
    # Create a minimal Base for migration purposes
    from sqlalchemy.ext.declarative import declarative_base
    Base = declarative_base()

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Set the SQLAlchemy URL using environment-aware configuration
if database_url:
    # Handle Railway's postgres:// URL format (convert to postgresql://)
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    config.set_main_option("sqlalchemy.url", database_url)
else:
    # Fallback to .ini file configuration
    print("Warning: No database URL configured, using alembic.ini default")

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
