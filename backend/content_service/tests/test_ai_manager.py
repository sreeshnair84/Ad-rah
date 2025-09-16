import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from io import StringIO
import sys
import os

# Add the backend directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ai_manager import AIManagerCLI, main
from app.services.ai_service_manager import AIServiceManager
from app.services.ai_agent_framework import AnalysisRequest, ContentType, AnalysisResult, ModerationAction


class TestAIManagerCLI:
    """Comprehensive unit tests for AIManagerCLI"""

    @pytest.fixture
    def mock_service_manager(self):
        """Mock service manager for testing"""
        mock_manager = Mock(spec=AIServiceManager)

        # Mock status response
        mock_manager.get_status.return_value = {
            "primary_agent": "gemini",
            "agents": {
                "gemini": {
                    "provider": "gemini",
                    "enabled": True,
                    "is_fallback": False,
                    "priority": 8
                },
                "openai": {
                    "provider": "openai",
                    "enabled": True,
                    "is_fallback": True,
                    "priority": 7
                }
            },
            "performance_metrics": {
                "gemini": {
                    "total_requests": 10,
                    "successful_requests": 9,
                    "average_response_time": 1.5
                }
            }
        }

        # Mock health check
        mock_manager.health_check_all = AsyncMock(return_value={
            "gemini_agent": True,
            "openai_agent": False
        })

        # Mock pipeline
        mock_pipeline = Mock()
        mock_manager.get_pipeline.return_value = mock_pipeline

        # Mock analysis result
        mock_result = AnalysisResult(
            content_id="test_content",
            confidence=0.85,
            action=ModerationAction.APPROVED,
            reasoning="Test analysis completed",
            categories=["test"],
            safety_scores={"overall": 0.85},
            quality_score=0.8,
            brand_safety_score=0.9,
            compliance_score=0.95,
            concerns=[],
            suggestions=[],
            processing_time=1.2,
            model_used="gemini_test"
        )
        mock_pipeline.process_content = AsyncMock(return_value=mock_result)

        return mock_manager

    @pytest.fixture
    def cli(self, mock_service_manager):
        """CLI instance with mocked service manager"""
        with patch('ai_manager.get_ai_service_manager', return_value=mock_service_manager):
            cli = AIManagerCLI()
            cli.service_manager = mock_service_manager
            return cli

    @pytest.mark.asyncio
    async def test_list_providers(self, cli, capsys):
        """Test listing providers"""
        await cli.list_providers()

        captured = capsys.readouterr()
        assert "📋 Available AI Providers:" in captured.out
        assert "GEMINI" in captured.out
        assert "OPENAI" in captured.out
        assert "✅" in captured.out  # Enabled status
        assert "❌" in captured.out  # Disabled status

    @pytest.mark.asyncio
    async def test_show_status(self, cli, capsys):
        """Test showing current status"""
        await cli.show_status()

        captured = capsys.readouterr()
        assert "📊 AI Service Status:" in captured.out
        assert "Primary Agent: gemini" in captured.out
        assert "🟢 gemini: gemini" in captured.out
        assert "🔴 openai: openai" in captured.out
        assert "Success Rate: 90.0%" in captured.out

    @pytest.mark.asyncio
    async def test_switch_provider_success(self, cli, capsys):
        """Test successful provider switching"""
        cli.service_manager.switch_primary_agent.return_value = True

        await cli.switch_provider("openai")

        captured = capsys.readouterr()
        assert "🔄 Switching to openai..." in captured.out
        assert "✅ Successfully switched to openai" in captured.out
        cli.service_manager.switch_primary_agent.assert_called_once_with("openai")

    @pytest.mark.asyncio
    async def test_switch_provider_failure(self, cli, capsys):
        """Test failed provider switching"""
        cli.service_manager.switch_primary_agent.return_value = False

        await cli.switch_provider("invalid_provider")

        captured = capsys.readouterr()
        assert "❌ Failed to switch to invalid_provider" in captured.out

    @pytest.mark.asyncio
    async def test_enable_provider_success(self, cli, capsys):
        """Test successful provider enabling"""
        cli.service_manager.enable_agent.return_value = True

        await cli.enable_provider("openai")

        captured = capsys.readouterr()
        assert "🟢 Enabling openai..." in captured.out
        assert "✅ Successfully enabled openai" in captured.out

    @pytest.mark.asyncio
    async def test_disable_provider_success(self, cli, capsys):
        """Test successful provider disabling"""
        cli.service_manager.disable_agent.return_value = True

        await cli.disable_provider("openai")

        captured = capsys.readouterr()
        assert "🔴 Disabling openai..." in captured.out
        assert "✅ Successfully disabled openai" in captured.out

    @pytest.mark.asyncio
    async def test_test_provider_success(self, cli, capsys):
        """Test successful provider testing"""
        await cli.test_provider("gemini")

        captured = capsys.readouterr()
        assert "🧪 Testing gemini..." in captured.out
        assert "✅ Test successful for gemini" in captured.out
        assert "Action: approved" in captured.out
        assert "Confidence: 0.850" in captured.out
        assert "Model Used: gemini_test" in captured.out

    @pytest.mark.asyncio
    async def test_test_provider_failure(self, cli, capsys):
        """Test failed provider testing"""
        cli.service_manager.get_pipeline.return_value.process_content.side_effect = Exception("Test error")

        await cli.test_provider("gemini")

        captured = capsys.readouterr()
        assert "❌ Test failed for gemini: Test error" in captured.out

    @pytest.mark.asyncio
    async def test_update_config_success(self, cli, capsys):
        """Test successful configuration update"""
        cli.service_manager.update_agent_config.return_value = True

        await cli.update_config("gemini", "model", "gemini-1.5-pro")

        captured = capsys.readouterr()
        assert "⚙️  Updating gemini config: model = gemini-1.5-pro" in captured.out
        assert "✅ Successfully updated gemini configuration" in captured.out

    @pytest.mark.asyncio
    async def test_update_config_type_conversion(self, cli):
        """Test configuration value type conversion"""
        cli.service_manager.update_agent_config.return_value = True

        # Test boolean conversion
        await cli.update_config("gemini", "enabled", "true")
        cli.service_manager.update_agent_config.assert_called_with("gemini", {"enabled": True})

        # Test integer conversion
        await cli.update_config("gemini", "timeout", "30")
        cli.service_manager.update_agent_config.assert_called_with("gemini", {"timeout": 30})

        # Test float conversion
        await cli.update_config("gemini", "temperature", "0.7")
        cli.service_manager.update_agent_config.assert_called_with("gemini", {"temperature": 0.7})

    @pytest.mark.asyncio
    async def test_check_health(self, cli, capsys):
        """Test health check functionality"""
        await cli.check_health()

        captured = capsys.readouterr()
        assert "🏥 Checking health of all providers..." in captured.out
        assert "GEMINI_AGENT" in captured.out
        assert "OPENAI_AGENT" in captured.out
        assert "🟢" in captured.out  # Healthy
        assert "🔴" in captured.out  # Unhealthy

    def test_show_examples(self, cli, capsys):
        """Test showing usage examples"""
        cli.show_examples()

        captured = capsys.readouterr()
        assert "💡 Usage Examples:" in captured.out
        assert "python ai_manager.py list" in captured.out
        assert "python ai_manager.py status" in captured.out
        assert "python ai_manager.py switch gemini" in captured.out


