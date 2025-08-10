"""
Odoo to FIRS UBL Mapping Utility

This module provides utilities for mapping Odoo invoice data to the FIRS e-Invoice
format using the UBL (Universal Business Language) standard. It ensures that all
required fields for FIRS compliance are correctly mapped and validated.
"""
import os
import json
import logging
from uuid import uuid4
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

class OdooFIRSMapper:
    """
    Maps Odoo invoice data to FIRS-compliant format.
    
    This class handles the transformation of Odoo invoice data to the
    format required by the FIRS e-Invoice API, ensuring that all required
    fields are present and correctly formatted.
    """
    
    def __init__(self):
        """Initialize the mapper with reference data."""
        self.reference_data_dir = os.path.join(settings.REFERENCE_DATA_DIR, 'firs')
        self._load_reference_data()
    
    def _load_reference_data(self):
        """Load reference data from JSON files."""
        try:
            # Load invoice types
            invoice_types_path = os.path.join(self.reference_data_dir, 'invoice_types.json')
            with open(invoice_types_path, 'r') as f:
                self.invoice_types = json.load(f).get('invoice_types', [])
            logger.info(f"Loaded {len(self.invoice_types)} invoice types from reference data")
            
            # Load currencies
            currencies_path = os.path.join(self.reference_data_dir, 'currencies.json')
            with open(currencies_path, 'r') as f:
                self.currencies = json.load(f).get('currencies', [])
            logger.info(f"Loaded {len(self.currencies)} currencies from reference data")
            
            # Load VAT exemptions
            vat_exemptions_path = os.path.join(self.reference_data_dir, 'vat_exemptions.json')
            with open(vat_exemptions_path, 'r') as f:
                self.vat_exemptions = json.load(f).get('vat_exemptions', [])
            logger.info(f"Loaded {len(self.vat_exemptions)} VAT exemptions from reference data")
            
        except Exception as e:
            logger.error(f"Error loading reference data: {str(e)}")
            # Initialize with empty lists if loading fails
            self.invoice_types = []
            self.currencies = []
            self.vat_exemptions = []
    
    def get_invoice_type_code(self, odoo_type: str) -> str:
        """
        Map Odoo invoice type to FIRS invoice type code.
        
        Args:
            odoo_type: Odoo invoice type ('out_invoice', 'out_refund', etc.)
            
        Returns:
            FIRS invoice type code
        """
        # Default mapping
        type_mapping = {
            'out_invoice': 'standard',
            'out_refund': 'credit_note',
            'in_invoice': 'standard',
            'in_refund': 'credit_note',
            'entry': 'standard'
        }
        
        firs_type = type_mapping.get(odoo_type, 'standard')
        
        # Validate against reference data if available
        if self.invoice_types:
            valid_types = [t.get('code') for t in self.invoice_types]
            if firs_type not in valid_types:
                logger.warning(f"Invoice type {firs_type} not found in reference data. Using 'standard' as fallback.")
                firs_type = 'standard'
        
        return firs_type
    
    def get_currency_code(self, odoo_currency: str) -> str:
        """
        Map Odoo currency to FIRS currency code.
        
        Args:
            odoo_currency: Odoo currency code
            
        Returns:
            FIRS currency code
        """
        # Default is NGN if not found
        default_currency = 'NGN'
        
        if not odoo_currency:
            return default_currency
            
        # If we have reference data, validate against it
        if self.currencies:
            valid_codes = [c.get('code') for c in self.currencies]
            if odoo_currency.upper() in valid_codes:
                return odoo_currency.upper()
            logger.warning(f"Currency {odoo_currency} not found in reference data. Using {default_currency} as fallback.")
        
        return default_currency
    
    def get_vat_exemption_code(self, odoo_tax_id: Optional[str], tax_rate: float) -> Optional[str]:
        """
        Map Odoo tax to FIRS VAT exemption code.
        
        Args:
            odoo_tax_id: Odoo tax ID
            tax_rate: Tax rate percentage
            
        Returns:
            FIRS VAT exemption code or None if not exempt
        """
        # If tax rate is 0, we need an exemption code
        if tax_rate == 0:
            # Default exemption code
            default_exemption = 'VAT-EXEMPT-1'
            
            # If we have reference data, find a suitable exemption
            if self.vat_exemptions:
                # First try to match by code if odoo_tax_id looks like an exemption code
                for exemption in self.vat_exemptions:
                    if exemption.get('code') == odoo_tax_id:
                        return exemption.get('code')
                
                # If not found, use the first exemption as default
                if self.vat_exemptions:
                    return self.vat_exemptions[0].get('code', default_exemption)
            
            return default_exemption
        
        # Not exempt
        return None
    
    def map_partner_to_party(self, partner_data: Dict[str, Any], is_supplier: bool = False) -> Dict[str, Any]:
        """
        Map Odoo partner data to FIRS party format.
        
        Args:
            partner_data: Odoo partner data
            is_supplier: Whether this partner is a supplier (for field naming)
            
        Returns:
            FIRS party data in the format required by FIRS API
        """
        # Extract TIN from VAT number if available
        tin = partner_data.get('vat', '').strip()
        # If TIN starts with "NG", remove it
        if tin and tin.upper().startswith('NG'):
            tin = tin[2:].strip()
        
        # Format Nigerian TIN (12345678-1234)
        if tin and len(tin) >= 8:
            # Extract base and suffix, handling various formats
            if '-' in tin:
                parts = tin.split('-')
                base_tin = parts[0].strip()[:8]
                suffix = parts[1].strip()[:4] if len(parts) > 1 else '0001'
            else:
                base_tin = tin[:8]
                suffix = tin[8:].strip()[:4] if len(tin) > 8 else '0001'
            
            tin = f"{base_tin}-{suffix}"
        elif not tin:
            # Use default TIN format if missing (FIRS requires TIN)
            tin = "TIN-" + ("000001" if is_supplier else "000002")
            logger.warning(f"Missing TIN for {'supplier' if is_supplier else 'customer'} {partner_data.get('name', '')}, using default: {tin}")
        
        # Extract and validate email (mandatory for FIRS)
        email = partner_data.get('email', '').strip()
        if not email:
            # Use a placeholder email if missing (FIRS requires email)
            email = f"{'supplier' if is_supplier else 'customer'}@taxpoynt.example.com"
            logger.warning(f"Missing email for {'supplier' if is_supplier else 'customer'} {partner_data.get('name', '')}, using placeholder: {email}")
        
        # Extract phone (format with country code for FIRS)
        phone = partner_data.get('phone', partner_data.get('mobile', '')).strip()
        if phone and not phone.startswith('+'):
            # Add Nigeria country code if missing
            phone = f"+234{phone.lstrip('0')}"
        
        # Extract address information
        address = partner_data.get('address', {})
        if not address and 'street' in partner_data:
            # If address is not a nested object, construct it from flat fields
            address = {
                'street': partner_data.get('street', ''),
                'street2': partner_data.get('street2', ''),
                'city': partner_data.get('city', ''),
                'state': partner_data.get('state_id', {}).get('name', '') if isinstance(partner_data.get('state_id'), dict) else partner_data.get('state', ''),
                'zip': partner_data.get('zip', ''),
                'country': partner_data.get('country_id', {}).get('code', 'NG') if isinstance(partner_data.get('country_id'), dict) else partner_data.get('country_code', 'NG')
            }
        
        # Get street name (mandatory for FIRS)
        street_name = address.get('street', '')
        if not street_name:
            street_name = "Unknown Street"
            logger.warning(f"Missing street address for {'supplier' if is_supplier else 'customer'} {partner_data.get('name', '')}, using placeholder")
        
        # Get city name (mandatory for FIRS)
        city_name = address.get('city', '')
        if not city_name:
            city_name = "Unknown City"
            logger.warning(f"Missing city for {'supplier' if is_supplier else 'customer'} {partner_data.get('name', '')}, using placeholder")
        
        # Get country code (mandatory for FIRS)
        country_code = address.get('country', 'NG')
        if len(country_code) > 2:
            # Try to extract ISO code if full country name is provided
            country_code = country_code[:2].upper()
        
        # Get postal code
        postal_zone = address.get('zip', '')
        
        # Format for FIRS API structure
        if is_supplier:
            party_type = "accounting_supplier_party"
        else:
            party_type = "accounting_customer_party"
        
        # Build party data according to FIRS API specifications
        party_data = {
            "party_name": partner_data.get('name', ''),
            "tin": tin,
            "email": email,
            "business_description": partner_data.get('business_description', f"{'Supplier' if is_supplier else 'Customer'} of goods and services")
        }
        
        # Add telephone if available
        if phone:
            party_data["telephone"] = phone
        
        # Add postal address
        party_data["postal_address"] = {
            "street_name": street_name,
            "city_name": city_name,
            "postal_zone": postal_zone,
            "country": country_code
        }
        
        return party_data
    
    def map_line_item(self, line_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map Odoo invoice line to FIRS line item according to BIS Billing 3.0 format.
        
        Args:
            line_data: Odoo invoice line data
            
        Returns:
            FIRS invoice line item formatted for API submission
        """
        # Extract line identification
        line_id = line_data.get('id', str(uuid4()))
        if isinstance(line_id, (int, float)):
            line_id = f"LINE-{line_id}"
        
        # Get item description
        description = line_data.get('name', '') or line_data.get('product_id', {}).get('name', '') if isinstance(line_data.get('product_id'), dict) else ''
        if not description:
            description = "Unnamed Item"
            logger.warning(f"Missing description for line item {line_id}, using placeholder")
        
        # Extract quantity information
        quantity = float(line_data.get('quantity', 1))
        if quantity <= 0:
            quantity = 1
            logger.warning(f"Invalid quantity for line item {line_id}, defaulting to 1")
        
        # Extract unit of measure
        uom = line_data.get('uom_id', {}).get('name', 'Unit') if isinstance(line_data.get('uom_id'), dict) else line_data.get('uom', 'EA')
        if not uom:
            uom = "EA"  # Each (standard UBL unit)
        
        # Extract price information
        unit_price = float(line_data.get('price_unit', 0.0))
        
        # Calculate line extension amount (quantity * unit price)
        line_extension_amount = unit_price * quantity
        
        # Extract tax information
        tax_rate = 0.0
        taxes = line_data.get('tax_ids', [])
        if taxes and isinstance(taxes, list):
            # Get the average tax rate if multiple taxes
            tax_sum = sum(tax.get('amount', 0) for tax in taxes if isinstance(tax, dict))
            tax_rate = tax_sum / len(taxes) if taxes else 0.0
        elif isinstance(taxes, dict):
            tax_rate = taxes.get('amount', 0.0)
        
        # If tax_rate is provided directly, use that
        if 'tax_rate' in line_data:
            tax_rate = line_data.get('tax_rate', 0.0)
        
        # Calculate tax amount
        tax_amount = line_extension_amount * (tax_rate / 100)
        
        # Calculate discount
        discount_percentage = float(line_data.get('discount', 0.0))
        discount_amount = (unit_price * quantity * discount_percentage / 100)
        
        # Determine tax scheme
        tax_scheme_id = "VAT"
        if tax_rate == 0:
            tax_id = line_data.get('tax_ids', [])
            if isinstance(tax_id, list) and tax_id and isinstance(tax_id[0], dict):
                tax_id = tax_id[0].get('id', '')
            exemption_code = self.get_vat_exemption_code(tax_id, tax_rate)
            if exemption_code:
                tax_scheme_id = exemption_code
        
        # Build line item in FIRS/UBL format
        invoice_line = {
            "id": str(line_id),
            "invoiced_quantity": quantity,
            "invoiced_quantity_unit_code": uom,
            "line_extension_amount": line_extension_amount,
            "item": {
                "name": description,
                "description": description
            },
            "price": {
                "price_amount": unit_price,
                "base_quantity": 1,
                "base_quantity_unit_code": uom
            }
        }
        
        # Add tax information if applicable
        if tax_rate > 0 or tax_scheme_id != "VAT":
            invoice_line["tax_total"] = {
                "tax_amount": tax_amount,
                "tax_subtotal": {
                    "taxable_amount": line_extension_amount,
                    "tax_amount": tax_amount,
                    "tax_category": {
                        "id": tax_scheme_id,
                        "percent": tax_rate,
                        "tax_scheme": {
                            "id": "FIRS"
                        }
                    }
                }
            }
        
        # Add allowance/charge for discounts if applicable
        if discount_percentage > 0 and discount_amount > 0:
            invoice_line["allowance_charge"] = {
                "charge_indicator": False,  # False = allowance (discount), True = charge
                "allowance_charge_reason": "Discount",
                "amount": discount_amount,
                "base_amount": line_extension_amount + discount_amount
            }
        
        return invoice_line
    
    def map_odoo_invoice_to_firs(self, odoo_invoice: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map Odoo invoice to FIRS invoice format according to API specification.
        
        Args:
            odoo_invoice: Odoo invoice data
            
        Returns:
            FIRS-compliant invoice data ready for API submission
        """
        # Extract basic invoice information
        invoice_number = odoo_invoice.get('name', '') or odoo_invoice.get('number', '')
        invoice_date = odoo_invoice.get('invoice_date', '') or odoo_invoice.get('date_invoice', '')
        
        # Format date if it's a datetime object or string
        if isinstance(invoice_date, datetime):
            invoice_date = invoice_date.strftime('%Y-%m-%d')
        elif isinstance(invoice_date, str) and 'T' in invoice_date:
            # Handle ISO format dates
            invoice_date = invoice_date.split('T')[0]
        
        # Format issue time
        issue_time = datetime.now().strftime('%H:%M:%S')
        if isinstance(odoo_invoice.get('create_date'), datetime):
            issue_time = odoo_invoice['create_date'].strftime('%H:%M:%S')
        
        # Generate IRN if not provided
        # IRN format: REF-HEXCODE-YYYYMMDD
        invoice_ref = invoice_number.replace('/', '').replace(' ', '').upper()
        if len(invoice_ref) > 8:
            invoice_ref = invoice_ref[:8]
        elif len(invoice_ref) < 3:
            invoice_ref = f"INV{invoice_ref}"
            
        hex_part = uuid4().hex[:8].upper()
        date_part = datetime.now().strftime('%Y%m%d')
        irn = f"{invoice_ref}-{hex_part}-{date_part}"
        
        # Get invoice type code
        odoo_type = odoo_invoice.get('type', 'out_invoice')
        invoice_type_code = "380"  # Commercial Invoice
        if odoo_type == 'out_refund':
            invoice_type_code = "381"  # Credit Note
        elif odoo_type == 'in_refund':
            invoice_type_code = "383"  # Debit Note
        
        # Get currency
        currency_code = odoo_invoice.get('currency_id', {}).get('name', 'NGN') if isinstance(odoo_invoice.get('currency_id'), dict) else odoo_invoice.get('currency', 'NGN')
        currency_code = self.get_currency_code(currency_code)
        
        # Map partners to parties
        partner_data = odoo_invoice.get('partner_id', {}) if isinstance(odoo_invoice.get('partner_id'), dict) else odoo_invoice.get('partner', {})
        company_data = odoo_invoice.get('company_id', {}) if isinstance(odoo_invoice.get('company_id'), dict) else odoo_invoice.get('company', {})
        
        # Get business ID (use company ID or generate one)
        business_id = str(company_data.get('id', uuid4()))
        
        # Process partners with proper FIRS formatting
        accounting_customer_party = self.map_partner_to_party(partner_data, is_supplier=False)
        accounting_supplier_party = self.map_partner_to_party(company_data, is_supplier=True)
        
        # Map line items
        invoice_lines = []
        lines = odoo_invoice.get('invoice_line_ids', []) or odoo_invoice.get('invoice_lines', []) or odoo_invoice.get('lines', [])
        
        for line in lines:
            mapped_line = self.map_line_item(line)
            if mapped_line:
                invoice_lines.append(mapped_line)
        
        # Calculate monetary totals
        total_line_extension = sum(float(line.get('line_extension_amount', 0)) for line in invoice_lines)
        total_tax_exclusive = total_line_extension
        total_tax_amount = sum(float(line.get('tax_amount', 0)) for line in invoice_lines)
        total_tax_inclusive = total_tax_exclusive + total_tax_amount
        
        # Build tax totals
        tax_totals = []
        if total_tax_amount > 0:
            tax_totals.append({
                "tax_amount": total_tax_amount,
                "tax_subtotal": [
                    {
                        "taxable_amount": total_tax_exclusive,
                        "tax_amount": total_tax_amount,
                        "tax_category": {
                            "id": "VAT",
                            "percent": (total_tax_amount / total_tax_exclusive * 100) if total_tax_exclusive > 0 else 0
                        }
                    }
                ]
            })
        
        # Get due date
        due_date = odoo_invoice.get('invoice_date_due', '') or odoo_invoice.get('date_due', '')
        if isinstance(due_date, datetime):
            due_date = due_date.strftime('%Y-%m-%d')
        elif not due_date:
            # Default to 30 days from invoice date
            try:
                invoice_date_obj = datetime.strptime(invoice_date, '%Y-%m-%d')
                due_date = (invoice_date_obj + timedelta(days=30)).strftime('%Y-%m-%d')
            except:
                due_date = invoice_date
        
        # Build the FIRS-compliant invoice structure
        firs_invoice = {
            "business_id": business_id,
            "irn": irn,
            "issue_date": invoice_date,
            "due_date": due_date,
            "issue_time": issue_time,
            "invoice_type_code": invoice_type_code,
            "payment_status": "PENDING",
            "document_currency_code": currency_code,
            "tax_currency_code": currency_code,
            "accounting_supplier_party": accounting_supplier_party,
            "accounting_customer_party": accounting_customer_party,
            "legal_monetary_total": {
                "line_extension_amount": total_line_extension,
                "tax_exclusive_amount": total_tax_exclusive,
                "tax_inclusive_amount": total_tax_inclusive,
                "payable_amount": total_tax_inclusive
            },
            "invoice_line": invoice_lines
        }
        
        # Add tax totals if applicable
        if tax_totals:
            firs_invoice["tax_total"] = tax_totals
        
        # Add payment means if available
        payment_term = odoo_invoice.get('payment_term_id', {}).get('name', '') if isinstance(odoo_invoice.get('payment_term_id'), dict) else odoo_invoice.get('payment_terms', '')
        if payment_term:
            firs_invoice["payment_terms_note"] = payment_term
            firs_invoice["payment_means"] = [{
                "payment_means_code": "30",  # Credit transfer
                "payment_due_date": due_date
            }]
        
        # Add notes if available
        notes = odoo_invoice.get('narration', '') or odoo_invoice.get('comment', '')
        if notes:
            firs_invoice["note"] = notes
        
        # Validate invoice has all required fields for FIRS
        self._validate_firs_invoice(firs_invoice)
        
        return firs_invoice
    
    def _validate_firs_invoice(self, invoice: Dict[str, Any]) -> None:
        """
        Validate that the FIRS invoice has all required fields according to FIRS API specification.
        
        Args:
            invoice: FIRS invoice data
            
        Raises:
            ValueError: If any required fields are missing
        """
        # List of required top-level fields for FIRS invoice
        required_fields = [
            'business_id', 
            'irn', 
            'issue_date', 
            'issue_time',
            'invoice_type_code',
            'document_currency_code',
            'accounting_supplier_party',
            'accounting_customer_party',
            'legal_monetary_total',
            'invoice_line'
        ]
        
        missing_fields = [field for field in required_fields if field not in invoice]
        
        if missing_fields:
            raise ValueError(f"FIRS invoice missing required fields: {', '.join(missing_fields)}")
        
        # Validate party information has required fields
        for party_type in ['accounting_supplier_party', 'accounting_customer_party']:
            party = invoice.get(party_type, {})
            party_required_fields = ['party_name', 'tin', 'email', 'postal_address']
            party_missing_fields = [field for field in party_required_fields if field not in party]
            
            if party_missing_fields:
                raise ValueError(f"{party_type.replace('_', ' ').title()} missing required fields: {', '.join(party_missing_fields)}")
            
            # Validate postal address has required fields
            address = party.get('postal_address', {})
            address_required_fields = ['street_name', 'city_name', 'country']
            address_missing_fields = [field for field in address_required_fields if field not in address]
            
            if address_missing_fields:
                raise ValueError(f"{party_type.replace('_', ' ').title()} postal address missing required fields: {', '.join(address_missing_fields)}")
        
        # Validate monetary totals
        monetary_total = invoice.get('legal_monetary_total', {})
        monetary_required_fields = ['line_extension_amount', 'tax_exclusive_amount', 'tax_inclusive_amount', 'payable_amount']
        monetary_missing_fields = [field for field in monetary_required_fields if field not in monetary_total]
        
        if monetary_missing_fields:
            raise ValueError(f"Legal monetary total missing required fields: {', '.join(monetary_missing_fields)}")
        
        # Validate invoice lines
        invoice_lines = invoice.get('invoice_line', [])
        if not invoice_lines:
            raise ValueError("Invoice must have at least one line item")
        
        for i, line in enumerate(invoice_lines):
            line_required_fields = ['id', 'invoiced_quantity', 'line_extension_amount', 'item', 'price']
            line_missing_fields = [field for field in line_required_fields if field not in line]
            
            if line_missing_fields:
                raise ValueError(f"Invoice line {i+1} missing required fields: {', '.join(line_missing_fields)}")
            
            # Validate item has required fields
            item = line.get('item', {})
            if not item.get('name'):
                raise ValueError(f"Invoice line {i+1} item missing required 'name' field")
            
            # Validate price has required fields
            price = line.get('price', {})
            if not isinstance(price.get('price_amount'), (int, float)):
                raise ValueError(f"Invoice line {i+1} price missing required 'price_amount' field")

# Create a default instance for easy importing
odoo_firs_mapper = OdooFIRSMapper()
