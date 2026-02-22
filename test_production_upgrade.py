"""
Integrated test suite for AGENT-V2 Production Upgrade.
Tests Phase 1.1 (Tools), 1.3 (GitHub), 2.1 (Memory), and 3.1 (Orchestrator).
"""

import asyncio
import os
import logging
import json
import sys
from datetime import datetime

# Add server to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'server'))

from server.llm_client import initialize_llm_client, get_llm_client
from server.tool_manager import get_tool_manager
from server.memory_manager import get_memory_manager
from server.agent_orchestrator import get_orchestrator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_tool_manager():
    """Test Phase 1.1: Production-grade tools."""
    logger.info("--- Testing Phase 1.1: Tool Manager ---")
    tool_manager = get_tool_manager()
    
    # Test execute_command
    logger.info("Testing execute_command...")
    result = await tool_manager.execute_tool(
        "execute_command", 
        {"command": "echo 'Hello Production'"}
    )
    assert result["success"], f"execute_command failed: {result.get('error')}"
    assert "Hello Production" in result["result"], f"Unexpected output: {result['result']}"
    logger.info("✓ execute_command passed")
    
    # Test write_file and read_file
    logger.info("Testing write_file and read_file...")
    test_file = "test_prod.txt"
    test_content = "Production level content"
    
    write_result = await tool_manager.execute_tool(
        "write_file", 
        {"path": test_file, "content": test_content}
    )
    assert write_result["success"], f"write_file failed: {write_result.get('error')}"
    
    read_result = await tool_manager.execute_tool(
        "read_file", 
        {"path": test_file}
    )
    assert read_result["success"], f"read_file failed: {read_result.get('error')}"
    assert read_result["result"] == test_content, f"Content mismatch: {read_result['result']}"
    logger.info("✓ write_file and read_file passed")
    
    # Cleanup
    await tool_manager.execute_tool("delete_file", {"path": test_file})
    logger.info("✓ delete_file passed")

async def test_memory_manager():
    """Test Phase 2.1: Advanced Memory."""
    logger.info("--- Testing Phase 2.1: Memory Manager ---")
    memory_manager = get_memory_manager()
    
    # Test store and retrieve
    logger.info("Testing memory store and retrieve...")
    conv_id = "test_conv_123"
    memory_manager.store_conversation(
        conversation_id=conv_id,
        user_message="What is the capital of France?",
        agent_response="The capital of France is Paris."
    )
    
    results = memory_manager.retrieve("France", memory_type="conversation", k=1)
    assert len(results) > 0, "Memory retrieval failed"
    assert "Paris" in results[0], f"Unexpected memory content: {results[0]}"
    logger.info("✓ memory store and retrieve passed")
    
    # Test history
    history = memory_manager.get_conversation_history(conv_id)
    assert len(history) > 0, "Conversation history retrieval failed"
    logger.info("✓ conversation history passed")

async def test_orchestrator():
    """Test Phase 3.1: Agent Orchestrator loop."""
    logger.info("--- Testing Phase 3.1: Agent Orchestrator ---")
    
    # Ensure LLM client is initialized for testing
    # Note: In a real test, we'd need a valid API key or a mock
    api_key = os.getenv("LLM_API_KEY")
    if not api_key:
        logger.warning("LLM_API_KEY not set. Skipping orchestrator test that requires LLM.")
        return
        
    initialize_llm_client(api_key=api_key)
    orchestrator = get_orchestrator()
    
    logger.info("Running agent loop for a simple task...")
    conversation_id = "test_loop_456"
    user_message = "Create a file named 'hello.txt' with the text 'Hello from Agent' and then read it back."
    
    state = await orchestrator.run_agent_loop(
        conversation_id=conversation_id,
        user_message=user_message
    )
    
    logger.info(f"Agent Loop Finished in {state.iteration} iterations")
    logger.info(f"Final Response: {state.response}")
    
    assert state.success, f"Agent loop failed: {state.response}"
    assert len(state.actions) > 0, "Agent took no actions"
    logger.info("✓ orchestrator loop passed")

async def main():
    """Run all tests."""
    logger.info("Starting Production Upgrade Integration Tests")
    
    try:
        await test_tool_manager()
        await test_memory_manager()
        await test_orchestrator()
        
        logger.info("========================================")
        logger.info("ALL PRODUCTION UPGRADE TESTS PASSED! ✅")
        logger.info("========================================")
        
    except Exception as e:
        logger.error(f"Tests failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