class TestMainFunction:
    """Tests for the main CLI entry point"""

    @patch('ai_manager.AIManagerCLI')
    @patch('sys.argv', ['ai_manager.py', 'list'])
    @pytest.mark.asyncio
    async def test_main_list_command(self, mock_cli_class):
        """Test main function with list command"""
        mock_cli_instance = Mock()
        mock_cli_instance.list_providers = AsyncMock()
        mock_cli_class.return_value = mock_cli_instance

        await main()

        mock_cli_instance.list_providers.assert_called_once()

    @patch('ai_manager.AIManagerCLI')
    @patch('sys.argv', ['ai_manager.py', 'invalid_command'])
    @pytest.mark.asyncio
    async def test_main_invalid_command(self, mock_cli_class):
        """Test main function with invalid command"""
        with patch('argparse.ArgumentParser.print_help') as mock_help:
            await main()
            mock_help.assert_called_once()

    @patch('ai_manager.AIManagerCLI')
    @patch('sys.argv', ['ai_manager.py', 'switch', 'gemini'])
    @pytest.mark.asyncio
    async def test_main_switch_command(self, mock_cli_class):
        """Test main function with switch command"""
        mock_cli_instance = Mock()
        mock_cli_instance.switch_provider = AsyncMock()
        mock_cli_class.return_value = mock_cli_instance

        await main()

        mock_cli_instance.switch_provider.assert_called_once_with('gemini')

    @patch('ai_manager.AIManagerCLI')
    @patch('sys.argv', ['ai_manager.py', 'list'])
    @pytest.mark.asyncio
    async def test_main_keyboard_interrupt(self, mock_cli_class):
        """Test main function with keyboard interrupt"""
        mock_cli_instance = Mock()
        mock_cli_instance.list_providers = AsyncMock(side_effect=KeyboardInterrupt())
        mock_cli_class.return_value = mock_cli_instance

        with patch('builtins.print') as mock_print:
            await main()
            mock_print.assert_called_with("\n⚡ Operation cancelled")

    @patch('ai_manager.AIManagerCLI')
    @patch('sys.argv', ['ai_manager.py', 'list'])
    @pytest.mark.asyncio
    async def test_main_general_exception(self, mock_cli_class):
        """Test main function with general exception"""
        mock_cli_instance = Mock()
        mock_cli_instance.list_providers = AsyncMock(side_effect=Exception("Test error"))
        mock_cli_class.return_value = mock_cli_instance

        with patch('builtins.print') as mock_print:
            await main()
            mock_print.assert_called_with("❌ Error: Test error")


class TestErrorHandling:
    """Tests for error handling scenarios"""

    @pytest.fixture
    def cli_with_errors(self):
        """CLI instance configured to raise errors"""
        with patch('ai_manager.get_ai_service_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_manager.get_status.side_effect = Exception("Service unavailable")
            mock_get_manager.return_value = mock_manager

            cli = AIManagerCLI()
            return cli

    @pytest.mark.asyncio
    async def test_list_providers_error_handling(self, cli_with_errors, capsys):
        """Test error handling in list_providers"""
        await cli_with_errors.list_providers()

        captured = capsys.readouterr()
        assert "❌ Error:" in captured.out

    @pytest.mark.asyncio
    async def test_show_status_error_handling(self, cli_with_errors, capsys):
        """Test error handling in show_status"""
        await cli_with_errors.show_status()

        captured = capsys.readouterr()
        assert "❌ Error:" in captured.out


if __name__ == "__main__":
    pytest.main([__file__])