import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core_platform.data_management.db_async import get_async_session
from core_platform.data_management.models.banking import BankAccount, BankingConnection
from core_platform.data_management.repositories.banking_repo_async import (
    create_banking_connection,
    delete_banking_connection,
    get_banking_connection,
    list_banking_connections,
    list_bank_accounts,
    update_banking_connection,
)
from .mono_integration_service import MonoIntegrationService
from core_platform.data_management.models import AuditEventType
from si_services.utils.audit import record_audit_event

try:
    from platform.backend.external_integrations.financial_systems.banking.open_banking.providers.mono.client import (
        MonoClient,
        MonoClientConfig,
    )
    from platform.backend.external_integrations.financial_systems.banking.open_banking.providers.mono.observability import (
        LATENCY_ALERT_SECONDS,
    )
    from platform.backend.external_integrations.financial_systems.banking.open_banking.providers.mono.pipeline import (
        MonoTransactionPipeline,
    )
    from platform.backend.external_integrations.financial_systems.banking.open_banking.providers.mono.transaction_sync import (
        MonoTransactionSyncService,
        SyncStateStore,
    )
    from platform.backend.external_integrations.financial_systems.banking.open_banking.providers.mono.transformer import (
        MonoTransactionTransformer,
    )
    from platform.backend.core_platform.services.banking_ingestion_service import BankingIngestionService
except ImportError:  # pragma: no cover - backend-local imports
    from external_integrations.financial_systems.banking.open_banking.providers.mono.client import (  # type: ignore
        MonoClient,
        MonoClientConfig,
    )
    from external_integrations.financial_systems.banking.open_banking.providers.mono.observability import (  # type: ignore
        LATENCY_ALERT_SECONDS,
    )
    from external_integrations.financial_systems.banking.open_banking.providers.mono.pipeline import (  # type: ignore
        MonoTransactionPipeline,
    )
    from external_integrations.financial_systems.banking.open_banking.providers.mono.transaction_sync import (  # type: ignore
        MonoTransactionSyncService,
        SyncStateStore,
    )
    from external_integrations.financial_systems.banking.open_banking.providers.mono.transformer import (  # type: ignore
        MonoTransactionTransformer,
    )
    from core_platform.services.banking_ingestion_service import BankingIngestionService  # type: ignore

logger = logging.getLogger(__name__)

_FLAG_ENV = "MONO_TRANSACTIONS_ENABLED"
_TRUTHY_VALUES = {"1", "true", "yes", "on"}


@dataclass
class _AccountSyncStateStore(SyncStateStore):
    """Persist Mono cursors in bank account metadata while keeping per-run dedupe in memory."""

    session: AsyncSession
    _account_cache: Dict[str, BankAccount] = field(default_factory=dict)
    _dedupe: Dict[str, set[str]] = field(default_factory=dict)
    last_cursor: Optional[str] = None

    async def get_cursor(self, account_id: str) -> Optional[str]:
        account = await self._get_account(account_id)
        metadata = dict(account.account_metadata or {})
        return metadata.get("mono_last_cursor")

    async def set_cursor(self, account_id: str, cursor: Optional[str]) -> None:
        account = await self._get_account(account_id)
        metadata = dict(account.account_metadata or {})
        metadata["mono_last_cursor"] = cursor
        account.account_metadata = metadata
        self.last_cursor = cursor

    async def register_transaction(self, account_id: str, dedupe_key: str) -> bool:
        bucket = self._dedupe.setdefault(account_id, set())
        if dedupe_key in bucket:
            return False
        bucket.add(dedupe_key)
        return True

    async def _get_account(self, provider_account_id: str) -> BankAccount:
        if provider_account_id in self._account_cache:
            return self._account_cache[provider_account_id]

        stmt = (
            select(BankAccount)
            .where(BankAccount.provider_account_id == provider_account_id)
            .limit(1)
        )
        result = await self.session.execute(stmt)
        account = result.scalar_one_or_none()
        if not account:
            raise ValueError(f"Bank account with provider account id '{provider_account_id}' not found")
        self._account_cache[provider_account_id] = account
        return account


