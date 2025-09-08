"""
Core Platform Event Bus
=======================
Event-driven communication system for the TaxPoynt platform.
"""

import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid
import weakref


class EventPriority(Enum):
    """Event priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Event:
    """Base event class"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    priority: EventPriority = EventPriority.NORMAL
    source: str = ""
    correlation_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary"""
        return {
            'id': self.id,
            'type': self.type,
            'data': self.data,
            'timestamp': self.timestamp.isoformat(),
            'priority': self.priority.value,
            'source': self.source,
            'correlation_id': self.correlation_id
        }


class EventBus:
    """
    Central event bus for platform-wide event handling
    
    Features:
    - Async event publishing and subscription
    - Event filtering and routing
    - Priority-based event handling
    - Correlation ID support for request tracking
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._subscribers: Dict[str, Set[Callable]] = {}
        self._handlers: List[Callable] = []
        self._running = False
        self._event_queue: asyncio.Queue = asyncio.Queue()
        self._stats = {
            'events_published': 0,
            'events_processed': 0,
            'events_failed': 0,
            'subscribers_count': 0
        }
        
        self.logger.info("EventBus initialized")
    
    async def initialize(self) -> bool:
        """
        Initialize the EventBus asynchronously.
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            self._running = True
            self.logger.info("EventBus initialized asynchronously")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize EventBus: {e}")
            return False
    
    def subscribe(self, event_type: str, handler: Callable) -> None:
        """
        Subscribe to events of a specific type
        
        Args:
            event_type: Type of events to subscribe to
            handler: Function to call when event is received
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = set()
        
        self._subscribers[event_type].add(handler)
        self._stats['subscribers_count'] = sum(len(handlers) for handlers in self._subscribers.values())
        
        self.logger.info(f"Subscribed handler to event type: {event_type}")
    
    def unsubscribe(self, event_type: str, handler: Callable) -> bool:
        """
        Unsubscribe from events of a specific type
        
        Args:
            event_type: Type of events to unsubscribe from
            handler: Handler function to remove
            
        Returns:
            True if handler was found and removed, False otherwise
        """
        if event_type in self._subscribers:
            if handler in self._subscribers[event_type]:
                self._subscribers[event_type].remove(handler)
                self._stats['subscribers_count'] = sum(len(handlers) for handlers in self._subscribers.values())
                self.logger.info(f"Unsubscribed handler from event type: {event_type}")
                return True
        
        return False
    
    async def publish(self, event: Event) -> None:
        """
        Publish an event to the bus
        
        Args:
            event: Event to publish
        """
        try:
            await self._event_queue.put(event)
            self._stats['events_published'] += 1
            
            self.logger.debug(f"Published event: {event.type} (ID: {event.id})")
            
        except Exception as e:
            self.logger.error(f"Failed to publish event {event.id}: {e}")
            self._stats['events_failed'] += 1
    
    async def publish_event(self, event_type: str, data: Dict[str, Any], 
                           priority: EventPriority = EventPriority.NORMAL,
                           source: str = "", correlation_id: Optional[str] = None) -> str:
        """
        Convenience method to create and publish an event
        
        Args:
            event_type: Type of event
            data: Event data
            priority: Event priority
            source: Source of the event
            correlation_id: Correlation ID for request tracking
            
        Returns:
            Event ID
        """
        event = Event(
            type=event_type,
            data=data,
            priority=priority,
            source=source,
            correlation_id=correlation_id
        )
        
        await self.publish(event)
        return event.id
    
    async def _process_events(self) -> None:
        """Process events from the queue"""
        while self._running:
            try:
                # Wait for an event with timeout to allow checking _running flag
                event = await asyncio.wait_for(self._event_queue.get(), timeout=1.0)
                
                await self._handle_event(event)
                self._stats['events_processed'] += 1
                
            except asyncio.TimeoutError:
                # Timeout is expected, continue processing
                continue
            except Exception as e:
                self.logger.error(f"Error processing event: {e}")
                self._stats['events_failed'] += 1
    
    async def _handle_event(self, event: Event) -> None:
        """Handle a single event by calling all subscribers"""
        handlers = self._subscribers.get(event.type, set())
        
        if not handlers:
            self.logger.debug(f"No handlers for event type: {event.type}")
            return
        
        # Call all handlers for this event type
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
                    
            except Exception as e:
                self.logger.error(f"Handler failed for event {event.id}: {e}")
                self._stats['events_failed'] += 1
    
    async def start(self) -> None:
        """Start the event bus processing"""
        if self._running:
            return
        
        self._running = True
        
        # Start event processing task
        asyncio.create_task(self._process_events())
        
        self.logger.info("EventBus started")
    
    async def stop(self) -> None:
        """Stop the event bus processing"""
        self._running = False
        
        # Process any remaining events
        while not self._event_queue.empty():
            try:
                event = self._event_queue.get_nowait()
                await self._handle_event(event)
            except asyncio.QueueEmpty:
                break
            except Exception as e:
                self.logger.error(f"Error processing remaining event: {e}")
        
        self.logger.info("EventBus stopped")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get event bus statistics"""
        return {
            **self._stats,
            'queue_size': self._event_queue.qsize(),
            'event_types': list(self._subscribers.keys()),
            'running': self._running
        }
    
    def clear_subscribers(self) -> None:
        """Clear all subscribers (useful for testing)"""
        self._subscribers.clear()
        self._stats['subscribers_count'] = 0
        self.logger.info("All subscribers cleared")


# Global event bus instance
_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Get the global event bus instance"""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


# Convenience functions
async def publish_event(event_type: str, data: Dict[str, Any], 
                       priority: EventPriority = EventPriority.NORMAL,
                       source: str = "", correlation_id: Optional[str] = None) -> str:
    """Publish an event using the global event bus"""
    bus = get_event_bus()
    return await bus.publish_event(event_type, data, priority, source, correlation_id)


def subscribe_to_events(event_type: str, handler: Callable) -> None:
    """Subscribe to events using the global event bus"""
    bus = get_event_bus()
    bus.subscribe(event_type, handler)