"""
UBL Schema Validator

Validates documents against UBL (Universal Business Language) schemas.
Extracted from odoo_ubl_validator.py - provides granular UBL schema validation.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple, Union
from decimal import Decimal
from datetime import datetime
import re

from .bis_mandatory_fields import BIS_MANDATORY_FIELD_SPECS, get_value_by_path

logger = logging.getLogger(__name__)


class UBLValidator:
    """
    Validates invoice documents against UBL schema requirements.
    Focuses specifically on BIS Billing 3.0 UBL format compliance.
    """
    
    def __init__(self):
        self.mandatory_field_specs = BIS_MANDATORY_FIELD_SPECS
        self.required_fields = self._get_required_fields()
        self.field_formats = self._get_field_formats()
        self.currency_codes = self._get_valid_currency_codes()
        self.country_codes = self._get_valid_country_codes()
    
    def validate_ubl_document(self, document: Dict[str, Any]) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Validate a complete UBL document against schema requirements.
        
        Args:
            document: UBL document to validate
            
        Returns:
            Tuple of (is_valid, validation_errors)
        """
        validation_errors = []
        
        try:
            # Ensure mandatory BIS fields exist
            mandatory_errors = self._validate_mandatory_fields(document)
            validation_errors.extend(mandatory_errors)

            # Validate invoice structure
            invoice_errors = self._validate_invoice_structure(document)
            validation_errors.extend(invoice_errors)
            
            # Validate supplier party
            if "accounting_supplier_party" in document:
                supplier_errors = self._validate_supplier_party(document["accounting_supplier_party"])
                validation_errors.extend(supplier_errors)
            
            # Validate customer party
            if "accounting_customer_party" in document:
                customer_errors = self._validate_customer_party(document["accounting_customer_party"])
                validation_errors.extend(customer_errors)
            
            # Validate invoice lines
            if "invoice_lines" in document:
                line_errors = self._validate_invoice_lines(document["invoice_lines"])
                validation_errors.extend(line_errors)
            
            # Validate tax information
            if "tax_total" in document:
                tax_errors = self._validate_tax_total(document["tax_total"])
                validation_errors.extend(tax_errors)
            
            # Validate monetary totals
            if "legal_monetary_total" in document:
                total_errors = self._validate_monetary_total(document["legal_monetary_total"])
                validation_errors.extend(total_errors)
            
            is_valid = len(validation_errors) == 0
            return is_valid, validation_errors
            
        except Exception as e:
            logger.error(f"Error validating UBL document: {e}")
            validation_errors.append({
                "field": "document",
                "error": "VALIDATION_ERROR",
                "message": f"Document validation failed: {str(e)}",
                "severity": "error"
            })
            return False, validation_errors

    def _validate_mandatory_fields(self, document: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Verify presence of all mandatory BIS Billing fields."""

        errors: List[Dict[str, Any]] = []

        for spec in self.mandatory_field_specs:
            value = get_value_by_path(document, spec.path)

            is_missing = value is None
            if isinstance(value, str) and spec.default != "":
                is_missing = is_missing or len(value.strip()) == 0

            if is_missing:
                errors.append(
                    {
                        "field": spec.path,
                        "error": "MISSING_REQUIRED_FIELD",
                        "message": f"{spec.label} is required for BIS Billing 3.0 compliance",
                        "severity": "error",
                    }
                )

        return errors

    def _validate_invoice_structure(self, document: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate main invoice structure and required fields"""
        errors: List[Dict[str, Any]] = []

        invoice_number = document.get("invoice_number")
        if invoice_number and not self._validate_invoice_number_format(invoice_number):
            errors.append(
                {
                    "field": "invoice_number",
                    "error": "INVALID_FORMAT",
                    "message": "Invoice number format is invalid",
                    "severity": "error",
                }
            )

        invoice_date = document.get("invoice_date")
        if invoice_date and not self._validate_date_format(invoice_date):
            errors.append(
                {
                    "field": "invoice_date",
                    "error": "INVALID_DATE_FORMAT",
                    "message": "Invoice date format is invalid (expected: YYYY-MM-DD)",
                    "severity": "error",
                }
            )

        currency_code = document.get("currency_code")
        if currency_code and currency_code not in self.currency_codes:
            errors.append(
                {
                    "field": "currency_code",
                    "error": "INVALID_CURRENCY",
                    "message": f"Invalid currency code: {currency_code}",
                    "severity": "error",
                }
            )

        return errors
    
    def _validate_supplier_party(self, supplier: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate supplier party information"""
        errors: List[Dict[str, Any]] = []

        party = supplier.get("party") if isinstance(supplier, dict) else {}
        if not party:
            errors.append(
                {
                    "field": "accounting_supplier_party.party",
                    "error": "MISSING_SUPPLIER_PARTY",
                    "message": "Supplier party information is required",
                    "severity": "error",
                }
            )
            return errors

        party_names = party.get("party_name", [])
        if not any(isinstance(entry, dict) and entry.get("name") for entry in party_names):
            errors.append(
                {
                    "field": "accounting_supplier_party.party.party_name",
                    "error": "EMPTY_PARTY_NAME",
                    "message": "Supplier party name cannot be empty",
                    "severity": "error",
                }
            )

        postal_address = party.get("postal_address")
        if postal_address:
            errors.extend(self._validate_postal_address(postal_address, "supplier"))
        else:
            errors.append(
                {
                    "field": "accounting_supplier_party.party.postal_address",
                    "error": "MISSING_ADDRESS_FIELD",
                    "message": "Supplier postal address is required",
                    "severity": "error",
                }
            )

        tax_scheme = party.get("party_tax_scheme")
        if tax_scheme:
            errors.extend(self._validate_party_tax_scheme(tax_scheme, "supplier"))
        else:
            errors.append(
                {
                    "field": "accounting_supplier_party.party.party_tax_scheme",
                    "error": "MISSING_TAX_SCHEME",
                    "message": "Supplier tax scheme information is required",
                    "severity": "error",
                }
            )

        legal_entities = party.get("party_legal_entity") or []
        if not legal_entities:
            errors.append(
                {
                    "field": "accounting_supplier_party.party.party_legal_entity",
                    "error": "MISSING_LEGAL_ENTITY",
                    "message": "Supplier legal entity details are required",
                    "severity": "error",
                }
            )
        else:
            for index, entity in enumerate(legal_entities):
                registration_name = entity.get("registration_name") if isinstance(entity, dict) else None
                if not registration_name or not str(registration_name).strip():
                    errors.append(
                        {
                            "field": f"accounting_supplier_party.party.party_legal_entity[{index}].registration_name",
                            "error": "MISSING_LEGAL_ENTITY_NAME",
                            "message": "Supplier legal entity registration name is required",
                            "severity": "error",
                        }
                    )
                company_id = entity.get("company_id") if isinstance(entity, dict) else None
                if not company_id or not str(company_id).strip():
                    errors.append(
                        {
                            "field": f"accounting_supplier_party.party.party_legal_entity[{index}].company_id",
                            "error": "MISSING_LEGAL_ENTITY_ID",
                            "message": "Supplier legal entity registration identifier is required",
                            "severity": "error",
                        }
                    )

        return errors
    
    def _validate_customer_party(self, customer: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate customer party information"""
        errors: List[Dict[str, Any]] = []

        party = customer.get("party") if isinstance(customer, dict) else {}
        if not party:
            errors.append(
                {
                    "field": "accounting_customer_party.party",
                    "error": "MISSING_CUSTOMER_PARTY",
                    "message": "Customer party information is required",
                    "severity": "error",
                }
            )
            return errors

        party_names = party.get("party_name", [])
        if not any(isinstance(entry, dict) and entry.get("name") for entry in party_names):
            errors.append(
                {
                    "field": "accounting_customer_party.party.party_name",
                    "error": "EMPTY_PARTY_NAME",
                    "message": "Customer party name cannot be empty",
                    "severity": "error",
                }
            )

        postal_address = party.get("postal_address")
        if postal_address:
            errors.extend(self._validate_postal_address(postal_address, "customer"))
        else:
            errors.append(
                {
                    "field": "accounting_customer_party.party.postal_address",
                    "error": "MISSING_ADDRESS_FIELD",
                    "message": "Customer postal address is required",
                    "severity": "error",
                }
            )

        tax_scheme = party.get("party_tax_scheme")
        if tax_scheme:
            errors.extend(self._validate_party_tax_scheme(tax_scheme, "customer"))
        else:
            errors.append(
                {
                    "field": "accounting_customer_party.party.party_tax_scheme",
                    "error": "MISSING_TAX_SCHEME",
                    "message": "Customer tax scheme information is required",
                    "severity": "warning",
                }
            )

        return errors
    
    def _validate_invoice_lines(self, lines: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate invoice line items"""
        errors: List[Dict[str, Any]] = []

        if not lines:
            errors.append(
                {
                    "field": "invoice_lines",
                    "error": "NO_INVOICE_LINES",
                    "message": "Invoice must contain at least one line item",
                    "severity": "error",
                }
            )
            return errors

        for index, line in enumerate(lines):
            line_prefix = f"invoice_lines[{index}]"

            quantity_info = line.get("invoiced_quantity", {})
            quantity_value = quantity_info.get("value") if isinstance(quantity_info, dict) else None
            if not self._validate_decimal_positive(quantity_value):
                errors.append(
                    {
                        "field": f"{line_prefix}.invoiced_quantity.value",
                        "error": "INVALID_QUANTITY",
                        "message": "Invoiced quantity must be a positive number",
                        "severity": "error",
                    }
                )

            price_info = line.get("price", {})
            price_amount = price_info.get("price_amount") if isinstance(price_info, dict) else {}
            price_value = price_amount.get("value") if isinstance(price_amount, dict) else None
            if not self._validate_decimal_non_negative(price_value):
                errors.append(
                    {
                        "field": f"{line_prefix}.price.price_amount.value",
                        "error": "INVALID_PRICE",
                        "message": "Line unit price must be non-negative",
                        "severity": "error",
                    }
                )

            extension_amount = line.get("line_extension_amount", {})
            extension_value = extension_amount.get("value") if isinstance(extension_amount, dict) else None
            if not self._validate_decimal_non_negative(extension_value):
                errors.append(
                    {
                        "field": f"{line_prefix}.line_extension_amount.value",
                        "error": "INVALID_AMOUNT",
                        "message": "Line extension amount must be non-negative",
                        "severity": "error",
                    }
                )

            item_info = line.get("item", {})
            if not isinstance(item_info, dict) or not item_info.get("name"):
                errors.append(
                    {
                        "field": f"{line_prefix}.item.name",
                        "error": "MISSING_ITEM_NAME",
                        "message": "Invoice line item name is required",
                        "severity": "error",
                    }
                )

            tax_total = line.get("tax_total", {})
            if isinstance(tax_total, dict):
                tax_amount = tax_total.get("tax_amount", {})
                tax_value = tax_amount.get("value") if isinstance(tax_amount, dict) else None
                if not self._validate_decimal_non_negative(tax_value):
                    errors.append(
                        {
                            "field": f"{line_prefix}.tax_total.tax_amount.value",
                            "error": "INVALID_TAX_AMOUNT",
                            "message": "Line tax amount must be non-negative",
                            "severity": "error",
                        }
                    )

        return errors
    
    def _validate_tax_total(self, tax_total: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate tax total information"""
        errors: List[Dict[str, Any]] = []

        tax_amount = tax_total.get("tax_amount", {})
        tax_value = tax_amount.get("value") if isinstance(tax_amount, dict) else None
        if not self._validate_decimal_non_negative(tax_value):
            errors.append(
                {
                    "field": "tax_total.tax_amount.value",
                    "error": "INVALID_TAX_AMOUNT",
                    "message": "Tax amount must be non-negative",
                    "severity": "error",
                }
            )

        tax_subtotals = tax_total.get("tax_subtotals", [])
        for index, subtotal in enumerate(tax_subtotals):
            taxable_amount = subtotal.get("taxable_amount", {}) if isinstance(subtotal, dict) else {}
            taxable_value = taxable_amount.get("value") if isinstance(taxable_amount, dict) else None
            if not self._validate_decimal_non_negative(taxable_value):
                errors.append(
                    {
                        "field": f"tax_total.tax_subtotals[{index}].taxable_amount.value",
                        "error": "INVALID_TAXABLE_AMOUNT",
                        "message": "Taxable amount must be non-negative",
                        "severity": "error",
                    }
                )

            subtotal_amount = subtotal.get("tax_amount", {}) if isinstance(subtotal, dict) else {}
            subtotal_value = subtotal_amount.get("value") if isinstance(subtotal_amount, dict) else None
            if not self._validate_decimal_non_negative(subtotal_value):
                errors.append(
                    {
                        "field": f"tax_total.tax_subtotals[{index}].tax_amount.value",
                        "error": "INVALID_TAX_AMOUNT",
                        "message": "Tax amount must be non-negative",
                        "severity": "error",
                    }
                )

        return errors
    
    def _validate_monetary_total(self, monetary_total: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate legal monetary total"""
        errors: List[Dict[str, Any]] = []

        monetary_fields = [
            "line_extension_amount",
            "tax_exclusive_amount",
            "tax_inclusive_amount",
            "payable_amount",
        ]

        for field in monetary_fields:
            amount_info = monetary_total.get(field, {})
            amount_value = amount_info.get("value") if isinstance(amount_info, dict) else None
            if amount_value is not None and not self._validate_decimal_non_negative(amount_value):
                errors.append(
                    {
                        "field": f"legal_monetary_total.{field}.value",
                        "error": "INVALID_MONETARY_AMOUNT",
                        "message": f"{field.replace('_', ' ')} must be non-negative",
                        "severity": "error",
                    }
                )

        return errors
    
    def _validate_postal_address(self, address: Dict[str, Any], party_type: str) -> List[Dict[str, Any]]:
        """Validate postal address structure"""
        errors: List[Dict[str, Any]] = []

        required_address_fields = ["street_name", "city_name", "country"]

        for field in required_address_fields:
            value = address.get(field)
            if field == "country":
                if not isinstance(value, dict) or not value.get("identification_code"):
                    errors.append(
                        {
                            "field": f"{party_type}.postal_address.country.identification_code",
                            "error": "MISSING_ADDRESS_FIELD",
                            "message": "Country identification code is required",
                            "severity": "error",
                        }
                    )
                    continue
            elif value is None or (isinstance(value, str) and not value.strip()):
                errors.append(
                    {
                        "field": f"{party_type}.postal_address.{field}",
                        "error": "MISSING_ADDRESS_FIELD",
                        "message": f"Required address field '{field}' is missing",
                        "severity": "error",
                    }
                )

        country = address.get("country")
        if isinstance(country, dict):
            country_code = country.get("identification_code")
            if country_code and country_code not in self.country_codes:
                errors.append(
                    {
                        "field": f"{party_type}.postal_address.country.identification_code",
                        "error": "INVALID_COUNTRY_CODE",
                        "message": f"Invalid country code: {country_code}",
                        "severity": "error",
                    }
                )

        return errors
    
    def _validate_party_tax_scheme(self, tax_scheme: Union[List[Dict[str, Any]], Dict[str, Any]], party_type: str) -> List[Dict[str, Any]]:
        """Validate party tax scheme information"""
        errors: List[Dict[str, Any]] = []

        schemes = tax_scheme if isinstance(tax_scheme, list) else [tax_scheme]
        if not schemes:
            errors.append(
                {
                    "field": f"{party_type}.party_tax_scheme",
                    "error": "MISSING_TAX_SCHEME",
                    "message": "At least one tax scheme entry is required",
                    "severity": "error",
                }
            )
            return errors

        for index, scheme in enumerate(schemes):
            if not isinstance(scheme, dict):
                errors.append(
                    {
                        "field": f"{party_type}.party_tax_scheme[{index}]",
                        "error": "INVALID_TAX_SCHEME",
                        "message": "Tax scheme entries must be objects",
                        "severity": "error",
                    }
                )
                continue

            company_id = scheme.get("company_id")
            if not company_id or not str(company_id).strip():
                errors.append(
                    {
                        "field": f"{party_type}.party_tax_scheme[{index}].company_id",
                        "error": "MISSING_TAX_ID",
                        "message": "Tax identification number (TIN) is required",
                        "severity": "error",
                    }
                )
            elif not self._validate_tin_format(str(company_id)):
                errors.append(
                    {
                        "field": f"{party_type}.party_tax_scheme[{index}].company_id",
                        "error": "INVALID_TIN_FORMAT",
                        "message": "Tax identification number format is invalid",
                        "severity": "warning",
                    }
                )

        return errors
    
    def _validate_invoice_number_format(self, invoice_number: str) -> bool:
        """Validate invoice number format"""
        if not invoice_number or len(invoice_number.strip()) == 0:
            return False
        # Invoice number should be alphanumeric with allowed special characters
        pattern = r'^[A-Za-z0-9\-_/]+$'
        return bool(re.match(pattern, invoice_number.strip()))
    
    def _validate_date_format(self, date_value: Any) -> bool:
        """Validate date format (YYYY-MM-DD)"""
        if isinstance(date_value, datetime):
            return True
        if isinstance(date_value, str):
            try:
                datetime.strptime(date_value, '%Y-%m-%d')
                return True
            except ValueError:
                return False
        return False
    
    def _validate_decimal_positive(self, value: Any) -> bool:
        """Validate that value is a positive decimal"""
        try:
            decimal_value = Decimal(str(value))
            return decimal_value > 0
        except (ValueError, TypeError):
            return False
    
    def _validate_decimal_non_negative(self, value: Any) -> bool:
        """Validate that value is a non-negative decimal"""
        try:
            decimal_value = Decimal(str(value))
            return decimal_value >= 0
        except (ValueError, TypeError):
            return False
    
    def _validate_tin_format(self, tin: str) -> bool:
        """Validate Nigerian TIN format"""
        if not tin:
            return False
        # Nigerian TIN format: 8-14 digits
        pattern = r'^\d{8,14}$'
        return bool(re.match(pattern, tin.strip()))
    
    def _get_required_fields(self) -> Dict[str, List[str]]:
        """Get required fields for UBL document validation"""
        return {
            "invoice": [
                "invoice_number",
                "invoice_type_code", 
                "invoice_date",
                "currency_code",
                "accounting_supplier_party",
                "accounting_customer_party",
                "invoice_lines",
                "tax_total",
                "legal_monetary_total"
            ],
            "supplier": [
                "party_name",
                "postal_address",
                "party_tax_scheme",
                "party_legal_entity"
            ],
            "customer": [
                "party_name",
                "postal_address"
            ],
            "invoice_line": [
                "id",
                "invoiced_quantity",
                "line_extension_amount",
                "item",
                "price"
            ],
            "item": [
                "name"
            ]
        }
    
    def _get_field_formats(self) -> Dict[str, str]:
        """Get field format patterns"""
        return {
            "invoice_number": r'^[A-Za-z0-9\-_/]+$',
            "date": r'^\d{4}-\d{2}-\d{2}$',
            "tin": r'^\d{8,14}$',
            "decimal": r'^\d+(\.\d{1,2})?$'
        }
    
    def _get_valid_currency_codes(self) -> List[str]:
        """Get valid ISO currency codes"""
        return [
            "NGN",  # Nigerian Naira
            "USD",  # US Dollar
            "EUR",  # Euro
            "GBP",  # British Pound
            "CAD",  # Canadian Dollar
            "AUD",  # Australian Dollar
            "JPY",  # Japanese Yen
            "CHF",  # Swiss Franc
            "CNY",  # Chinese Yuan
            "INR"   # Indian Rupee
        ]
    
    def _get_valid_country_codes(self) -> List[str]:
        """Get valid ISO country codes"""
        return [
            "NG",  # Nigeria
            "US",  # United States
            "GB",  # United Kingdom
            "DE",  # Germany
            "FR",  # France
            "CA",  # Canada
            "AU",  # Australia
            "JP",  # Japan
            "CH",  # Switzerland
            "CN",  # China
            "IN"   # India
        ]


# Global instance for easy access
ubl_validator = UBLValidator()
