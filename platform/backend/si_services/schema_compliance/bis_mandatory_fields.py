"""BIS Billing 3.0 mandatory field definitions and helpers.

This module centralises the list of mandatory fields required by the
BIS Billing 3.0 (UBL 2.1) specification and provides helpers for
getting/setting values via dot-path expressions.  The same definitions
are reused by the schema transformer (to populate defaults) and the
schema validator (to produce actionable error messages).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class MandatoryFieldSpec:
    """Description of a mandatory BIS Billing field."""

    path: str
    label: str
    default: Optional[Any] = None


def _split_path(path: str) -> List[str]:
    """Split a dotted path into components while keeping list indexes."""

    parts: List[str] = []
    for part in path.split('.'):
        if '[' in part and part.endswith(']'):
            base, index = part.split('[', 1)
            parts.append(base)
            parts.append(f"[{index}")
        else:
            parts.append(part)
    return parts


def get_value_by_path(data: Any, path: str) -> Any:
    """Retrieve a value from a nested structure using dot/list notation."""

    if path == '':
        return data

    current = data
    for component in _split_path(path):
        if component.startswith('['):
            if not isinstance(current, list):
                return None
            try:
                index = int(component[1:-1])
            except ValueError:
                return None
            if index >= len(current):
                return None
            current = current[index]
        else:
            if not isinstance(current, dict) or component not in current:
                return None
            current = current[component]
    return current


def _ensure_list_size(values: List[Any], index: int) -> None:
    """Grow *values* until *index* is valid by appending empty dicts."""

    while len(values) <= index:
        values.append({})


def set_value_by_path(data: Dict[str, Any], path: str, value: Any) -> None:
    """Set a value within a nested dict/list structure using a dotted path."""

    current: Any = data
    parts = _split_path(path)
    for i, component in enumerate(parts):
        is_last = i == len(parts) - 1

        if component.startswith('['):
            # list access
            if not isinstance(current, list):
                raise TypeError(f"Cannot index non-list at {component} for path {path}")
            index = int(component[1:-1])
            _ensure_list_size(current, index)
            if is_last:
                current[index] = value
            else:
                if not isinstance(current[index], (dict, list)):
                    current[index] = {}
                current = current[index]
        else:
            # dict access
            if not isinstance(current, dict):
                raise TypeError(f"Cannot traverse non-dict at {component} for path {path}")
            if is_last:
                current[component] = value
            else:
                if component not in current or not isinstance(current[component], (dict, list)):
                    # Determine whether next component is a list index
                    next_component = parts[i + 1]
                    current[component] = [] if next_component.startswith('[') else {}
                current = current[component]


BIS_MANDATORY_FIELD_SPECS: List[MandatoryFieldSpec] = [
    MandatoryFieldSpec("profile_id", "Profile identifier", "urn:fdc:peppol.eu:2017:poacc:billing:01:1.0"),
    MandatoryFieldSpec("customization_id", "Customization identifier", "urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:3.0"),
    MandatoryFieldSpec("id", "Internal invoice identifier"),
    MandatoryFieldSpec("uuid", "Invoice UUID"),
    MandatoryFieldSpec("invoice_number", "Invoice number"),
    MandatoryFieldSpec("invoice_type_code", "Invoice type code", "380"),
    MandatoryFieldSpec("invoice_date", "Invoice issue date"),
    MandatoryFieldSpec("due_date", "Invoice due date"),
    MandatoryFieldSpec("currency_code", "Document currency code", "NGN"),
    MandatoryFieldSpec("accounting_supplier_party.party.party_name[0].name", "Supplier name"),
    MandatoryFieldSpec("accounting_supplier_party.party.postal_address.street_name", "Supplier street"),
    MandatoryFieldSpec("accounting_supplier_party.party.postal_address.additional_street_name", "Supplier address line 2", ""),
    MandatoryFieldSpec("accounting_supplier_party.party.postal_address.city_name", "Supplier city"),
    MandatoryFieldSpec("accounting_supplier_party.party.postal_address.postal_zone", "Supplier postal code", ""),
    MandatoryFieldSpec("accounting_supplier_party.party.postal_address.country_subentity", "Supplier state", ""),
    MandatoryFieldSpec("accounting_supplier_party.party.postal_address.country.identification_code", "Supplier country code", "NG"),
    MandatoryFieldSpec("accounting_supplier_party.party.party_tax_scheme[0].company_id", "Supplier tax identifier"),
    MandatoryFieldSpec("accounting_supplier_party.party.party_tax_scheme[0].tax_scheme.id", "Supplier tax scheme code", "VAT"),
    MandatoryFieldSpec("accounting_supplier_party.party.party_legal_entity[0].registration_name", "Supplier legal name"),
    MandatoryFieldSpec("accounting_supplier_party.party.party_legal_entity[0].company_id", "Supplier registration number", "UNKNOWN"),
    MandatoryFieldSpec("accounting_supplier_party.party.contact.telephone", "Supplier telephone", "00000000000"),
    MandatoryFieldSpec("accounting_supplier_party.party.contact.electronic_mail", "Supplier email", "no-reply@example.com"),
    MandatoryFieldSpec("accounting_customer_party.party.party_name[0].name", "Customer name"),
    MandatoryFieldSpec("accounting_customer_party.party.postal_address.street_name", "Customer street", "UNKNOWN"),
    MandatoryFieldSpec("accounting_customer_party.party.postal_address.additional_street_name", "Customer address line 2", ""),
    MandatoryFieldSpec("accounting_customer_party.party.postal_address.city_name", "Customer city", "UNKNOWN"),
    MandatoryFieldSpec("accounting_customer_party.party.postal_address.postal_zone", "Customer postal code", ""),
    MandatoryFieldSpec("accounting_customer_party.party.postal_address.country_subentity", "Customer state", ""),
    MandatoryFieldSpec("accounting_customer_party.party.postal_address.country.identification_code", "Customer country code", "NG"),
    MandatoryFieldSpec("accounting_customer_party.party.contact.telephone", "Customer telephone", "N/A"),
    MandatoryFieldSpec("accounting_customer_party.party.contact.electronic_mail", "Customer email", "unknown@example.com"),
    MandatoryFieldSpec("invoice_lines[0].id", "First invoice line identifier"),
    MandatoryFieldSpec("invoice_lines[0].invoiced_quantity.value", "First invoice line quantity"),
    MandatoryFieldSpec("invoice_lines[0].invoiced_quantity.unit_code", "First invoice line unit code", "EA"),
    MandatoryFieldSpec("invoice_lines[0].line_extension_amount.value", "First invoice line extension amount"),
    MandatoryFieldSpec("invoice_lines[0].line_extension_amount.currency_id", "First invoice line currency", "NGN"),
    MandatoryFieldSpec("invoice_lines[0].item.name", "First invoice line item name"),
    MandatoryFieldSpec("invoice_lines[0].item.description", "First invoice line description", ""),
    MandatoryFieldSpec("invoice_lines[0].price.price_amount.value", "First invoice line unit price"),
    MandatoryFieldSpec("invoice_lines[0].price.price_amount.currency_id", "First invoice line price currency", "NGN"),
    MandatoryFieldSpec("invoice_lines[0].tax_total.tax_amount.value", "First invoice line tax amount", "0.00"),
    MandatoryFieldSpec("invoice_lines[0].tax_total.tax_amount.currency_id", "First invoice line tax currency", "NGN"),
    MandatoryFieldSpec("invoice_lines[0].tax_total.tax_category.id", "First invoice line tax category", "VAT"),
    MandatoryFieldSpec("invoice_lines[0].tax_total.tax_category.percent", "First invoice line tax rate", "7.5"),
    MandatoryFieldSpec("tax_total.tax_amount.value", "Invoice tax amount", "0.00"),
    MandatoryFieldSpec("tax_total.tax_amount.currency_id", "Invoice tax currency", "NGN"),
    MandatoryFieldSpec("tax_total.tax_subtotals[0].taxable_amount.value", "Invoice taxable amount", "0.00"),
    MandatoryFieldSpec("tax_total.tax_subtotals[0].taxable_amount.currency_id", "Invoice taxable currency", "NGN"),
    MandatoryFieldSpec("tax_total.tax_subtotals[0].tax_amount.value", "Invoice tax subtotal amount", "0.00"),
    MandatoryFieldSpec("tax_total.tax_subtotals[0].tax_amount.currency_id", "Invoice tax subtotal currency", "NGN"),
    MandatoryFieldSpec("tax_total.tax_subtotals[0].tax_category.id", "Invoice tax subtotal category", "VAT"),
    MandatoryFieldSpec("tax_total.tax_subtotals[0].tax_category.percent", "Invoice tax subtotal rate", "7.5"),
    MandatoryFieldSpec("legal_monetary_total.line_extension_amount.value", "Total line extension amount", "0.00"),
    MandatoryFieldSpec("legal_monetary_total.tax_inclusive_amount.value", "Total tax inclusive amount", "0.00"),
    MandatoryFieldSpec("legal_monetary_total.payable_amount.value", "Total payable amount", "0.00"),
    MandatoryFieldSpec("legal_monetary_total.payable_amount.currency_id", "Payable currency", "NGN"),
]


MANDATORY_FIELD_PATHS = [spec.path for spec in BIS_MANDATORY_FIELD_SPECS]


__all__ = [
    "MandatoryFieldSpec",
    "BIS_MANDATORY_FIELD_SPECS",
    "MANDATORY_FIELD_PATHS",
    "get_value_by_path",
    "set_value_by_path",
]

