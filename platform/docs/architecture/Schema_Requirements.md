# Schema Requirements
I'll help you understand how to create a standardized FIRS invoice schema for transforming invoices into a compliant structure. Let me search for the most current FIRS requirements.Based on the latest FIRS requirements for Nigeria's e-invoicing mandate, I'll create a standardized invoice schema structure for you. Nigeria has adopted the BIS Billing 3.0 Universal Business Language (UBL) schema, which requires 55 mandatory fields across eight categories and supports both XML and JSON formatsI'll also create a transformation implementation that shows how to convert your existing invoices into this FIRS-compliant format:## Key Points About FIRS Invoice Standardization

Based on the current FIRS e-invoicing mandate rolling out in Nigeria:

### **Schema Requirements**
Nigeria has adopted the BIS Billing 3.0 Universal Business Language (UBL) schema with 55 mandatory fields across eight categories, supporting both XML and JSON formats. The system uses a pre-clearance model where invoices must first be validated by the FIRSMBS system before being delivered to buyers.

### **Implementation Timeline**
- Large taxpayers: Pilot phase from July 2025, mandatory from August 2025
- Medium and small enterprises: Required from January 2026

### **How to Use the Schema**

1. **Structure Your Data**: Use the first artifact (FIRS Standardized Invoice Schema) as your template. It includes all required fields organized into 8 main categories:
   - Document metadata
   - Supplier information
   - Buyer information
   - Line items with VAT calculations
   - Tax summary
   - Payment information
   - Additional references
   - Digital signature and audit trail

2. **Transform Existing Invoices**: Use the second artifact (FIRS Invoice Transformer) to convert your existing invoice formats. The transformer:
   - Accepts multiple input formats (custom, QuickBooks, SAP, Excel)
   - Validates all mandatory fields
   - Automatically calculates VAT at 7.5%
   - Handles B2B, B2C, and government transactions differently
   - Generates the required digital signature

3. **API Integration**: Submit invoices via the FIRS MBS Portal or integrate with the FIRS MBS e-invoice API using the endpoint structure shown in the schema.

### **Critical Compliance Points**

- **B2B Transactions**: Must include buyer's TIN
- **B2C Transactions**: Simplified buyer information but still require reporting
- **VAT Calculation**: Standard rate is 7.5% (some exemptions apply)
- **Unique Identifier**: Each validated invoice receives a unique FIRS identifier
- **Withholding Tax**: Applies to government contracts (typically 5%)

The transformer I've provided handles these requirements automatically and includes validation to ensure compliance before submission to FIRS.

