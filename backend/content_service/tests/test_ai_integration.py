import pytest
import asyncio
import os
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from pathlib import Path
import tempfile

# Add the backend directory to the path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.ai_service_manager import AIServiceManager, get_ai_service_manager
from app.services.ai_agent_framework import (
    AgentCoordinator,
    ModerationPipeline,
    AnalysisRequest,
    ContentType,
    AnalysisResult,
    ModerationAction,
    BaseAIAgent,
    ModelProvider
)
from ai_manager import AIManagerCLI


@pytest.fixture
def mock_agents():
    """Create mock agents for testing"""
    gemini_agent = MockAIAgent("gemini_agent", ModelProvider.GEMINI, {"api_key": "test"}, True)
    openai_agent = MockAIAgent("openai_agent", ModelProvider.OPENAI, {"api_key": "test"}, True)
    ollama_agent = MockAIAgent("ollama_agent", ModelProvider.OLLAMA, {}, False)  # Unavailable

    return {
        "gemini_agent": gemini_agent,
        "openai_agent": openai_agent,
        "ollama_agent": ollama_agent
    }


class MockAIAgent(BaseAIAgent):
    """Mock AI agent for testing"""

    def __init__(self, name: str, provider: ModelProvider, config: dict, available: bool = True):
        super().__init__(name, provider, config)
        self._available = available
        self.call_count = 0
        self.last_request = None

    def _initialize(self) -> None:
        self.enabled = True

    async def analyze_content(self, request: AnalysisRequest) -> AnalysisResult:
        self.call_count += 1
        self.last_request = request

        return AnalysisResult(
            content_id=request.content_id,
            confidence=0.85,
            action=ModerationAction.APPROVED,
            reasoning=f"Mock analysis by {self.name}",
            categories=["test"],
            safety_scores={"overall": 0.85},
            quality_score=0.8,
            brand_safety_score=0.9,
            compliance_score=0.95,
            concerns=[],
            suggestions=[],
            processing_time=1.0,
            model_used=f"{self.name}_model"
        )

    async def health_check(self) -> bool:
        return self._available

    def get_supported_content_types(self):
        return [ContentType.TEXT, ContentType.IMAGE]

    def is_available(self) -> bool:
        return self._available


class TestAIServiceIntegration:
    """Integration tests for the complete AI service system"""

    @pytest.fixture
    def integration_setup(self, mock_agents):
        """Set up complete integration environment"""
        with patch.dict(os.environ, {
            'GEMINI_API_KEY': 'test_gemini_key',
            'OPENAI_API_KEY': 'test_openai_key'
        }):
            # Mock the agent creation to prevent real API calls
            def mock_create_agent(provider, config):
                if provider == ModelProvider.GEMINI:
                    return mock_agents["gemini_agent"]
                elif provider == ModelProvider.OPENAI:
                    return mock_agents["openai_agent"]
                elif provider == ModelProvider.OLLAMA:
                    return mock_agents["ollama_agent"]
                return None

            # Patch the create_agent function in the ai_service_manager module
            with patch('app.services.ai_service_manager.create_agent', side_effect=mock_create_agent):
                # Also mock the google.generativeai and openai modules to prevent real API calls
                with patch('google.generativeai.configure'):
                    with patch('google.generativeai.GenerativeModel'):
                        with patch('openai.OpenAI'):
                            with patch('aiohttp.ClientSession'):
                                manager = AIServiceManager()
                                return manager, mock_agents

    @pytest.mark.asyncio
    async def test_full_content_moderation_flow(self, integration_setup):
        """Test complete content moderation flow from request to result"""
        manager, mock_agents = integration_setup

        # Create a test request
        request = AnalysisRequest(
            content_id="test_content_123",
            content_type=ContentType.TEXT,
            text_content="This is a test message for content moderation."
        )

        # Get the pipeline and process content
        pipeline = manager.get_pipeline()
        result = await pipeline.process_content(request)

        # Verify the result
        assert result.content_id == "test_content_123"
        assert result.action == ModerationAction.APPROVED
        assert result.confidence == 0.85
        assert "Mock analysis" in result.reasoning
        assert result.processing_time >= 0

        # Verify that an agent was called
        called_agents = [agent for agent in mock_agents.values() if agent.call_count > 0]
        assert len(called_agents) > 0

    @pytest.mark.asyncio
    async def test_agent_fallback_mechanism(self, integration_setup):
        """Test that system falls back to available agents when primary fails"""
        manager, mock_agents = integration_setup

        # Make gemini agent fail
        mock_agents["gemini_agent"]._available = False

        request = AnalysisRequest(
            content_id="test_fallback",
            content_type=ContentType.TEXT,
            text_content="Test fallback mechanism"
        )

        pipeline = manager.get_pipeline()
        result = await pipeline.process_content(request)

        # Should still get a result (fallback to openai)
        assert result.content_id == "test_fallback"
        assert result.action == ModerationAction.APPROVED

        # Verify openai agent was called (as fallback)
        assert mock_agents["openai_agent"].call_count > 0

    @pytest.mark.asyncio
    async def test_performance_metrics_tracking(self, integration_setup):
        """Test that performance metrics are properly tracked"""
        manager, mock_agents = integration_setup

        # Make multiple requests
        for i in range(3):
            request = AnalysisRequest(
                content_id=f"perf_test_{i}",
                content_type=ContentType.TEXT,
                text_content=f"Performance test message {i}"
            )

            pipeline = manager.get_pipeline()
            await pipeline.process_content(request)

        # Check performance metrics
        status = manager.get_status()
        metrics = status.get("performance_metrics", {})

        # Should have metrics for the called agent
        assert len(metrics) > 0

        for agent_name, agent_metrics in metrics.items():
            if agent_metrics["total_requests"] > 0:
                assert "total_requests" in agent_metrics
                assert "successful_requests" in agent_metrics
                assert "average_response_time" in agent_metrics
                assert agent_metrics["total_requests"] >= 3

    @pytest.mark.asyncio
    async def test_health_check_integration(self, integration_setup):
        """Test health check across all agents"""
        manager, mock_agents = integration_setup

        # Make one agent unhealthy
        mock_agents["ollama_agent"]._available = False

        health_status = await manager.health_check_all()

        # Verify health status
        assert "gemini_agent" in health_status
        assert "openai_agent" in health_status
        assert "ollama_agent" in health_status

        assert health_status["gemini_agent"] is True
        assert health_status["openai_agent"] is True
        assert health_status["ollama_agent"] is False

    def test_configuration_persistence(self, integration_setup, tmp_path):
        """Test that configuration changes are persisted"""
        manager, mock_agents = integration_setup

        # Set custom config file
        config_file = tmp_path / "test_config.json"
        manager.config_file_path = config_file

        # Make configuration changes
        manager.current_primary_agent = "openai"
        manager.agent_configs["gemini"].enabled = False

        # Save configuration
        manager.save_config_file()

        # Create new manager instance and load config
        new_manager, _ = integration_setup
        new_manager.config_file_path = config_file
        new_manager._load_config_file()

        # Verify configuration was loaded
        assert new_manager.current_primary_agent == "openai"
        assert new_manager.agent_configs["gemini"].enabled is False

    def test_agent_switching_integration(self, integration_setup):
        """Test switching between primary agents"""
        manager, mock_agents = integration_setup

        # Initially should have a primary agent
        initial_primary = manager.current_primary_agent
        assert initial_primary is not None

        # Switch to openai
        success = manager.switch_primary_agent("openai")
        assert success is True
        assert manager.current_primary_agent == "openai"

        # Switch back to gemini
        success = manager.switch_primary_agent("gemini")
        assert success is True
        assert manager.current_primary_agent == "gemini"


