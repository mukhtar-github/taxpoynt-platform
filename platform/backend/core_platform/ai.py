"""
Core Platform AI Service
========================
AI service for generating insights and intelligent analysis.
"""

import asyncio
import logging
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

logger = logging.getLogger(__name__)

# OpenAI client import with fallback
try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    logger.warning("OpenAI package not available - AI service will run in mock mode")
    OPENAI_AVAILABLE = False


class AIProvider(Enum):
    """AI service providers"""
    OPENAI = "openai"
    AZURE_OPENAI = "azure_openai"
    ANTHROPIC = "anthropic"
    LOCAL_MODEL = "local_model"
    MOCK = "mock"


class AICapability(Enum):
    """AI service capabilities"""
    TEXT_GENERATION = "text_generation"
    INSIGHT_GENERATION = "insight_generation"
    ANOMALY_DETECTION = "anomaly_detection"
    TREND_ANALYSIS = "trend_analysis"
    CLASSIFICATION = "classification"
    SUMMARIZATION = "summarization"


@dataclass
class AIConfig:
    """AI service configuration"""
    provider: AIProvider = AIProvider.MOCK
    api_key: Optional[str] = None
    api_endpoint: Optional[str] = None
    model_name: str = "gpt-3.5-turbo"
    max_tokens: int = 1000
    temperature: float = 0.7
    timeout_seconds: int = 30
    retry_attempts: int = 3
    enable_caching: bool = True
    mock_responses: bool = True  # For development/testing


@dataclass
class AIRequest:
    """AI service request"""
    request_id: str = ""
    prompt: str = ""
    context: Dict[str, Any] = None
    capabilities: List[AICapability] = None
    parameters: Dict[str, Any] = None
    
    def __post_init__(self):
        if not self.request_id:
            self.request_id = str(uuid.uuid4())
        if self.context is None:
            self.context = {}
        if self.capabilities is None:
            self.capabilities = [AICapability.TEXT_GENERATION]
        if self.parameters is None:
            self.parameters = {}


@dataclass
class AIResponse:
    """AI service response"""
    request_id: str = ""
    content: str = ""
    insights: List[Dict[str, Any]] = None
    confidence: float = 0.0
    processing_time_ms: int = 0
    tokens_used: int = 0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.insights is None:
            self.insights = []
        if self.metadata is None:
            self.metadata = {}


