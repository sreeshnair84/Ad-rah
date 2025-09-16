import pytest
import asyncio
import json
import os
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from pathlib import Path
import tempfile

# Add the backend directory to the path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.ai_service_manager import AIServiceManager, AgentConfig, get_ai_service_manager
from app.services.ai_agents import ModelProvider
from app.services.ai_agent_framework import AgentCoordinator, ModerationPipeline


class TestAgentConfig:
    """Tests for AgentConfig dataclass"""

    def test_agent_config_creation(self):
        """Test creating an AgentConfig instance"""
        config = AgentConfig(
            name="test_agent",
            provider=ModelProvider.GEMINI,
            enabled=True,
            is_fallback=False,
            config={"api_key": "test_key", "model": "test_model"},
            priority=5
        )

        assert config.name == "test_agent"
        assert config.provider == ModelProvider.GEMINI
        assert config.enabled is True
        assert config.is_fallback is False
        assert config.config["api_key"] == "test_key"
        assert config.priority == 5

    def test_agent_config_defaults(self):
        """Test AgentConfig default values"""
        config = AgentConfig(
            name="test_agent",
            provider=ModelProvider.OPENAI,
            enabled=False,
            is_fallback=True,
            config={}
        )

        assert config.priority == 5  # Default priority
        assert config.supported_content_types is None


