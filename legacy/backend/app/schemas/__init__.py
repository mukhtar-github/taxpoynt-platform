from app.schemas.user import User, UserCreate, UserUpdate
from app.schemas.client import Client, ClientCreate, ClientUpdate, ClientInDB
from app.schemas.integration import (
    Integration, IntegrationCreate, IntegrationUpdate, IntegrationInDB,
    IntegrationHistory, IntegrationHistoryCreate, IntegrationHistoryInDB,
    IntegrationTestResult, IntegrationTemplateCreate
)
from app.schemas.organization import (
    Organization, OrganizationCreate, OrganizationUpdate, OrganizationInDB,
    OrganizationWithUsers, BrandingSettings, LogoUpload
)

# Add new schemas here when created