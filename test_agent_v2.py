import asyncio
import os
import json
import logging
from server.agent_orchestrator import get_orchestrator
from server.llm_client import initialize_llm_client, get_llm_client, LLMResponse
from server.agent_config import AGENT_NAME, AGENT_VERSION
from server.agent_state import ToolCall
from unittest.mock import MagicMock, AsyncMock

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def run_test(test_name, query, mock_responses=None):
    print(f"\n>>> Running Test: {test_name}")
    print(f"Query: {query}")
    
    # Mock LLM client if responses are provided
    if mock_responses:
        client_manager = get_llm_client()
        client = client_manager.get_client()
        client.chat_completion_async = AsyncMock(side_effect=[
            LLMResponse(content=resp, finish_reason="stop", provider="mock")
            for resp in mock_responses
        ])

    orchestrator = get_orchestrator()
    try:
        state = await orchestrator.run_agent_loop(
            conversation_id=f"test-{test_name}",
            user_message=query
        )
        
        print(f"Success: {state.success}")
        print(f"Iterations: {state.iteration}")
        print(f"Final Response: {state.response}")
        
        if state.errors:
            print(f"Errors: {json.dumps(state.errors, indent=2)}")
            
        return state
    except Exception as e:
        print(f"Critical Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

async def main():
    # Set dummy API key if not present for initialization check
    if not os.getenv("LLM_API_KEY"):
        os.environ["LLM_API_KEY"] = "sk-dummy-key"
    
    initialize_llm_client(api_key=os.environ["LLM_API_KEY"])
    
    # Test 1: Basic Personality and Greeting
    personality_mock = [
        json.dumps({
            "reasoning": "User greeted me. I should introduce myself and my capabilities.",
            "plan": ["Introduce myself", "List capabilities"],
            "next_action": "respond",
            "tool_input": {},
            "confidence": 1.0
        }),
        "Hello! I am Manus Agent Pro, your autonomous AI assistant. I can help with coding, web browsing, file management, and more."
    ]
    await run_test("Personality", "Hello, who are you and what can you do?", personality_mock)
    
    # Test 2: Coding Task
    coding_mock = [
        json.dumps({
            "reasoning": "I need to write a python script for Fibonacci and save it to 'fib.py'.",
            "plan": ["Write the script content", "Use write_file tool to save it"],
            "next_action": "write_file",
            "tool_input": {"path": "fib.py", "content": "def fib(n):\n    a, b = 0, 1\n    res = []\n    for _ in range(n):\n        res.append(a)\n        a, b = b, a + b\n    return res\n\nprint(fib(10))"},
            "confidence": 1.0
        }),
        json.dumps({
            "reasoning": "File saved successfully. Now I should respond to the user.",
            "plan": ["Confirm file creation"],
            "next_action": "respond",
            "tool_input": {},
            "confidence": 1.0
        }),
        "I have written the Fibonacci script and saved it to 'fib.py'."
    ]
    await run_test("Coding", "Write a python script that calculates the first 10 fibonacci numbers and saves it to 'fib.py'", coding_mock)
    
    # Test 3: File System and Observation
    file_ops_mock = [
        json.dumps({
            "reasoning": "I need to read the content of 'fib.py'.",
            "plan": ["Use read_file tool"],
            "next_action": "read_file",
            "tool_input": {"path": "fib.py"},
            "confidence": 1.0
        }),
        json.dumps({
            "reasoning": "I have the file content. Now I will explain it to the user.",
            "plan": ["Describe content"],
            "next_action": "respond",
            "tool_input": {},
            "confidence": 1.0
        }),
        "The file 'fib.py' contains a function to calculate Fibonacci numbers and prints the first 10."
    ]
    await run_test("FileOps", "Read the content of 'fib.py' and tell me what's inside.", file_ops_mock)

if __name__ == "__main__":
    asyncio.run(main())