class TestCLIIntegration:
    """Integration tests for CLI with service manager"""

    @pytest.fixture
    def cli_integration_setup(self):
        """Set up CLI with mocked service manager"""
        with patch.dict(os.environ, {
            'GEMINI_API_KEY': 'test_gemini_key',
            'OPENAI_API_KEY': 'test_openai_key'
        }):
            with patch('app.services.ai_service_manager.create_agent') as mock_create_agent:
                # Create mock agents
                gemini_agent = MockAIAgent("gemini_agent", ModelProvider.GEMINI, {"api_key": "test"}, True)
                openai_agent = MockAIAgent("openai_agent", ModelProvider.OPENAI, {"api_key": "test"}, True)

                def create_agent_side_effect(provider, config):
                    if provider == ModelProvider.GEMINI:
                        return gemini_agent
                    elif provider == ModelProvider.OPENAI:
                        return openai_agent
                    return None

                mock_create_agent.side_effect = create_agent_side_effect

                # Mock external dependencies
                with patch('google.generativeai.configure'):
                    with patch('google.generativeai.GenerativeModel'):
                        with patch('openai.OpenAI'):
                            with patch('aiohttp.ClientSession'):
                                cli = AIManagerCLI()
                                return cli, gemini_agent, openai_agent

    @pytest.mark.asyncio
    async def test_cli_status_integration(self, cli_integration_setup, capsys):
        """Test CLI status command with real service manager"""
        cli, gemini_agent, openai_agent = cli_integration_setup

        await cli.show_status()

        captured = capsys.readouterr()
        assert "📊 AI Service Status:" in captured.out
        assert "Primary Agent:" in captured.out
        assert "Agent Health:" in captured.out

    @pytest.mark.asyncio
    async def test_cli_switch_integration(self, cli_integration_setup, capsys):
        """Test CLI switch command integration"""
        cli, gemini_agent, openai_agent = cli_integration_setup

        await cli.switch_provider("openai")

        captured = capsys.readouterr()
        assert "🔄 Switching to openai..." in captured.out

        # Verify the switch actually happened
        assert cli.service_manager.current_primary_agent == "openai"

    @pytest.mark.asyncio
    async def test_cli_test_provider_integration(self, cli_integration_setup, capsys):
        """Test CLI test provider command with real processing"""
        cli, gemini_agent, openai_agent = cli_integration_setup

        await cli.test_provider("gemini")

        captured = capsys.readouterr()
        assert "🧪 Testing gemini..." in captured.out
        assert "✅ Test successful for gemini" in captured.out

        # Verify the agent was actually called
        assert gemini_agent.call_count == 1
        assert gemini_agent.last_request.content_type == ContentType.TEXT


