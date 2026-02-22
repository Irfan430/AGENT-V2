import asyncio
import os
import json
import logging
from server.agent_orchestrator import get_orchestrator
from server.llm_client import initialize_llm_client
from server.agent_config import AGENT_NAME, AGENT_VERSION

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_manus_capabilities():
    """
    Tests the agent's ability to handle a complex, multi-step task similar to Manus AI.
    Task: Research a topic, create a file with findings, and then summarize it.
    """
    print(f"=== Testing {AGENT_NAME} v{AGENT_VERSION} (Manus-like Capabilities) ===")
    
    # Ensure API Key is set
    api_key = os.getenv("LLM_API_KEY")
    if not api_key:
        print("Error: LLM_API_KEY environment variable not set.")
        return

    # Initialize LLM Client
    initialize_llm_client(api_key=api_key)
    
    orchestrator = get_orchestrator()
    
    # Complex Task: Research and File Management
    user_query = "Research the current state of autonomous AI agents in 2026, write a summary to a file named 'ai_agents_2026.txt', and then tell me the file size."
    
    print(f"\nUser Query: {user_query}")
    print("Running agent loop (this may take a few iterations)...")
    
    try:
        state = await orchestrator.run_agent_loop(
            conversation_id="test-manus-123",
            user_message=user_query
        )
        
        print("\n=== Agent Loop Completed ===")
        print(f"Success: {state.success}")
        print(f"Iterations: {state.iteration}")
        print(f"Final Response: {state.response}")
        
        print("\n--- Thought Process ---")
        for i, thought in enumerate(state.thoughts):
            print(f"Iteration {i+1} Reasoning: {thought.reasoning}")
            if i < len(state.actions):
                action = state.actions[i]
                print(f"Action: {action.description}")
                if action.tool_call:
                    print(f"Tool: {action.tool_call['tool_name']} with input {action.tool_call['tool_input']}")
            if i < len(state.observations):
                obs = state.observations[i]
                print(f"Observation Success: {obs.success}")
        
        if state.success:
            print("\n✅ Test Passed: Agent successfully navigated the multi-step task.")
        else:
            print("\n❌ Test Failed: Agent did not complete the task successfully.")
            if state.errors:
                print(f"Errors encountered: {state.errors}")

    except Exception as e:
        print(f"\n❌ Critical Error during test: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_manus_capabilities())
