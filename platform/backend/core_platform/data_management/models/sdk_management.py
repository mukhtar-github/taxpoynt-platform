"""
SDK Management Models
====================
Database models for SDK management, distribution, and analytics.
Provides both production data storage and demo data fallbacks.
"""

from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, ForeignKey, JSON, BigInteger, Numeric, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
import enum
from typing import Any, Dict, List, Optional

from .base import BaseModel, TimestampMixin

class SDKLanguage(enum.Enum):
    """Supported programming languages for SDKs."""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    JAVA = "java"
    CSHARP = "csharp"
    PHP = "php"
    GO = "go"
    RUBY = "ruby"
    SWIFT = "swift"
    KOTLIN = "kotlin"
    RUST = "rust"

class SDKStatus(enum.Enum):
    """SDK release status."""
    DRAFT = "draft"
    BETA = "beta"
    STABLE = "stable"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"

class FeedbackType(enum.Enum):
    """Types of SDK feedback."""
    GENERAL = "general"
    BUG_REPORT = "bug_report"
    FEATURE_REQUEST = "feature_request"
    DOCUMENTATION = "documentation"
    PERFORMANCE = "performance"
    INTEGRATION = "integration"

class TestStatus(enum.Enum):
    """Sandbox test execution status."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"

class SDK(BaseModel):
    """Main SDK model for catalog and metadata."""
    
    __tablename__ = "sdks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, index=True)
    language = Column(Enum(SDKLanguage), nullable=False, index=True)
    version = Column(String(20), nullable=False)
    description = Column(Text, nullable=False)
    features = Column(JSON, nullable=False, default=list)
    requirements = Column(JSON, nullable=False, default=list)
    compatibility = Column(JSON, nullable=False, default=list)
    examples = Column(JSON, nullable=False, default=list)
    download_count = Column(Integer, default=0, index=True)
    rating = Column(Numeric(3, 2), default=0.0)
    status = Column(Enum(SDKStatus), default=SDKStatus.BETA)
    is_active = Column(Boolean, default=True, index=True)
    metadata = Column(JSON, nullable=True)  # Additional flexible metadata
    
    # Relationships
    versions = relationship("SDKVersion", back_populates="sdk", cascade="all, delete-orphan")
    downloads = relationship("SDKDownload", back_populates="sdk", cascade="all, delete-orphan")
    usage_logs = relationship("SDKUsageLog", back_populates="sdk", cascade="all, delete-orphan")
    feedback = relationship("SDKFeedback", back_populates="sdk", cascade="all, delete-orphan")
    documentation = relationship("SDKDocumentation", back_populates="sdk", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<SDK(name='{self.name}', language='{self.language}', version='{self.version}')>"
    
    @property
    def display_name(self) -> str:
        """Get formatted display name."""
        return f"{self.name} ({self.language.value.title()})"
    
    @property
    def is_stable(self) -> bool:
        """Check if SDK is stable."""
        return self.status == SDKStatus.STABLE
    
    def increment_download_count(self) -> None:
        """Increment download counter."""
        self.download_count += 1

class SDKVersion(BaseModel):
    """SDK version management and file storage."""
    
    __tablename__ = "sdk_versions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sdk_id = Column(UUID(as_uuid=True), ForeignKey("sdks.id"), nullable=False, index=True)
    version = Column(String(20), nullable=False, index=True)
    release_notes = Column(Text, nullable=True)
    file_path = Column(String(500), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    checksum = Column(String(64), nullable=False)
    is_stable = Column(Boolean, default=False, index=True)
    is_active = Column(Boolean, default=True, index=True)
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    sdk = relationship("SDK", back_populates="versions")
    downloads = relationship("SDKDownload", back_populates="version")
    
    def __repr__(self):
        return f"<SDKVersion(sdk='{self.sdk.name}', version='{self.version}')>"
    
    @property
    def formatted_file_size(self) -> str:
        """Get human-readable file size."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if self.file_size < 1024.0:
                return f"{self.file_size:.1f} {unit}"
            self.file_size /= 1024.0
        return f"{self.file_size:.1f} TB"

