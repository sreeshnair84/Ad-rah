import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import json
import logging
from pathlib import Path

from .ai_agent_framework import AgentCoordinator, ModerationPipeline, ContentType, get_moderation_pipeline
from .ai_agents import create_agent, ModelProvider

logger = logging.getLogger(__name__)

@dataclass
class AgentConfig:
    """Configuration for an AI agent"""
    name: str
    provider: ModelProvider
    enabled: bool
    is_fallback: bool
    config: Dict[str, Any]
    supported_content_types: Optional[List[ContentType]] = None
    priority: int = 5  # 1-10, higher is better

class AIServiceManager:
    """Manages multiple AI services and provides easy switching between providers"""
    
    def __init__(self):
        self.coordinator: Optional[AgentCoordinator] = None
        self.pipeline: Optional[ModerationPipeline] = None
        self.agent_configs: Dict[str, AgentConfig] = {}
        self.current_primary_agent: Optional[str] = None
        self.config_file_path = Path("ai_service_config.json")
        
        self._load_default_configs()
        self._initialize_services()
    
    def _load_default_configs(self) -> None:
        """Load default agent configurations"""
        
        # Gemini configuration
        self.agent_configs["gemini"] = AgentConfig(
            name="gemini",
            provider=ModelProvider.GEMINI,
            enabled=bool(os.getenv("GEMINI_API_KEY")),
            is_fallback=False,
            priority=8,
            config={
                "api_key": os.getenv("GEMINI_API_KEY"),
                "model": "gemini-1.5-flash",
                "timeout": 30
            }
        )
        
        # OpenAI configuration
        self.agent_configs["openai"] = AgentConfig(
            name="openai",
            provider=ModelProvider.OPENAI,
            enabled=bool(os.getenv("OPENAI_API_KEY")),
            is_fallback=True,
            priority=7,
            config={
                "api_key": os.getenv("OPENAI_API_KEY"),
                "model": "gpt-4o",
                "base_url": "https://api.openai.com/v1",
                "timeout": 30
            }
        )
        
        # Azure OpenAI configuration
        self.agent_configs["azure_openai"] = AgentConfig(
            name="azure_openai",
            provider=ModelProvider.AZURE_OPENAI,
            enabled=bool(os.getenv("AZURE_OPENAI_API_KEY")),
            is_fallback=True,
            priority=6,
            config={
                "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
                "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"),
                "deployment": os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4"),
                "api_version": "2024-02-01",
                "timeout": 30
            }
        )
        
        # Ollama configuration (local)
        self.agent_configs["ollama"] = AgentConfig(
            name="ollama",
            provider=ModelProvider.OLLAMA,
            enabled=True,  # Always enabled if service is running
            is_fallback=True,
            priority=5,
            config={
                "base_url": os.getenv("OLLAMA_URL", "http://localhost:11434"),
                "model": os.getenv("OLLAMA_MODEL", "llama3.2"),
                "timeout": 60
            }
        )
        
        # Anthropic configuration
        self.agent_configs["anthropic"] = AgentConfig(
            name="anthropic",
            provider=ModelProvider.ANTHROPIC,
            enabled=bool(os.getenv("ANTHROPIC_API_KEY")),
            is_fallback=True,
            priority=7,
            config={
                "api_key": os.getenv("ANTHROPIC_API_KEY"),
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 2048,
                "timeout": 30
            }
        )
        
        # Load custom configurations if available
        self._load_config_file()
    
    def _load_config_file(self) -> None:
        """Load configurations from file"""
        
        if not self.config_file_path.exists():
            return
        
        try:
            with open(self.config_file_path, 'r') as f:
                config_data = json.load(f)
            
            for agent_name, agent_data in config_data.get("agents", {}).items():
                if agent_name in self.agent_configs:
                    # Update existing config
                    self.agent_configs[agent_name].enabled = agent_data.get("enabled", False)
                    self.agent_configs[agent_name].is_fallback = agent_data.get("is_fallback", False)
                    self.agent_configs[agent_name].priority = agent_data.get("priority", 5)
                    self.agent_configs[agent_name].config.update(agent_data.get("config", {}))
            
            self.current_primary_agent = config_data.get("primary_agent")
            
            logger.info(f"Loaded AI service configuration from {self.config_file_path}")
            
        except Exception as e:
            logger.warning(f"Failed to load config file: {str(e)}")
    
    def save_config_file(self) -> None:
        """Save current configurations to file"""
        
        try:
            config_data = {
                "primary_agent": self.current_primary_agent,
                "agents": {}
            }
            
            for agent_name, agent_config in self.agent_configs.items():
                config_data["agents"][agent_name] = {
                    "enabled": agent_config.enabled,
                    "is_fallback": agent_config.is_fallback,
                    "priority": agent_config.priority,
                    "config": {k: v for k, v in agent_config.config.items() if k != "api_key"}  # Don't save API keys
                }
            
            with open(self.config_file_path, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            logger.info(f"Saved AI service configuration to {self.config_file_path}")
            
        except Exception as e:
            logger.error(f"Failed to save config file: {str(e)}")
    
    def _initialize_services(self) -> None:
        """Initialize AI services"""
        
        try:
            # Create coordinator and pipeline
            self.coordinator = AgentCoordinator()
            self.pipeline = get_moderation_pipeline()
            self.pipeline.coordinator = self.coordinator
            
            # Register agents based on priority
            sorted_agents = sorted(
                self.agent_configs.values(),
                key=lambda x: x.priority,
                reverse=True
            )
            
            for agent_config in sorted_agents:
                if not agent_config.enabled:
                    continue
                
                try:
                    agent = create_agent(agent_config.provider, agent_config.config)
                    
                    if agent.is_available():
                        self.coordinator.register_agent(agent, agent_config.is_fallback)
                        
                        if not self.current_primary_agent and not agent_config.is_fallback:
                            self.current_primary_agent = agent_config.name
                        
                        logger.info(f"Registered agent: {agent_config.name} ({agent_config.provider})")
                    else:
                        logger.warning(f"Agent {agent_config.name} is not available")
                        
                except Exception as e:
                    logger.error(f"Failed to initialize agent {agent_config.name}: {str(e)}")
                    continue
            
            # Set up routing rules
            self._setup_routing_rules()
            
            logger.info("AI service manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize AI services: {str(e)}")
            raise
    
    def _setup_routing_rules(self) -> None:
        """Setup content type routing rules"""
        
        if not self.coordinator:
            return
        
        routing_rules = {}
        
        # Get available agents for each content type
        for content_type in ContentType:
            suitable_agents = []
            
            for agent_name, agent in self.coordinator.agents.items():
                if agent.is_available() and content_type in agent.get_supported_content_types():
                    agent_config = self.agent_configs.get(agent_name.replace("_agent", ""))
                    if agent_config:
                        suitable_agents.append((agent_name, agent_config.priority))
            
            # Sort by priority
            suitable_agents.sort(key=lambda x: x[1], reverse=True)
            routing_rules[content_type] = [agent[0] for agent in suitable_agents]
        
        self.coordinator.set_routing_rules(routing_rules)
        logger.info(f"Setup routing rules: {routing_rules}")
    
    def switch_primary_agent(self, agent_name: str) -> bool:
        """Switch to a different primary agent"""
        
        if agent_name not in self.agent_configs:
            logger.error(f"Unknown agent: {agent_name}")
            return False
        
        agent_config = self.agent_configs[agent_name]
        
        if not agent_config.enabled:
            logger.error(f"Agent {agent_name} is not enabled")
            return False
        
        # Check if agent is available
        agent_instance = None
        for coordinator_agent_name, coordinator_agent in self.coordinator.agents.items():
            if coordinator_agent_name.startswith(agent_name):
                agent_instance = coordinator_agent
                break
        
        if not agent_instance or not agent_instance.is_available():
            logger.error(f"Agent {agent_name} is not available")
            return False
        
        old_primary = self.current_primary_agent
        self.current_primary_agent = agent_name
        
        # Update routing to prefer this agent
        self._setup_routing_rules()
        
        logger.info(f"Switched primary agent from {old_primary} to {agent_name}")
        return True
    
    def enable_agent(self, agent_name: str) -> bool:
        """Enable an agent"""
        
        if agent_name not in self.agent_configs:
            return False
        
        self.agent_configs[agent_name].enabled = True
        
        try:
            agent_config = self.agent_configs[agent_name]
            agent = create_agent(agent_config.provider, agent_config.config)
            
            if agent.is_available():
                self.coordinator.register_agent(agent, agent_config.is_fallback)
                self._setup_routing_rules()
                logger.info(f"Enabled agent: {agent_name}")
                return True
            else:
                logger.warning(f"Agent {agent_name} could not be enabled - not available")
                return False
                
        except Exception as e:
            logger.error(f"Failed to enable agent {agent_name}: {str(e)}")
            return False
    
    def disable_agent(self, agent_name: str) -> bool:
        """Disable an agent"""
        
        if agent_name not in self.agent_configs:
            return False
        
        self.agent_configs[agent_name].enabled = False
        
        # Remove from coordinator if present
        agent_key = f"{agent_name}_agent"
        if agent_key in self.coordinator.agents:
            del self.coordinator.agents[agent_key]
            
            # Remove from fallback chain
            if agent_key in self.coordinator.fallback_chain:
                self.coordinator.fallback_chain.remove(agent_key)
            
            self._setup_routing_rules()
            logger.info(f"Disabled agent: {agent_name}")
        
        # Switch primary if this was the primary
        if self.current_primary_agent == agent_name:
            self._select_new_primary()
        
        return True
    
    def _select_new_primary(self) -> None:
        """Select a new primary agent when current one is disabled"""
        
        available_agents = [
            (name, config) for name, config in self.agent_configs.items()
            if config.enabled and not config.is_fallback
        ]
        
        if available_agents:
            # Select highest priority non-fallback agent
            available_agents.sort(key=lambda x: x[1].priority, reverse=True)
            self.current_primary_agent = available_agents[0][0]
            logger.info(f"Selected new primary agent: {self.current_primary_agent}")
        else:
            self.current_primary_agent = None
            logger.warning("No primary agent available")
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of all agents"""
        
        status = {
            "primary_agent": self.current_primary_agent,
            "agents": {},
            "performance_metrics": {}
        }
        
        for agent_name, agent_config in self.agent_configs.items():
            agent_status = {
                "provider": agent_config.provider.value,
                "enabled": agent_config.enabled,
                "is_fallback": agent_config.is_fallback,
                "priority": agent_config.priority,
                "available": False,
                "health": False
            }
            
            # Check if agent is registered and available
            coordinator_agent_name = f"{agent_name}_agent"
            if coordinator_agent_name in self.coordinator.agents:
                agent_instance = self.coordinator.agents[coordinator_agent_name]
                agent_status["available"] = agent_instance.is_available()
            
            status["agents"][agent_name] = agent_status
        
        # Include performance metrics
        if self.coordinator:
            status["performance_metrics"] = self.coordinator.get_performance_metrics()
        
        return status
    
    async def health_check_all(self) -> Dict[str, bool]:
        """Perform health check on all agents"""
        
        if not self.coordinator:
            return {}
        
        return await self.coordinator.health_check_all()
    
    def update_agent_config(self, agent_name: str, config_updates: Dict[str, Any]) -> bool:
        """Update agent configuration"""
        
        if agent_name not in self.agent_configs:
            return False
        
        try:
            # Update configuration
            self.agent_configs[agent_name].config.update(config_updates)
            
            # If agent is enabled, reinitialize it
            if self.agent_configs[agent_name].enabled:
                self.disable_agent(agent_name)
                self.enable_agent(agent_name)
            
            logger.info(f"Updated configuration for agent: {agent_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update agent {agent_name} config: {str(e)}")
            return False
    
    def get_pipeline(self) -> ModerationPipeline:
        """Get the moderation pipeline"""
        return self.pipeline

# Global service manager instance
_service_manager: Optional[AIServiceManager] = None

def get_ai_service_manager() -> AIServiceManager:
    """Get or create the global AI service manager"""
    global _service_manager
    
    if _service_manager is None:
        _service_manager = AIServiceManager()
    
    return _service_manager

def switch_ai_provider(provider_name: str) -> bool:
    """Convenient function to switch AI provider"""
    manager = get_ai_service_manager()
    return manager.switch_primary_agent(provider_name)