class TestAIServiceManager:
    """Comprehensive tests for AIServiceManager"""

    @pytest.fixture
    def temp_config_file(self):
        """Create a temporary config file for testing"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_data = {
                "primary_agent": "openai",
                "agents": {
                    "gemini": {
                        "enabled": False,
                        "is_fallback": True,
                        "priority": 6,
                        "config": {"model": "gemini-1.5-flash"}
                    }
                }
            }
            json.dump(config_data, f)
            f.flush()
            yield f.name

        # Cleanup
        os.unlink(f.name)

    @pytest.fixture
    def mock_coordinator(self):
        """Mock AgentCoordinator"""
        coordinator = Mock(spec=AgentCoordinator)
        coordinator.agents = {}
        coordinator.fallback_chain = []
        coordinator.get_performance_metrics.return_value = {}
        coordinator.health_check_all = AsyncMock(return_value={})
        return coordinator

    @pytest.fixture
    def mock_pipeline(self):
        """Mock ModerationPipeline"""
        pipeline = Mock(spec=ModerationPipeline)
        return pipeline

    @pytest.fixture
    def service_manager(self, mock_coordinator, mock_pipeline):
        """Service manager instance with mocked dependencies"""
        with patch('app.services.ai_service_manager.AgentCoordinator', return_value=mock_coordinator), \
             patch('app.services.ai_service_manager.get_moderation_pipeline', return_value=mock_pipeline), \
             patch.dict(os.environ, {
                 'GEMINI_API_KEY': 'test_gemini_key',
                 'OPENAI_API_KEY': 'test_openai_key'
             }):
            manager = AIServiceManager()
            return manager

    def test_initialization_with_api_keys(self, service_manager):
        """Test initialization when API keys are available"""
        assert 'gemini' in service_manager.agent_configs
        assert 'openai' in service_manager.agent_configs
        assert service_manager.agent_configs['gemini'].enabled is True
        assert service_manager.agent_configs['openai'].enabled is True

    def test_initialization_without_api_keys(self):
        """Test initialization when API keys are not available"""
        with patch.dict(os.environ, {}, clear=True):
            with patch('app.services.ai_service_manager.AgentCoordinator'), \
                 patch('app.services.ai_service_manager.get_moderation_pipeline'):
                manager = AIServiceManager()
                assert manager.agent_configs['gemini'].enabled is False
                assert manager.agent_configs['openai'].enabled is False

    def test_load_config_file(self, service_manager, temp_config_file):
        """Test loading configuration from file"""
        # Set the config file path
        service_manager.config_file_path = Path(temp_config_file)

        # Load the config
        service_manager._load_config_file()

        # Verify the config was loaded
        assert service_manager.current_primary_agent == "openai"
        assert service_manager.agent_configs['gemini'].enabled is False
        assert service_manager.agent_configs['gemini'].is_fallback is True
        assert service_manager.agent_configs['gemini'].priority == 6

    def test_load_config_file_not_exists(self, service_manager):
        """Test loading config when file doesn't exist"""
        # Reset primary agent to None to test the scenario
        service_manager.current_primary_agent = None
        service_manager.config_file_path = Path("nonexistent_file.json")
        # Should not raise an exception
        service_manager._load_config_file()
        assert service_manager.current_primary_agent is None

    def test_save_config_file(self, service_manager, tmp_path):
        """Test saving configuration to file"""
        config_file = tmp_path / "test_config.json"
        service_manager.config_file_path = config_file

        # Set some test data
        service_manager.current_primary_agent = "gemini"
        service_manager.agent_configs['gemini'].enabled = False

        # Save config
        service_manager.save_config_file()

        # Verify file was created and contains correct data
        assert config_file.exists()

        with open(config_file, 'r') as f:
            saved_config = json.load(f)

        assert saved_config["primary_agent"] == "gemini"
        assert saved_config["agents"]["gemini"]["enabled"] is False
        # API keys should not be saved
        assert "api_key" not in saved_config["agents"]["gemini"]["config"]

    def test_switch_primary_agent_success(self, service_manager):
        """Test successful primary agent switching"""
        # Setup
        service_manager.agent_configs['openai'].enabled = True
        service_manager.coordinator.agents = {'openai_agent': Mock()}

        # Mock the agent availability check
        mock_agent = Mock()
        mock_agent.is_available.return_value = True
        mock_agent.get_supported_content_types.return_value = []  # Return empty list
        service_manager.coordinator.agents['openai_agent'] = mock_agent

        # Test switching
        result = service_manager.switch_primary_agent('openai')

        assert result is True
        assert service_manager.current_primary_agent == 'openai'

    def test_switch_primary_agent_unknown_provider(self, service_manager):
        """Test switching to unknown provider"""
        result = service_manager.switch_primary_agent('unknown_provider')
        assert result is False

    def test_switch_primary_agent_disabled_provider(self, service_manager):
        """Test switching to disabled provider"""
        service_manager.agent_configs['openai'].enabled = False
        result = service_manager.switch_primary_agent('openai')
        assert result is False

    def test_switch_primary_agent_unavailable_provider(self, service_manager):
        """Test switching to unavailable provider"""
        service_manager.agent_configs['openai'].enabled = True
        service_manager.coordinator.agents = {'openai_agent': Mock()}

        # Mock agent as unavailable
        mock_agent = Mock()
        mock_agent.is_available.return_value = False
        service_manager.coordinator.agents['openai_agent'] = mock_agent

        result = service_manager.switch_primary_agent('openai')
        assert result is False

    def test_enable_agent_success(self, service_manager):
        """Test successful agent enabling"""
        with patch('app.services.ai_service_manager.create_agent') as mock_create_agent:
            mock_agent = Mock()
            mock_agent.is_available.return_value = True
            mock_create_agent.return_value = mock_agent

            # Reset the mock call count to focus on this specific call
            service_manager.coordinator.register_agent.reset_mock()

            result = service_manager.enable_agent('openai')

            assert result is True
            assert service_manager.agent_configs['openai'].enabled is True
            service_manager.coordinator.register_agent.assert_called_once_with(mock_agent, True)

    def test_enable_agent_creation_failure(self, service_manager):
        """Test agent enabling when agent creation fails"""
        with patch('app.services.ai_service_manager.create_agent') as mock_create_agent:
            mock_create_agent.side_effect = Exception("Creation failed")

            result = service_manager.enable_agent('openai')

            assert result is False
            assert service_manager.agent_configs['openai'].enabled is False

    def test_enable_agent_unavailable(self, service_manager):
        """Test agent enabling when agent is not available"""
        with patch('app.services.ai_service_manager.create_agent') as mock_create_agent:
            mock_agent = Mock()
            mock_agent.is_available.return_value = False
            mock_create_agent.return_value = mock_agent

            result = service_manager.enable_agent('openai')

            assert result is False

    def test_disable_agent_success(self, service_manager):
        """Test successful agent disabling"""
        # Setup
        service_manager.agent_configs['openai'].enabled = True
        service_manager.coordinator.agents = {'openai_agent': Mock()}
        service_manager.coordinator.fallback_chain = ['openai_agent']

        result = service_manager.disable_agent('openai')

        assert result is True
        assert service_manager.agent_configs['openai'].enabled is False
        # Agent should be removed from coordinator
        assert 'openai_agent' not in service_manager.coordinator.agents

    def test_disable_agent_unknown_provider(self, service_manager):
        """Test disabling unknown provider"""
        result = service_manager.disable_agent('unknown_provider')
        assert result is False

    def test_get_status(self, service_manager):
        """Test getting service status"""
        # Setup mock agent
        mock_agent = Mock()
        mock_agent.is_available.return_value = True
        service_manager.coordinator.agents = {'gemini_agent': mock_agent}

        status = service_manager.get_status()

        assert 'primary_agent' in status
        assert 'agents' in status
        assert 'performance_metrics' in status
        assert 'gemini' in status['agents']
        assert status['agents']['gemini']['available'] is True

    @pytest.mark.asyncio
    async def test_health_check_all(self, service_manager):
        """Test health check for all agents"""
        expected_health = {'gemini_agent': True, 'openai_agent': False}
        service_manager.coordinator.health_check_all.return_value = expected_health

        result = await service_manager.health_check_all()

        assert result == expected_health
        service_manager.coordinator.health_check_all.assert_called_once()

    def test_update_agent_config_success(self, service_manager):
        """Test successful agent configuration update"""
        service_manager.agent_configs['gemini'].enabled = True

        result = service_manager.update_agent_config('gemini', {'model': 'new_model'})

        assert result is True
        assert service_manager.agent_configs['gemini'].config['model'] == 'new_model'

    def test_update_agent_config_unknown_agent(self, service_manager):
        """Test updating config for unknown agent"""
        result = service_manager.update_agent_config('unknown_agent', {'model': 'new_model'})
        assert result is False

    def test_update_agent_config_with_reinitialization(self, service_manager):
        """Test config update triggers agent reinitialization"""
        service_manager.agent_configs['gemini'].enabled = True

        with patch.object(service_manager, 'disable_agent') as mock_disable, \
             patch.object(service_manager, 'enable_agent') as mock_enable:

            result = service_manager.update_agent_config('gemini', {'model': 'new_model'})

            assert result is True
            mock_disable.assert_called_once_with('gemini')
            mock_enable.assert_called_once_with('gemini')

    def test_get_pipeline(self, service_manager):
        """Test getting the moderation pipeline"""
        pipeline = service_manager.get_pipeline()
        assert pipeline == service_manager.pipeline


