# TaxPoynt E-Invoice Platform - API Endpoints Reference

**Version**: v1.0.0  
**Last Updated**: December 2024  
**Base URL**: `https://api.taxpoynt.com` (Production) / `http://localhost:8001` (Development)

## Table of Contents

1. [Authentication Endpoints](#authentication-endpoints)
2. [APP (Access Point Provider) Endpoints](#app-access-point-provider-endpoints)
3. [SI (System Integrator) Endpoints](#si-system-integrator-endpoints)
4. [Hybrid (Cross-Role) Endpoints](#hybrid-cross-role-endpoints)
5. [Response Format](#response-format)
6. [Error Codes](#error-codes)

---

## Authentication Endpoints

**Base Path**: `/api/v1/auth/`

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `POST` | `/api/v1/auth/register` | User registration with organization creation | ❌ |
| `POST` | `/api/v1/auth/login` | User authentication with JWT token | ❌ |
| `GET` | `/api/v1/auth/me` | Get current user profile and organization | ✅ |
| `POST` | `/api/v1/auth/logout` | User logout and token invalidation | ✅ |
| `GET` | `/api/v1/auth/health` | Authentication service health check | ❌ |

---

## APP (Access Point Provider) Endpoints

**Base Path**: `/api/v1/app/`  
**Role Required**: Access Point Provider

### Core APP Services

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/app/health` | APP services health check |
| `GET` | `/api/v1/app/status` | APP status overview with metrics |
| `GET` | `/api/v1/app/info` | APP information and capabilities |
| `GET` | `/api/v1/app/capabilities` | Detailed APP capabilities listing |
| `GET` | `/api/v1/app/dashboard` | General APP operations dashboard |
| `GET` | `/api/v1/app/configuration` | APP configuration settings |
| `PUT` | `/api/v1/app/configuration` | Update APP configuration |

### FIRS Integration (`/api/v1/app/firs/`)

#### System Information
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/app/firs/system/info` | FIRS system information and capabilities |
| `GET` | `/api/v1/app/firs/system/health` | FIRS system health and connectivity |

#### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/app/firs/auth/authenticate` | Authenticate with FIRS systems |
| `POST` | `/api/v1/app/firs/auth/refresh-token` | Refresh FIRS authentication token |
| `GET` | `/api/v1/app/firs/auth/status` | Get FIRS authentication status |

#### Invoice Submission
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/app/firs/invoices/submit` | Submit individual invoice to FIRS |
| `POST` | `/api/v1/app/firs/invoices/submit-batch` | Submit multiple invoices in batch |
| `GET` | `/api/v1/app/firs/invoices/{submission_id}/status` | Get invoice submission status |
| `GET` | `/api/v1/app/firs/invoices/submissions` | List all invoice submissions |

#### Validation
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/app/firs/validation/validate-invoice` | Validate invoice against FIRS rules |
| `POST` | `/api/v1/app/firs/validation/validate-batch` | Validate batch of invoices |
| `GET` | `/api/v1/app/firs/validation/rules` | Get current FIRS validation rules |

#### Reporting
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/app/firs/reporting/generate` | Generate FIRS compliance reports |
| `GET` | `/api/v1/app/firs/reporting/dashboard` | FIRS-specific reporting dashboard |

#### Invoice Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| `PUT` | `/api/v1/app/firs/update/invoice` | Update submitted invoice in FIRS |

#### Certificate Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/app/firs/certificates/list` | List FIRS certificates |
| `GET` | `/api/v1/app/firs/certificates/{certificate_id}` | Get certificate details |
| `POST` | `/api/v1/app/firs/certificates/renew/{certificate_id}` | Renew FIRS certificate |

#### Error & Logs
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/app/firs/errors/list` | Get FIRS integration errors |
| `GET` | `/api/v1/app/firs/logs/integration` | Get FIRS integration logs |

### Certificate Management (`/api/v1/app/certificates/`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/app/certificates/overview` | Certificate management overview |
| `GET` | `/api/v1/app/certificates` | List all certificates |
| `POST` | `/api/v1/app/certificates` | Create new certificate |
| `GET` | `/api/v1/app/certificates/{certificate_id}` | Get certificate details |
| `PUT` | `/api/v1/app/certificates/{certificate_id}` | Update certificate |

### Compliance Validation (`/api/v1/app/compliance/`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/app/compliance/standards` | Get supported compliance standards |
| `POST` | `/api/v1/app/compliance/validate/ubl` | UBL format validation |
| `POST` | `/api/v1/app/compliance/validate/peppol` | PEPPOL standards validation |
| `POST` | `/api/v1/app/compliance/validate/iso20022` | ISO 20022 financial messaging |
| `POST` | `/api/v1/app/compliance/validate/iso27001` | ISO 27001 security management |
| `POST` | `/api/v1/app/compliance/validate/gdpr` | GDPR/NDPA data protection |
| `POST` | `/api/v1/app/compliance/validate/wco-hs` | WCO Harmonized System |
| `POST` | `/api/v1/app/compliance/validate/lei` | Legal Entity Identifier |

### Taxpayer Management (`/api/v1/app/taxpayers/`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/app/taxpayers` | List onboarded taxpayers |
| `POST` | `/api/v1/app/taxpayers` | Create/onboard new taxpayer |
| `GET` | `/api/v1/app/taxpayers/{taxpayer_id}` | Get taxpayer details |
| `PUT` | `/api/v1/app/taxpayers/{taxpayer_id}` | Update taxpayer information |
| `DELETE` | `/api/v1/app/taxpayers/{taxpayer_id}` | Remove taxpayer |

### Invoice Submission (`/api/v1/app/invoices/`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/app/invoices/generate` | Generate compliant invoices |
| `POST` | `/api/v1/app/invoices/submit` | Submit invoices to authorities |
| `GET` | `/api/v1/app/invoices/{invoice_id}` | Get invoice details |
| `GET` | `/api/v1/app/invoices/{invoice_id}/status` | Get submission status |

### Grant Management (`/api/v1/app/grants/`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/app/grants/milestones` | Track FIRS grant milestones |
| `GET` | `/api/v1/app/grants/performance` | Performance metrics |
| `POST` | `/api/v1/app/grants/reports/generate` | Generate grant reports |

---

## SI (System Integrator) Endpoints

**Base Path**: `/api/v1/si/`  
**Role Required**: System Integrator

### Core SI Services

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/si/health` | SI services health check |
| `GET` | `/api/v1/si/status/integrations` | Integration status overview |

### Organization Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/si/organizations` | List managed organizations |
| `POST` | `/api/v1/si/organizations` | Create new organization |
| `GET` | `/api/v1/si/organizations/{org_id}` | Get organization details |
| `PUT` | `/api/v1/si/organizations/{org_id}` | Update organization |

### Business System Integrations

#### ERP Systems (`/api/v1/si/integrations/erp/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/si/integrations/erp` | List ERP connections |
| `POST` | `/api/v1/si/integrations/erp` | Create ERP connection |
| `PUT` | `/api/v1/si/integrations/erp/{connection_id}` | Update ERP connection |
| `POST` | `/api/v1/si/integrations/erp/{connection_id}/test` | Test ERP connection |

#### CRM Systems (`/api/v1/si/integrations/crm/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/si/integrations/crm` | List CRM connections |
| `POST` | `/api/v1/si/integrations/crm` | Create CRM connection |
| `PUT` | `/api/v1/si/integrations/crm/{connection_id}` | Update CRM connection |

#### POS Systems (`/api/v1/si/integrations/pos/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/si/integrations/pos` | List POS connections |
| `POST` | `/api/v1/si/integrations/pos` | Create POS connection |
| `PUT` | `/api/v1/si/integrations/pos/{connection_id}` | Update POS connection |

### ERP System Details (`/api/v1/si/erp/`)

**Supported ERP Systems**: SAP, Oracle, Microsoft Dynamics, NetSuite, Odoo

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/si/erp/systems` | List available ERP systems |
| `POST` | `/api/v1/si/erp/connect` | Connect to ERP system |
| `POST` | `/api/v1/si/erp/sync` | Sync data from ERP |
| `GET` | `/api/v1/si/erp/invoices` | Extract invoices from ERP |
| `GET` | `/api/v1/si/erp/customers` | Extract customer data |
| `GET` | `/api/v1/si/erp/vendors` | Extract vendor data |
| `GET` | `/api/v1/si/erp/products` | Extract product catalog |
| `GET` | `/api/v1/si/erp/financial-data` | Extract financial data |

### Banking Integrations (`/api/v1/si/banking/`)

**Supported Providers**: Mono, Stitch, Unified Banking

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/si/banking/available-systems` | Available banking systems |
| `GET` | `/api/v1/si/banking/open-banking` | List Open Banking connections |
| `POST` | `/api/v1/si/banking/open-banking` | Create banking connection |
| `GET` | `/api/v1/si/banking/open-banking/{connection_id}` | Get connection details |
| `PUT` | `/api/v1/si/banking/open-banking/{connection_id}` | Update connection |
| `DELETE` | `/api/v1/si/banking/open-banking/{connection_id}` | Remove connection |

#### Transaction Data
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/si/banking/accounts` | List linked accounts |
| `GET` | `/api/v1/si/banking/transactions` | Get account transactions |
| `GET` | `/api/v1/si/banking/balances` | Get account balances |
| `POST` | `/api/v1/si/banking/sync` | Sync banking data |

### Payment Processor Integrations (`/api/v1/si/payments/`)

**Supported Processors**: Paystack, Flutterwave, Moniepoint

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/si/payments/processors` | Available payment processors |
| `POST` | `/api/v1/si/payments/connect` | Connect to payment processor |
| `GET` | `/api/v1/si/payments/transactions` | Get payment transactions |
| `POST` | `/api/v1/si/payments/sync` | Sync payment data |

### Business System Specifics

#### Accounting Systems (`/api/v1/si/accounting/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/si/accounting/systems` | Available accounting systems |
| `POST` | `/api/v1/si/accounting/connect` | Connect to accounting system |
| `GET` | `/api/v1/si/accounting/chart-of-accounts` | Get chart of accounts |
| `GET` | `/api/v1/si/accounting/transactions` | Get accounting transactions |

#### E-commerce Platforms (`/api/v1/si/ecommerce/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/si/ecommerce/platforms` | Available e-commerce platforms |
| `POST` | `/api/v1/si/ecommerce/connect` | Connect to e-commerce platform |
| `GET` | `/api/v1/si/ecommerce/orders` | Get e-commerce orders |
| `GET` | `/api/v1/si/ecommerce/products` | Get product catalog |

#### Inventory Management (`/api/v1/si/inventory/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/si/inventory/systems` | Available inventory systems |
| `POST` | `/api/v1/si/inventory/connect` | Connect to inventory system |
| `GET` | `/api/v1/si/inventory/items` | Get inventory items |
| `GET` | `/api/v1/si/inventory/movements` | Get inventory movements |

### Transaction Processing

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/si/transactions` | List processed transactions |
| `POST` | `/api/v1/si/transactions/process` | Process transaction batch |
| `GET` | `/api/v1/si/transactions/{transaction_id}` | Get transaction details |
| `GET` | `/api/v1/si/transactions/{transaction_id}/status` | Get processing status |
| `POST` | `/api/v1/si/transactions/bulk-import` | Bulk import transactions |

### Invoice Generation

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/si/invoices/generate` | Generate FIRS-compliant invoices |
| `GET` | `/api/v1/si/invoices/{invoice_id}` | Get generated invoice |
| `GET` | `/api/v1/si/invoices/batch/{batch_id}` | Get batch generation status |

### Compliance & Validation

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/si/compliance/validate` | Validate transaction compliance |
| `GET` | `/api/v1/si/compliance/reports/onboarding` | Get onboarding report |
| `GET` | `/api/v1/si/compliance/reports/transactions` | Get transaction compliance report |

### Data Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/si/data/export` | Export organization and transaction data |
| `POST` | `/api/v1/si/data/sync` | Sync data from connected business systems |

---

## Hybrid (Cross-Role) Endpoints

**Base Path**: `/api/v1/hybrid/`  
**Role Required**: System Integrator + Access Point Provider (or Administrator)

### Core Hybrid Services

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/hybrid/health` | Hybrid services health check |
| `GET` | `/api/v1/hybrid/status` | Hybrid status overview |
| `GET` | `/api/v1/hybrid/info` | Hybrid services information |
| `GET` | `/api/v1/hybrid/capabilities` | Available hybrid capabilities |

### Cross-Role Operations (`/api/v1/hybrid/cross-role/`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/hybrid/cross-role/capabilities` | Available cross-role operations |
| `POST` | `/api/v1/hybrid/cross-role/invoice-processing/initiate` | Start end-to-end invoice processing |
| `GET` | `/api/v1/hybrid/cross-role/invoice-processing/{process_id}/status` | Get processing status |
| `POST` | `/api/v1/hybrid/cross-role/taxpayer-workflows/initiate` | Start taxpayer integration workflow |
| `POST` | `/api/v1/hybrid/cross-role/compliance-coordination` | Coordinate compliance validation |
| `POST` | `/api/v1/hybrid/cross-role/data-synchronization` | Sync data between SI and APP |

### Shared Resources (`/api/v1/hybrid/shared/`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/hybrid/shared/configuration` | Shared configuration data |
| `GET` | `/api/v1/hybrid/shared/reference-data` | Common reference data |
| `GET` | `/api/v1/hybrid/shared/templates` | Shared document templates |
| `GET` | `/api/v1/hybrid/shared/lookup-tables` | Common lookup tables |

### Orchestration (`/api/v1/hybrid/orchestration/`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/hybrid/orchestration/workflows/execute` | Execute complex workflows |
| `GET` | `/api/v1/hybrid/orchestration/workflows/{workflow_id}/status` | Get workflow status |
| `POST` | `/api/v1/hybrid/orchestration/batch-processing` | Execute batch operations |

### Monitoring (`/api/v1/hybrid/monitoring/`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/hybrid/monitoring/health/overview` | System health overview |
| `GET` | `/api/v1/hybrid/monitoring/metrics/performance` | Cross-role performance metrics |
| `GET` | `/api/v1/hybrid/monitoring/alerts` | Active system alerts |
| `GET` | `/api/v1/hybrid/monitoring/audit-trails` | Cross-role audit trails |
| `GET` | `/api/v1/hybrid/monitoring/resource-utilization` | Resource usage metrics |

### Role Coordination

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/hybrid/coordination/check-access` | Check coordination access permissions |
| `GET` | `/api/v1/hybrid/coordination/available-operations` | Get available coordination operations |

---

## Response Format

### Standard Response Structure

```json
{
  "success": true,
  "action": "operation_completed",
  "api_version": "v1",
  "timestamp": "2024-12-31T00:00:00Z",
  "data": {
    // Response data here
  }
}
```

### Error Response Structure

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": "Additional error details"
  },
  "api_version": "v1",
  "timestamp": "2024-12-31T00:00:00Z"
}
```

---

## Error Codes

| HTTP Status | Error Code | Description |
|-------------|------------|-------------|
| `400` | `BAD_REQUEST` | Invalid request parameters |
| `401` | `UNAUTHORIZED` | Authentication required |
| `403` | `FORBIDDEN` | Insufficient permissions |
| `404` | `NOT_FOUND` | Resource not found |
| `409` | `CONFLICT` | Resource conflict |
| `422` | `VALIDATION_ERROR` | Data validation failed |
| `429` | `RATE_LIMITED` | Too many requests |
| `500` | `INTERNAL_ERROR` | Server error |
| `502` | `GATEWAY_ERROR` | External service error |
| `503` | `SERVICE_UNAVAILABLE` | Service temporarily unavailable |

---

## Notes

- **Authentication**: Most endpoints require JWT Bearer token authentication
- **Rate Limiting**: API calls are rate-limited to ensure system stability  
- **Versioning**: All endpoints use `/api/v1/` versioning structure
- **FIRS Integration**: Full compliance with Nigerian e-invoicing regulations
- **Business Systems**: Comprehensive integration with 50+ business system types
- **Monitoring**: Built-in monitoring and observability across all operations
- **Compliance Standards**: Full support for UBL, PEPPOL, ISO 20022, ISO 27001, GDPR/NDPA, WCO HS, and LEI

---

**Total Endpoints**: 150+ endpoints across all service categories

**Documentation Version**: 1.0.0  
**Generated**: December 2024