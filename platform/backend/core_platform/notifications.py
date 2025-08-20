"""
Core Platform Notification Service
==================================
Notification delivery system for the TaxPoynt platform.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid


class NotificationType(Enum):
    """Types of notifications"""
    EMAIL = "email"
    SMS = "sms"
    WEBHOOK = "webhook"
    IN_APP = "in_app"
    SLACK = "slack"
    PUSH = "push"


class NotificationPriority(Enum):
    """Notification priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


class NotificationStatus(Enum):
    """Status of notification delivery"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class NotificationRecipient:
    """Notification recipient information"""
    id: str = ""
    email: Optional[str] = None
    phone: Optional[str] = None
    webhook_url: Optional[str] = None
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Notification:
    """Base notification class"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: NotificationType = NotificationType.EMAIL
    priority: NotificationPriority = NotificationPriority.NORMAL
    subject: str = ""
    message: str = ""
    recipient: NotificationRecipient = field(default_factory=NotificationRecipient)
    data: Dict[str, Any] = field(default_factory=dict)
    template_id: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    status: NotificationStatus = NotificationStatus.PENDING
    retry_count: int = 0
    max_retries: int = 3
    correlation_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert notification to dictionary"""
        return {
            'id': self.id,
            'type': self.type.value,
            'priority': self.priority.value,
            'subject': self.subject,
            'message': self.message,
            'recipient': {
                'id': self.recipient.id,
                'email': self.recipient.email,
                'phone': self.recipient.phone,
                'webhook_url': self.recipient.webhook_url,
                'user_id': self.recipient.user_id,
                'metadata': self.recipient.metadata
            },
            'data': self.data,
            'template_id': self.template_id,
            'scheduled_at': self.scheduled_at.isoformat() if self.scheduled_at else None,
            'created_at': self.created_at.isoformat(),
            'status': self.status.value,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'correlation_id': self.correlation_id
        }


class NotificationService:
    """
    Central notification service for platform-wide notifications
    
    Features:
    - Multiple delivery channels (email, SMS, webhook, etc.)
    - Priority-based delivery
    - Retry logic with exponential backoff
    - Template support
    - Delivery tracking and analytics
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self._notification_queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        self._stats = {
            'notifications_sent': 0,
            'notifications_failed': 0,
            'notifications_pending': 0,
            'delivery_rate': 0.0
        }
        
        # Configuration
        self.default_max_retries = self.config.get('max_retries', 3)
        self.retry_delays = [1, 5, 15, 30]  # seconds
        
        self.logger.info("NotificationService initialized")
    
    async def send_notification(self, notification: Notification) -> str:
        """
        Send a notification
        
        Args:
            notification: Notification to send
            
        Returns:
            Notification ID
        """
        try:
            await self._notification_queue.put(notification)
            self._stats['notifications_pending'] += 1
            
            self.logger.info(f"Queued notification: {notification.id} ({notification.type.value})")
            return notification.id
            
        except Exception as e:
            self.logger.error(f"Failed to queue notification {notification.id}: {e}")
            self._stats['notifications_failed'] += 1
            raise
    
    async def send_email(self, recipient_email: str, subject: str, message: str,
                        priority: NotificationPriority = NotificationPriority.NORMAL,
                        template_id: Optional[str] = None,
                        data: Optional[Dict[str, Any]] = None,
                        correlation_id: Optional[str] = None) -> str:
        """
        Convenience method to send email notification
        
        Args:
            recipient_email: Email address of recipient
            subject: Email subject
            message: Email message
            priority: Notification priority
            template_id: Optional template ID
            data: Additional data for template
            correlation_id: Correlation ID for tracking
            
        Returns:
            Notification ID
        """
        notification = Notification(
            type=NotificationType.EMAIL,
            priority=priority,
            subject=subject,
            message=message,
            recipient=NotificationRecipient(email=recipient_email),
            data=data or {},
            template_id=template_id,
            correlation_id=correlation_id
        )
        
        return await self.send_notification(notification)
    
    async def send_webhook(self, webhook_url: str, data: Dict[str, Any],
                          priority: NotificationPriority = NotificationPriority.NORMAL,
                          correlation_id: Optional[str] = None) -> str:
        """
        Convenience method to send webhook notification
        
        Args:
            webhook_url: Webhook URL to send to
            data: Data to send in webhook
            priority: Notification priority
            correlation_id: Correlation ID for tracking
            
        Returns:
            Notification ID
        """
        notification = Notification(
            type=NotificationType.WEBHOOK,
            priority=priority,
            subject=f"Webhook to {webhook_url}",
            message="Webhook notification",
            recipient=NotificationRecipient(webhook_url=webhook_url),
            data=data,
            correlation_id=correlation_id
        )
        
        return await self.send_notification(notification)
    
    async def _process_notifications(self) -> None:
        """Process notifications from the queue"""
        while self._running:
            try:
                # Wait for a notification with timeout to allow checking _running flag
                notification = await asyncio.wait_for(self._notification_queue.get(), timeout=1.0)
                
                await self._deliver_notification(notification)
                
            except asyncio.TimeoutError:
                # Timeout is expected, continue processing
                continue
            except Exception as e:
                self.logger.error(f"Error processing notification: {e}")
    
    async def _deliver_notification(self, notification: Notification) -> None:
        """Deliver a single notification"""
        try:
            # Simulate delivery based on notification type
            success = await self._simulate_delivery(notification)
            
            if success:
                notification.status = NotificationStatus.DELIVERED
                self._stats['notifications_sent'] += 1
                self.logger.info(f"Delivered notification {notification.id}")
            else:
                await self._handle_delivery_failure(notification)
                
        except Exception as e:
            self.logger.error(f"Failed to deliver notification {notification.id}: {e}")
            await self._handle_delivery_failure(notification)
        finally:
            self._stats['notifications_pending'] -= 1
            self._update_delivery_rate()
    
    async def _simulate_delivery(self, notification: Notification) -> bool:
        """
        Simulate notification delivery
        In a real implementation, this would integrate with actual services
        """
        # Simulate some processing time
        await asyncio.sleep(0.1)
        
        # Simulate 95% success rate
        import random
        return random.random() < 0.95
    
    async def _handle_delivery_failure(self, notification: Notification) -> None:
        """Handle failed notification delivery"""
        notification.retry_count += 1
        
        if notification.retry_count <= notification.max_retries:
            notification.status = NotificationStatus.RETRYING
            
            # Schedule retry with exponential backoff
            delay = self.retry_delays[min(notification.retry_count - 1, len(self.retry_delays) - 1)]
            
            self.logger.warning(f"Retrying notification {notification.id} in {delay}s (attempt {notification.retry_count})")
            
            # In a real implementation, you'd schedule this properly
            await asyncio.sleep(delay)
            await self._notification_queue.put(notification)
        else:
            notification.status = NotificationStatus.FAILED
            self._stats['notifications_failed'] += 1
            self.logger.error(f"Notification {notification.id} failed after {notification.retry_count} attempts")
    
    def _update_delivery_rate(self) -> None:
        """Update delivery rate statistics"""
        total = self._stats['notifications_sent'] + self._stats['notifications_failed']
        if total > 0:
            self._stats['delivery_rate'] = self._stats['notifications_sent'] / total
    
    async def start(self) -> None:
        """Start the notification service"""
        if self._running:
            return
        
        self._running = True
        
        # Start notification processing task
        asyncio.create_task(self._process_notifications())
        
        self.logger.info("NotificationService started")
    
    async def stop(self) -> None:
        """Stop the notification service"""
        self._running = False
        
        # Process any remaining notifications
        while not self._notification_queue.empty():
            try:
                notification = self._notification_queue.get_nowait()
                await self._deliver_notification(notification)
            except asyncio.QueueEmpty:
                break
            except Exception as e:
                self.logger.error(f"Error processing remaining notification: {e}")
        
        self.logger.info("NotificationService stopped")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get notification service statistics"""
        return {
            **self._stats,
            'queue_size': self._notification_queue.qsize(),
            'running': self._running
        }


# Global notification service instance
_notification_service: Optional[NotificationService] = None


def get_notification_service(config: Optional[Dict[str, Any]] = None) -> NotificationService:
    """Get the global notification service instance"""
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService(config)
    return _notification_service


# Convenience functions
async def send_email_notification(recipient_email: str, subject: str, message: str,
                                 priority: NotificationPriority = NotificationPriority.NORMAL) -> str:
    """Send an email notification using the global service"""
    service = get_notification_service()
    return await service.send_email(recipient_email, subject, message, priority)


async def send_webhook_notification(webhook_url: str, data: Dict[str, Any],
                                   priority: NotificationPriority = NotificationPriority.NORMAL) -> str:
    """Send a webhook notification using the global service"""
    service = get_notification_service()
    return await service.send_webhook(webhook_url, data, priority)