from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from enum import Enum
import logging
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)

class ModelProvider(str, Enum):
    """Supported AI model providers"""
    GEMINI = "gemini"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    HUGGINGFACE = "huggingface"
    AZURE_OPENAI = "azure_openai"

class ContentType(str, Enum):
    """Types of content for analysis"""
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    MIXED = "mixed"

class ModerationAction(str, Enum):
    """Possible moderation actions"""
    APPROVED = "approved"
    NEEDS_REVIEW = "needs_review"
    REJECTED = "rejected"
    ESCALATED = "escalated"

@dataclass
class AnalysisRequest:
    """Request object for content analysis"""
    content_id: str
    content_type: ContentType
    file_path: Optional[str] = None
    text_content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None
    priority: int = 5  # 1-10, 10 being highest

@dataclass
class AnalysisResult:
    """Result object from content analysis"""
    content_id: str
    confidence: float  # 0.0 to 1.0
    action: ModerationAction
    reasoning: str
    categories: List[str]
    safety_scores: Dict[str, float]
    quality_score: float
    brand_safety_score: float
    compliance_score: float
    concerns: List[str]
    suggestions: List[str]
    processing_time: float
    model_used: str
    raw_response: Optional[Dict[str, Any]] = None

class BaseAIAgent(ABC):
    """Abstract base class for AI moderation agents"""
    
    def __init__(self, name: str, provider: ModelProvider, config: Dict[str, Any]):
        self.name = name
        self.provider = provider
        self.config = config
        self.enabled = False
        self._initialize()
    
    @abstractmethod
    def _initialize(self) -> None:
        """Initialize the AI agent with provider-specific setup"""
        pass
    
    @abstractmethod
    async def analyze_content(self, request: AnalysisRequest) -> AnalysisResult:
        """Analyze content and return moderation result"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the agent is healthy and responsive"""
        pass
    
    @abstractmethod
    def get_supported_content_types(self) -> List[ContentType]:
        """Return list of supported content types"""
        pass
    
    def is_available(self) -> bool:
        """Check if agent is available for use"""
        return self.enabled

