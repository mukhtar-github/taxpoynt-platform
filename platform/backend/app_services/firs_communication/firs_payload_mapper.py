"""FIRS payload mapper for APP transmission flows.

Standardises platform invoice structures into the canonical FIRS schema
documented in `platform/docs/architecture/FIRSInvoice_version.json` and the
reference transformer (`FIRS_Invoice_Transformer.js`).

The mapper is intentionally forgiving: it accepts partial payloads and fills
in required FIRS fields with sensible defaults so that APP validation and
submission paths always operate on a predictable shape.
"""

from __future__ import annotations

import copy
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Iterable, List, Optional, Tuple


def build_firs_invoice(invoice: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Return a FIRS-aligned invoice payload from a platform invoice."""

    if not isinstance(invoice, dict):
        return {}

    if _is_firs_payload(invoice):
        return _normalise_existing_firs_invoice(invoice)

    mapped = _map_to_intermediate(invoice)
    return _build_firs_structure(mapped)


# ---------------------------------------------------------------------------
# Intermediate representation
# ---------------------------------------------------------------------------


class IntermediateInvoice(Dict[str, Any]):
    """Typed dict for clarity."""


def _map_to_intermediate(source: Dict[str, Any]) -> IntermediateInvoice:
    invoice_number = _first_match(
        source,
        "invoice_number",
        "invoiceNumber",
        "invoice_reference",
        "invoiceReference",
        "document_number",
        "documentNumber",
        "reference",
    ) or f"INV-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

    invoice_date = _normalise_date(
        _first_match(
            source,
            "invoice_date",
            "invoiceDate",
            "issue_date",
            "issueDate",
            "date",
            "created_at",
            "createdAt",
        )
    ) or datetime.utcnow().strftime("%Y-%m-%d")

    due_date = _normalise_date(
        _first_match(source, "due_date", "payment_due_date", "dueDate", "paymentDueDate")
    )

    invoice_type = _first_match(source, "invoice_type", "invoiceType", "invoice_type_code", "invoiceTypeCode")
    if invoice_type:
        invoice_type = str(invoice_type).upper()
    else:
        invoice_type = "STANDARD"

    currency = (_first_match(source, "currency", "currency_code", "currencyCode") or "NGN").upper()

    supplier = _extract_party(
        source,
        keys=("supplier", "seller", "accounting_supplier_party", "merchant", "company"),
        require_tin=True,
    )
    buyer = _extract_party(
        source,
        keys=("buyer", "customer", "accounting_customer_party", "customer_info", "recipient"),
        require_tin=False,
    )

    line_items = _normalise_line_items(
        source,
        _first_available_list(
            source,
            "line_items",
            "invoice_items",
            "items",
            "lines",
            "invoiceLines",
            "invoice_lines",
        ),
    )

    payment_terms = _first_match(source, "payment_terms", "paymentTerms") or "Net 30"
    payment_method = (_first_match(source, "payment_method", "paymentMethod") or "TRANSFER").upper()

    references = {
        "purchaseOrder": _first_match(source, "po_number", "purchase_order", "purchaseOrderNumber"),
        "contract": _first_match(source, "contract_reference", "contractRef"),
        "deliveryNote": _first_match(source, "delivery_note", "deliveryNoteNumber"),
        "previousInvoice": _first_match(source, "originalInvoice", "previousInvoiceNumber"),
    }

    withholding_tax = source.get("withholding_tax") or source.get("withholdingTax") or {}
    other_taxes = source.get("other_taxes") or source.get("otherTaxes") or []

    payment_reference = _first_match(source, "payment_reference", "paymentReference")

    delivery = source.get("delivery") or source.get("delivery_information") or {}

    return IntermediateInvoice(
        invoice_number=invoice_number,
        invoice_date=invoice_date,
        due_date=due_date,
        invoice_type=invoice_type,
        currency=currency,
        supplier=supplier,
        buyer=buyer,
        line_items=line_items,
        payment_terms=payment_terms,
        payment_method=payment_method,
        payment_reference=payment_reference,
        references=references,
        withholding_tax=withholding_tax,
        other_taxes=other_taxes,
        delivery=delivery,
    )


# ---------------------------------------------------------------------------
# Build FIRS structure
# ---------------------------------------------------------------------------


def _build_firs_structure(mapped: IntermediateInvoice) -> Dict[str, Any]:
    subtotal, total_vat, total_discount, total_payable = _compute_totals(mapped["line_items"])

    firs_invoice = {
        "version": "1.0",
        "standard": "BIS_Billing_3.0_UBL",
        "documentMetadata": {
            "invoiceNumber": mapped["invoice_number"],
            "invoiceDate": mapped["invoice_date"],
            "invoiceType": mapped["invoice_type"],
            "currencyCode": mapped["currency"],
            "documentStatus": "ISSUED",
            "dueDate": mapped.get("due_date") or _default_due_date(mapped["invoice_date"]),
            "taxPointDate": mapped["invoice_date"],
            "issueTime": datetime.utcnow().strftime("%H:%M:%S"),
        },
        "supplierInformation": _build_supplier(mapped["supplier"]),
        "buyerInformation": _build_buyer(mapped["buyer"]),
        "lineItems": _build_line_items(mapped["line_items"]),
        "taxSummary": {
            "subtotal": subtotal,
            "totalDiscount": total_discount,
            "totalVAT": total_vat,
            "withholdingTax": mapped.get("withholding_tax") or {},
            "otherTaxes": mapped.get("other_taxes") or [],
            "totalPayable": total_payable,
        },
        "paymentInformation": {
            "paymentTerms": mapped.get("payment_terms"),
            "paymentMethod": mapped.get("payment_method"),
            "paymentReference": mapped.get("payment_reference"),
        },
        "additionalDocumentReferences": {
            "purchaseOrderNumber": mapped["references"].get("purchaseOrder"),
            "contractReference": mapped["references"].get("contract"),
            "deliveryNoteNumber": mapped["references"].get("deliveryNote"),
            "previousInvoiceNumber": mapped["references"].get("previousInvoice"),
        },
        "deliveryInformation": _build_delivery(mapped.get("delivery")),
        "digitalSignature": {},
        "auditTrail": {},
    }

    # Backwards-compatible aliases for legacy consumers
    firs_invoice["invoice_number"] = mapped["invoice_number"]
    firs_invoice["invoice_reference"] = mapped["invoice_number"]
    firs_invoice["invoice_date"] = mapped["invoice_date"]
    firs_invoice["currency_code"] = mapped["currency"]
    firs_invoice["total_amount"] = firs_invoice["taxSummary"]["totalPayable"]
    firs_invoice["vat_amount"] = firs_invoice["taxSummary"]["totalVAT"]
    firs_invoice["subtotal_amount"] = firs_invoice["taxSummary"]["subtotal"]
    firs_invoice["line_items"] = firs_invoice["lineItems"]

    return firs_invoice


def _build_supplier(supplier: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "tin": supplier.get("tin"),
        "cacNumber": supplier.get("cacNumber") or supplier.get("cac_number"),
        "name": supplier.get("name"),
        "tradeName": supplier.get("tradeName") or supplier.get("trade_name"),
        "address": _build_address(supplier.get("address"), default_country="NG"),
        "contact": _build_contact(supplier.get("contact")),
        "bankDetails": supplier.get("bankDetails") or supplier.get("bank_details") or {},
        "industryClassificationCode": supplier.get("industryClassificationCode")
        or supplier.get("industry_code"),
    }


def _build_buyer(buyer: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "tin": buyer.get("tin") or "",
        "cacNumber": buyer.get("cacNumber") or buyer.get("cac_number") or "",
        "name": buyer.get("name"),
        "tradeName": buyer.get("tradeName") or buyer.get("trade_name"),
        "address": _build_address(buyer.get("address")),
        "contact": _build_contact(buyer.get("contact")),
        "customerType": (buyer.get("customerType") or buyer.get("customer_type") or "B2B").upper(),
    }


def _build_address(address: Optional[Dict[str, Any]], default_country: str = "") -> Dict[str, Any]:
    if not isinstance(address, dict):
        address = {}
    return {
        "streetName": _first_match(address, "streetName", "street", "address_line_1", "line1"),
        "buildingNumber": _first_match(address, "buildingNumber", "building", "number"),
        "cityName": _first_match(address, "cityName", "city", "town"),
        "postalZone": _first_match(address, "postalZone", "postal_code", "zip", "zipcode"),
        "stateCode": _first_match(address, "stateCode", "state", "state_code", "region"),
        "countryCode": _first_match(address, "countryCode", "country", "country_code") or default_country,
    }


def _build_contact(contact: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not isinstance(contact, dict):
        contact = {}
    return {
        "telephone": _first_match(contact, "telephone", "phone", "phone_number"),
        "email": _first_match(contact, "email", "email_address"),
        "contactPerson": _first_match(contact, "contactPerson", "person", "contact_name"),
    }


def _build_line_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    enriched: List[Dict[str, Any]] = []
    for idx, item in enumerate(items, start=1):
        qty = _to_decimal(item.get("quantity")) or Decimal("1")
        unit_price = _to_decimal(item.get("unitPrice")) or Decimal("0")
        gross = _to_decimal(item.get("grossAmount")) or (qty * unit_price)
        discount = _to_decimal(item.get("discountAmount")) or Decimal("0")
        net = _to_decimal(item.get("netAmount")) or (gross - discount)
        vat_amount = _to_decimal(item.get("vatAmount")) or Decimal("0")
        total = _to_decimal(item.get("totalAmount")) or (net + vat_amount)
        vat_rate = item.get("vatRate")
        if vat_rate is None:
            vat_rate = _resolve_vat_rate(vat_amount, net)
        vat_category = "ZERO_RATED" if vat_amount == 0 else "STANDARD"

        enriched.append(
            {
                "lineNumber": idx,
                "productCode": item.get("productCode") or item.get("item_code") or item.get("sku"),
                "productDescription": item.get("productDescription") or "Item",
                "hscode": item.get("hscode") or item.get("hs_code"),
                "quantity": float(qty),
                "unitOfMeasure": (item.get("unitOfMeasure") or "EA").upper(),
                "unitPrice": float(unit_price),
                "grossAmount": float(gross),
                "discountAmount": float(discount),
                "discountRate": float(_resolve_discount_rate(discount, gross)),
                "netAmount": float(net),
                "vatCategory": vat_category,
                "vatRate": vat_rate,
                "vatAmount": float(vat_amount),
                "totalAmount": float(total),
                "otherCharges": item.get("otherCharges") or [],
            }
        )

    return enriched


def _build_delivery(delivery: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not isinstance(delivery, dict):
        delivery = {}
    return {
        "deliveryDate": _normalise_date(delivery.get("deliveryDate") or delivery.get("date")),
        "deliveryAddress": _build_address(delivery.get("address") or {}, default_country="NG"),
        "deliveryTerms": delivery.get("terms"),
        "shippingMarks": delivery.get("shippingMarks"),
    }


# ---------------------------------------------------------------------------
# Existing FIRS payload normalisation
# ---------------------------------------------------------------------------


def _is_firs_payload(invoice: Dict[str, Any]) -> bool:
    return "documentMetadata" in invoice and "lineItems" in invoice


def _normalise_existing_firs_invoice(invoice: Dict[str, Any]) -> Dict[str, Any]:
    payload = copy.deepcopy(invoice)
    metadata = payload.setdefault("documentMetadata", {})
    metadata.setdefault("invoiceNumber", metadata.get("invoice_number"))
    metadata.setdefault("invoiceDate", _normalise_date(metadata.get("invoiceDate") or metadata.get("invoice_date")))
    metadata.setdefault("invoiceType", (metadata.get("invoiceType") or "STANDARD").upper())
    metadata.setdefault("currencyCode", (metadata.get("currencyCode") or "NGN").upper())
    metadata.setdefault("dueDate", metadata.get("dueDate") or _default_due_date(metadata.get("invoiceDate")))
    metadata.setdefault("taxPointDate", metadata.get("invoiceDate"))
    metadata.setdefault("documentStatus", metadata.get("documentStatus") or "ISSUED")

    payload.setdefault("supplierInformation", {})
    payload["supplierInformation"]["address"] = _build_address(payload["supplierInformation"].get("address"), "NG")
    payload["supplierInformation"]["contact"] = _build_contact(payload["supplierInformation"].get("contact"))

    payload.setdefault("buyerInformation", {})
    payload["buyerInformation"]["address"] = _build_address(payload["buyerInformation"].get("address"))
    payload["buyerInformation"]["contact"] = _build_contact(payload["buyerInformation"].get("contact"))

    payload["lineItems"] = _build_line_items(payload.get("lineItems", []))

    subtotal, total_vat, total_discount, total_payable = _compute_totals(payload["lineItems"])
    tax_summary = payload.setdefault("taxSummary", {})
    tax_summary.setdefault("subtotal", subtotal)
    tax_summary.setdefault("totalDiscount", total_discount)
    tax_summary.setdefault("totalVAT", total_vat)
    tax_summary.setdefault("otherTaxes", tax_summary.get("otherTaxes") or [])
    tax_summary.setdefault("totalPayable", total_payable)

    payment_info = payload.setdefault("paymentInformation", {})
    payment_info.setdefault("paymentTerms", payment_info.get("paymentTerms") or "Net 30")
    payment_info.setdefault("paymentMethod", (payment_info.get("paymentMethod") or "TRANSFER").upper())

    payload.setdefault("additionalDocumentReferences", {})
    payload.setdefault("deliveryInformation", _build_delivery(payload.get("deliveryInformation")))
    payload.setdefault("digitalSignature", payload.get("digitalSignature") or {})
    payload.setdefault("auditTrail", payload.get("auditTrail") or {})

    payload.setdefault("version", payload.get("version") or "1.0")
    payload.setdefault("standard", payload.get("standard") or "BIS_Billing_3.0_UBL")

    payload["invoice_number"] = payload["documentMetadata"].get("invoiceNumber")
    payload["invoice_reference"] = payload["invoice_number"]
    payload["invoice_date"] = payload["documentMetadata"].get("invoiceDate")
    payload["currency_code"] = payload["documentMetadata"].get("currencyCode")
    payload["total_amount"] = payload["taxSummary"].get("totalPayable")
    payload["vat_amount"] = payload["taxSummary"].get("totalVAT")
    payload["subtotal_amount"] = payload["taxSummary"].get("subtotal")
    payload["line_items"] = payload.get("lineItems")

    return payload


# ---------------------------------------------------------------------------
# Totals helpers
# ---------------------------------------------------------------------------


def _compute_totals(items: List[Dict[str, Any]]) -> Tuple[float, float, float, float]:
    subtotal = Decimal("0")
    total_vat = Decimal("0")
    total_discount = Decimal("0")

    for item in items:
        net = _to_decimal(item.get("netAmount")) or Decimal("0")
        vat = _to_decimal(item.get("vatAmount")) or Decimal("0")
        discount = _to_decimal(item.get("discountAmount")) or Decimal("0")
        subtotal += net
        total_vat += vat
        total_discount += discount

    total_payable = subtotal + total_vat

    return (
        float(subtotal),
        float(total_vat),
        float(total_discount),
        float(total_payable),
    )


def _default_due_date(invoice_date: Optional[str]) -> str:
    try:
        dt = datetime.strptime(invoice_date or datetime.utcnow().strftime("%Y-%m-%d"), "%Y-%m-%d")
    except ValueError:
        dt = datetime.utcnow()
    return (dt + timedelta(days=30)).strftime("%Y-%m-%d")


# ---------------------------------------------------------------------------
# Extraction helpers
# ---------------------------------------------------------------------------


def _extract_party(
    source: Dict[str, Any], *, keys: Iterable[str], require_tin: bool
) -> Dict[str, Any]:
    for key in keys:
        data = source.get(key)
        if isinstance(data, dict):
            break
    else:
        data = {}

    party = copy.deepcopy(data)
    party.setdefault("name", _first_match(data, "name", "legal_name", "company_name"))
    party.setdefault("tin", _first_match(data, "tin", "tax_id", "taxId", "tax_identification_number"))
    party.setdefault("cacNumber", _first_match(data, "cac_number", "cacNumber"))
    if require_tin and not party.get("tin"):
        party["tin"] = ""  # placeholder to highlight missing value while maintaining shape

    address = data.get("address") or data.get("postal_address") or {}
    party["address"] = {
        "streetName": _first_match(address, "street", "streetName", "address_line_1", "line1"),
        "buildingNumber": _first_match(address, "building_number", "buildingNumber"),
        "cityName": _first_match(address, "city", "cityName"),
        "postalZone": _first_match(address, "postal_code", "postalZone", "zip"),
        "stateCode": _first_match(address, "state", "stateCode", "state_code"),
        "countryCode": (_first_match(address, "country", "countryCode", "country_code") or ("NG" if require_tin else "")),
    }

    contact = data.get("contact") or {}
    party["contact"] = {
        "telephone": _first_match(contact, "telephone", "phone", "phone_number"),
        "email": _first_match(contact, "email", "email_address"),
        "contactPerson": _first_match(contact, "contactPerson", "contact_person", "person"),
    }

    return party


def _normalise_line_items(source: Dict[str, Any], collection: Optional[Iterable[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    normalised: List[Dict[str, Any]] = []

    if isinstance(collection, list) and collection:
        for raw in collection:
            if not isinstance(raw, dict):
                continue
            quantity = _to_decimal(_first_match(raw, "quantity", "qty", "units")) or Decimal("1")
            unit_price = _to_decimal(
                _first_match(raw, "unitPrice", "unit_price", "price", "unit_amount", "amount_ex_vat")
            ) or Decimal("0")
            discount = _to_decimal(_first_match(raw, "discountAmount", "discount", "discount_amount")) or Decimal("0")
            gross = _to_decimal(_first_match(raw, "grossAmount", "gross_amount")) or (quantity * unit_price)
            net = _to_decimal(_first_match(raw, "netAmount", "net_amount")) or (gross - discount)
            vat_amount = _to_decimal(_first_match(raw, "vatAmount", "vat_amount", "tax_amount", "vat")) or Decimal("0")
            total = _to_decimal(_first_match(raw, "totalAmount", "total_amount", "line_total", "amount")) or (net + vat_amount)
            vat_rate = _first_match(raw, "vatRate", "vat_rate")

            normalised.append(
                {
                    "productDescription": raw.get("productDescription")
                    or raw.get("description")
                    or raw.get("name")
                    or "Item",
                    "productCode": raw.get("productCode") or raw.get("item_code") or raw.get("sku"),
                    "hscode": raw.get("hscode") or raw.get("hs_code"),
                    "quantity": quantity,
                    "unitPrice": unit_price,
                    "unitOfMeasure": (raw.get("unitOfMeasure") or raw.get("unit_of_measure") or "EA").upper(),
                    "discountAmount": discount,
                    "grossAmount": gross,
                    "netAmount": net,
                    "vatAmount": vat_amount,
                    "totalAmount": total,
                    "vatRate": float(vat_rate) if vat_rate is not None else None,
                    "otherCharges": raw.get("otherCharges") or raw.get("other_charges") or [],
                }
            )

    if normalised:
        return normalised

    total_amount = _to_decimal(_first_match(source, "total_amount", "total", "amount", "grand_total")) or Decimal("0")
    vat_amount = _to_decimal(_first_match(source, "vat_amount", "vat", "tax_amount", "tax")) or Decimal("0")
    net = total_amount - vat_amount

    return [
        {
            "productDescription": "Invoice Amount",
            "productCode": None,
            "hscode": None,
            "quantity": Decimal("1"),
            "unitPrice": net,
            "unitOfMeasure": "EA",
            "discountAmount": Decimal("0"),
            "grossAmount": net,
            "netAmount": net,
            "vatAmount": vat_amount,
            "totalAmount": total_amount,
            "vatRate": float(_resolve_vat_rate(vat_amount, net)) if net else 0.0,
            "otherCharges": [],
        }
    ]


def _first_available_list(source: Dict[str, Any], *keys: str) -> Optional[List[Dict[str, Any]]]:
    for key in keys:
        value = source.get(key)
        if isinstance(value, list) and value:
            return value
    return None


# ---------------------------------------------------------------------------
# Misc utilities
# ---------------------------------------------------------------------------


def _first_match(source: Optional[Dict[str, Any]], *keys: str) -> Optional[Any]:
    if not isinstance(source, dict):
        return None
    for key in keys:
        if key in source and source[key] not in (None, ""):
            return source[key]
    return None


def _normalise_date(value: Any) -> Optional[str]:
    if not value:
        return None
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")
    text = str(value)
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%Y%m%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f"):
        try:
            return datetime.strptime(text[: len(fmt)], fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).strftime("%Y-%m-%d")
    except ValueError:
        return None


def _to_decimal(value: Any) -> Optional[Decimal]:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    text = str(value).strip()
    if not text:
        return None
    try:
        return Decimal(text.replace(",", ""))
    except InvalidOperation:
        return None


def _resolve_vat_rate(vat_amount: Decimal, net_amount: Decimal) -> float:
    if vat_amount is None or net_amount in (None, Decimal("0")):
        return 0.0
    try:
        return float(round((vat_amount / net_amount) * Decimal("100"), 3))
    except (InvalidOperation, ZeroDivisionError):
        return 0.0


def _resolve_discount_rate(discount: Decimal, gross: Decimal) -> float:
    if not discount or not gross:
        return 0.0
    try:
        return float(round((discount / gross) * Decimal("100"), 3))
    except (InvalidOperation, ZeroDivisionError):
        return 0.0


__all__ = ["build_firs_invoice"]
