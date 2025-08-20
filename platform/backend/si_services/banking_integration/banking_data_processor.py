"""
Banking Data Processor Service
==============================

Handles processing of banking data for SI workflows, including:
- Transaction data validation and normalization
- Mono transaction to TaxPoynt standard format transformation
- Banking data enrichment for e-invoicing compliance
- Account data processing and classification
- Income pattern analysis for automated invoice generation

Architecture follows si_services/erp_integration/erp_data_processor.py patterns.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

from external_integrations.financial_systems.banking.open_banking.providers.mono.models import (
    MonoTransaction,
    MonoAccount,
    MonoTransactionType
)

logger = logging.getLogger(__name__)


class BankingProcessingStatus(Enum):
    """Status of banking data processing operations"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    PARTIAL = "partial"


class BankingDataIssueType(Enum):
    """Types of banking data issues encountered during processing"""
    MISSING_TRANSACTION_DATA = "missing_transaction_data"
    INVALID_AMOUNT_FORMAT = "invalid_amount_format"
    DUPLICATE_TRANSACTION = "duplicate_transaction"
    ACCOUNT_MISMATCH = "account_mismatch"
    CURRENCY_INCONSISTENCY = "currency_inconsistency"
    BUSINESS_CLASSIFICATION_FAILED = "business_classification_failed"


class TransactionClassification(Enum):
    """Transaction classification for e-invoicing"""
    BUSINESS_INCOME = "business_income"
    BUSINESS_EXPENSE = "business_expense"
    PERSONAL_TRANSACTION = "personal_transaction"
    TRANSFER = "transfer"
    FEE = "fee"
    REFUND = "refund"
    UNKNOWN = "unknown"


@dataclass
class BankingProcessingRule:
    """Defines a banking data processing rule"""
    rule_id: str
    rule_name: str
    rule_type: str  # validation, transformation, classification, enrichment
    field_targets: List[str]
    condition: str
    action: str
    priority: int = 1
    enabled: bool = True
    description: Optional[str] = None


@dataclass
class BankingDataIssue:
    """Represents a banking data processing issue"""
    issue_id: str
    issue_type: BankingDataIssueType
    severity: str  # critical, high, medium, low
    field_name: str
    transaction_id: str
    description: str
    original_value: Optional[Any] = None
    suggested_value: Optional[Any] = None
    auto_correctable: bool = False
    detected_at: datetime = field(default_factory=datetime.now)


@dataclass
class BankingProcessingResult:
    """Result of banking data processing operation"""
    result_id: str
    status: BankingProcessingStatus
    total_transactions: int
    processed_transactions: int
    failed_transactions: int
    skipped_transactions: int
    start_time: datetime
    end_time: Optional[datetime] = None
    processing_duration: Optional[float] = None
    issues_detected: List[BankingDataIssue] = field(default_factory=list)
    corrections_applied: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StandardizedTransaction:
    """TaxPoynt standardized transaction structure"""
    transaction_id: str
    account_id: str
    reference: str
    amount_ngn: Decimal
    original_amount: Decimal
    original_currency: str
    transaction_type: TransactionClassification
    transaction_date: datetime
    value_date: datetime
    description: str
    narration: str
    balance_after: Optional[Decimal]
    counterparty_name: Optional[str] = None
    counterparty_account: Optional[str] = None
    business_category: Optional[str] = None
    invoice_eligible: bool = False
    tax_implications: Optional[Dict[str, Any]] = None
    raw_data: Optional[Dict[str, Any]] = None
    processed_at: datetime = field(default_factory=datetime.now)