class AgentCoordinator:
    """Coordinates multiple AI agents for robust moderation"""
    
    def __init__(self):
        self.agents: Dict[str, BaseAIAgent] = {}
        self.fallback_chain: List[str] = []
        self.routing_rules: Dict[ContentType, List[str]] = {}
        self.performance_metrics: Dict[str, Dict[str, Any]] = {}
    
    def register_agent(self, agent: BaseAIAgent, is_fallback: bool = False) -> None:
        """Register an AI agent"""
        self.agents[agent.name] = agent
        
        if is_fallback:
            self.fallback_chain.append(agent.name)
        
        # Initialize performance tracking
        self.performance_metrics[agent.name] = {
            "total_requests": 0,
            "successful_requests": 0,
            "average_response_time": 0.0,
            "last_used": None,
            "error_count": 0
        }
        
        logger.info(f"Registered AI agent: {agent.name} ({agent.provider})")
    
    def set_routing_rules(self, rules: Dict[ContentType, List[str]]) -> None:
        """Set routing rules for content types to specific agents"""
        self.routing_rules = rules
        logger.info(f"Updated routing rules: {rules}")
    
    async def analyze_content(self, request: AnalysisRequest) -> AnalysisResult:
        """Analyze content using the best available agent"""
        
        start_time = asyncio.get_event_loop().time()
        
        # Determine which agents to try
        candidate_agents = self._get_candidate_agents(request.content_type)
        
        last_error = None
        for agent_name in candidate_agents:
            agent = self.agents.get(agent_name)
            
            if not agent or not agent.is_available():
                continue
            
            try:
                # Update metrics
                self.performance_metrics[agent_name]["total_requests"] += 1
                self.performance_metrics[agent_name]["last_used"] = datetime.now()
                
                # Perform analysis
                result = await agent.analyze_content(request)
                
                # Update success metrics
                self.performance_metrics[agent_name]["successful_requests"] += 1
                processing_time = asyncio.get_event_loop().time() - start_time
                self._update_response_time(agent_name, processing_time)
                
                result.processing_time = processing_time
                result.model_used = f"{agent.name} ({agent.provider})"
                
                logger.info(f"Content {request.content_id} analyzed by {agent_name}: {result.action} (confidence: {result.confidence:.3f})")
                return result
                
            except Exception as e:
                last_error = e
                self.performance_metrics[agent_name]["error_count"] += 1
                logger.warning(f"Agent {agent_name} failed for content {request.content_id}: {str(e)}")
                continue
        
        # If all agents failed, return a fallback result
        logger.error(f"All agents failed for content {request.content_id}. Last error: {last_error}")
        return self._create_fallback_result(request, last_error)
    
    def _get_candidate_agents(self, content_type: ContentType) -> List[str]:
        """Get ordered list of candidate agents for content type"""
        
        # First, try agents specifically configured for this content type
        candidates = self.routing_rules.get(content_type, [])
        
        # Add agents that support this content type
        for agent_name, agent in self.agents.items():
            if (agent_name not in candidates and 
                agent.is_available() and 
                content_type in agent.get_supported_content_types()):
                candidates.append(agent_name)
        
        # Add fallback agents
        for fallback_agent in self.fallback_chain:
            if fallback_agent not in candidates:
                candidates.append(fallback_agent)
        
        return candidates
    
    def _update_response_time(self, agent_name: str, response_time: float) -> None:
        """Update average response time for agent"""
        metrics = self.performance_metrics[agent_name]
        current_avg = metrics["average_response_time"]
        total_requests = metrics["successful_requests"]
        
        if total_requests == 1:
            metrics["average_response_time"] = response_time
        else:
            # Exponential moving average
            metrics["average_response_time"] = (current_avg * 0.8) + (response_time * 0.2)
    
    def _create_fallback_result(self, request: AnalysisRequest, error: Exception) -> AnalysisResult:
        """Create a fallback result when all agents fail"""
        
        return AnalysisResult(
            content_id=request.content_id,
            confidence=0.5,  # Neutral confidence
            action=ModerationAction.NEEDS_REVIEW,  # Always require human review
            reasoning=f"All AI agents failed. Manual review required. Error: {str(error)}",
            categories=["system_error"],
            safety_scores={"overall": 0.5},
            quality_score=0.5,
            brand_safety_score=0.5,
            compliance_score=0.5,
            concerns=["System error - manual review required"],
            suggestions=["Please retry analysis or conduct manual review"],
            processing_time=0.0,
            model_used="fallback_system",
            raw_response={"error": str(error)}
        )
    
    async def health_check_all(self) -> Dict[str, bool]:
        """Check health of all registered agents"""
        
        health_status = {}
        
        for agent_name, agent in self.agents.items():
            try:
                health_status[agent_name] = await agent.health_check()
            except Exception as e:
                health_status[agent_name] = False
                logger.error(f"Health check failed for {agent_name}: {str(e)}")
        
        return health_status
    
    def get_performance_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get performance metrics for all agents"""
        return self.performance_metrics.copy()
    
    def get_best_agent_for_content_type(self, content_type: ContentType) -> Optional[str]:
        """Get the best performing agent for a specific content type"""
        
        candidates = self._get_candidate_agents(content_type)
        
        if not candidates:
            return None
        
        # Score agents based on success rate and response time
        best_agent = None
        best_score = -1
        
        for agent_name in candidates:
            if agent_name not in self.performance_metrics:
                continue
            
            metrics = self.performance_metrics[agent_name]
            total = metrics["total_requests"]
            
            if total == 0:
                continue
            
            success_rate = metrics["successful_requests"] / total
            avg_time = metrics["average_response_time"]
            
            # Score formula: prioritize success rate, then response time
            score = success_rate * 0.8 - (avg_time / 10.0) * 0.2
            
            if score > best_score:
                best_score = score
                best_agent = agent_name
        
        return best_agent

class ModerationPipeline:
    """High-level moderation pipeline using agentic framework"""
    
    def __init__(self, coordinator: AgentCoordinator):
        self.coordinator = coordinator
        self.preprocessing_steps: List[callable] = []
        self.postprocessing_steps: List[callable] = []
        self.escalation_rules: List[callable] = []
    
    def add_preprocessing_step(self, step: callable) -> None:
        """Add a preprocessing step"""
        self.preprocessing_steps.append(step)
    
    def add_postprocessing_step(self, step: callable) -> None:
        """Add a postprocessing step"""
        self.postprocessing_steps.append(step)
    
    def add_escalation_rule(self, rule: callable) -> None:
        """Add an escalation rule"""
        self.escalation_rules.append(rule)
    
    async def process_content(self, request: AnalysisRequest) -> AnalysisResult:
        """Process content through the full pipeline"""
        
        # Preprocessing
        for step in self.preprocessing_steps:
            request = await step(request)
        
        # AI Analysis
        result = await self.coordinator.analyze_content(request)
        
        # Postprocessing
        for step in self.postprocessing_steps:
            result = await step(result, request)
        
        # Check escalation rules
        for rule in self.escalation_rules:
            should_escalate = await rule(result, request)
            if should_escalate:
                result.action = ModerationAction.ESCALATED
                result.concerns.append("Content escalated due to policy rules")
                break
        
        return result

# Utility functions for common preprocessing/postprocessing steps
async def validate_file_safety(request: AnalysisRequest) -> AnalysisRequest:
    """Preprocessing: Validate file safety"""
    if request.file_path:
        # Add file validation logic here
        # - Virus scanning
        # - File type validation
        # - Size checks
        pass
    return request

async def enhance_with_context(result: AnalysisResult, request: AnalysisRequest) -> AnalysisResult:
    """Postprocessing: Enhance result with additional context"""
    if request.metadata:
        # Add context-aware adjustments
        # - Company-specific rules
        # - Historical patterns
        # - User preferences
        pass
    return result

async def check_high_risk_content(result: AnalysisResult, request: AnalysisRequest) -> bool:
    """Escalation rule: Check for high-risk content"""
    high_risk_categories = ["violence", "hate_speech", "adult_content", "illegal_content"]
    return any(category in result.categories for category in high_risk_categories)

async def check_low_confidence_threshold(result: AnalysisResult, request: AnalysisRequest) -> bool:
    """Escalation rule: Escalate low confidence decisions"""
    return result.confidence < 0.6

# Global pipeline instance
moderation_pipeline = None

def get_moderation_pipeline() -> ModerationPipeline:
    """Get or create the global moderation pipeline"""
    global moderation_pipeline
    
    if moderation_pipeline is None:
        coordinator = AgentCoordinator()
        moderation_pipeline = ModerationPipeline(coordinator)
        
        # Add default preprocessing steps
        moderation_pipeline.add_preprocessing_step(validate_file_safety)
        
        # Add default postprocessing steps
        moderation_pipeline.add_postprocessing_step(enhance_with_context)
        
        # Add default escalation rules
        moderation_pipeline.add_escalation_rule(check_high_risk_content)
        moderation_pipeline.add_escalation_rule(check_low_confidence_threshold)
    
    return moderation_pipeline
