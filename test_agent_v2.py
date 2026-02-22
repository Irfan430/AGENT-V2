#!/usr/bin/env python3
"""
Test script for AGENT-V2 with new production-grade components.
"""

import asyncio
import sys
import os

# Add server to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'server'))

from llm_client_v2 import (
    initialize_llm_client, 
    get_llm_client, 
    Message,
    list_supported_providers
)
from tool_manager_v2 import get_tool_manager
from error_handler import get_error_handler, get_self_correction_engine
from monitoring import get_health_checker, get_performance_monitor

async def test_llm_client():
    """Test LLM client with multiple providers."""
    print("\n" + "="*60)
    print("TEST 1: LLM Client - Supported Providers")
    print("="*60)
    
    providers = list_supported_providers()
    print(f"✓ Supported providers: {', '.join(providers)}")
    
    # Test DeepSeek initialization
    print("\nTesting DeepSeek initialization...")
    try:
        client = initialize_llm_client(provider="deepseek")
        print(f"✓ DeepSeek client initialized: {client.model}")
        
        # Test message creation
        messages = [
            Message(role="system", content="You are a helpful assistant."),
            Message(role="user", content="What is 2+2?")
        ]
        print(f"✓ Created {len(messages)} messages")
        
    except Exception as e:
        print(f"✗ DeepSeek initialization failed: {str(e)}")

def test_tool_manager():
    """Test tool manager."""
    print("\n" + "="*60)
    print("TEST 2: Tool Manager")
    print("="*60)
    
    tool_manager = get_tool_manager()
    
    # Get available tools
    tools = tool_manager.get_tools_list()
    print(f"✓ Available tools: {len(tools)}")
    
    for tool in tools:
        print(f"  - {tool['name']}: {tool['description']}")
    
    # Test tool info
    tool_info = tool_manager.get_tool_info("execute_command")
    if tool_info:
        print(f"\n✓ Tool info for 'execute_command':")
        print(f"  - Description: {tool_info['description']}")
        print(f"  - Requires approval: {tool_info['requires_approval']}")
        print(f"  - Max retries: {tool_info['max_retries']}")
        print(f"  - Timeout: {tool_info['timeout']}s")

async def test_error_handler():
    """Test error handler."""
    print("\n" + "="*60)
    print("TEST 3: Error Handler & Self-Correction")
    print("="*60)
    
    error_handler = get_error_handler()
    
    # Test error classification
    try:
        raise TimeoutError("Operation timed out after 30 seconds")
    except Exception as e:
        classification = error_handler.classify_error(e)
        print(f"✓ Error classified:")
        print(f"  - Type: {classification.error_type.value}")
        print(f"  - Severity: {classification.severity.value}")
        print(f"  - Recovery strategy: {classification.recovery_strategy.value}")
        print(f"  - Suggested action: {classification.suggested_action}")
    
    # Test error statistics
    stats = error_handler.get_error_statistics()
    print(f"\n✓ Error statistics:")
    print(f"  - Total errors: {stats['total_errors']}")
    print(f"  - Errors by type: {stats['error_by_type']}")
    print(f"  - Errors by severity: {stats['error_by_severity']}")

async def test_health_checker():
    """Test health checker."""
    print("\n" + "="*60)
    print("TEST 4: Health Checker & Monitoring")
    print("="*60)
    
    health_checker = get_health_checker()
    
    # Run health checks
    print("Running health checks...")
    results = await health_checker.run_all_checks()
    
    for name, result in results.items():
        status_symbol = "✓" if result.status.value == "healthy" else "⚠" if result.status.value == "degraded" else "✗"
        print(f"{status_symbol} {name}: {result.status.value} - {result.message}")
    
    # Get overall status
    overall_status = health_checker.get_overall_status()
    print(f"\n✓ Overall health status: {overall_status.value}")
    
    # Test metrics
    print("\n✓ Metrics collected:")
    metrics = health_checker.metrics_collector.get_all_metrics()
    for metric_name in list(metrics.keys())[:5]:
        print(f"  - {metric_name}")

def test_performance_monitor():
    """Test performance monitor."""
    print("\n" + "="*60)
    print("TEST 5: Performance Monitor")
    print("="*60)
    
    perf_monitor = get_performance_monitor()
    
    # Record some operation times
    perf_monitor.record_operation_time("api_call", 0.5)
    perf_monitor.record_operation_time("api_call", 0.6)
    perf_monitor.record_operation_time("api_call", 0.55)
    perf_monitor.record_operation_time("database_query", 0.2)
    
    # Get stats
    api_stats = perf_monitor.get_operation_stats("api_call")
    db_stats = perf_monitor.get_operation_stats("database_query")
    
    print(f"✓ API call stats:")
    print(f"  - Count: {api_stats['count']}")
    print(f"  - Avg: {api_stats['avg']:.3f}s")
    print(f"  - Min: {api_stats['min']:.3f}s")
    print(f"  - Max: {api_stats['max']:.3f}s")
    
    print(f"\n✓ Database query stats:")
    print(f"  - Count: {db_stats['count']}")
    print(f"  - Avg: {db_stats['avg']:.3f}s")

async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("AGENT-V2 PRODUCTION COMPONENTS TEST")
    print("="*60)
    
    try:
        # Test 1: LLM Client
        await test_llm_client()
        
        # Test 2: Tool Manager
        test_tool_manager()
        
        # Test 3: Error Handler
        await test_error_handler()
        
        # Test 4: Health Checker
        await test_health_checker()
        
        # Test 5: Performance Monitor
        test_performance_monitor()
        
        print("\n" + "="*60)
        print("✓ ALL TESTS COMPLETED SUCCESSFULLY")
        print("="*60 + "\n")
        
        return 0
    
    except Exception as e:
        print(f"\n✗ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