class TestErrorScenarios:
    """Integration tests for error scenarios"""

    @pytest.mark.asyncio
    async def test_all_agents_fail_scenario(self):
        """Test behavior when all agents fail"""
        with patch.dict(os.environ, {}, clear=True):  # No API keys
            with patch('app.services.ai_service_manager.create_agent') as mock_create_agent:
                # Make all agents fail
                mock_create_agent.side_effect = Exception("Agent creation failed")

                # Mock external dependencies to prevent real API calls
                with patch('google.generativeai.configure'):
                    with patch('google.generativeai.GenerativeModel'):
                        with patch('openai.OpenAI'):
                            with patch('aiohttp.ClientSession'):
                                manager = AIServiceManager()

                                request = AnalysisRequest(
                                    content_id="error_test",
                                    content_type=ContentType.TEXT,
                                    text_content="Test error handling"
                                )

                                pipeline = manager.get_pipeline()
                                result = await pipeline.process_content(request)

                                # Should get a fallback result
                                assert result.action == ModerationAction.NEEDS_REVIEW
                                assert "fallback_system" in result.model_used
                                assert "All AI agents failed" in result.reasoning

    @pytest.mark.asyncio
    async def test_service_initialization_with_partial_failures(self):
        """Test service initialization when some agents fail"""
        with patch.dict(os.environ, {
            'GEMINI_API_KEY': 'test_key',
            'OPENAI_API_KEY': 'test_key'
        }):
            with patch('app.services.ai_service_manager.create_agent') as mock_create_agent:
                call_count = 0

                def create_agent_side_effect(provider, config):
                    nonlocal call_count
                    call_count += 1
                    if call_count == 1:  # First call (gemini) succeeds
                        return MockAIAgent(f"{provider.value}_agent", provider, config, True)
                    else:  # Subsequent calls fail
                        raise Exception(f"Failed to create {provider.value} agent")

                mock_create_agent.side_effect = create_agent_side_effect

                # Mock external dependencies
                with patch('google.generativeai.configure'):
                    with patch('google.generativeai.GenerativeModel'):
                        with patch('openai.OpenAI'):
                            with patch('aiohttp.ClientSession'):
                                # Should not raise exception even with partial failures
                                manager = AIServiceManager()

                                # Should have at least one working agent
                                status = manager.get_status()
                                working_agents = [name for name, info in status["agents"].items()
                                                if info.get("available", False)]
                                assert len(working_agents) >= 1
class TestConcurrentRequests:
    """Tests for concurrent request handling"""

    @pytest.fixture
    def concurrent_setup(self, mock_agents):
        """Set up environment for concurrent tests"""
        with patch.dict(os.environ, {
            'GEMINI_API_KEY': 'test_gemini_key',
            'OPENAI_API_KEY': 'test_openai_key'
        }):
            # Mock the agent creation to prevent real API calls
            def mock_create_agent(provider, config):
                if provider == ModelProvider.GEMINI:
                    return mock_agents["gemini_agent"]
                elif provider == ModelProvider.OPENAI:
                    return mock_agents["openai_agent"]
                elif provider == ModelProvider.OLLAMA:
                    return mock_agents["ollama_agent"]
                return None

            # Patch the create_agent function in the ai_service_manager module
            with patch('app.services.ai_service_manager.create_agent', side_effect=mock_create_agent):
                # Also mock the google.generativeai and openai modules to prevent real API calls
                with patch('google.generativeai.configure'):
                    with patch('google.generativeai.GenerativeModel'):
                        with patch('openai.OpenAI'):
                            with patch('aiohttp.ClientSession'):
                                manager = AIServiceManager()
                                return manager, mock_agents

    @pytest.mark.asyncio
    async def test_concurrent_content_processing(self, concurrent_setup):
        """Test processing multiple requests concurrently"""
        manager, mock_agents = concurrent_setup

        # Create multiple requests
        requests = []
        for i in range(5):
            request = AnalysisRequest(
                content_id=f"concurrent_test_{i}",
                content_type=ContentType.TEXT,
                text_content=f"Concurrent test message {i}"
            )
            requests.append(request)

        # Process all requests concurrently
        pipeline = manager.get_pipeline()
        tasks = [pipeline.process_content(request) for request in requests]
        results = await asyncio.gather(*tasks)

        # Verify all results
        assert len(results) == 5
        for i, result in enumerate(results):
            assert result.content_id == f"concurrent_test_{i}"
            assert result.action == ModerationAction.APPROVED

        # Verify agent was called multiple times
        total_calls = sum(agent.call_count for agent in mock_agents.values())
        assert total_calls >= 5


if __name__ == "__main__":
    pytest.main([__file__])