class TestGlobalServiceManager:
    """Tests for global service manager functions"""

    @patch('app.services.ai_service_manager.AIServiceManager')
    def test_get_ai_service_manager_singleton(self, mock_manager_class):
        """Test that get_ai_service_manager returns a singleton"""
        mock_instance = Mock()
        mock_manager_class.return_value = mock_instance

        # Reset the global instance
        import app.services.ai_service_manager
        app.services.ai_service_manager._service_manager = None

        # Get manager twice
        manager1 = get_ai_service_manager()
        manager2 = get_ai_service_manager()

        assert manager1 is manager2
        assert manager1 is mock_instance
        mock_manager_class.assert_called_once()

    @patch('app.services.ai_service_manager.get_ai_service_manager')
    def test_switch_ai_provider(self, mock_get_manager):
        """Test switch_ai_provider convenience function"""
        mock_manager = Mock()
        mock_manager.switch_primary_agent.return_value = True
        mock_get_manager.return_value = mock_manager

        from app.services.ai_service_manager import switch_ai_provider
        result = switch_ai_provider('gemini')

        assert result is True
        mock_manager.switch_primary_agent.assert_called_once_with('gemini')


class TestErrorHandling:
    """Tests for error handling scenarios"""

    def test_initialization_with_corrupt_config_file(self):
        """Test initialization with corrupt config file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content")
            f.flush()

            with patch('app.services.ai_service_manager.AgentCoordinator'), \
                 patch('app.services.ai_service_manager.get_moderation_pipeline'):
                manager = AIServiceManager()
                manager.config_file_path = Path(f.name)

                # Should not raise exception
                manager._load_config_file()

        os.unlink(f.name)

    def test_save_config_file_with_exception(self, tmp_path):
        """Test save config file when file operation fails"""
        # Create a service manager instance for this test
        with patch('app.services.ai_service_manager.AgentCoordinator'), \
             patch('app.services.ai_service_manager.get_moderation_pipeline'):
            service_manager = AIServiceManager()
            
            # Create a directory where we can't write
            config_file = tmp_path / "readonly_dir" / "config.json"
            config_file.parent.mkdir()
            config_file.parent.chmod(0o444)  # Read-only

            service_manager.config_file_path = config_file

            # Should not raise exception
            service_manager.save_config_file()

            # Cleanup
            config_file.parent.chmod(0o755)


if __name__ == "__main__":
    pytest.main([__file__])