@dataclass
class StandardizedAccount:
    """TaxPoynt standardized account structure"""
    account_id: str
    account_number: str
    account_name: str
    bank_name: str
    bank_code: str
    account_type: str
    currency: str
    balance: Decimal
    available_balance: Optional[Decimal]
    business_account: bool = False
    linked_entities: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class BankingDataProcessor:
    """
    Processes banking data from various providers into TaxPoynt standard format.
    
    Key responsibilities:
    - Transform provider-specific formats to standard format
    - Validate and clean banking data
    - Classify transactions for e-invoicing eligibility
    - Enrich data with business intelligence
    - Prepare data for FIRS compliance
    """
    
    def __init__(self):
        """Initialize banking data processor"""
        self.processing_rules = self._load_processing_rules()
        self.business_keywords = self._load_business_keywords()
        self.currency_rates = {}  # For currency conversion
        
    def _load_processing_rules(self) -> List[BankingProcessingRule]:
        """Load processing rules configuration"""
        return [
            BankingProcessingRule(
                rule_id="validate_amount",
                rule_name="Validate Transaction Amount",
                rule_type="validation",
                field_targets=["amount"],
                condition="amount > 0",
                action="mark_invalid_if_false",
                priority=1,
                description="Ensure transaction amounts are positive"
            ),
            BankingProcessingRule(
                rule_id="classify_business_income",
                rule_name="Classify Business Income",
                rule_type="classification",
                field_targets=["type", "narration", "amount"],
                condition="type == 'credit' and contains_business_keywords",
                action="set_classification_business_income",
                priority=2,
                description="Classify credit transactions as business income"
            ),
            BankingProcessingRule(
                rule_id="invoice_eligibility",
                rule_name="Determine Invoice Eligibility",
                rule_type="enrichment",
                field_targets=["classification", "amount", "narration"],
                condition="classification == 'business_income' and amount >= 1000",
                action="mark_invoice_eligible",
                priority=3,
                description="Mark qualifying transactions for invoice generation"
            )
        ]
    
    def _load_business_keywords(self) -> Dict[str, List[str]]:
        """Load business classification keywords"""
        return {
            "income_keywords": [
                "payment", "invoice", "service", "consultation", "project",
                "contract", "deposit", "installment", "fee", "subscription",
                "sales", "revenue", "billing", "professional", "retainer"
            ],
            "expense_keywords": [
                "supplies", "equipment", "software", "license", "rent",
                "utilities", "insurance", "marketing", "advertising", "travel"
            ],
            "personal_keywords": [
                "grocery", "fuel", "transport", "entertainment", "shopping",
                "dining", "personal", "family", "gift", "charity"
            ]
        }
    
    async def process_mono_transactions(
        self,
        transactions: List[MonoTransaction],
        account: MonoAccount,
        si_id: str
    ) -> BankingProcessingResult:
        """
        Process Mono transactions into standardized format.
        
        Args:
            transactions: List of Mono transactions
            account: Mono account information
            si_id: System Integrator ID
            
        Returns:
            BankingProcessingResult with processing summary
        """
        try:
            start_time = datetime.now()
            result_id = f"banking_proc_{si_id}_{start_time.strftime('%Y%m%d_%H%M%S')}"
            
            logger.info(f"Processing {len(transactions)} Mono transactions for SI: {si_id}")
            
            processed_transactions = []
            issues = []
            failed_count = 0
            skipped_count = 0
            
            for transaction in transactions:
                try:
                    # Transform Mono transaction to standard format
                    standardized = await self._transform_mono_transaction(transaction, account)
                    
                    # Apply processing rules
                    validation_result = await self._apply_processing_rules(standardized, transaction)
                    
                    if validation_result.get("valid", True):
                        processed_transactions.append(standardized)
                    else:
                        failed_count += 1
                        issues.extend(validation_result.get("issues", []))
                        
                except Exception as e:
                    logger.error(f"Error processing transaction {transaction.id}: {str(e)}")
                    failed_count += 1
                    issues.append(BankingDataIssue(
                        issue_id=f"proc_error_{transaction.id}",
                        issue_type=BankingDataIssueType.MISSING_TRANSACTION_DATA,
                        severity="high",
                        field_name="transaction",
                        transaction_id=transaction.id,
                        description=f"Processing error: {str(e)}"
                    ))
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            result = BankingProcessingResult(
                result_id=result_id,
                status=BankingProcessingStatus.COMPLETED,
                total_transactions=len(transactions),
                processed_transactions=len(processed_transactions),
                failed_transactions=failed_count,
                skipped_transactions=skipped_count,
                start_time=start_time,
                end_time=end_time,
                processing_duration=duration,
                issues_detected=issues,
                metadata={
                    "si_id": si_id,
                    "account_id": account.id,
                    "provider": "mono",
                    "processed_data": processed_transactions
                }
            )
            
            logger.info(f"Banking data processing completed: {result.processed_transactions}/{result.total_transactions} transactions processed")
            return result
            
        except Exception as e:
            logger.error(f"Banking data processing failed for SI {si_id}: {str(e)}", exc_info=True)
            raise RuntimeError(f"Banking data processing failed: {str(e)}")
    
    async def _transform_mono_transaction(
        self,
        transaction: MonoTransaction,
        account: MonoAccount
    ) -> StandardizedTransaction:
        """Transform Mono transaction to standardized format"""
        
        # Classify transaction type
        classification = self._classify_transaction(transaction)
        
        # Determine invoice eligibility
        invoice_eligible = self._is_invoice_eligible(transaction, classification)
        
        # Extract business category
        business_category = self._extract_business_category(transaction)
        
        # Prepare tax implications
        tax_implications = self._analyze_tax_implications(transaction, classification)
        
        return StandardizedTransaction(
            transaction_id=transaction.id,
            account_id=account.id,
            reference=transaction.reference,
            amount_ngn=transaction.amount_naira,
            original_amount=transaction.amount_naira,  # Mono already in NGN
            original_currency="NGN",
            transaction_type=classification,
            transaction_date=transaction.date,
            value_date=transaction.date,  # Mono doesn't distinguish value date
            description=transaction.narration,
            narration=transaction.narration,
            balance_after=transaction.balance,
            counterparty_name=None,  # Would need additional Mono API calls
            counterparty_account=None,
            business_category=business_category,
            invoice_eligible=invoice_eligible,
            tax_implications=tax_implications,
            raw_data={
                "mono_transaction": transaction.dict(),
                "provider": "mono"
            }
        )
    
    def _classify_transaction(self, transaction: MonoTransaction) -> TransactionClassification:
        """Classify transaction for business purposes"""
        narration = transaction.narration.lower()
        
        # Check for business income keywords
        if (transaction.type == MonoTransactionType.CREDIT and 
            any(keyword in narration for keyword in self.business_keywords["income_keywords"])):
            return TransactionClassification.BUSINESS_INCOME
        
        # Check for business expense keywords
        if (transaction.type == MonoTransactionType.DEBIT and 
            any(keyword in narration for keyword in self.business_keywords["expense_keywords"])):
            return TransactionClassification.BUSINESS_EXPENSE
        
        # Check for personal transaction keywords
        if any(keyword in narration for keyword in self.business_keywords["personal_keywords"]):
            return TransactionClassification.PERSONAL_TRANSACTION
        
        # Check for transfers (account-to-account)
        if "transfer" in narration or "tfr" in narration:
            return TransactionClassification.TRANSFER
        
        # Check for fees
        if any(word in narration for word in ["fee", "charge", "commission"]):
            return TransactionClassification.FEE
        
        # Default classification based on type
        if transaction.type == MonoTransactionType.CREDIT:
            return TransactionClassification.BUSINESS_INCOME
        elif transaction.type == MonoTransactionType.DEBIT:
            return TransactionClassification.BUSINESS_EXPENSE
        
        return TransactionClassification.UNKNOWN
    
    def _is_invoice_eligible(
        self,
        transaction: MonoTransaction,
        classification: TransactionClassification
    ) -> bool:
        """Determine if transaction is eligible for invoice generation"""
        
        # Only business income transactions are eligible
        if classification != TransactionClassification.BUSINESS_INCOME:
            return False
        
        # Must be above minimum amount (1000 NGN)
        if transaction.amount_naira < 1000:
            return False
        
        # Check for round amounts (often business payments)
        is_round = (transaction.amount_naira % 1000 == 0) or (transaction.amount_naira % 500 == 0)
        
        # Check for business indicators in narration
        narration = transaction.narration.lower()
        has_business_indicator = any(
            keyword in narration 
            for keyword in self.business_keywords["income_keywords"]
        )
        
        return is_round or has_business_indicator
    
    def _extract_business_category(self, transaction: MonoTransaction) -> Optional[str]:
        """Extract business category from transaction details"""
        narration = transaction.narration.lower()
        
        # Service categories
        if any(word in narration for word in ["consulting", "consultation", "advisory"]):
            return "Professional Services"
        elif any(word in narration for word in ["software", "development", "coding", "tech"]):
            return "Technology Services"
        elif any(word in narration for word in ["design", "creative", "marketing"]):
            return "Creative Services"
        elif any(word in narration for word in ["training", "education", "course"]):
            return "Education Services"
        elif any(word in narration for word in ["sales", "product", "goods"]):
            return "Product Sales"
        
        return None
    
    def _analyze_tax_implications(
        self,
        transaction: MonoTransaction,
        classification: TransactionClassification
    ) -> Dict[str, Any]:
        """Analyze tax implications for the transaction"""
        
        implications = {
            "vat_applicable": False,
            "withholding_tax_applicable": False,
            "estimated_vat_amount": 0,
            "estimated_wht_amount": 0,
            "tax_rate_applied": None
        }
        
        if classification == TransactionClassification.BUSINESS_INCOME:
            # For business income above certain thresholds
            if transaction.amount_naira >= 10000:  # 10k NGN threshold
                implications["vat_applicable"] = True
                implications["estimated_vat_amount"] = float(transaction.amount_naira * Decimal("0.075"))  # 7.5% VAT
                implications["tax_rate_applied"] = "7.5%"
            
            # Withholding tax for certain service categories
            if transaction.amount_naira >= 50000:  # 50k NGN threshold
                implications["withholding_tax_applicable"] = True
                implications["estimated_wht_amount"] = float(transaction.amount_naira * Decimal("0.05"))  # 5% WHT
        
        return implications
    
    async def _apply_processing_rules(
        self,
        standardized: StandardizedTransaction,
        original: MonoTransaction
    ) -> Dict[str, Any]:
        """Apply processing rules to standardized transaction"""
        
        validation_result = {"valid": True, "issues": []}
        
        for rule in self.processing_rules:
            if not rule.enabled:
                continue
                
            try:
                # Apply rule based on type
                if rule.rule_type == "validation":
                    validation_issue = self._apply_validation_rule(rule, standardized, original)
                    if validation_issue:
                        validation_result["issues"].append(validation_issue)
                        if validation_issue.severity in ["critical", "high"]:
                            validation_result["valid"] = False
                
                elif rule.rule_type == "classification":
                    self._apply_classification_rule(rule, standardized, original)
                
                elif rule.rule_type == "enrichment":
                    self._apply_enrichment_rule(rule, standardized, original)
                    
            except Exception as e:
                logger.error(f"Error applying rule {rule.rule_id}: {str(e)}")
        
        return validation_result
    
    def _apply_validation_rule(
        self,
        rule: BankingProcessingRule,
        standardized: StandardizedTransaction,
        original: MonoTransaction
    ) -> Optional[BankingDataIssue]:
        """Apply validation rule and return issue if validation fails"""
        
        if rule.rule_id == "validate_amount":
            if standardized.amount_ngn <= 0:
                return BankingDataIssue(
                    issue_id=f"val_amount_{standardized.transaction_id}",
                    issue_type=BankingDataIssueType.INVALID_AMOUNT_FORMAT,
                    severity="critical",
                    field_name="amount_ngn",
                    transaction_id=standardized.transaction_id,
                    description="Transaction amount must be positive",
                    original_value=float(standardized.amount_ngn),
                    auto_correctable=False
                )
        
        return None
    
    def _apply_classification_rule(
        self,
        rule: BankingProcessingRule,
        standardized: StandardizedTransaction,
        original: MonoTransaction
    ):
        """Apply classification rule to modify transaction classification"""
        # Classification rules are already applied in _classify_transaction
        pass
    
    def _apply_enrichment_rule(
        self,
        rule: BankingProcessingRule,
        standardized: StandardizedTransaction,
        original: MonoTransaction
    ):
        """Apply enrichment rule to add additional data"""
        
        if rule.rule_id == "invoice_eligibility":
            # Already handled in _is_invoice_eligible
            pass
    
    async def process_mono_account(self, account: MonoAccount, si_id: str) -> StandardizedAccount:
        """Process Mono account into standardized format"""
        
        return StandardizedAccount(
            account_id=account.id,
            account_number=account.account_number,
            account_name=account.name,
            bank_name=account.institution.name,
            bank_code=account.institution.bank_code,
            account_type=account.type,
            currency=account.currency,
            balance=account.balance,
            available_balance=account.available_balance,
            business_account=True,  # Assume business account for SI context
            linked_entities=[si_id],
            metadata={
                "provider": "mono",
                "raw_data": account.dict(),
                "processed_at": datetime.now().isoformat()
            }
        )
    
    def get_processing_statistics(self, result: BankingProcessingResult) -> Dict[str, Any]:
        """Get detailed processing statistics"""
        
        processed_data = result.metadata.get("processed_data", [])
        
        stats = {
            "processing_summary": {
                "total_transactions": result.total_transactions,
                "processed_transactions": result.processed_transactions,
                "failed_transactions": result.failed_transactions,
                "success_rate": result.processed_transactions / result.total_transactions if result.total_transactions > 0 else 0,
                "processing_duration": result.processing_duration
            },
            "transaction_classification": {},
            "invoice_eligibility": {
                "eligible_count": 0,
                "ineligible_count": 0,
                "total_eligible_amount": 0
            },
            "issues_summary": {},
            "business_categories": {}
        }
        
        # Analyze processed transactions
        for transaction in processed_data:
            # Classification stats
            classification = transaction.transaction_type.value
            stats["transaction_classification"][classification] = stats["transaction_classification"].get(classification, 0) + 1
            
            # Invoice eligibility
            if transaction.invoice_eligible:
                stats["invoice_eligibility"]["eligible_count"] += 1
                stats["invoice_eligibility"]["total_eligible_amount"] += float(transaction.amount_ngn)
            else:
                stats["invoice_eligibility"]["ineligible_count"] += 1
            
            # Business categories
            if transaction.business_category:
                category = transaction.business_category
                stats["business_categories"][category] = stats["business_categories"].get(category, 0) + 1
        
        # Issue analysis
        for issue in result.issues_detected:
            issue_type = issue.issue_type.value
            stats["issues_summary"][issue_type] = stats["issues_summary"].get(issue_type, 0) + 1
        
        return stats