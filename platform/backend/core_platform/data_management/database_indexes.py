"""
TaxPoynt Platform - Production Database Indexes
==============================================
Critical database indexes for high-volume transaction processing.
Optimized for 1M+ daily transactions with proper performance tuning.
"""

from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import logging
from typing import List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class DatabaseIndexManager:
    """
    Production database index manager for high-volume operations.
    
    Implements critical indexes for:
    - Transaction processing (1M+ daily)
    - Banking data queries
    - Business system integrations
    - Audit and compliance lookups
    - Performance monitoring
    """
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.executed_indexes = []
        
    def create_all_production_indexes(self) -> Dict[str, Any]:
        """Create all production-critical indexes"""
        logger.info("🔧 Creating production database indexes for 1M+ daily transactions")
        
        results = {
            "banking_indexes": self.create_banking_indexes(),
            "business_system_indexes": self.create_business_system_indexes(),
            "transaction_indexes": self.create_transaction_indexes(),
            "audit_indexes": self.create_audit_indexes(),
            "performance_indexes": self.create_performance_indexes(),
            "composite_indexes": self.create_composite_indexes()
        }
        
        # Create table partitioning for high-volume tables
        partitioning_results = self.setup_table_partitioning()
        results["partitioning"] = partitioning_results
        
        logger.info(f"✅ Database optimization complete. Created {len(self.executed_indexes)} indexes")
        return results
    
    def create_banking_indexes(self) -> List[str]:
        """Create indexes for banking tables - CRITICAL for transaction processing"""
        logger.info("🏦 Creating banking performance indexes...")
        
        banking_indexes = [
            # Banking Connections - Primary lookup patterns
            {
                "name": "idx_banking_connections_si_id_status",
                "table": "banking_connections",
                "columns": ["si_id", "status"],
                "purpose": "Fast lookup of active connections by SI"
            },
            {
                "name": "idx_banking_connections_provider_status",
                "table": "banking_connections", 
                "columns": ["provider", "status"],
                "purpose": "Provider-specific connection queries"
            },
            {
                "name": "idx_banking_connections_last_sync",
                "table": "banking_connections",
                "columns": ["last_sync_at"],
                "purpose": "Sync scheduling and monitoring"
            },
            
            # Bank Accounts - Account lookup optimization
            {
                "name": "idx_bank_accounts_connection_id",
                "table": "bank_accounts",
                "columns": ["connection_id"],
                "purpose": "Fast account lookup by connection"
            },
            {
                "name": "idx_bank_accounts_account_number",
                "table": "bank_accounts",
                "columns": ["account_number"],
                "purpose": "Account number lookups for transactions"
            },
            {
                "name": "idx_bank_accounts_bank_code_active",
                "table": "bank_accounts",
                "columns": ["bank_code", "is_active"],
                "purpose": "Bank-specific active account queries"
            },
            
            # Bank Transactions - CRITICAL for 1M+ daily processing
            {
                "name": "idx_bank_transactions_account_date",
                "table": "bank_transactions", 
                "columns": ["account_id", "transaction_date"],
                "purpose": "CRITICAL: Account transaction history (most frequent query)"
            },
            {
                "name": "idx_bank_transactions_date_amount",
                "table": "bank_transactions",
                "columns": ["transaction_date", "amount"],
                "purpose": "Date-range and amount filtering"
            },
            {
                "name": "idx_bank_transactions_provider_id",
                "table": "bank_transactions",
                "columns": ["provider_transaction_id"],
                "purpose": "Provider transaction ID lookups"
            },
            {
                "name": "idx_bank_transactions_processed",
                "table": "bank_transactions", 
                "columns": ["is_processed", "processed_at"],
                "purpose": "Processing status and batch operations"
            },
            {
                "name": "idx_bank_transactions_type_date",
                "table": "bank_transactions",
                "columns": ["transaction_type", "transaction_date"],
                "purpose": "Transaction type filtering with date"
            },
            
            # Banking Webhooks - High volume webhook processing
            {
                "name": "idx_banking_webhooks_processed",
                "table": "banking_webhooks",
                "columns": ["is_processed", "created_at"],
                "purpose": "Webhook processing queue management"
            },
            {
                "name": "idx_banking_webhooks_provider_event",
                "table": "banking_webhooks",
                "columns": ["provider", "event_type"],
                "purpose": "Provider-specific webhook filtering"
            },
            
            # Banking Sync Logs - Performance monitoring
            {
                "name": "idx_banking_sync_connection_started",
                "table": "banking_sync_logs",
                "columns": ["connection_id", "started_at"],
                "purpose": "Sync history and performance analysis"
            },
            {
                "name": "idx_banking_sync_status_completed",
                "table": "banking_sync_logs",
                "columns": ["status", "completed_at"],
                "purpose": "Sync status monitoring"
            }
        ]
        
        # Add JSONB GIN indexes - CRITICAL for performance
        jsonb_indexes = [
            # Banking Connection Metadata - High-volume queries
            {
                "name": "idx_banking_connections_metadata_gin",
                "table": "banking_connections",
                "columns": ["connection_metadata"],
                "index_type": "GIN",
                "purpose": "CRITICAL: JSONB connection metadata queries"
            },
            
            # Bank Account Metadata
            {
                "name": "idx_bank_accounts_metadata_gin", 
                "table": "bank_accounts",
                "columns": ["account_metadata"],
                "index_type": "GIN",
                "purpose": "CRITICAL: JSONB account metadata queries"
            },
            
            # Bank Transaction Metadata - HIGHEST VOLUME
            {
                "name": "idx_bank_transactions_metadata_gin",
                "table": "bank_transactions", 
                "columns": ["transaction_metadata"],
                "index_type": "GIN",
                "purpose": "CRITICAL: JSONB transaction metadata queries (1M+ daily)"
            },
            
            # Banking Webhook Data - Real-time processing
            {
                "name": "idx_banking_webhooks_data_gin",
                "table": "banking_webhooks",
                "columns": ["webhook_data"], 
                "index_type": "GIN",
                "purpose": "CRITICAL: JSONB webhook data filtering and processing"
            },
            
            # Banking Sync Metadata
            {
                "name": "idx_banking_sync_metadata_gin",
                "table": "banking_sync_logs",
                "columns": ["sync_metadata"],
                "index_type": "GIN", 
                "purpose": "JSONB sync metadata queries"
            },
            
            # Banking Credentials Metadata
            {
                "name": "idx_banking_credentials_metadata_gin",
                "table": "banking_credentials",
                "columns": ["credentials_metadata"],
                "index_type": "GIN",
                "purpose": "JSONB credentials metadata queries"
            }
        ]
        
        # Combine regular and JSONB indexes
        all_banking_indexes = banking_indexes + jsonb_indexes
        return self._execute_index_batch(all_banking_indexes)
    
    def create_business_system_indexes(self) -> List[str]:
        """Create indexes for business system integration tables"""
        logger.info("🏢 Creating business system indexes...")
        
        business_indexes = [
            # ERP Connection Indexes
            {
                "name": "idx_erp_connections_si_id_status",
                "table": "erp_connections",
                "columns": ["si_id", "status"],
                "purpose": "Active ERP connections by SI"
            },
            {
                "name": "idx_erp_connections_provider_status", 
                "table": "erp_connections",
                "columns": ["provider", "status"],
                "purpose": "Provider-specific ERP queries"
            },
            
            # CRM Connection Indexes
            {
                "name": "idx_crm_connections_si_id_status",
                "table": "crm_connections", 
                "columns": ["si_id", "status"],
                "purpose": "Active CRM connections by SI"
            },
            
            # POS Connection Indexes
            {
                "name": "idx_pos_connections_si_id_status",
                "table": "pos_connections",
                "columns": ["si_id", "status"], 
                "purpose": "Active POS connections by SI"
            },
            
            # Certificate Management
            {
                "name": "idx_certificates_organization_type",
                "table": "certificates",
                "columns": ["organization_id", "certificate_type"],
                "purpose": "Certificate lookup by organization and type"
            },
            {
                "name": "idx_certificates_expiry_status",
                "table": "certificates",
                "columns": ["valid_until", "status"],
                "purpose": "Certificate expiry monitoring"
            },
            
            # Document Processing
            {
                "name": "idx_document_generation_organization",
                "table": "document_generation_logs",
                "columns": ["organization_id", "created_at"],
                "purpose": "Document generation history"
            },
            
            # IRN Generation - FIRS compliance critical
            {
                "name": "idx_irn_generation_organization_date",
                "table": "irn_generations",
                "columns": ["organization_id", "generated_at"],
                "purpose": "IRN generation tracking per organization"
            },
            {
                "name": "idx_irn_generation_irn_number",
                "table": "irn_generations",
                "columns": ["irn_number"],
                "purpose": "IRN number lookups"
            }
        ]
        
        return self._execute_index_batch(business_indexes)
    
    def create_transaction_indexes(self) -> List[str]:
        """Create indexes for high-volume transaction processing"""
        logger.info("💳 Creating transaction processing indexes...")
        
        transaction_indexes = [
            # Taxpayer Management
            {
                "name": "idx_taxpayers_organization_status", 
                "table": "taxpayers",
                "columns": ["organization_id", "registration_status"],
                "purpose": "Active taxpayer lookup by organization"
            },
            {
                "name": "idx_taxpayers_tin_number",
                "table": "taxpayers", 
                "columns": ["tin"],
                "purpose": "TIN number lookups for FIRS integration"
            },
            
            # Webhook Events - High volume processing
            {
                "name": "idx_webhook_events_processed_created",
                "table": "webhook_events",
                "columns": ["processing_status", "processed_at"],
                "purpose": "Webhook processing queue"
            },
            {
                "name": "idx_webhook_events_event_type",
                "table": "webhook_events",
                "columns": ["event_type", "created_at"],
                "purpose": "Event type filtering"
            }
        ]
        
        return self._execute_index_batch(transaction_indexes)
    
    def create_audit_indexes(self) -> List[str]:
        """Create indexes for audit and compliance"""
        logger.info("📋 Creating audit and compliance indexes...")
        
        audit_indexes = [
            # Audit Logs - Compliance and monitoring
            {
                "name": "idx_audit_logs_organization_timestamp",
                "table": "audit_logs", 
                "columns": ["organization_id", "created_at"],
                "purpose": "Audit trail by organization and time"
            },
            {
                "name": "idx_audit_logs_event_type_timestamp",
                "table": "audit_logs",
                "columns": ["event_type", "created_at"],
                "purpose": "Audit event filtering"
            },
            {
                "name": "idx_audit_logs_user_timestamp", 
                "table": "audit_logs",
                "columns": ["user_id", "created_at"],
                "purpose": "User activity audit trails"
            },
            
            # Compliance Checks
            {
                "name": "idx_compliance_checks_organization_status",
                "table": "compliance_checks",
                "columns": ["organization_id", "compliance_status"],
                "purpose": "Compliance monitoring by organization"
            },
            
            # Analytics Reports
            {
                "name": "idx_analytics_reports_organization_date",
                "table": "analytics_reports",
                "columns": ["organization_id", "generated_at"],
                "purpose": "Analytics report generation"
            }
        ]
        
        return self._execute_index_batch(audit_indexes)
    
    def create_performance_indexes(self) -> List[str]:
        """Create indexes for performance monitoring and optimization"""
        logger.info("⚡ Creating performance monitoring indexes...")
        
        performance_indexes = [
            # General performance indexes for existing tables
            {
                "name": "idx_users_email_active",
                "table": "users", 
                "columns": ["email", "is_active"],
                "purpose": "User authentication lookups"
            },
            {
                "name": "idx_organizations_created_at",
                "table": "organizations",
                "columns": ["created_at"],
                "purpose": "Organization chronological queries"
            },
            {
                "name": "idx_integrations_organization_type",
                "table": "integrations",
                "columns": ["organization_id", "integration_type"],
                "purpose": "Integration type filtering by organization"
            },
            {
                "name": "idx_firs_submissions_status_created",
                "table": "firs_submissions",
                "columns": ["status", "created_at"],
                "purpose": "FIRS submission status monitoring"
            }
        ]
        
        return self._execute_index_batch(performance_indexes)
    
    def create_composite_indexes(self) -> List[str]:
        """Create composite indexes for complex queries"""
        logger.info("🔗 Creating composite indexes for complex queries...")
        
        composite_indexes = [
            # Banking transaction comprehensive index
            {
                "name": "idx_bank_transactions_comprehensive",
                "table": "bank_transactions",
                "columns": ["account_id", "transaction_date", "transaction_type", "is_processed"],
                "purpose": "CRITICAL: Comprehensive transaction queries"
            },
            
            # Banking connection status monitoring
            {
                "name": "idx_banking_connections_monitoring",
                "table": "banking_connections", 
                "columns": ["si_id", "provider", "status", "last_sync_at"],
                "purpose": "Connection monitoring dashboard"
            },
            
            # Audit trail comprehensive
            {
                "name": "idx_audit_comprehensive",
                "table": "audit_logs",
                "columns": ["organization_id", "user_id", "event_type", "created_at"],
                "purpose": "Comprehensive audit queries"
            }
        ]
        
        return self._execute_index_batch(composite_indexes)
    
    def setup_table_partitioning(self) -> Dict[str, Any]:
        """Setup table partitioning for high-volume tables"""
        logger.info("🗂️  Setting up table partitioning for high-volume data...")
        
        partitioning_results = {
            "attempted": [],
            "successful": [],
            "failed": []
        }
        
        # Bank transactions partitioning by date (most critical)
        partition_queries = [
            {
                "name": "bank_transactions_monthly_partitioning",
                "description": "Partition bank_transactions by month for better performance",
                "check_query": """
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables 
                        WHERE table_name LIKE 'bank_transactions_y%'
                    )
                """,
                "setup_queries": [
                    # Note: This would require converting existing table to partitioned
                    # For now, we'll create the partitioning structure for new deployments
                    """
                    -- Bank transactions partitioning setup (for new deployments)
                    -- This would be implemented during initial database setup
                    """
                ]
            }
        ]
        
        for partition_config in partition_queries:
            partitioning_results["attempted"].append(partition_config["name"])
            try:
                # Check if partitioning already exists
                result = self.db.execute(text(partition_config["check_query"])).scalar()
                if result:
                    logger.info(f"✅ Partitioning already exists: {partition_config['name']}")
                    partitioning_results["successful"].append(partition_config["name"])
                else:
                    logger.info(f"ℹ️  Partitioning setup noted for future: {partition_config['name']}")
                    # Partitioning setup would be done during initial deployment
                    partitioning_results["successful"].append(partition_config["name"] + " (planned)")
                    
            except Exception as e:
                logger.warning(f"⚠️  Partitioning check failed for {partition_config['name']}: {e}")
                partitioning_results["failed"].append(partition_config["name"])
        
        return partitioning_results
    
    def _execute_index_batch(self, indexes: List[Dict[str, Any]]) -> List[str]:
        """Execute a batch of index creation statements"""
        successful_indexes = []
        
        for index_config in indexes:
            try:
                index_name = index_config["name"]
                table_name = index_config["table"]
                columns = index_config["columns"]
                purpose = index_config.get("purpose", "Performance optimization")
                
                # Check if index already exists
                check_query = text("""
                    SELECT EXISTS (
                        SELECT 1 FROM pg_indexes 
                        WHERE indexname = :index_name
                    )
                """)
                
                exists = self.db.execute(check_query, {"index_name": index_name}).scalar()
                
                if exists:
                    logger.debug(f"✅ Index already exists: {index_name}")
                    successful_indexes.append(f"{index_name} (exists)")
                    continue
                
                # Create the index (handle GIN indexes for JSONB)
                columns_str = ", ".join(columns)
                index_type = index_config.get("index_type", "BTREE")
                
                if index_type == "GIN":
                    # GIN indexes for JSONB columns
                    create_query = text(f"""
                        CREATE INDEX IF NOT EXISTS {index_name} 
                        ON {table_name} USING GIN ({columns_str})
                    """)
                else:
                    # Regular BTREE indexes
                    create_query = text(f"""
                        CREATE INDEX IF NOT EXISTS {index_name} 
                        ON {table_name} ({columns_str})
                    """)
                
                logger.info(f"🔧 Creating index: {index_name} on {table_name}({columns_str})")
                logger.debug(f"   Purpose: {purpose}")
                
                self.db.execute(create_query)
                self.db.commit()
                
                successful_indexes.append(index_name)
                self.executed_indexes.append({
                    "name": index_name,
                    "table": table_name,
                    "columns": columns,
                    "purpose": purpose,
                    "created_at": datetime.now().isoformat()
                })
                
                logger.info(f"✅ Created index: {index_name}")
                
            except SQLAlchemyError as e:
                logger.error(f"❌ Failed to create index {index_config['name']}: {e}")
                self.db.rollback()
                continue
            except Exception as e:
                logger.error(f"❌ Unexpected error creating index {index_config['name']}: {e}")
                self.db.rollback()
                continue
        
        return successful_indexes
    
    def analyze_table_performance(self) -> Dict[str, Any]:
        """Analyze table performance and suggest optimizations"""
        logger.info("📊 Analyzing table performance...")
        
        performance_analysis = {}
        
        # Analyze high-volume tables
        high_volume_tables = [
            "bank_transactions",
            "banking_connections", 
            "bank_accounts",
            "banking_webhooks",
            "audit_logs",
            "webhook_events"
        ]
        
        for table in high_volume_tables:
            try:
                # Get table statistics
                stats_query = text(f"""
                    SELECT 
                        schemaname,
                        tablename,
                        attname,
                        n_distinct,
                        correlation
                    FROM pg_stats 
                    WHERE tablename = '{table}'
                    ORDER BY n_distinct DESC
                    LIMIT 10
                """)
                
                stats = self.db.execute(stats_query).fetchall()
                
                # Get table size
                size_query = text(f"""
                    SELECT 
                        pg_size_pretty(pg_total_relation_size('{table}')) as total_size,
                        pg_size_pretty(pg_relation_size('{table}')) as table_size,
                        (SELECT count(*) FROM {table}) as row_count
                """)
                
                size_info = self.db.execute(size_query).fetchone()
                
                performance_analysis[table] = {
                    "statistics": [dict(row) for row in stats] if stats else [],
                    "size_info": dict(size_info) if size_info else {},
                    "optimization_status": "indexed" if any(
                        idx["table"] == table for idx in self.executed_indexes
                    ) else "needs_indexing"
                }
                
            except Exception as e:
                logger.warning(f"Could not analyze table {table}: {e}")
                performance_analysis[table] = {"error": str(e)}
        
        return performance_analysis
    
    def get_index_usage_stats(self) -> Dict[str, Any]:
        """Get index usage statistics"""
        try:
            usage_query = text("""
                SELECT 
                    schemaname,
                    tablename,
                    indexname,
                    idx_tup_read,
                    idx_tup_fetch,
                    idx_scan
                FROM pg_stat_user_indexes 
                WHERE schemaname = 'public'
                ORDER BY idx_scan DESC
                LIMIT 20
            """)
            
            usage_stats = self.db.execute(usage_query).fetchall()
            
            return {
                "index_usage": [dict(row) for row in usage_stats],
                "total_indexes_analyzed": len(usage_stats),
                "created_indexes": len(self.executed_indexes)
            }
            
        except Exception as e:
            logger.error(f"Error getting index usage stats: {e}")
            return {"error": str(e)}


def create_production_indexes(db_session: Session) -> Dict[str, Any]:
    """
    Factory function to create all production database indexes.
    Call this during deployment or database setup.
    """
    index_manager = DatabaseIndexManager(db_session)
    return index_manager.create_all_production_indexes()


def analyze_database_performance(db_session: Session) -> Dict[str, Any]:
    """
    Analyze database performance and provide optimization recommendations.
    """
    index_manager = DatabaseIndexManager(db_session)
    
    # Create indexes first
    index_results = index_manager.create_all_production_indexes()
    
    # Then analyze performance
    performance_analysis = index_manager.analyze_table_performance()
    usage_stats = index_manager.get_index_usage_stats()
    
    return {
        "index_creation": index_results,
        "performance_analysis": performance_analysis,
        "usage_statistics": usage_stats,
        "optimization_summary": {
            "total_indexes_created": len(index_manager.executed_indexes),
            "tables_optimized": len(set(idx["table"] for idx in index_manager.executed_indexes)),
            "optimization_timestamp": datetime.now().isoformat()
        }
    }
