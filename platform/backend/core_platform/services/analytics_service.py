"""
Analytics Service
================

Core service for processing and analyzing onboarding analytics data.
Provides comprehensive insights into user behavior, completion rates, and performance metrics.

Features:
- Real-time event processing
- Metrics calculation and aggregation
- Performance analytics
- Funnel analysis
- User journey tracking
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import json
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)


@dataclass
class OnboardingEvent:
    """Onboarding analytics event"""
    event_type: str
    step_id: str
    user_id: str
    user_role: str
    timestamp: str
    session_id: str
    metadata: Dict[str, Any]


@dataclass
class StepMetrics:
    """Metrics for a specific onboarding step"""
    step_id: str
    total_starts: int
    total_completions: int
    total_errors: int
    total_skips: int
    completion_rate: float
    error_rate: float
    skip_rate: float
    average_duration: float
    median_duration: float
    drop_off_rate: float


@dataclass
class UserJourney:
    """Complete user onboarding journey"""
    user_id: str
    user_role: str
    session_id: str
    start_time: str
    end_time: Optional[str]
    total_duration: Optional[int]
    completed_steps: List[str]
    failed_steps: List[str]
    skipped_steps: List[str]
    current_step: Optional[str]
    is_completed: bool
    drop_off_step: Optional[str]


@dataclass
class FunnelStep:
    """Funnel analysis step"""
    step_id: str
    step_name: str
    total_users: int
    completed_users: int
    conversion_rate: float
    drop_off_count: int
    drop_off_rate: float


class OnboardingAnalyticsService:
    """
    Service for processing onboarding analytics data and generating insights.
    """

    def __init__(self):
        self.service_name = "Onboarding Analytics Service"
        self.version = "1.0.0"
        
        # In-memory storage for demo (replace with database in production)
        self._events: List[OnboardingEvent] = []
        self._user_sessions: Dict[str, Dict[str, Any]] = {}
        
        # Step order definitions for funnel analysis
        self._step_orders = {
            'si': [
                'service_introduction',
                'integration_choice', 
                'business_systems_setup',
                'financial_systems_setup',
                'banking_connected',
                'reconciliation_setup',
                'integration_setup',
                'onboarding_complete'
            ],
            'app': [
                'service_introduction',
                'business_verification',
                'firs_integration_setup',
                'compliance_settings',
                'taxpayer_setup',
                'onboarding_complete'
            ],
            'hybrid': [
                'service_introduction',
                'service_selection',
                'business_verification',
                'integration_setup',
                'compliance_setup',
                'onboarding_complete'
            ]
        }
        
        logger.info(f"{self.service_name} v{self.version} initialized")

    async def handle_operation(self, operation: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle analytics operations"""
        try:
            logger.info(f"Handling analytics operation: {operation}")
            
            if operation == "process_onboarding_events":
                return await self._process_events(payload)
            elif operation == "get_onboarding_metrics":
                return await self._get_metrics(payload)
            elif operation == "get_dashboard_data":
                return await self._get_dashboard_data(payload)
            elif operation == "get_user_journey":
                return await self._get_user_journey(payload)
            elif operation == "get_step_performance":
                return await self._get_step_performance(payload)
            elif operation == "get_funnel_analysis":
                return await self._get_funnel_analysis(payload)
            else:
                raise ValueError(f"Unknown analytics operation: {operation}")
                
        except Exception as e:
            logger.error(f"Error handling analytics operation {operation}: {str(e)}", exc_info=True)
            raise RuntimeError(f"Analytics operation failed: {str(e)}")

    async def _process_events(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming analytics events"""
        try:
            events_data = payload.get("events", [])
            batch_timestamp = payload.get("batch_timestamp")
            
            processed_events = []
            for event_data in events_data:
                event = OnboardingEvent(
                    event_type=event_data["eventType"],
                    step_id=event_data["stepId"],
                    user_id=event_data["userId"],
                    user_role=event_data["userRole"],
                    timestamp=event_data["timestamp"],
                    session_id=event_data["sessionId"],
                    metadata=event_data.get("metadata", {})
                )
                
                # Store event
                self._events.append(event)
                
                # Update user session tracking
                self._update_user_session(event)
                
                processed_events.append(asdict(event))
            
            logger.info(f"Processed {len(processed_events)} analytics events")
            
            return {
                "operation": "process_onboarding_events",
                "success": True,
                "processed_events": len(processed_events),
                "batch_timestamp": batch_timestamp
            }
            
        except Exception as e:
            logger.error(f"Error processing analytics events: {str(e)}")
            raise

    async def _get_metrics(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Get aggregated onboarding metrics"""
        try:
            start_date = datetime.fromisoformat(payload["start_date"].replace('Z', '+00:00'))
            end_date = datetime.fromisoformat(payload["end_date"].replace('Z', '+00:00'))
            role_filter = payload.get("role_filter")
            step_filter = payload.get("step_filter")
            
            # Filter events by date range and criteria
            filtered_events = self._filter_events(start_date, end_date, role_filter, step_filter)
            
            # Calculate metrics
            metrics = self._calculate_metrics(filtered_events, role_filter)
            
            return {
                "operation": "get_onboarding_metrics",
                "success": True,
                "metrics": metrics,
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "filters": {
                    "role": role_filter,
                    "step": step_filter
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting analytics metrics: {str(e)}")
            raise

    async def _get_dashboard_data(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Get real-time dashboard data"""
        try:
            now = datetime.utcnow()
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Get today's events
            today_events = self._filter_events(today_start, now)
            
            # Calculate dashboard metrics
            active_sessions = len(set(e.session_id for e in today_events if e.event_type == 'session_start'))
            completed_sessions = len([e for e in today_events if e.event_type == 'session_complete'])
            completion_rate = (completed_sessions / active_sessions * 100) if active_sessions > 0 else 0
            
            # Find top drop-off step
            drop_offs = Counter()
            for event in today_events:
                if event.event_type == 'session_abandon':
                    drop_offs[event.step_id] += 1
            
            top_drop_off = drop_offs.most_common(1)[0][0] if drop_offs else "None"
            
            # Calculate average session time
            session_durations = []
            for event in today_events:
                if event.event_type == 'session_complete' and 'sessionDuration' in event.metadata:
                    session_durations.append(event.metadata['sessionDuration'])
            
            avg_session_time = sum(session_durations) / len(session_durations) if session_durations else 0
            
            return {
                "operation": "get_dashboard_data",
                "success": True,
                "data": {
                    "activeUsers": active_sessions,
                    "completionRateToday": round(completion_rate, 1),
                    "topDropOffStep": top_drop_off,
                    "averageSessionTime": round(avg_session_time / 1000 / 60, 1)  # Convert to minutes
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting dashboard data: {str(e)}")
            raise

    async def _get_user_journey(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed user journey analytics"""
        try:
            user_id = payload["user_id"]
            
            # Get all events for user
            user_events = [e for e in self._events if e.user_id == user_id]
            user_events.sort(key=lambda x: x.timestamp)
            
            if not user_events:
                return {
                    "operation": "get_user_journey",
                    "success": True,
                    "journey": None,
                    "message": "No journey data found for user"
                }
            
            # Build journey
            journey = self._build_user_journey(user_events)
            
            return {
                "operation": "get_user_journey",
                "success": True,
                "journey": asdict(journey)
            }
            
        except Exception as e:
            logger.error(f"Error getting user journey: {str(e)}")
            raise

    async def _get_step_performance(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Get step performance analytics"""
        try:
            step_id = payload["step_id"]
            role_filter = payload.get("role_filter")
            days = payload.get("days", 30)
            
            # Filter events for the step
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            step_events = [
                e for e in self._events 
                if e.step_id == step_id 
                and start_date <= datetime.fromisoformat(e.timestamp.replace('Z', '+00:00')) <= end_date
                and (not role_filter or e.user_role == role_filter)
            ]
            
            # Calculate step metrics
            metrics = self._calculate_step_metrics(step_id, step_events)
            
            return {
                "operation": "get_step_performance",
                "success": True,
                "step_performance": asdict(metrics)
            }
            
        except Exception as e:
            logger.error(f"Error getting step performance: {str(e)}")
            raise

    async def _get_funnel_analysis(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Get funnel analysis for onboarding flow"""
        try:
            role_filter = payload.get("role_filter")
            days = payload.get("days", 30)
            
            # Get relevant step order
            if role_filter and role_filter in self._step_orders:
                step_order = self._step_orders[role_filter]
            else:
                # Combine all steps if no role filter
                step_order = list(set().union(*self._step_orders.values()))
            
            # Filter events
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            filtered_events = self._filter_events(start_date, end_date, role_filter)
            
            # Calculate funnel
            funnel_steps = self._calculate_funnel(filtered_events, step_order, role_filter)
            
            return {
                "operation": "get_funnel_analysis",
                "success": True,
                "funnel": [asdict(step) for step in funnel_steps],
                "role_filter": role_filter,
                "days": days
            }
            
        except Exception as e:
            logger.error(f"Error getting funnel analysis: {str(e)}")
            raise

    def _filter_events(self, 
                      start_date: datetime, 
                      end_date: datetime, 
                      role_filter: Optional[str] = None,
                      step_filter: Optional[str] = None) -> List[OnboardingEvent]:
        """Filter events by criteria"""
        filtered = []
        
        for event in self._events:
            event_time = datetime.fromisoformat(event.timestamp.replace('Z', '+00:00'))
            
            if not (start_date <= event_time <= end_date):
                continue
                
            if role_filter and event.user_role != role_filter:
                continue
                
            if step_filter and event.step_id != step_filter:
                continue
                
            filtered.append(event)
        
        return filtered

    def _calculate_metrics(self, events: List[OnboardingEvent], role_filter: Optional[str]) -> Dict[str, Any]:
        """Calculate comprehensive onboarding metrics"""
        if not events:
            return {
                "completionRate": 0,
                "averageCompletionTime": 0,
                "dropOffPoints": [],
                "stepPerformance": [],
                "userSegments": [],
                "totalUsers": 0,
                "totalSessions": 0
            }
        
        # Basic counts
        total_sessions = len(set(e.session_id for e in events if e.event_type == 'session_start'))
        completed_sessions = len([e for e in events if e.event_type == 'session_complete'])
        completion_rate = (completed_sessions / total_sessions * 100) if total_sessions > 0 else 0
        
        # Average completion time
        completion_times = []
        for event in events:
            if event.event_type == 'session_complete' and 'sessionDuration' in event.metadata:
                completion_times.append(event.metadata['sessionDuration'])
        
        avg_completion_time = sum(completion_times) / len(completion_times) if completion_times else 0
        
        # Drop-off analysis
        drop_offs = Counter()
        for event in events:
            if event.event_type == 'session_abandon':
                drop_offs[event.step_id] += 1
        
        drop_off_points = [
            {
                "stepId": step_id,
                "dropOffRate": count / total_sessions * 100 if total_sessions > 0 else 0,
                "userCount": count
            }
            for step_id, count in drop_offs.most_common(5)
        ]
        
        # Step performance
        step_performance = []
        step_groups = defaultdict(list)
        for event in events:
            step_groups[event.step_id].append(event)
        
        for step_id, step_events in step_groups.items():
            if step_id not in ['session_start', 'session_complete']:
                metrics = self._calculate_step_metrics(step_id, step_events)
                step_performance.append(asdict(metrics))
        
        # User segments by role
        user_segments = []
        if not role_filter:
            role_groups = defaultdict(list)
            for event in events:
                role_groups[event.user_role].append(event)
            
            for role, role_events in role_groups.items():
                role_sessions = len(set(e.session_id for e in role_events if e.event_type == 'session_start'))
                role_completed = len([e for e in role_events if e.event_type == 'session_complete'])
                role_completion_rate = (role_completed / role_sessions * 100) if role_sessions > 0 else 0
                
                role_times = [
                    e.metadata['sessionDuration'] 
                    for e in role_events 
                    if e.event_type == 'session_complete' and 'sessionDuration' in e.metadata
                ]
                role_avg_time = sum(role_times) / len(role_times) if role_times else 0
                
                role_drop_offs = Counter(
                    e.step_id for e in role_events if e.event_type == 'session_abandon'
                )
                common_drop_off = role_drop_offs.most_common(1)[0][0] if role_drop_offs else "None"
                
                user_segments.append({
                    "role": role,
                    "completionRate": round(role_completion_rate, 1),
                    "averageTime": round(role_avg_time / 1000 / 60, 1),  # Convert to minutes
                    "commonDropOff": common_drop_off
                })
        
        return {
            "completionRate": round(completion_rate, 1),
            "averageCompletionTime": round(avg_completion_time / 1000 / 60, 1),  # Convert to minutes
            "dropOffPoints": drop_off_points,
            "stepPerformance": step_performance,
            "userSegments": user_segments,
            "totalUsers": len(set(e.user_id for e in events)),
            "totalSessions": total_sessions
        }

    def _calculate_step_metrics(self, step_id: str, events: List[OnboardingEvent]) -> StepMetrics:
        """Calculate metrics for a specific step"""
        starts = len([e for e in events if e.event_type == 'step_start'])
        completions = len([e for e in events if e.event_type == 'step_complete'])
        errors = len([e for e in events if e.event_type == 'step_error'])
        skips = len([e for e in events if e.event_type == 'step_skip'])
        
        completion_rate = (completions / starts * 100) if starts > 0 else 0
        error_rate = (errors / starts * 100) if starts > 0 else 0
        skip_rate = (skips / starts * 100) if starts > 0 else 0
        drop_off_rate = ((starts - completions - skips) / starts * 100) if starts > 0 else 0
        
        # Calculate durations
        durations = []
        for event in events:
            if event.event_type == 'step_complete' and 'duration' in event.metadata:
                durations.append(event.metadata['duration'])
        
        avg_duration = sum(durations) / len(durations) if durations else 0
        median_duration = sorted(durations)[len(durations) // 2] if durations else 0
        
        return StepMetrics(
            step_id=step_id,
            total_starts=starts,
            total_completions=completions,
            total_errors=errors,
            total_skips=skips,
            completion_rate=round(completion_rate, 1),
            error_rate=round(error_rate, 1),
            skip_rate=round(skip_rate, 1),
            average_duration=round(avg_duration / 1000, 1),  # Convert to seconds
            median_duration=round(median_duration / 1000, 1),
            drop_off_rate=round(drop_off_rate, 1)
        )

    def _calculate_funnel(self, events: List[OnboardingEvent], step_order: List[str], role_filter: Optional[str]) -> List[FunnelStep]:
        """Calculate conversion funnel"""
        funnel_steps = []
        
        # Get unique users who started sessions
        session_users = set(e.user_id for e in events if e.event_type == 'session_start')
        total_users = len(session_users)
        
        for i, step_id in enumerate(step_order):
            # Users who reached this step
            step_users = set(
                e.user_id for e in events 
                if e.step_id == step_id and e.event_type in ['step_start', 'step_complete']
            )
            
            # Users who completed this step
            completed_users = set(
                e.user_id for e in events 
                if e.step_id == step_id and e.event_type == 'step_complete'
            )
            
            reached_count = len(step_users)
            completed_count = len(completed_users)
            
            conversion_rate = (completed_count / reached_count * 100) if reached_count > 0 else 0
            drop_off_count = reached_count - completed_count
            drop_off_rate = (drop_off_count / reached_count * 100) if reached_count > 0 else 0
            
            funnel_steps.append(FunnelStep(
                step_id=step_id,
                step_name=step_id.replace('_', ' ').title(),
                total_users=reached_count,
                completed_users=completed_count,
                conversion_rate=round(conversion_rate, 1),
                drop_off_count=drop_off_count,
                drop_off_rate=round(drop_off_rate, 1)
            ))
        
        return funnel_steps

    def _build_user_journey(self, events: List[OnboardingEvent]) -> UserJourney:
        """Build complete user journey from events"""
        if not events:
            raise ValueError("No events provided for user journey")
        
        first_event = events[0]
        last_event = events[-1]
        
        # Extract journey data
        session_start = next((e for e in events if e.event_type == 'session_start'), None)
        session_end = next((e for e in events if e.event_type in ['session_complete', 'session_abandon']), None)
        
        completed_steps = list(set(e.step_id for e in events if e.event_type == 'step_complete'))
        failed_steps = list(set(e.step_id for e in events if e.event_type == 'step_error'))
        skipped_steps = list(set(e.step_id for e in events if e.event_type == 'step_skip'))
        
        is_completed = any(e.event_type == 'session_complete' for e in events)
        current_step = last_event.step_id if not is_completed else None
        drop_off_step = session_end.step_id if session_end and session_end.event_type == 'session_abandon' else None
        
        # Calculate duration
        total_duration = None
        if session_start and session_end:
            start_time = datetime.fromisoformat(session_start.timestamp.replace('Z', '+00:00'))
            end_time = datetime.fromisoformat(session_end.timestamp.replace('Z', '+00:00'))
            total_duration = int((end_time - start_time).total_seconds() * 1000)
        
        return UserJourney(
            user_id=first_event.user_id,
            user_role=first_event.user_role,
            session_id=first_event.session_id,
            start_time=session_start.timestamp if session_start else first_event.timestamp,
            end_time=session_end.timestamp if session_end else None,
            total_duration=total_duration,
            completed_steps=completed_steps,
            failed_steps=failed_steps,
            skipped_steps=skipped_steps,
            current_step=current_step,
            is_completed=is_completed,
            drop_off_step=drop_off_step
        )

    def _update_user_session(self, event: OnboardingEvent):
        """Update user session tracking"""
        session_key = f"{event.user_id}_{event.session_id}"
        
        if session_key not in self._user_sessions:
            self._user_sessions[session_key] = {
                "user_id": event.user_id,
                "session_id": event.session_id,
                "user_role": event.user_role,
                "start_time": event.timestamp,
                "last_activity": event.timestamp,
                "events": []
            }
        
        self._user_sessions[session_key]["events"].append(asdict(event))
        self._user_sessions[session_key]["last_activity"] = event.timestamp