class AIService:
    """
    AI service for generating insights and intelligent analysis.
    
    Provides a unified interface for various AI capabilities including
    insight generation, anomaly detection, and trend analysis.
    """
    
    def __init__(self, config: Optional[AIConfig] = None):
        """
        Initialize AI service.
        
        Args:
            config: AI service configuration
        """
        self.config = config or AIConfig()
        self.is_initialized = False
        self._available = False
        self._capabilities: List[AICapability] = []
        self._openai_client: Optional[AsyncOpenAI] = None
        
    async def initialize(self) -> bool:
        """
        Initialize the AI service.
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            if self.config.provider == AIProvider.OPENAI:
                # Real OpenAI service initialization
                if not OPENAI_AVAILABLE:
                    logger.error("OpenAI package not available - falling back to mock mode")
                    self.config.provider = AIProvider.MOCK
                    return await self._initialize_mock()
                
                # Get API key from config or environment
                api_key = self.config.api_key or os.getenv("OPENAI_API_KEY")
                if not api_key:
                    logger.error("OpenAI API key not provided - falling back to mock mode")
                    self.config.provider = AIProvider.MOCK
                    return await self._initialize_mock()
                
                # Initialize OpenAI client
                self._openai_client = AsyncOpenAI(api_key=api_key)
                
                # Test the connection
                try:
                    # Simple test to verify API key works
                    response = await self._openai_client.chat.completions.create(
                        model=self.config.model_name,
                        messages=[{"role": "user", "content": "Hello"}],
                        max_tokens=5
                    )
                    logger.info(f"OpenAI connection test successful - Model: {self.config.model_name}")
                except Exception as e:
                    logger.error(f"OpenAI connection test failed: {e} - falling back to mock mode")
                    self.config.provider = AIProvider.MOCK
                    self._openai_client = None
                    return await self._initialize_mock()
                
                self._available = True
                self._capabilities = [
                    AICapability.INSIGHT_GENERATION,
                    AICapability.TREND_ANALYSIS,
                    AICapability.ANOMALY_DETECTION,
                    AICapability.CLASSIFICATION,
                    AICapability.SUMMARIZATION
                ]
                logger.info(f"✅ Real OpenAI AI service initialized successfully - Model: {self.config.model_name}")
                
            elif self.config.provider == AIProvider.MOCK:
                return await self._initialize_mock()
            else:
                logger.warning(f"AI provider {self.config.provider} not implemented, falling back to mock mode")
                self.config.provider = AIProvider.MOCK
                return await self._initialize_mock()
            
            self.is_initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize AI service: {e}")
            self._available = False
            return False
    
    async def _initialize_mock(self) -> bool:
        """Initialize mock AI service"""
        self._available = True
        self._capabilities = [
            AICapability.INSIGHT_GENERATION,
            AICapability.TREND_ANALYSIS,
            AICapability.ANOMALY_DETECTION,
            AICapability.CLASSIFICATION,
            AICapability.SUMMARIZATION
        ]
        logger.info("Mock AI service initialized successfully")
        return True
    
    def is_available(self) -> bool:
        """
        Check if AI service is available.
        
        Returns:
            True if AI service is available, False otherwise
        """
        return self._available and self.is_initialized
    
    def get_capabilities(self) -> List[AICapability]:
        """
        Get available AI capabilities.
        
        Returns:
            List of available capabilities
        """
        return self._capabilities.copy()
    
    async def generate_insights(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate insights from provided data.
        
        Args:
            data: Input data for insight generation
            
        Returns:
            Dictionary containing generated insights
        """
        if not self.is_available():
            logger.warning("AI service not available for insight generation")
            return {"insights": []}
        
        try:
            if self.config.provider == AIProvider.OPENAI and self._openai_client:
                return await self._generate_openai_insights(data)
            elif self.config.provider == AIProvider.MOCK:
                return await self._generate_mock_insights(data)
            else:
                # Fallback to mock if real AI not available
                return await self._generate_mock_insights(data)
                
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            # Fallback to mock insights on error
            try:
                return await self._generate_mock_insights(data)
            except:
                return {"insights": []}
    
    async def _generate_openai_insights(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate insights using OpenAI.
        
        Args:
            data: Input data for insight generation
            
        Returns:
            OpenAI-generated insights response
        """
        try:
            # Create prompt for business insights
            prompt = self._create_insights_prompt(data)
            
            response = await self._openai_client.chat.completions.create(
                model=self.config.model_name,
                messages=[
                    {"role": "system", "content": "You are a TaxPoynt AI assistant specializing in Nigerian business e-invoicing insights. Provide actionable business insights based on financial data."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature
            )
            
            # Parse OpenAI response into structured insights
            content = response.choices[0].message.content
            insights = self._parse_openai_insights_response(content, data)
            
            return {
                "insights": insights,
                "source": "openai",
                "model": self.config.model_name,
                "tokens_used": response.usage.total_tokens if response.usage else 0,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating OpenAI insights: {e}")
            # Fallback to mock insights
            return await self._generate_mock_insights(data)
    
    def _create_insights_prompt(self, data: Dict[str, Any]) -> str:
        """Create prompt for OpenAI insights generation"""
        prompt_parts = [
            "Analyze the following Nigerian business financial data and provide actionable insights:",
            "",
            f"Data Summary: {json.dumps(data, indent=2)[:1000]}...",  # Limit prompt size
            "",
            "Please provide insights in the following areas:",
            "1. Revenue patterns and trends",
            "2. Tax compliance opportunities",
            "3. Cash flow optimization",
            "4. Business performance indicators",
            "5. Risk factors and recommendations",
            "",
            "Format your response as structured insights with clear titles, descriptions, and actionable recommendations."
        ]
        return "\n".join(prompt_parts)
    
    def _parse_openai_insights_response(self, content: str, original_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse OpenAI response into structured insights format"""
        insights = []
        
        # Basic parsing - split by numbered sections
        sections = content.split('\n\n')
        
        for i, section in enumerate(sections):
            if len(section.strip()) > 20:  # Only meaningful sections
                insights.append({
                    "title": f"AI Insight {i+1}",
                    "description": section.strip()[:500],  # Limit description length
                    "type": "ai_generated",
                    "confidence": 0.8,  # Default confidence for OpenAI
                    "impact": 0.7,
                    "source": "openai",
                    "recommendations": [
                        "Review this AI-generated insight",
                        "Validate with your business context",
                        "Consider implementing suggested actions"
                    ]
                })
        
        # If no meaningful insights parsed, create a summary insight
        if not insights:
            insights.append({
                "title": "AI Business Analysis",
                "description": content[:500] + "..." if len(content) > 500 else content,
                "type": "ai_summary",
                "confidence": 0.7,
                "impact": 0.6,
                "source": "openai",
                "recommendations": ["Review AI analysis for business insights"]
            })
        
        return insights[:5]  # Limit to 5 insights max
    
    async def _generate_mock_insights(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate mock insights for development and testing.
        
        Args:
            data: Input data
            
        Returns:
            Mock insights response
        """
        await asyncio.sleep(0.1)  # Simulate AI processing time
        
        # Extract some basic metrics for mock insights
        metrics_count = len(data.get("metrics", {}))
        kpis_count = len(data.get("kpis", {}))
        trends_count = len(data.get("trends", {}))
        
        mock_insights = []
        
        if metrics_count > 10:
            mock_insights.append({
                "title": "High Metrics Volume Detected",
                "description": f"System is tracking {metrics_count} metrics, which indicates good observability coverage.",
                "type": "performance",
                "confidence": 0.85,
                "impact": 0.6,
                "recommendations": [
                    "Consider consolidating similar metrics",
                    "Review metric collection frequency",
                    "Implement metric lifecycle management"
                ]
            })
        
        if kpis_count > 5:
            mock_insights.append({
                "title": "KPI Monitoring Active",
                "description": f"Platform is actively monitoring {kpis_count} KPIs for business insights.",
                "type": "business",
                "confidence": 0.9,
                "impact": 0.8,
                "recommendations": [
                    "Establish KPI review cadence",
                    "Set up automated alerting for critical KPIs",
                    "Create KPI dashboard for stakeholders"
                ]
            })
        
        if trends_count > 0:
            mock_insights.append({
                "title": "Trend Analysis Available",
                "description": f"System has identified {trends_count} trends for analysis.",
                "type": "trend",
                "confidence": 0.75,
                "impact": 0.7,
                "recommendations": [
                    "Review trend patterns for seasonality",
                    "Set up predictive alerts",
                    "Document trend analysis methodology"
                ]
            })
        
        # Always include a general system health insight
        mock_insights.append({
            "title": "Platform Analytics Active",
            "description": "TaxPoynt platform analytics system is operational and collecting insights.",
            "type": "system",
            "confidence": 0.95,
            "impact": 0.5,
            "recommendations": [
                "Continue monitoring system performance",
                "Review analytics configuration regularly",
                "Ensure data quality standards are met"
            ]
        })
        
        return {
            "insights": mock_insights,
            "metadata": {
                "generation_time": datetime.now().isoformat(),
                "data_sources": ["metrics", "kpis", "trends"],
                "model": "mock-ai-v1.0",
                "confidence_avg": sum(insight.get("confidence", 0) for insight in mock_insights) / len(mock_insights)
            }
        }
    
    async def detect_anomalies(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect anomalies in provided data.
        
        Args:
            data: Input data for anomaly detection
            
        Returns:
            Dictionary containing detected anomalies
        """
        if not self.is_available():
            return {"anomalies": []}
        
        try:
            # Mock anomaly detection
            return {
                "anomalies": [],
                "metadata": {
                    "detection_time": datetime.now().isoformat(),
                    "method": "mock-detection"
                }
            }
        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")
            return {"anomalies": []}
    
    async def analyze_trends(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze trends in provided data.
        
        Args:
            data: Input data for trend analysis
            
        Returns:
            Dictionary containing trend analysis results
        """
        if not self.is_available():
            return {"trends": []}
        
        try:
            # Mock trend analysis
            return {
                "trends": [],
                "metadata": {
                    "analysis_time": datetime.now().isoformat(),
                    "method": "mock-analysis"
                }
            }
        except Exception as e:
            logger.error(f"Error analyzing trends: {e}")
            return {"trends": []}
    
    async def classify_data(self, data: Any, categories: List[str]) -> Dict[str, Any]:
        """
        Classify data into provided categories.
        
        Args:
            data: Data to classify
            categories: Available categories
            
        Returns:
            Dictionary containing classification results
        """
        if not self.is_available():
            return {"classification": None, "confidence": 0.0}
        
        try:
            # Mock classification
            return {
                "classification": categories[0] if categories else "unknown",
                "confidence": 0.8,
                "metadata": {
                    "classification_time": datetime.now().isoformat(),
                    "available_categories": categories
                }
            }
        except Exception as e:
            logger.error(f"Error classifying data: {e}")
            return {"classification": None, "confidence": 0.0}
    
    async def summarize_text(self, text: str, max_length: int = 200) -> Dict[str, Any]:
        """
        Summarize provided text.
        
        Args:
            text: Text to summarize
            max_length: Maximum summary length
            
        Returns:
            Dictionary containing summary
        """
        if not self.is_available():
            return {"summary": text[:max_length] + "..." if len(text) > max_length else text}
        
        try:
            # Mock summarization
            summary = text[:max_length] + "..." if len(text) > max_length else text
            return {
                "summary": summary,
                "original_length": len(text),
                "summary_length": len(summary),
                "compression_ratio": len(summary) / len(text) if text else 0,
                "metadata": {
                    "summarization_time": datetime.now().isoformat(),
                    "method": "mock-summarization"
                }
            }
        except Exception as e:
            logger.error(f"Error summarizing text: {e}")
            return {"summary": text}
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform AI service health check.
        
        Returns:
            Health status dictionary
        """
        return {
            "status": "healthy" if self.is_available() else "unavailable",
            "provider": self.config.provider.value,
            "model": self.config.model_name,
            "capabilities": [cap.value for cap in self._capabilities],
            "is_initialized": self.is_initialized,
            "config": {
                "max_tokens": self.config.max_tokens,
                "temperature": self.config.temperature,
                "timeout_seconds": self.config.timeout_seconds
            }
        }


# Global AI service instance
_ai_service: Optional[AIService] = None


def get_ai_service() -> AIService:
    """
    Get global AI service instance.
    
    Returns:
        AIService instance
    """
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service


def initialize_ai_service(config: Optional[AIConfig] = None) -> AIService:
    """
    Initialize global AI service.
    
    Args:
        config: Optional AI configuration
        
    Returns:
        AIService instance
    """
    global _ai_service
    _ai_service = AIService(config)
    return _ai_service


# Export main class for direct import
AIService = AIService