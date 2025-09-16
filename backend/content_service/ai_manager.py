# Copyright (c) 2025 Adara Screen by Hebron
# Owner: Sujesh M S
# All Rights Reserved
#
# This software is proprietary to Adara Screen by Hebron.
# Unauthorized use, reproduction, or distribution is strictly prohibited.

#!/usr/bin/env python3
"""
AI Provider Management CLI for Digital Signage Platform

This CLI tool allows you to easily switch between different AI providers,
manage configurations, and test AI services.

Usage:
    python ai_manager.py list                          # List all providers
    python ai_manager.py status                        # Show current status
    python ai_manager.py switch <provider>             # Switch primary provider
    python ai_manager.py enable <provider>             # Enable a provider
    python ai_manager.py disable <provider>            # Disable a provider
    python ai_manager.py test <provider>               # Test a provider
    python ai_manager.py config <provider> <key> <value>  # Update config
    python ai_manager.py health                        # Check health of all providers
"""

import asyncio
import sys
import os
import argparse
from typing import Dict, Any
import json

# Add the app directory to the path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from services.ai_service_manager import get_ai_service_manager, switch_ai_provider
from services.ai_agent_framework import AnalysisRequest, ContentType

class AIManagerCLI:
    def __init__(self):
        self.service_manager = get_ai_service_manager()
    
    async def list_providers(self):
        """List all available AI providers"""
        print("📋 Available AI Providers:")
        print("=" * 50)
        
        status = self.service_manager.get_status()
        
        for agent_name, agent_info in status["agents"].items():
            icon = "✅" if agent_info["enabled"] else "❌"
            primary = "🌟" if agent_name == status["primary_agent"] else "  "
            fallback = "(fallback)" if agent_info["is_fallback"] else ""
            
            print(f"{primary} {icon} {agent_name.upper()}")
            print(f"    Provider: {agent_info['provider']}")
            print(f"    Priority: {agent_info['priority']}")
            print(f"    Status: {'Enabled' if agent_info['enabled'] else 'Disabled'} {fallback}")
            print()
    
    async def show_status(self):
        """Show current AI service status"""
        print("📊 AI Service Status:")
        print("=" * 50)
        
        status = self.service_manager.get_status()
        health_status = await self.service_manager.health_check_all()
        
        print(f"Primary Agent: {status['primary_agent'] or 'None'}")
        print()
        
        print("Agent Health:")
        for agent_name, agent_info in status["agents"].items():
            agent_key = f"{agent_name}_agent"
            health = health_status.get(agent_key, False)
            health_icon = "🟢" if health else "🔴"
            status_icon = "✅" if agent_info["enabled"] else "❌"
            
            print(f"  {status_icon} {health_icon} {agent_name}: {agent_info['provider']}")
        
        print()
        print("Performance Metrics:")
        for agent_name, metrics in status.get("performance_metrics", {}).items():
            if metrics["total_requests"] > 0:
                success_rate = (metrics["successful_requests"] / metrics["total_requests"]) * 100
                print(f"  📈 {agent_name}:")
                print(f"    Success Rate: {success_rate:.1f}%")
                print(f"    Avg Response Time: {metrics['average_response_time']:.3f}s")
                print(f"    Total Requests: {metrics['total_requests']}")
    
    async def switch_provider(self, provider_name: str):
        """Switch to a different primary provider"""
        print(f"🔄 Switching to {provider_name}...")
        
        success = self.service_manager.switch_primary_agent(provider_name)
        
        if success:
            print(f"✅ Successfully switched to {provider_name}")
        else:
            print(f"❌ Failed to switch to {provider_name}")
            print("   Make sure the provider is enabled and available")
    
    async def enable_provider(self, provider_name: str):
        """Enable a provider"""
        print(f"🟢 Enabling {provider_name}...")
        
        success = self.service_manager.enable_agent(provider_name)
        
        if success:
            print(f"✅ Successfully enabled {provider_name}")
        else:
            print(f"❌ Failed to enable {provider_name}")
            print("   Check configuration and API keys")
    
    async def disable_provider(self, provider_name: str):
        """Disable a provider"""
        print(f"🔴 Disabling {provider_name}...")
        
        success = self.service_manager.disable_agent(provider_name)
        
        if success:
            print(f"✅ Successfully disabled {provider_name}")
        else:
            print(f"❌ Failed to disable {provider_name}")
    
    async def test_provider(self, provider_name: str):
        """Test a specific provider with sample content"""
        print(f"🧪 Testing {provider_name}...")
        
        # Create a test request
        test_request = AnalysisRequest(
            content_id="test_content",
            content_type=ContentType.TEXT,
            text_content="This is a test message for content moderation. Hello world!"
        )
        
        try:
            # Get the pipeline and test
            pipeline = self.service_manager.get_pipeline()
            result = await pipeline.process_content(test_request)
            
            print(f"✅ Test successful for {provider_name}")
            print(f"   Action: {result.action}")
            print(f"   Confidence: {result.confidence:.3f}")
            print(f"   Model Used: {result.model_used}")
            print(f"   Processing Time: {result.processing_time:.3f}s")
            print(f"   Reasoning: {result.reasoning[:100]}...")
            
        except Exception as e:
            print(f"❌ Test failed for {provider_name}: {str(e)}")
    
    async def update_config(self, provider_name: str, key: str, value: str):
        """Update configuration for a provider"""
        print(f"⚙️  Updating {provider_name} config: {key} = {value}")
        
        # Convert value to appropriate type
        if value.lower() in ['true', 'false']:
            value = value.lower() == 'true'
        elif value.isdigit():
            value = int(value)
        elif '.' in value and value.replace('.', '').isdigit():
            value = float(value)
        
        config_updates = {key: value}
        success = self.service_manager.update_agent_config(provider_name, config_updates)
        
        if success:
            print(f"✅ Successfully updated {provider_name} configuration")
        else:
            print(f"❌ Failed to update {provider_name} configuration")
    
    async def check_health(self):
        """Check health of all providers"""
        print("🏥 Checking health of all providers...")
        print("=" * 50)
        
        health_status = await self.service_manager.health_check_all()
        
        for agent_name, is_healthy in health_status.items():
            icon = "🟢" if is_healthy else "🔴"
            status = "Healthy" if is_healthy else "Unhealthy"
            clean_name = agent_name.replace("_agent", "")
            print(f"{icon} {clean_name.upper()}: {status}")
    
    def show_examples(self):
        """Show usage examples"""
        print("💡 Usage Examples:")
        print("=" * 50)
        print("# List all providers")
        print("python ai_manager.py list")
        print()
        print("# Show current status")
        print("python ai_manager.py status")
        print()
        print("# Switch to Gemini")
        print("python ai_manager.py switch gemini")
        print()
        print("# Switch to local Ollama")
        print("python ai_manager.py switch ollama")
        print()
        print("# Enable OpenAI")
        print("python ai_manager.py enable openai")
        print()
        print("# Test a provider")
        print("python ai_manager.py test gemini")
        print()
        print("# Update configuration")
        print("python ai_manager.py config gemini model gemini-1.5-pro")
        print()
        print("# Check health")
        print("python ai_manager.py health")