class SDKDownload(BaseModel):
    """Track SDK downloads for analytics and user history."""
    
    __tablename__ = "sdk_downloads"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sdk_id = Column(UUID(as_uuid=True), ForeignKey("sdks.id"), nullable=False, index=True)
    version_id = Column(UUID(as_uuid=True), ForeignKey("sdk_versions.id"), nullable=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(Text, nullable=True)
    download_method = Column(String(50), default="web")  # web, api, cli
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    sdk = relationship("SDK", back_populates="downloads")
    version = relationship("SDKVersion", back_populates="downloads")
    user = relationship("User")
    organization = relationship("Organization")
    
    def __repr__(self):
        return f"<SDKDownload(sdk='{self.sdk.name}', user='{self.user.email}')>"

class SDKUsageLog(BaseModel):
    """Track SDK usage patterns and performance metrics."""
    
    __tablename__ = "sdk_usage_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sdk_id = Column(UUID(as_uuid=True), ForeignKey("sdks.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    endpoint = Column(String(200), nullable=False, index=True)
    method = Column(String(10), nullable=False)
    response_time = Column(Integer, nullable=False)  # milliseconds
    status_code = Column(Integer, nullable=False, index=True)
    error_message = Column(Text, nullable=True)
    request_size = Column(Integer, nullable=True)  # bytes
    response_size = Column(Integer, nullable=True)  # bytes
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    sdk = relationship("SDK", back_populates="usage_logs")
    user = relationship("User")
    organization = relationship("Organization")
    
    def __repr__(self):
        return f"<SDKUsageLog(sdk='{self.sdk.name}', endpoint='{self.endpoint}', status={self.status_code})>"

class SandboxScenario(BaseModel):
    """Predefined API testing scenarios for SDK sandbox."""
    
    __tablename__ = "sandbox_scenarios"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=False)
    endpoint = Column(String(200), nullable=False)
    method = Column(String(10), nullable=False)
    headers = Column(JSON, nullable=False, default=dict)
    body = Column(JSON, nullable=True)
    expected_response = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    category = Column(String(50), nullable=True, index=True)
    difficulty = Column(String(20), default="beginner")  # beginner, intermediate, advanced
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    test_results = relationship("SandboxTestResult", back_populates="scenario", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<SandboxScenario(name='{self.name}', endpoint='{self.endpoint}')>"

class SandboxTestResult(BaseModel):
    """Results from sandbox test executions."""
    
    __tablename__ = "sandbox_test_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scenario_id = Column(UUID(as_uuid=True), ForeignKey("sandbox_scenarios.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    status = Column(Enum(TestStatus), nullable=False, index=True)
    response_time = Column(Integer, nullable=False)  # milliseconds
    status_code = Column(Integer, nullable=True)
    response_body = Column(JSON, nullable=True)
    headers_sent = Column(JSON, nullable=True)
    body_sent = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    scenario = relationship("SandboxScenario", back_populates="test_results")
    user = relationship("User")
    organization = relationship("Organization")
    
    def __repr__(self):
        return f"<SandboxTestResult(scenario='{self.scenario.name}', status='{self.status.value}')>"

class SDKDocumentation(BaseModel):
    """SDK documentation content and versioning."""
    
    __tablename__ = "sdk_documentation"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sdk_id = Column(UUID(as_uuid=True), ForeignKey("sdks.id"), nullable=False, index=True)
    language = Column(String(10), nullable=False, index=True)
    content_type = Column(String(50), nullable=False, index=True)  # overview, quick_start, api_reference, etc.
    content = Column(JSON, nullable=False)
    version = Column(String(20), nullable=False)
    is_published = Column(Boolean, default=False, index=True)
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    sdk = relationship("SDK", back_populates="documentation")
    
    def __repr__(self):
        return f"<SDKDocumentation(sdk='{self.sdk.name}', type='{self.content_type}', lang='{self.language}')>"

class SDKFeedback(BaseModel):
    """User feedback and ratings for SDKs."""
    
    __tablename__ = "sdk_feedback"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sdk_id = Column(UUID(as_uuid=True), ForeignKey("sdks.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    feedback_type = Column(Enum(FeedbackType), nullable=False, index=True)
    rating = Column(Integer, nullable=False)  # 1-5 scale
    comments = Column(Text, nullable=True)
    is_public = Column(Boolean, default=True, index=True)
    is_resolved = Column(Boolean, default=False, index=True)
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    sdk = relationship("SDK", back_populates="feedback")
    user = relationship("User")
    organization = relationship("Organization")
    
    def __repr__(self):
        return f"<SDKFeedback(sdk='{self.sdk.name}', type='{self.feedback_type.value}', rating={self.rating})>"

class SDKAnalytics(BaseModel):
    """Aggregated SDK analytics and metrics."""
    
    __tablename__ = "sdk_analytics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sdk_id = Column(UUID(as_uuid=True), ForeignKey("sdks.id"), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)
    period = Column(String(10), nullable=False, index=True)  # daily, weekly, monthly
    downloads = Column(Integer, default=0)
    active_users = Column(Integer, default=0)
    api_calls = Column(Integer, default=0)
    avg_response_time = Column(Integer, default=0)  # milliseconds
    error_rate = Column(Numeric(5, 4), default=0.0)  # percentage
    top_features = Column(JSON, nullable=True)
    top_organizations = Column(JSON, nullable=True)
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    sdk = relationship("SDK")
    
    def __repr__(self):
        return f"<SDKAnalytics(sdk='{self.sdk.name}', date='{self.date}', period='{self.period}')>"

# Demo data fallback for development/testing
DEMO_SDK_DATA = {
    "python": {
        "id": "demo-python-sdk",
        "name": "Python SDK",
        "language": "python",
        "version": "1.0.0",
        "description": "Official Python SDK for TaxPoynt platform integration",
        "features": ["Authentication", "Invoice Management", "Compliance Checking", "Webhook Handling"],
        "requirements": ["requests>=2.25.0", "pydantic>=1.8.0"],
        "compatibility": ["Python 3.8+", "FastAPI", "Django", "Flask"],
        "examples": ["Basic Integration", "Invoice Creation", "Webhook Processing"],
        "download_count": 1250,
        "rating": 4.5,
        "status": "stable"
    },
    "javascript": {
        "id": "demo-javascript-sdk",
        "name": "JavaScript/Node.js SDK",
        "language": "javascript",
        "version": "1.0.0",
        "description": "Official JavaScript SDK for TaxPoynt platform integration",
        "features": ["Browser & Node.js Support", "TypeScript Types", "Promise-based API", "Error Handling"],
        "requirements": ["axios>=0.21.0", "joi>=17.0.0"],
        "compatibility": ["Node.js 16+", "Modern Browsers", "React", "Vue.js"],
        "examples": ["Frontend Integration", "Backend API", "Webhook Endpoints"],
        "download_count": 890,
        "rating": 4.7,
        "status": "stable"
    }
}

DEMO_SCENARIOS = {
    "authentication": {
        "id": "demo-auth-scenario",
        "name": "Authentication Test",
        "description": "Test API key authentication and token generation",
        "endpoint": "/api/v1/auth/login",
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "body": {"api_key": "your_api_key", "api_secret": "your_api_secret"},
        "expected_response": {"status": "success", "token": "jwt_token_here"}
    },
    "invoice_creation": {
        "id": "demo-invoice-scenario",
        "name": "Invoice Creation Test",
        "description": "Test creating a new invoice through the API",
        "endpoint": "/api/v1/invoices",
        "method": "POST",
        "headers": {"Authorization": "Bearer {token}", "Content-Type": "application/json"},
        "body": {
            "invoice_number": "INV-001",
            "amount": 1000.00,
            "currency": "NGN",
            "customer_name": "Test Customer",
            "items": [{"name": "Test Item", "quantity": 1, "unit_price": 1000.00}]
        },
        "expected_response": {"status": "success", "invoice_id": "inv_123"}
    }
}
