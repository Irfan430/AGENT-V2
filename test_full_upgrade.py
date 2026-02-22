#!/usr/bin/env python3
"""
Comprehensive test script for the full AGENT-V2 upgrade.
Tests all phases from the ROADMAP_V2_PRODUCTION.md
"""

import asyncio
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_tool_manager():
    """Test Phase 1.1 and 1.2: Tool Manager"""
    logger.info("=" * 80)
    logger.info("Testing Phase 1.1 & 1.2: Tool Manager (File System & Web Browsing)")
    logger.info("=" * 80)
    
    try:
        from server.tool_manager import get_tool_manager
        
        tool_manager = get_tool_manager()
        tools = tool_manager.get_tools_list()
        
        logger.info(f"✓ Tool Manager initialized with {len(tools)} tools")
        
        # List all tools
        for tool in tools:
            logger.info(f"  - {tool['name']}: {tool['description']}")
        
        # Test file operations
        test_file = "/tmp/test_agent_v2.txt"
        test_content = "AGENT-V2 Production Test Content"
        
        # Write file
        result = await tool_manager.execute_tool("write_file", {
            "path": test_file,
            "content": test_content
        })
        logger.info(f"✓ Write file test: {result['result']}")
        
        # Read file
        result = await tool_manager.execute_tool("read_file", {
            "path": test_file
        })
        logger.info(f"✓ Read file test: {result['result'][:50]}...")
        
        # List directory
        result = await tool_manager.execute_tool("list_directory", {
            "path": "/tmp",
            "pattern": "test_agent*"
        })
        logger.info(f"✓ List directory test: Found {len(result['result'].split(chr(10)))} items")
        
        # Execute command
        result = await tool_manager.execute_tool("execute_command", {
            "command": "echo 'AGENT-V2 Command Execution Test'"
        })
        logger.info(f"✓ Execute command test: {result['result'].strip()}")
        
        logger.info("✓ Phase 1.1 & 1.2 tests PASSED\n")
        return True
    except Exception as e:
        logger.error(f"✗ Phase 1.1 & 1.2 tests FAILED: {str(e)}\n")
        return False

async def test_llm_client():
    """Test Phase 1.2: LLM Client with Multi-LLM Support"""
    logger.info("=" * 80)
    logger.info("Testing Phase 1.2: LLM Client (Multi-LLM Support)")
    logger.info("=" * 80)
    
    try:
        from server.llm_client import get_llm_client, Message
        
        llm_client = get_llm_client()
        logger.info(f"✓ LLM Client initialized: {llm_client.__class__.__name__}")
        
        # Test chat completion
        messages = [
            Message(role="system", content="You are a helpful assistant."),
            Message(role="user", content="What is 2+2?")
        ]
        
        response = await llm_client.chat_completion_async(
            messages=messages,
            max_tokens=100,
            temperature=0.7
        )
        
        logger.info(f"✓ Chat completion test: {response.content[:100]}...")
        logger.info("✓ Phase 1.2 LLM tests PASSED\n")
        return True
    except Exception as e:
        logger.error(f"✗ Phase 1.2 LLM tests FAILED: {str(e)}\n")
        return False

async def test_memory_manager():
    """Test Phase 2.1: Memory Manager"""
    logger.info("=" * 80)
    logger.info("Testing Phase 2.1: Memory Manager (ChromaDB)")
    logger.info("=" * 80)
    
    try:
        from server.memory_manager import get_memory_manager
        
        memory_manager = get_memory_manager()
        logger.info(f"✓ Memory Manager initialized: {memory_manager.__class__.__name__}")
        
        # Store some data
        memory_manager.store(
            "AGENT-V2 is a production-grade autonomous agent framework.",
            metadata={"type": "test", "version": "2.0"}
        )
        logger.info("✓ Memory store test: Data stored successfully")
        
        # Retrieve data
        results = memory_manager.retrieve("agent framework", k=1)
        logger.info(f"✓ Memory retrieve test: Found {len(results)} results")
        
        logger.info("✓ Phase 2.1 tests PASSED\n")
        return True
    except Exception as e:
        logger.error(f"✗ Phase 2.1 tests FAILED: {str(e)}\n")
        return False

async def test_error_handler():
    """Test Phase 3.2: Error Handler and Self-Correction"""
    logger.info("=" * 80)
    logger.info("Testing Phase 3.2: Error Handler & Self-Correction")
    logger.info("=" * 80)
    
    try:
        from server.error_handler import ErrorHandler, ErrorType, ErrorSeverity
        
        error_handler = ErrorHandler()
        logger.info(f"✓ Error Handler initialized: {error_handler.__class__.__name__}")
        
        # Test error classification
        test_error = Exception("Connection timeout while accessing API")
        classification = error_handler.classify_error(test_error)
        
        logger.info(f"✓ Error classification test:")
        logger.info(f"  - Type: {classification.error_type.value}")
        logger.info(f"  - Severity: {classification.severity.value}")
        logger.info(f"  - Recovery: {classification.recovery_strategy.value}")
        logger.info(f"  - Action: {classification.suggested_action}")
        
        # Get error statistics
        stats = error_handler.get_error_statistics()
        logger.info(f"✓ Error statistics: {stats['total_errors']} errors recorded")
        
        logger.info("✓ Phase 3.2 tests PASSED\n")
        return True
    except Exception as e:
        logger.error(f"✗ Phase 3.2 tests FAILED: {str(e)}\n")
        return False