async def main():
    parser = argparse.ArgumentParser(
        description="AI Provider Management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List command
    subparsers.add_parser('list', help='List all providers')
    
    # Status command
    subparsers.add_parser('status', help='Show current status')
    
    # Switch command
    switch_parser = subparsers.add_parser('switch', help='Switch primary provider')
    switch_parser.add_argument('provider', help='Provider name (gemini, openai, ollama, etc.)')
    
    # Enable command
    enable_parser = subparsers.add_parser('enable', help='Enable a provider')
    enable_parser.add_argument('provider', help='Provider name')
    
    # Disable command
    disable_parser = subparsers.add_parser('disable', help='Disable a provider')
    disable_parser.add_argument('provider', help='Provider name')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Test a provider')
    test_parser.add_argument('provider', help='Provider name')
    
    # Config command
    config_parser = subparsers.add_parser('config', help='Update configuration')
    config_parser.add_argument('provider', help='Provider name')
    config_parser.add_argument('key', help='Configuration key')
    config_parser.add_argument('value', help='Configuration value')
    
    # Health command
    subparsers.add_parser('health', help='Check health of all providers')
    
    # Examples command
    subparsers.add_parser('examples', help='Show usage examples')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cli = AIManagerCLI()
    
    try:
        if args.command == 'list':
            await cli.list_providers()
        elif args.command == 'status':
            await cli.show_status()
        elif args.command == 'switch':
            await cli.switch_provider(args.provider)
        elif args.command == 'enable':
            await cli.enable_provider(args.provider)
        elif args.command == 'disable':
            await cli.disable_provider(args.provider)
        elif args.command == 'test':
            await cli.test_provider(args.provider)
        elif args.command == 'config':
            await cli.update_config(args.provider, args.key, args.value)
        elif args.command == 'health':
            await cli.check_health()
        elif args.command == 'examples':
            cli.show_examples()
    
    except KeyboardInterrupt:
        print("\n⚡ Operation cancelled")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