class SIBankingService:
    """
    Main banking service for System Integrators.
    
    Handles all banking-related operations and delegates to appropriate
    provider-specific services.
    """
    
    def __init__(self):
        """Initialize banking service"""
        self.mono_service = MonoIntegrationService()

    @staticmethod
    def _current_timestamp() -> str:
        """Return UTC timestamp in ISO 8601 format with trailing Z."""
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        
    async def handle_operation(self, operation: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle banking operation from message router.
        
        Args:
            operation: Operation name
            payload: Operation payload
            
        Returns:
            Dict with operation result
        """
        try:
            logger.info(f"Handling banking operation: {operation}")
            
            # Extract common parameters
            si_id = payload.get("si_id")
            api_version = payload.get("api_version", "v1")
            
            if not si_id:
                raise ValueError("SI ID is required for banking operations")
            
            # Route to appropriate handler
            if operation == "create_mono_widget_link":
                return await self._handle_create_mono_widget_link(si_id, payload)
            elif operation == "process_mono_callback":
                return await self._handle_process_mono_callback(si_id, payload)
            elif operation.startswith("process_") and operation.endswith("_callback"):
                return await self._handle_generic_banking_callback(si_id, payload, operation)
            elif operation == "list_open_banking_connections":
                return await self._handle_list_open_banking_connections(si_id, payload)
            elif operation == "create_open_banking_connection":
                return await self._handle_create_open_banking_connection(si_id, payload)
            elif operation == "get_open_banking_connection":
                return await self._handle_get_open_banking_connection(si_id, payload)
            elif operation == "update_open_banking_connection":
                return await self._handle_update_open_banking_connection(si_id, payload)
            elif operation == "delete_open_banking_connection":
                return await self._handle_delete_open_banking_connection(si_id, payload)
            elif operation == "get_banking_transactions":
                return await self._handle_get_banking_transactions(si_id, payload)
            elif operation == "sync_banking_transactions":
                return await self._handle_sync_banking_transactions(si_id, payload)
            elif operation == "get_banking_accounts":
                return await self._handle_get_banking_accounts(si_id, payload)
            elif operation == "get_account_balance":
                return await self._handle_get_account_balance(si_id, payload)
            elif operation == "test_banking_connection":
                return await self._handle_test_banking_connection(si_id, payload)
            elif operation == "get_banking_connection_health":
                return await self._handle_get_banking_connection_health(si_id, payload)
            elif operation == "get_banking_statistics":
                return await self._handle_get_banking_statistics(si_id, payload)
            else:
                raise ValueError(f"Unknown banking operation: {operation}")
                
        except Exception as e:
            logger.error(f"Error handling banking operation {operation}: {str(e)}", exc_info=True)
            raise RuntimeError(f"Banking operation failed: {str(e)}")
    
    async def _handle_create_mono_widget_link(self, si_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Mono widget link creation"""
        widget_config = payload.get("widget_config")
        if not widget_config:
            raise ValueError("Widget config is required")
            
        result = await self.mono_service.create_mono_widget_link(si_id, widget_config)
        
        return {
            "operation": "create_mono_widget_link",
            "success": True,
            "data": result,
            "si_id": si_id
        }
    
    async def _handle_process_mono_callback(self, si_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Mono banking callback processing"""
        callback_data = payload.get("callback_data")
        if not callback_data:
            raise ValueError("Callback data is required")
            
        result = await self.mono_service.process_mono_callback(si_id, callback_data)
        
        return {
            "operation": "process_mono_callback",
            "success": result.get("success", False),
            "data": result,
            "si_id": si_id
        }
    
    async def _handle_generic_banking_callback(self, si_id: str, payload: Dict[str, Any], operation: str) -> Dict[str, Any]:
        """Handle generic banking callback from any provider"""
        callback_data = payload.get("callback_data")
        provider = payload.get("provider", "mono")
        
        if not callback_data:
            raise ValueError("Callback data is required")
        
        # Route to appropriate provider service
        if provider == "mono":
            result = await self.mono_service.process_mono_callback(si_id, callback_data)
        else:
            # For future providers, add routing logic here
            result = {
                "success": False,
                "error": "unsupported_provider",
                "message": f"Provider '{provider}' not supported yet",
                "si_id": si_id
            }
        
        return {
            "operation": operation,
            "success": result.get("success", False),
            "data": result,
            "provider": provider,
            "si_id": si_id
        }
    
    async def _handle_list_open_banking_connections(self, si_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle listing Open Banking connections"""
        filters = payload.get("filters", {})
        async for db in get_async_session():
            result = await list_banking_connections(
                db,
                si_id=si_id,
                provider=filters.get("provider"),
                limit=int(filters.get("limit", 50)),
                offset=int(filters.get("offset", 0)),
            )
            return {
                "operation": "list_open_banking_connections",
                "success": True,
                "data": result,
                "si_id": si_id,
            }
    
    async def _handle_create_open_banking_connection(self, si_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle creating Open Banking connection"""
        connection_data = payload.get("connection_data")
        if not connection_data:
            raise ValueError("Connection data is required")

        async for db in get_async_session():
            created = await create_banking_connection(
                db,
                si_id=si_id,
                organization_id=connection_data.get("organization_id"),
                provider=connection_data["provider"],
                provider_connection_id=connection_data.get("provider_connection_id", "pending"),
                status=connection_data.get("status", "pending"),
                metadata=connection_data.get("connection_config", {}),
            )
            await db.commit()
            try:
                await record_audit_event(
                    db,
                    event_type=AuditEventType.INTEGRATION_CHANGE,
                    description="open_banking_connection_created",
                    user_id=None,
                    organization_id=created.get("organization_id") if isinstance(created, dict) else None,
                    target_type="banking_connection",
                    target_id=str(created.get("id")) if isinstance(created, dict) and created.get("id") else created.get("provider_connection_id", "unknown") if isinstance(created, dict) else "unknown",
                    new_values={"provider": created.get("provider")} if isinstance(created, dict) else {},
                    correlation_id=payload.get("correlation_id"),
                )
            except Exception:
                pass
            return {
                "operation": "create_open_banking_connection",
                "success": True,
                "data": created,
                "si_id": si_id,
            }
    
    async def _handle_get_open_banking_connection(self, si_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle getting Open Banking connection"""
        connection_id = payload.get("connection_id")
        if not connection_id:
            raise ValueError("Connection ID is required")
        async for db in get_async_session():
            result = await get_banking_connection(db, connection_id)
            return {
                "operation": "get_open_banking_connection",
                "success": result is not None,
                "data": result or {"error": "not_found"},
                "si_id": si_id,
            }
    
    async def _handle_update_open_banking_connection(self, si_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle updating Open Banking connection"""
        connection_id = payload.get("connection_id")
        updates = payload.get("updates", {})
        
        if not connection_id:
            raise ValueError("Connection ID is required")
        async for db in get_async_session():
            updated = await update_banking_connection(db, connection_id, updates)
            await db.commit()
            try:
                await record_audit_event(
                    db,
                    event_type=AuditEventType.INTEGRATION_CHANGE,
                    description="open_banking_connection_updated",
                    user_id=None,
                    organization_id=updated.get("organization_id") if isinstance(updated, dict) else None,
                    target_type="banking_connection",
                    target_id=str(connection_id),
                    new_values=updates,
                    correlation_id=payload.get("correlation_id"),
                )
            except Exception:
                pass
            return {
                "operation": "update_open_banking_connection",
                "success": updated is not None,
                "data": updated or {"error": "not_found"},
                "si_id": si_id,
            }
    
    async def _handle_delete_open_banking_connection(self, si_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle deleting Open Banking connection"""
        connection_id = payload.get("connection_id")
        if not connection_id:
            raise ValueError("Connection ID is required")
        async for db in get_async_session():
            await delete_banking_connection(db, connection_id)
            await db.commit()
            try:
                await record_audit_event(
                    db,
                    event_type=AuditEventType.INTEGRATION_CHANGE,
                    description="open_banking_connection_deleted",
                    user_id=None,
                    organization_id=None,
                    target_type="banking_connection",
                    target_id=str(connection_id),
                    correlation_id=payload.get("correlation_id"),
                )
            except Exception:
                pass
            return {
                "operation": "delete_open_banking_connection",
                "success": True,
                "data": {"connection_id": connection_id, "deleted": True},
                "si_id": si_id,
            }
    
    async def _handle_get_banking_transactions(self, si_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle getting banking transactions"""
        filters = payload.get("filters", {})
        
        result = await self.mono_service.get_banking_transactions(si_id, filters)
        
        return {
            "operation": "get_banking_transactions",
            "success": True,
            "data": result,
            "si_id": si_id
        }
    
    async def _handle_sync_banking_transactions(self, si_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle syncing banking transactions"""
        sync_enabled = os.getenv(_FLAG_ENV, "false").lower() in _TRUTHY_VALUES
        sync_config = payload.get("sync_config") or {}

        def _build_sync_response(
            *,
            sync_started: bool,
            feature_enabled: bool,
            credentials_configured: bool,
            message: Optional[str] = None,
            fetched_count: int = 0,
            persisted: int = 0,
            duplicates: int = 0,
            connection_id: Optional[str] = None,
            account_id: Optional[str] = None,
            mono_account_id: Optional[str] = None,
            last_cursor: Optional[str] = None,
            last_synced_at: Optional[str] = None,
            extra: Optional[Dict[str, Any]] = None,
        ) -> Dict[str, Any]:
            data = {
                "sync_started": sync_started,
                "feature_enabled": feature_enabled,
                "credentials_configured": credentials_configured,
                "fetched_count": fetched_count,
                "persisted": persisted,
                "duplicates": duplicates,
                "connection_id": connection_id,
                "account_id": account_id,
                "mono_account_id": mono_account_id,
                "last_cursor": last_cursor,
                "last_synced_at": last_synced_at,
            }
            if message:
                data["message"] = message
            if extra:
                data.update(extra)
            return {
                "operation": "sync_banking_transactions",
                "success": True,
                "data": data,
                "si_id": si_id,
            }

        if not sync_enabled:
            logger.info("Mono transactions sync requested while feature flag disabled", extra={"si_id": si_id})
            return _build_sync_response(
                sync_started=False,
                feature_enabled=False,
                credentials_configured=False,
                message=f"Mono transactions disabled – set {_FLAG_ENV}=true to enable pipeline",
            )

        mono_secret = os.getenv("MONO_SECRET_KEY")
        mono_app_id = os.getenv("MONO_APP_ID")
        mono_base_url = os.getenv("MONO_BASE_URL", "https://api.withmono.com")

        if not mono_secret or not mono_app_id:
            logger.info(
                "Mono transactions sync requested without credentials",
                extra={"si_id": si_id},
            )
            return _build_sync_response(
                sync_started=False,
                feature_enabled=True,
                credentials_configured=False,
                message="Mono credentials missing. Set MONO_SECRET_KEY and MONO_APP_ID to enable syncing.",
            )

        account_db_id_value = sync_config.get("account_db_id") or sync_config.get("account_id")
        if not account_db_id_value:
            raise ValueError("account_db_id is required in sync_config when Mono transactions are enabled")

        try:
            account_db_id = UUID(str(account_db_id_value))
        except ValueError as exc:
            raise ValueError("account_db_id must be a valid UUID") from exc

        mono_account_id = sync_config.get("mono_account_id")
        page_size = int(os.getenv("MONO_PAGE_LIMIT", "100"))

        async for db in get_async_session():
            account: BankAccount = await db.get(BankAccount, account_db_id)
            if not account:
                raise ValueError(f"Bank account {account_db_id} not found")

            connection: BankingConnection = await db.get(BankingConnection, account.connection_id)
            if not connection:
                raise ValueError(f"Banking connection {account.connection_id} not found")

            mono_account_identifier = mono_account_id or account.provider_account_id
            if not mono_account_identifier:
                raise ValueError("Mono account identifier unavailable (provide mono_account_id or ensure provider_account_id is stored)")

            state_store = _AccountSyncStateStore(session=db)

            async def _emit(event: str, event_payload: Dict[str, Any]) -> None:
                logger.info(
                    "Mono pipeline event",
                    extra={
                        "event": event,
                        "si_id": si_id,
                        "account_id": mono_account_identifier,
                        "account_db_id": str(account.id),
                        "payload": event_payload,
                    },
                )

            mono_client = MonoClient(
                MonoClientConfig(
                    base_url=mono_base_url,
                    secret_key=mono_secret,
                    app_id=mono_app_id,
                    rate_limit_per_minute=int(os.getenv("MONO_RATE_LIMIT_PER_MINUTE", "60")),
                    request_timeout=float(os.getenv("MONO_REQUEST_TIMEOUT", "30")),
                )
            )

            try:
                sync_service = MonoTransactionSyncService(
                    mono_client,
                    state_store,
                    _emit,
                    page_size=page_size,
                )
                ingestion_service = BankingIngestionService(db, _emit)
                pipeline = MonoTransactionPipeline(sync_service, MonoTransactionTransformer(), ingestion_service, _emit)

                result = await pipeline.run(
                    account_id=mono_account_identifier,
                    account_number=account.account_number,
                    provider_account_id=account.provider_account_id,
                    connection_db_id=connection.id,
                    account_db_id=account.id,
                )

                account.account_metadata = {
                    **(account.account_metadata or {}),
                    "mono_last_synced_at": self._current_timestamp(),
                    "mono_last_cursor": state_store.last_cursor,
                }
                connection.last_sync_at = datetime.now(timezone.utc)

                await db.commit()
            finally:
                await mono_client.aclose()

            fetched_count = result.inserted_count + result.duplicate_count
            last_synced_at_iso = connection.last_sync_at.isoformat() if connection.last_sync_at else None

            return _build_sync_response(
                sync_started=True,
                feature_enabled=True,
                credentials_configured=True,
                fetched_count=fetched_count,
                persisted=result.inserted_count,
                duplicates=result.duplicate_count,
                account_id=str(account.id),
                connection_id=str(connection.id),
                mono_account_id=mono_account_identifier,
                last_cursor=state_store.last_cursor,
                last_synced_at=last_synced_at_iso,
                extra={"latency_sla_seconds": LATENCY_ALERT_SECONDS},
            )
    
    async def _handle_get_banking_accounts(self, si_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle getting banking accounts"""
        filters = payload.get("filters", {})
        async for db in get_async_session():
            result = await list_bank_accounts(
                db,
                si_id=si_id,
                provider=filters.get("provider"),
                limit=int(filters.get("limit", 50)),
                offset=int(filters.get("offset", 0)),
            )

            return {
                "operation": "get_banking_accounts",
                "success": True,
                "data": result,
                "si_id": si_id
            }
    
    async def _handle_get_account_balance(self, si_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle getting account balance"""
        account_id = payload.get("account_id")
        if not account_id:
            raise ValueError("Account ID is required")
            
        # For now, return mock balance
        result = {
            "account_id": account_id,
            "balance": 1500000.00,  # 1.5M NGN
            "currency": "NGN",
            "last_updated": self._current_timestamp(),
            "si_id": si_id
        }
        
        return {
            "operation": "get_account_balance",
            "success": True,
            "data": result,
            "si_id": si_id
        }
    
    async def _handle_test_banking_connection(self, si_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle testing banking connection"""
        connection_id = payload.get("connection_id")
        if not connection_id:
            raise ValueError("Connection ID is required")
            
        result = await self.mono_service.test_banking_connection(si_id, connection_id)
        
        return {
            "operation": "test_banking_connection",
            "success": True,
            "data": result,
            "si_id": si_id
        }
    
    async def _handle_get_banking_connection_health(self, si_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle getting banking connection health"""
        connection_id = payload.get("connection_id")
        if not connection_id:
            raise ValueError("Connection ID is required")
            
        # For now, return mock health data
        result = {
            "connection_id": connection_id,
            "status": "healthy",
            "last_check": self._current_timestamp(),
            "uptime": "99.9%",
            "response_time": "150ms",
            "si_id": si_id
        }
        
        return {
            "operation": "get_banking_connection_health",
            "success": True,
            "data": result,
            "si_id": si_id
        }
    
    async def _handle_get_banking_statistics(self, si_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle getting banking integration statistics"""
        try:
            # Get stats from Mono service
            # In a real implementation, you'd aggregate data from connected accounts
            result = {
                "connections": {
                    "total": 0,
                    "active": 0,
                    "mono": 0,
                    "stitch": 0,
                    "other": 0
                },
                "transactions": {
                    "total": 0,
                    "this_month": 0,
                    "volume": 0
                },
                "accounts": {
                    "connected": 0,
                    "active": 0
                },
                "health": {
                    "overall": "ready",
                    "connection_success_rate": "N/A",
                    "status": "No banking connections configured"
                },
                "si_id": si_id,
                "generated_at": self._current_timestamp()
            }
            
            return {
                "operation": "get_banking_statistics",
                "success": True,
                "data": result,
                "si_id": si_id
            }
            
        except Exception as e:
            logger.error(f"Error getting banking statistics for SI {si_id}: {str(e)}")
            raise RuntimeError(f"Failed to get banking statistics: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on banking service"""
        try:
            mono_health = await self.mono_service.health_check()
            
            return {
                "status": "healthy",
                "services": {
                    "mono": mono_health
                }
            }
            
        except Exception as e:
            logger.error(f"Banking service health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def cleanup(self):
        """Cleanup resources"""
        await self.mono_service.cleanup()