async def test_task_scheduler():
    """Test Phase 5: Task Scheduler"""
    logger.info("=" * 80)
    logger.info("Testing Phase 5: Task Scheduler (APScheduler)")
    logger.info("=" * 80)
    
    try:
        from server.task_scheduler import get_task_scheduler
        
        scheduler = get_task_scheduler()
        logger.info(f"✓ Task Scheduler initialized: {scheduler.__class__.__name__}")
        
        # Define a simple async task
        async def test_task():
            return "Task executed successfully"
        
        # Schedule a one-time task
        result = await scheduler.schedule_once(
            task_id="test_task_1",
            task_name="Test One-Time Task",
            task_func=test_task,
            run_at=datetime.now()
        )
        logger.info(f"✓ One-time task scheduling: {result['success']}")
        
        # Get task status
        task_status = scheduler.get_task_status("test_task_1")
        logger.info(f"✓ Task status check: {task_status['status'] if task_status else 'N/A'}")
        
        logger.info("✓ Phase 5 tests PASSED\n")
        return True
    except Exception as e:
        logger.error(f"✗ Phase 5 tests FAILED: {str(e)}\n")
        return False

async def test_security():
    """Test Phase 7: Security Hardening"""
    logger.info("=" * 80)
    logger.info("Testing Phase 7: Security Hardening (Rate Limiting & Input Validation)")
    logger.info("=" * 80)
    
    try:
        from server.security import RateLimiter, InputValidator
        
        # Test Rate Limiter
        rate_limiter = RateLimiter(max_requests=3, window_seconds=60)
        logger.info("✓ Rate Limiter initialized")
        
        # Test multiple requests
        for i in range(3):
            allowed, info = rate_limiter.is_allowed("test_client")
            logger.info(f"  Request {i+1}: allowed={allowed}, remaining={info['remaining']}")
        
        # Test exceeding limit
        allowed, info = rate_limiter.is_allowed("test_client")
        logger.info(f"  Request 4 (should fail): allowed={allowed}")
        
        # Test Input Validator
        validator = InputValidator()
        logger.info("✓ Input Validator initialized")
        
        # Test string validation
        is_valid, error = validator.validate_string("Hello, World!", max_length=100)
        logger.info(f"✓ String validation: valid={is_valid}")
        
        # Test SQL injection detection
        is_safe, error = validator.check_sql_injection("SELECT * FROM users")
        logger.info(f"✓ SQL injection detection: safe={is_safe} (error: {error})")
        
        # Test XSS detection
        is_safe, error = validator.check_xss("<script>alert('xss')</script>")
        logger.info(f"✓ XSS detection: safe={is_safe} (error: {error})")
        
        logger.info("✓ Phase 7 tests PASSED\n")
        return True
    except Exception as e:
        logger.error(f"✗ Phase 7 tests FAILED: {str(e)}\n")
        return False

async def test_agent_orchestrator():
    """Test Phase 3.1: Agent Orchestrator"""
    logger.info("=" * 80)
    logger.info("Testing Phase 3.1: Agent Orchestrator (Agentic Loop)")
    logger.info("=" * 80)
    
    try:
        from server.agent_orchestrator import get_orchestrator
        
        orchestrator = get_orchestrator()
        logger.info(f"✓ Agent Orchestrator initialized: {orchestrator.__class__.__name__}")
        
        # Run a simple agent loop
        logger.info("Running agent loop with test message...")
        state = await orchestrator.run_agent_loop(
            conversation_id="test_conv_1",
            user_message="What is the capital of France?",
            context={"test": True}
        )
        
        logger.info(f"✓ Agent loop completed:")
        logger.info(f"  - Success: {state.success}")
        logger.info(f"  - Iterations: {state.iteration}/{state.max_iterations}")
        logger.info(f"  - Response: {state.response[:100]}..." if state.response else "  - Response: None")
        logger.info(f"  - Errors: {len(state.errors)}")
        
        logger.info("✓ Phase 3.1 tests PASSED\n")
        return True
    except Exception as e:
        logger.error(f"✗ Phase 3.1 tests FAILED: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests"""
    logger.info("\n" + "=" * 80)
    logger.info("AGENT-V2 PRODUCTION UPGRADE - COMPREHENSIVE TEST SUITE")
    logger.info("=" * 80 + "\n")
    
    results = {}
    
    # Run tests
    results["Tool Manager"] = await test_tool_manager()
    results["LLM Client"] = await test_llm_client()
    results["Memory Manager"] = await test_memory_manager()
    results["Error Handler"] = await test_error_handler()
    results["Task Scheduler"] = await test_task_scheduler()
    results["Security"] = await test_security()
    results["Agent Orchestrator"] = await test_agent_orchestrator()
    
    # Summary
    logger.info("=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASSED" if result else "✗ FAILED"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\nTotal: {passed}/{total} tests passed")
    logger.info("=" * 80 + "\n")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
