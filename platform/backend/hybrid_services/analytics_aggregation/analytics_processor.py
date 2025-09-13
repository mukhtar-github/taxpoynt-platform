"""
Analytics Processor - Hybrid Services
====================================

High-level analytics processor that coordinates existing analytics components.
Integrates with unified_metrics, kpi_calculator, trend_analyzer, and insight_generator.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Union

from .unified_metrics import create_unified_metrics, MetricScope
from .kpi_calculator import create_kpi_calculator
from .trend_analyzer import create_trend_analyzer
from .insight_generator import create_insight_generator

logger = logging.getLogger(__name__)


class AnalyticsProcessor:
    """
    High-level analytics processor that coordinates all analytics components.
    Provides a unified interface for cross-role analytics processing.
    """
    
    def __init__(self):
        self.unified_metrics = create_unified_metrics()
        self.kpi_calculator = create_kpi_calculator(self.unified_metrics)
        self.trend_analyzer = create_trend_analyzer(self.unified_metrics, self.kpi_calculator)
        self.insight_generator = create_insight_generator(
            self.unified_metrics,
            self.kpi_calculator,
            self.trend_analyzer,
            None  # cross_role_reporting will be initialized later if needed
        )
        self.is_initialized = False
        
    async def initialize(self):
        """Initialize all analytics components"""
        if self.is_initialized:
            return
            
        logger.info("Initializing Analytics Processor")
        
        # Initialize components in dependency order
        await self.unified_metrics.initialize()
        await self.kpi_calculator.initialize()
        await self.trend_analyzer.initialize()
        await self.insight_generator.initialize()
        
        self.is_initialized = True
        logger.info("Analytics Processor initialized successfully")
    
    async def process_analytics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process analytics data using unified components"""
        if not self.is_initialized:
            await self.initialize()
            
        metric_type = data.get('type', 'general')
        
        # Create and aggregate metric
        metric_snapshot = await self.unified_metrics.create_metric_snapshot(
            MetricScope.SYSTEM_WIDE,
            include_breakdown=True
        )
        
        # Calculate relevant KPIs
        kpi_dashboard = await self.kpi_calculator.get_kpi_dashboard()
        
        # Get insights
        insights = await self.insight_generator.get_insights(limit=5)
        
        return {
            'processed': True,
            'metric_type': metric_type,
            'metric_snapshot': metric_snapshot.to_dict() if metric_snapshot else {},
            'kpi_summary': kpi_dashboard.to_dict() if kpi_dashboard else {},
            'insights': [insight.to_dict() for insight in insights] if insights else [],
            'timestamp': datetime.now().isoformat()
        }
    
    async def get_analytics_summary(self) -> Dict[str, Any]:
        """Get comprehensive analytics summary"""
        if not self.is_initialized:
            await self.initialize()
            
        return {
            'unified_metrics': await self.unified_metrics.get_metrics_summary(),
            'kpi_calculator': await self.kpi_calculator.get_kpi_summary(),
            'trend_analyzer': await self.trend_analyzer.get_trend_summary(),
            'insight_generator': await self.insight_generator.get_insight_summary(),
            'timestamp': datetime.now().isoformat()
        }


class AdvancedAnalyticsEngine:
    """Advanced analytics engine for complex data analysis"""
    
    def __init__(self):
        self.processor = AnalyticsProcessor()
        
    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform advanced analytics"""
        result = await self.processor.process_analytics(data)
        result.update({
            'analysis_type': 'advanced',
            'confidence': 0.95
        })
        return result


class BusinessIntelligenceService:
    """Business intelligence service for reporting and insights"""
    
    def __init__(self):
        self.processor = AnalyticsProcessor()
        
    async def generate_report(self, report_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate business intelligence report"""
        analytics_result = await self.processor.get_analytics_summary()
        
        return {
            'report_type': report_type,
            'analytics_data': analytics_result,
            'data_points': len(data),
            'generated_at': datetime.now().isoformat(),
            'status': 'completed'
        }