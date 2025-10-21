"""
Data Extraction Package

This package provides comprehensive data extraction capabilities for ERP systems
including batch processing, incremental synchronization, data reconciliation,
and automated scheduling.

Components:
- erp_data_extractor: Core ERP data extraction with pluggable adapters
- batch_processor: Large-scale batch processing with parallel execution
- incremental_sync: Incremental data updates and delta synchronization
- data_reconciler: Data consistency checks and automated reconciliation
- extraction_scheduler: Automated scheduling and job management
"""

import logging

from .erp_data_extractor import (
    ERPDataExtractor,
    ERPAdapter,
    OdooAdapter,
    SAPAdapter,
    ERPType,
    ExtractionStatus,
    ExtractionFilter,
    ExtractionResult,
    InvoiceData,
    create_adapter,
    erp_data_extractor
)

from .batch_processor import (
    BatchProcessor,
    BatchConfig,
    BatchJob,
    BatchResult,
    BatchStatus,
    ProcessingPriority,
    ProcessingMetrics,
    create_batch_processor
)

from .incremental_sync import (
    IncrementalSyncService,
    SyncConfig,
    SyncState,
    SyncStatus,
    SyncStrategy,
    SyncResult,
    ChangeRecord,
    ChangeType,
    ConflictResolver,
    create_incremental_sync_service
)

from .data_reconciler import (
    DataReconciler,
    ReconciliationConfig,
    ReconciliationResult,
    ReconciliationType,
    Discrepancy,
    DiscrepancySeverity,
    ReconciliationStatus,
    ReconciliationMetrics,
    create_data_reconciler
)

logger = logging.getLogger(__name__)

try:
    from .extraction_scheduler import (
        ExtractionScheduler,
        SchedulerConfig,
        ScheduledJob,
        JobExecution,
        ScheduleConfig,
        ScheduleType,
        JobType,
        JobStatus,
        ExecutionStatus,
        JobDependency,
        create_extraction_scheduler,
    )
    _SCHEDULER_AVAILABLE = True
except ModuleNotFoundError as scheduler_import_err:  # pragma: no cover - optional dependency
    logger.warning(
        "Extraction scheduler unavailable; continuing without scheduler support: %s",
        scheduler_import_err,
    )
    ExtractionScheduler = None  # type: ignore
    SchedulerConfig = None  # type: ignore
    ScheduledJob = None  # type: ignore
    JobExecution = None  # type: ignore
    ScheduleConfig = None  # type: ignore
    ScheduleType = None  # type: ignore
    JobType = None  # type: ignore
    JobStatus = None  # type: ignore
    ExecutionStatus = None  # type: ignore
    JobDependency = None  # type: ignore
    create_extraction_scheduler = None  # type: ignore
    _SCHEDULER_AVAILABLE = False

__all__ = [
    # ERP Data Extractor
    "ERPDataExtractor",
    "ERPAdapter", 
    "OdooAdapter",
    "SAPAdapter",
    "ERPType",
    "ExtractionStatus",
    "ExtractionFilter",
    "ExtractionResult",
    "InvoiceData",
    "create_adapter",
    "erp_data_extractor",
    
    # Batch Processor
    "BatchProcessor",
    "BatchConfig",
    "BatchJob",
    "BatchResult",
    "BatchStatus",
    "ProcessingPriority",
    "ProcessingMetrics",
    "create_batch_processor",
    
    # Incremental Sync
    "IncrementalSyncService",
    "SyncConfig",
    "SyncState",
    "SyncStatus",
    "SyncStrategy",
    "SyncResult",
    "ChangeRecord",
    "ChangeType",
    "ConflictResolver",
    "create_incremental_sync_service",
    
    # Data Reconciler
    "DataReconciler",
    "ReconciliationConfig",
    "ReconciliationResult",
    "ReconciliationType",
    "Discrepancy",
    "DiscrepancySeverity",
    "ReconciliationStatus",
    "ReconciliationMetrics",
    "create_data_reconciler",
]

if _SCHEDULER_AVAILABLE:
    __all__.extend([
        "ExtractionScheduler",
        "SchedulerConfig",
        "ScheduledJob",
        "JobExecution",
        "ScheduleConfig",
        "ScheduleType",
        "JobType",
        "JobStatus",
        "ExecutionStatus",
        "JobDependency",
        "create_extraction_scheduler",
    ])

__version__ = "1.0.0"
__author__ = "TaxPoynt Platform Team"
__description__ = "Comprehensive ERP data extraction and processing system"
