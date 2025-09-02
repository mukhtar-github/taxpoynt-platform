"""
Comprehensive FIRS Invoice Generator
====================================
Aggregates data from business systems (ERP, CRM, POS, E-commerce) and 
financial systems (Banking, Payment processors) to generate FIRS-compliant invoices.

This service implements the complete data convergence strategy for
SI (System Integrator) role invoice generation.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Any, Optional, Tuple
from uuid import UUID, uuid4
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

# Fixed imports - use relative imports instead of platform.backend
from core_platform.data_management.models.firs_submission import (
    FIRSSubmission, SubmissionStatus, ValidationStatus
)
from external_integrations.financial_systems.banking.open_banking.invoice_automation.firs_formatter import (
    FIRSFormatter, FormattingResult
)
# Conditional imports for connectors (graceful failure for missing connectors)
try:
    from external_integrations.business_systems.erp.sap_connector import SAPConnector
except ImportError:
    SAPConnector = None

try:
    from external_integrations.business_systems.erp.odoo_connector import OdooConnector
except ImportError:
    OdooConnector = None

try:
    from external_integrations.business_systems.crm.salesforce_connector import SalesforceConnector
except ImportError:
    SalesforceConnector = None

try:
    from external_integrations.business_systems.pos.square_connector import SquareConnector
except ImportError:
    SquareConnector = None

try:
    from external_integrations.business_systems.ecommerce.shopify_connector import ShopifyConnector
except ImportError:
    ShopifyConnector = None

try:
    from external_integrations.financial_systems.banking.mono_connector import MonoConnector
except ImportError:
    MonoConnector = None

try:
    from external_integrations.financial_systems.payments.paystack_connector import PaystackConnector
except ImportError:
    PaystackConnector = None

logger = logging.getLogger(__name__)


class DataSourceType(str, Enum):
    """Types of data sources for invoice generation."""
    ERP = "erp"
    CRM = "crm"
    POS = "pos"
    ECOMMERCE = "ecommerce"
    BANKING = "banking"
    PAYMENT = "payment"


class TransactionConfidence(str, Enum):
    """Confidence levels for auto-reconciled transactions."""
    HIGH = "high"      # 95%+
    MEDIUM = "medium"  # 85-94%
    LOW = "low"        # <85%


@dataclass
class BusinessTransactionData:
    """Unified transaction data structure from any business system."""
    id: str
    source_type: DataSourceType
    source_id: str
    transaction_id: str
    date: datetime
    customer_name: str
    customer_email: Optional[str]
    customer_tin: Optional[str]
    amount: Decimal
    currency: str
    description: str
    line_items: List[Dict[str, Any]]
    tax_amount: Decimal
    vat_rate: Decimal
    payment_status: str
    payment_method: Optional[str]
    confidence: float
    raw_data: Dict[str, Any]


@dataclass
class FIRSInvoiceGenerationRequest:
    """Request for generating FIRS-compliant invoices."""
    organization_id: UUID
    transaction_ids: List[str]
    invoice_type: str = "standard"
    consolidate: bool = False
    include_digital_signature: bool = True
    customer_overrides: Optional[Dict[str, str]] = None


@dataclass
class FIRSInvoiceGenerationResult:
    """Result of FIRS invoice generation."""
    success: bool
    invoices: List[Dict[str, Any]]
    errors: List[str]
    warnings: List[str]
    total_amount: Decimal
    irns_generated: List[str]


class ComprehensiveFIRSInvoiceGenerator:
    """
    Comprehensive FIRS invoice generator that aggregates data from
    all connected business and financial systems.
    """

    def __init__(
        self,
        db_session: AsyncSession,
        firs_formatter: FIRSFormatter
    ):
        self.db = db_session
        self.firs_formatter = firs_formatter
        
        # Initialize connectors for all supported systems (graceful handling of missing connectors)
        self.connectors = {
            DataSourceType.ERP: {
                'sap': SAPConnector() if SAPConnector else None,
                'odoo': OdooConnector() if OdooConnector else None
            },
            DataSourceType.CRM: {
                'salesforce': SalesforceConnector() if SalesforceConnector else None
            },
            DataSourceType.POS: {
                'square': SquareConnector() if SquareConnector else None
            },
            DataSourceType.ECOMMERCE: {
                'shopify': ShopifyConnector() if ShopifyConnector else None
            },
            DataSourceType.BANKING: {
                'mono': MonoConnector() if MonoConnector else None
            },
            DataSourceType.PAYMENT: {
                'paystack': PaystackConnector() if PaystackConnector else None,
                'flutterwave': None  # To be implemented
            }
        }

        self.stats = {
            'transactions_processed': 0,
            'invoices_generated': 0,
            'total_amount_processed': Decimal('0'),
            'errors_encountered': 0
        }

    async def aggregate_business_data(
        self,
        organization_id: UUID,
        date_range: Optional[Tuple[datetime, datetime]] = None
    ) -> List[BusinessTransactionData]:
        """
        Aggregate transaction data from all connected business and financial systems.
        
        Args:
            organization_id: Organization ID
            date_range: Optional date range for transactions
            
        Returns:
            List of unified transaction data
        """
        logger.info(f"Aggregating business data for organization {organization_id}")
        
        if not date_range:
            # Default to last 30 days
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=30)
            date_range = (start_date, end_date)

        all_transactions = []

        # Aggregate from ERP systems
        erp_transactions = await self._aggregate_erp_data(organization_id, date_range)
        all_transactions.extend(erp_transactions)

        # Aggregate from CRM systems
        crm_transactions = await self._aggregate_crm_data(organization_id, date_range)
        all_transactions.extend(crm_transactions)

        # Aggregate from POS systems
        pos_transactions = await self._aggregate_pos_data(organization_id, date_range)
        all_transactions.extend(pos_transactions)

        # Aggregate from E-commerce systems
        ecom_transactions = await self._aggregate_ecommerce_data(organization_id, date_range)
        all_transactions.extend(ecom_transactions)

        # Aggregate from Banking systems
        banking_transactions = await self._aggregate_banking_data(organization_id, date_range)
        all_transactions.extend(banking_transactions)

        # Aggregate from Payment processors
        payment_transactions = await self._aggregate_payment_data(organization_id, date_range)
        all_transactions.extend(payment_transactions)

        # Cross-reference and reconcile transactions
        reconciled_transactions = await self._cross_reference_transactions(all_transactions)

        logger.info(f"Aggregated {len(reconciled_transactions)} transactions from {len(all_transactions)} raw transactions")
        return reconciled_transactions

    async def _aggregate_erp_data(
        self,
        organization_id: UUID,
        date_range: Tuple[datetime, datetime]
    ) -> List[BusinessTransactionData]:
        """Aggregate data from ERP systems (SAP, Odoo, etc.)."""
        transactions = []

        # SAP ERP Data
        try:
            sap_connector = self.connectors[DataSourceType.ERP]['sap']
            sap_invoices = await sap_connector.get_invoices_by_date_range(
                organization_id, date_range[0], date_range[1]
            )
            
            for invoice in sap_invoices:
                transaction = BusinessTransactionData(
                    id=f"sap-{invoice['id']}",
                    source_type=DataSourceType.ERP,
                    source_id="sap",
                    transaction_id=invoice['invoice_number'],
                    date=invoice['invoice_date'],
                    customer_name=invoice['customer']['name'],
                    customer_email=invoice['customer'].get('email'),
                    customer_tin=invoice['customer'].get('tin'),
                    amount=Decimal(str(invoice['total_amount'])),
                    currency=invoice.get('currency', 'NGN'),
                    description=invoice['description'],
                    line_items=invoice['line_items'],
                    tax_amount=Decimal(str(invoice['tax_amount'])),
                    vat_rate=Decimal(str(invoice.get('vat_rate', 7.5))),
                    payment_status=invoice.get('payment_status', 'pending'),
                    payment_method=invoice.get('payment_method'),
                    confidence=98.5,  # High confidence for ERP data
                    raw_data=invoice
                )
                transactions.append(transaction)

        except Exception as e:
            logger.error(f"Failed to aggregate SAP data: {e}")

        # Odoo ERP Data
        try:
            odoo_connector = self.connectors[DataSourceType.ERP]['odoo']
            odoo_invoices = await odoo_connector.get_invoices_by_date_range(
                organization_id, date_range[0], date_range[1]
            )
            
            for invoice in odoo_invoices:
                transaction = BusinessTransactionData(
                    id=f"odoo-{invoice['id']}",
                    source_type=DataSourceType.ERP,
                    source_id="odoo",
                    transaction_id=invoice['name'],
                    date=invoice['invoice_date'],
                    customer_name=invoice['partner_id']['name'],
                    customer_email=invoice['partner_id'].get('email'),
                    customer_tin=invoice['partner_id'].get('vat'),
                    amount=Decimal(str(invoice['amount_total'])),
                    currency=invoice.get('currency_id', {}).get('name', 'NGN'),
                    description=invoice.get('name', 'Odoo Invoice'),
                    line_items=invoice['invoice_line_ids'],
                    tax_amount=Decimal(str(invoice['amount_tax'])),
                    vat_rate=Decimal('7.5'),
                    payment_status=invoice.get('payment_state', 'not_paid'),
                    payment_method=None,
                    confidence=96.8,
                    raw_data=invoice
                )
                transactions.append(transaction)

        except Exception as e:
            logger.error(f"Failed to aggregate Odoo data: {e}")

        return transactions

    async def _aggregate_crm_data(
        self,
        organization_id: UUID,
        date_range: Tuple[datetime, datetime]
    ) -> List[BusinessTransactionData]:
        """Aggregate data from CRM systems (Salesforce, HubSpot, etc.)."""
        transactions = []

        # Salesforce CRM Data
        try:
            sf_connector = self.connectors[DataSourceType.CRM]['salesforce']
            sf_deals = await sf_connector.get_closed_deals_by_date_range(
                organization_id, date_range[0], date_range[1]
            )
            
            for deal in sf_deals:
                if deal.get('amount') and deal.get('stage') == 'Closed Won':
                    transaction = BusinessTransactionData(
                        id=f"sf-{deal['id']}",
                        source_type=DataSourceType.CRM,
                        source_id="salesforce",
                        transaction_id=deal['name'],
                        date=deal['close_date'],
                        customer_name=deal['account']['name'],
                        customer_email=deal.get('contact', {}).get('email'),
                        customer_tin=deal.get('account', {}).get('tax_id'),
                        amount=Decimal(str(deal['amount'])),
                        currency='NGN',
                        description=deal['description'] or deal['name'],
                        line_items=[{
                            'description': deal['name'],
                            'quantity': 1,
                            'unit_price': float(deal['amount']),
                            'total': float(deal['amount']),
                            'tax_rate': 7.5,
                            'tax_amount': float(deal['amount']) * 0.075
                        }],
                        tax_amount=Decimal(str(deal['amount'])) * Decimal('0.075'),
                        vat_rate=Decimal('7.5'),
                        payment_status='pending',
                        payment_method=None,
                        confidence=94.2,
                        raw_data=deal
                    )
                    transactions.append(transaction)

        except Exception as e:
            logger.error(f"Failed to aggregate Salesforce data: {e}")

        return transactions

    async def _aggregate_pos_data(
        self,
        organization_id: UUID,
        date_range: Tuple[datetime, datetime]
    ) -> List[BusinessTransactionData]:
        """Aggregate data from POS systems (Square, Shopify POS, etc.)."""
        transactions = []

        # Square POS Data
        try:
            square_connector = self.connectors[DataSourceType.POS]['square']
            square_payments = await square_connector.get_payments_by_date_range(
                organization_id, date_range[0], date_range[1]
            )
            
            for payment in square_payments:
                if payment.get('status') == 'COMPLETED':
                    transaction = BusinessTransactionData(
                        id=f"square-{payment['id']}",
                        source_type=DataSourceType.POS,
                        source_id="square",
                        transaction_id=payment['id'],
                        date=payment['created_at'],
                        customer_name=payment.get('buyer_email_address', 'Walk-in Customer'),
                        customer_email=payment.get('buyer_email_address'),
                        customer_tin=None,
                        amount=Decimal(str(payment['amount_money']['amount'])) / 100,  # Square uses cents
                        currency=payment['amount_money']['currency'],
                        description='Square POS Sale',
                        line_items=[{
                            'description': 'POS Sale',
                            'quantity': 1,
                            'unit_price': float(payment['amount_money']['amount']) / 100,
                            'total': float(payment['amount_money']['amount']) / 100,
                            'tax_rate': 7.5,
                            'tax_amount': (float(payment['amount_money']['amount']) / 100) * 0.075
                        }],
                        tax_amount=Decimal(str(payment['amount_money']['amount'])) / 100 * Decimal('0.075'),
                        vat_rate=Decimal('7.5'),
                        payment_status='paid',
                        payment_method='Card Payment',
                        confidence=99.1,
                        raw_data=payment
                    )
                    transactions.append(transaction)

        except Exception as e:
            logger.error(f"Failed to aggregate Square data: {e}")

        return transactions

    async def _aggregate_ecommerce_data(
        self,
        organization_id: UUID,
        date_range: Tuple[datetime, datetime]
    ) -> List[BusinessTransactionData]:
        """Aggregate data from E-commerce systems (Shopify, WooCommerce, etc.)."""
        transactions = []

        # Shopify Store Data
        try:
            shopify_connector = self.connectors[DataSourceType.ECOMMERCE]['shopify']
            shopify_orders = await shopify_connector.get_orders_by_date_range(
                organization_id, date_range[0], date_range[1]
            )
            
            for order in shopify_orders:
                if order.get('financial_status') == 'paid':
                    transaction = BusinessTransactionData(
                        id=f"shopify-{order['id']}",
                        source_type=DataSourceType.ECOMMERCE,
                        source_id="shopify",
                        transaction_id=order['order_number'],
                        date=order['created_at'],
                        customer_name=f"{order['customer']['first_name']} {order['customer']['last_name']}",
                        customer_email=order['customer']['email'],
                        customer_tin=None,
                        amount=Decimal(str(order['total_price'])),
                        currency=order['currency'],
                        description=f"E-commerce Order #{order['order_number']}",
                        line_items=[{
                            'description': item['title'],
                            'quantity': item['quantity'],
                            'unit_price': float(item['price']),
                            'total': float(item['price']) * item['quantity'],
                            'tax_rate': 7.5,
                            'tax_amount': float(item['price']) * item['quantity'] * 0.075
                        } for item in order['line_items']],
                        tax_amount=Decimal(str(order['total_tax'])),
                        vat_rate=Decimal('7.5'),
                        payment_status='paid',
                        payment_method=order.get('gateway', 'Online Payment'),
                        confidence=97.8,
                        raw_data=order
                    )
                    transactions.append(transaction)

        except Exception as e:
            logger.error(f"Failed to aggregate Shopify data: {e}")

        return transactions

    async def _aggregate_banking_data(
        self,
        organization_id: UUID,
        date_range: Tuple[datetime, datetime]
    ) -> List[BusinessTransactionData]:
        """Aggregate data from Banking systems (Mono Open Banking, etc.)."""
        transactions = []

        # Mono Banking Data
        try:
            mono_connector = self.connectors[DataSourceType.BANKING]['mono']
            mono_transactions = await mono_connector.get_transactions_by_date_range(
                organization_id, date_range[0], date_range[1]
            )
            
            for txn in mono_transactions:
                if txn.get('type') == 'credit' and txn.get('amount', 0) > 0:
                    transaction = BusinessTransactionData(
                        id=f"mono-{txn['_id']}",
                        source_type=DataSourceType.BANKING,
                        source_id="mono",
                        transaction_id=txn['_id'],
                        date=txn['date'],
                        customer_name=txn.get('narration', 'Bank Transfer Customer'),
                        customer_email=None,
                        customer_tin=None,
                        amount=Decimal(str(txn['amount'])),
                        currency='NGN',
                        description=txn.get('narration', 'Bank Transfer Payment'),
                        line_items=[{
                            'description': txn.get('narration', 'Service Payment'),
                            'quantity': 1,
                            'unit_price': float(txn['amount']) / 1.075,  # Remove VAT to get base
                            'total': float(txn['amount']) / 1.075,
                            'tax_rate': 7.5,
                            'tax_amount': float(txn['amount']) * 0.075 / 1.075
                        }],
                        tax_amount=Decimal(str(txn['amount'])) * Decimal('0.075') / Decimal('1.075'),
                        vat_rate=Decimal('7.5'),
                        payment_status='paid',
                        payment_method='Bank Transfer',
                        confidence=87.3,  # Lower confidence for banking transactions
                        raw_data=txn
                    )
                    transactions.append(transaction)

        except Exception as e:
            logger.error(f"Failed to aggregate Mono banking data: {e}")

        return transactions

    async def _aggregate_payment_data(
        self,
        organization_id: UUID,
        date_range: Tuple[datetime, datetime]
    ) -> List[BusinessTransactionData]:
        """Aggregate data from Payment processors (Paystack, Flutterwave, etc.)."""
        transactions = []

        # Paystack Payment Data
        try:
            paystack_connector = self.connectors[DataSourceType.PAYMENT]['paystack']
            paystack_transactions = await paystack_connector.get_successful_transactions_by_date_range(
                organization_id, date_range[0], date_range[1]
            )
            
            for txn in paystack_transactions:
                if txn.get('status') == 'success':
                    transaction = BusinessTransactionData(
                        id=f"paystack-{txn['id']}",
                        source_type=DataSourceType.PAYMENT,
                        source_id="paystack",
                        transaction_id=txn['reference'],
                        date=txn['created_at'],
                        customer_name=txn['customer']['email'],  # Use email as name
                        customer_email=txn['customer']['email'],
                        customer_tin=None,
                        amount=Decimal(str(txn['amount'])) / 100,  # Paystack uses kobo
                        currency=txn['currency'],
                        description=txn.get('metadata', {}).get('description', 'Online Payment'),
                        line_items=[{
                            'description': 'Payment Processor Transaction',
                            'quantity': 1,
                            'unit_price': float(txn['amount']) / 100 / 1.075,
                            'total': float(txn['amount']) / 100 / 1.075,
                            'tax_rate': 7.5,
                            'tax_amount': float(txn['amount']) / 100 * 0.075 / 1.075
                        }],
                        tax_amount=Decimal(str(txn['amount'])) / 100 * Decimal('0.075') / Decimal('1.075'),
                        vat_rate=Decimal('7.5'),
                        payment_status='paid',
                        payment_method='Paystack',
                        confidence=92.5,
                        raw_data=txn
                    )
                    transactions.append(transaction)

        except Exception as e:
            logger.error(f"Failed to aggregate Paystack data: {e}")

        return transactions

    async def _cross_reference_transactions(
        self,
        transactions: List[BusinessTransactionData]
    ) -> List[BusinessTransactionData]:
        """
        Cross-reference transactions from different sources to eliminate duplicates
        and improve data quality.
        """
        # Group transactions by amount and date for potential matching
        grouped_transactions = {}
        
        for txn in transactions:
            # Create a key based on amount and date (within same day)
            key = (
                txn.amount,
                txn.date.date(),
                txn.customer_name.lower().strip() if txn.customer_name else ""
            )
            
            if key not in grouped_transactions:
                grouped_transactions[key] = []
            grouped_transactions[key].append(txn)

        reconciled = []
        
        for group in grouped_transactions.values():
            if len(group) == 1:
                # Single transaction, no duplicates
                reconciled.append(group[0])
            else:
                # Multiple transactions with same amount/date - choose best quality
                best_transaction = max(group, key=lambda t: t.confidence)
                
                # Merge data from other sources if beneficial
                for other_txn in group:
                    if other_txn != best_transaction:
                        # Add payment confirmation if available
                        if (other_txn.source_type in [DataSourceType.BANKING, DataSourceType.PAYMENT] 
                            and other_txn.payment_status == 'paid'):
                            best_transaction.payment_status = 'paid'
                            best_transaction.payment_method = other_txn.payment_method
                            # Increase confidence due to payment confirmation
                            best_transaction.confidence = min(99.9, best_transaction.confidence + 5.0)

                reconciled.append(best_transaction)

        logger.info(f"Cross-referenced {len(transactions)} transactions into {len(reconciled)} reconciled transactions")
        return reconciled

    async def generate_firs_invoices(
        self,
        request: FIRSInvoiceGenerationRequest
    ) -> FIRSInvoiceGenerationResult:
        """
        Generate FIRS-compliant invoices from aggregated business data.
        
        Args:
            request: Invoice generation request
            
        Returns:
            Invoice generation result
        """
        logger.info(f"Generating FIRS invoices for {len(request.transaction_ids)} transactions")

        try:
            # Get aggregated transaction data
            all_transactions = await self.aggregate_business_data(request.organization_id)
            
            # Filter for requested transactions
            selected_transactions = [
                txn for txn in all_transactions 
                if txn.id in request.transaction_ids
            ]

            if not selected_transactions:
                return FIRSInvoiceGenerationResult(
                    success=False,
                    invoices=[],
                    errors=["No transactions found for the provided IDs"],
                    warnings=[],
                    total_amount=Decimal('0'),
                    irns_generated=[]
                )

            invoices = []
            irns_generated = []
            errors = []
            warnings = []
            total_amount = Decimal('0')

            if request.consolidate and len(selected_transactions) > 1:
                # Generate single consolidated invoice
                invoice_result = await self._generate_consolidated_invoice(
                    selected_transactions, request
                )
                invoices.append(invoice_result)
                irns_generated.append(invoice_result['irn'])
                total_amount += Decimal(str(invoice_result['total_amount']))
            else:
                # Generate individual invoices
                for transaction in selected_transactions:
                    try:
                        invoice_result = await self._generate_individual_invoice(
                            transaction, request
                        )
                        invoices.append(invoice_result)
                        irns_generated.append(invoice_result['irn'])
                        total_amount += Decimal(str(invoice_result['total_amount']))
                    except Exception as e:
                        error_msg = f"Failed to generate invoice for transaction {transaction.id}: {e}"
                        errors.append(error_msg)
                        logger.error(error_msg)

            # Update statistics
            self.stats['transactions_processed'] += len(selected_transactions)
            self.stats['invoices_generated'] += len(invoices)
            self.stats['total_amount_processed'] += total_amount
            if errors:
                self.stats['errors_encountered'] += len(errors)

            return FIRSInvoiceGenerationResult(
                success=len(invoices) > 0,
                invoices=invoices,
                errors=errors,
                warnings=warnings,
                total_amount=total_amount,
                irns_generated=irns_generated
            )

        except Exception as e:
            error_msg = f"Failed to generate FIRS invoices: {e}"
            logger.error(error_msg)
            return FIRSInvoiceGenerationResult(
                success=False,
                invoices=[],
                errors=[error_msg],
                warnings=[],
                total_amount=Decimal('0'),
                irns_generated=[]
            )

    async def _generate_individual_invoice(
        self,
        transaction: BusinessTransactionData,
        request: FIRSInvoiceGenerationRequest
    ) -> Dict[str, Any]:
        """Generate individual FIRS invoice from transaction data."""
        
        # Generate IRN (Invoice Reference Number)
        irn = await self._generate_irn(transaction, request.organization_id)
        
        # Create FIRS-compliant invoice data
        invoice_data = {
            'irn': irn,
            'invoice_number': f"TXP-{transaction.transaction_id}",
            'invoice_date': transaction.date.isoformat(),
            'due_date': (transaction.date + timedelta(days=30)).isoformat(),
            'customer': {
                'name': transaction.customer_name,
                'email': transaction.customer_email,
                'tin': transaction.customer_tin
            },
            'line_items': transaction.line_items,
            'subtotal': float(transaction.amount - transaction.tax_amount),
            'tax_amount': float(transaction.tax_amount),
            'total_amount': float(transaction.amount),
            'currency': transaction.currency,
            'payment_status': transaction.payment_status,
            'source_data': {
                'source_type': transaction.source_type.value,
                'source_id': transaction.source_id,
                'transaction_id': transaction.transaction_id,
                'confidence': transaction.confidence
            }
        }

        # Save to database
        firs_submission = FIRSSubmission(
            organization_id=request.organization_id,
            invoice_number=invoice_data['invoice_number'],
            irn=irn,
            status=SubmissionStatus.GENERATED,
            validation_status=ValidationStatus.VALID,
            invoice_data=invoice_data,
            original_data=transaction.raw_data,
            total_amount=transaction.amount,
            currency=transaction.currency,
            customer_name=transaction.customer_name,
            customer_email=transaction.customer_email,
            customer_tin=transaction.customer_tin
        )

        self.db.add(firs_submission)
        await self.db.commit()

        return invoice_data

    async def _generate_consolidated_invoice(
        self,
        transactions: List[BusinessTransactionData],
        request: FIRSInvoiceGenerationRequest
    ) -> Dict[str, Any]:
        """Generate consolidated FIRS invoice from multiple transactions."""
        
        # Use first transaction for customer details (can be overridden)
        primary_transaction = transactions[0]
        
        # Generate IRN for consolidated invoice
        irn = await self._generate_irn(primary_transaction, request.organization_id, is_consolidated=True)
        
        # Aggregate all line items
        all_line_items = []
        total_amount = Decimal('0')
        total_tax = Decimal('0')
        
        for txn in transactions:
            all_line_items.extend(txn.line_items)
            total_amount += txn.amount
            total_tax += txn.tax_amount

        # Create consolidated invoice data
        invoice_data = {
            'irn': irn,
            'invoice_number': f"TXP-CONSOLIDATED-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            'invoice_date': datetime.utcnow().isoformat(),
            'due_date': (datetime.utcnow() + timedelta(days=30)).isoformat(),
            'customer': {
                'name': request.customer_overrides.get('customer_name', primary_transaction.customer_name) if request.customer_overrides else primary_transaction.customer_name,
                'email': request.customer_overrides.get('customer_email', primary_transaction.customer_email) if request.customer_overrides else primary_transaction.customer_email,
                'tin': primary_transaction.customer_tin
            },
            'line_items': all_line_items,
            'subtotal': float(total_amount - total_tax),
            'tax_amount': float(total_tax),
            'total_amount': float(total_amount),
            'currency': primary_transaction.currency,
            'consolidated_from': [txn.id for txn in transactions],
            'source_data': {
                'consolidation': True,
                'transaction_count': len(transactions),
                'source_types': list(set(txn.source_type.value for txn in transactions)),
                'average_confidence': sum(txn.confidence for txn in transactions) / len(transactions)
            }
        }

        # Save to database
        firs_submission = FIRSSubmission(
            organization_id=request.organization_id,
            invoice_number=invoice_data['invoice_number'],
            irn=irn,
            status=SubmissionStatus.GENERATED,
            validation_status=ValidationStatus.VALID,
            invoice_data=invoice_data,
            original_data={'consolidated_transactions': [txn.raw_data for txn in transactions]},
            total_amount=total_amount,
            currency=primary_transaction.currency,
            customer_name=invoice_data['customer']['name'],
            customer_email=invoice_data['customer']['email'],
            customer_tin=invoice_data['customer']['tin']
        )

        self.db.add(firs_submission)
        await self.db.commit()

        return invoice_data

    async def _generate_irn(
        self,
        transaction: BusinessTransactionData,
        organization_id: UUID,
        is_consolidated: bool = False
    ) -> str:
        """Generate FIRS-compliant Invoice Reference Number (IRN)."""
        
        # IRN Format: InvoiceNumber-ServiceID-YYYYMMDD
        base_number = f"TXP-{transaction.transaction_id}" if not is_consolidated else f"TXP-CONS-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        service_id = "94ND90NR"  # FIRS-assigned Service ID
        date_part = transaction.date.strftime('%Y%m%d')
        
        irn = f"{base_number}-{service_id}-{date_part}"
        return irn

    async def get_generation_statistics(self) -> Dict[str, Any]:
        """Get invoice generation statistics."""
        return {
            'transactions_processed': self.stats['transactions_processed'],
            'invoices_generated': self.stats['invoices_generated'],
            'total_amount_processed': float(self.stats['total_amount_processed']),
            'errors_encountered': self.stats['errors_encountered'],
            'success_rate': (
                (self.stats['invoices_generated'] / max(1, self.stats['transactions_processed'])) * 100
            )
        }
