# TaxPoynt E-Invoice Platform

> Enterprise Nigerian e-invoicing and business integration platform serving as a certified FIRS Access Point Provider (APP)

[![Deploy Backend](https://github.com/mukhtar-github/taxpoynt-platform/actions/workflows/backend-deploy.yml/badge.svg)](https://github.com/mukhtar-github/taxpoynt-platform/actions/workflows/backend-deploy.yml)
[![Deploy Frontend](https://github.com/mukhtar-github/taxpoynt-platform/actions/workflows/frontend-deploy.yml/badge.svg)](https://github.com/mukhtar-github/taxpoynt-platform/actions/workflows/frontend-deploy.yml)
[![Security Scan](https://github.com/mukhtar-github/taxpoynt-platform/actions/workflows/security-scan.yml/badge.svg)](https://github.com/mukhtar-github/taxpoynt-platform/actions/workflows/security-scan.yml)

## 🚀 Overview

TaxPoynt is a comprehensive middleware service that facilitates seamless integration between financial software (ERP, CRM, POS) and Nigeria's Federal Inland Revenue Service (FIRS) for electronic invoicing compliance. As a certified Access Point Provider (APP), TaxPoynt handles the complexity of FIRS compliance while providing simple APIs for business integration.

## ✨ Key Features

- **🏢 Multi-Role Architecture**: APP, SI (System Integrator), and Hybrid service modes
- **🔗 30+ Business Integrations**: ERP, CRM, POS, Accounting systems
- **🛡️ FIRS Compliance**: Automated e-invoice validation and transmission
- **🔒 Enterprise Security**: ISO 27001 compliant with end-to-end encryption
- **📊 Real-time Analytics**: Comprehensive dashboards and reporting
- **🌐 Nigerian Localization**: Multi-language support with cultural optimization

## 🏗️ Architecture

```
platform/
├── frontend/              # Role-based UI interfaces
│   ├── app_interface/     # APP role dashboard
│   ├── si_interface/      # SI role dashboard  
│   ├── business_interface/# Business customer interface
│   └── shared_components/ # Reusable UI components
├── backend/               # Microservices architecture
│   ├── api_gateway/       # Request routing & authentication
│   ├── app_services/      # APP-specific services
│   ├── si_services/       # SI-specific services
│   ├── hybrid_services/   # Cross-role services
│   ├── core_platform/     # Shared platform services
│   └── external_integrations/ # Business system connectors
└── tests/                 # Comprehensive testing suite
```

### Universal Processor (Optional)
- The platform includes a universal transaction processing pipeline for standardized validation and readiness across all sources (ERP/CRM/POS/E‑commerce/Banking).
- Enable in SI generation with:
  - `export USE_UNIVERSAL_PROCESSOR=true`
- Odoo connector types supported end‑to‑end:
  - ERP: `ERP_ODOO`
  - CRM: `CRM_ODOO`
  - POS: `POS_ODOO`
  - E‑commerce: `ECOMMERCE_ODOO`
- Defaults: these Odoo customer‑facing types have slightly higher confidence thresholds (e.g., `ECOMMERCE_ODOO` > 0.7) to improve data quality for invoice generation.

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ and Python 3.11+
- PostgreSQL 14+ and Redis 6+
- FIRS API credentials (sandbox available)

### Development Setup

1. **Clone and Install**
   ```bash
   git clone https://github.com/mukhtar-github/taxpoynt-platform.git
   cd taxpoynt-platform
   cp .env.example .env  # Configure your environment
   ```

2. **Backend Setup**
   ```bash
   cd platform/backend
   pip install -r requirements.txt
   alembic upgrade head  # Database migrations
   uvicorn app.main:app --reload
   ```

   Optional: use async DB sessions in new endpoints (scaffold)
   ```python
   # Example FastAPI handler
   from fastapi import Depends
   from sqlalchemy.ext.asyncio import AsyncSession
   from core_platform.data_management.db_async import get_async_session

   async def handler(db: AsyncSession = Depends(get_async_session)):
       result = await db.execute("SELECT 1")
       return {"ok": True}
   ```

   Optional strictness for router validation (recommended during development):
   ```bash
   # Fail on unmapped operations at runtime
   export ROUTER_STRICT_OPS=true

   # Validate route→operation mapping at startup (best-effort)
   export ROUTER_VALIDATE_ON_STARTUP=true
   # Raise on mismatches during startup (useful in CI)
   export ROUTER_FAIL_FAST_ON_STARTUP=true
   ```

3. **Frontend Setup**
   ```bash
   cd platform/frontend
   npm install
   npm run dev
   ```

4. **Access Applications**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## 🏢 Service Modes

### APP (Access Point Provider)
- Direct FIRS API integration
- Compliance monitoring and reporting
- Multi-tenant invoice processing
- Regulatory audit trails

### SI (System Integrator)  
- Business system connectors
- Custom integration development
- White-label solutions
- Subscription management

### Hybrid
- Combined APP + SI capabilities
- Cross-role analytics
- Unified billing and reporting
- Enterprise deployment options

## 🔌 Supported Integrations

**ERP Systems**: Odoo, SAP, Oracle, Dynamics 365, NetSuite (focus on Odoo for SMEs)
**CRM Platforms**: Odoo CRM (Nigerian deployments)
**POS Systems**: Odoo POS (Nigerian deployments)
**E‑commerce**: Odoo Website/e‑commerce, Jumia
**Accounting**: Sage (regionally common)
**Financial Systems**: Nigerian banking APIs and processors (Paystack, Flutterwave, Interswitch, Mono)

## 🛡️ Compliance & Security

- **FIRS Certified APP**: Official Access Point Provider status
- **ISO 27001**: Information security management
- **NDPA Compliant**: Nigerian Data Protection Act
- **UBL Standards**: Universal Business Language format
- **End-to-end Encryption**: AES-256 encryption at rest and in transit

## 📊 Deployment

### Production (Recommended)
- **Frontend**: Vercel (automated via GitHub Actions)
- **Backend**: Railway (multi-service deployment)
- **Database**: PostgreSQL with Redis caching
- **Monitoring**: Integrated analytics and error tracking

### Environment Configuration
Copy `.env.example` to `.env` and configure:
- FIRS API credentials
- Database connections  
- Third-party integrations
- Security keys and certificates

## 📚 Documentation

- [API Documentation](./docs/api/) - Complete API reference
- [Integration Guides](./docs/integration/) - Business system connectors
- [Architecture Overview](./docs/architecture/) - System design and components
- [Deployment Guide](./docs/deployment/) - Production setup instructions

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines and code of conduct.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License
This project is licensed under the GNU Affero General Public License v3.0 (AGPL-3.0).  
See the [LICENSE](./LICENSE) file for details.

## 🆘 Support

- **Documentation**: [docs.taxpoynt.com](https://docs.taxpoynt.com)
- **Community**: [GitHub Discussions](https://github.com/mukhtar-github/taxpoynt-platform/discussions)
- **Issues**: [GitHub Issues](https://github.com/mukhtar-github/taxpoynt-platform/issues)
- **Enterprise Support**: support@taxpoynt.com

---

<div align="center">
  <strong>Making Nigerian e-invoicing compliance simple for every business</strong>
  <br>
  Built with ❤️ for the Nigerian business community
</div>
