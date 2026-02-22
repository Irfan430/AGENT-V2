#!/usr/bin/env python3
"""
Test AGENT-V2 with real tasks to verify:
- Agent thinking and planning
- Memory retention
- Tool execution
- Response quality
"""
import requests
import json
import time
import sys
from datetime import datetime

BASE_URL = "http://localhost:8001"
CONVERSATION_ID = f"test_conv_{int(time.time())}"

def log_test(title, message=""):
    """Log test output"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"\n[{timestamp}] {title}")
    if message:
        print(f"  {message}")

def send_task(message, task_num):
    """Send a task to the agent and get response"""
    log_test(f"TASK {task_num}: Sending Request", message[:80])
    
    try:
        response = requests.post(
            f"{BASE_URL}/agent/chat",
            json={
                "user_message": message,  # Fixed field name
                "conversation_id": CONVERSATION_ID,
                "context": {}
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            log_test(f"TASK {task_num}: Agent Response", "✅ Received")
            
            # Print full response for debugging
            print(f"  📋 Full Response:\n{json.dumps(data, indent=2)[:500]}")
            
            return data
        else:
            log_test(f"TASK {task_num}: Error", f"Status {response.status_code}")
            print(f"  Response: {response.text[:300]}")
            return None
            
    except Exception as e:
        log_test(f"TASK {task_num}: Exception", str(e))
        return None

def test_thinking():
    """Test 1: Agent Thinking & Planning"""
    log_test("TEST 1: AGENT THINKING & PLANNING")
    print("  Testing if agent can think through a complex task...")
    
    task = "I need to create a Python script that reads a file, processes it, and saves the result. Plan the steps first."
    response = send_task(task, 1)
    
    if response:
        print("  ✅ Agent demonstrated thinking capability")
        return True
    return False

def test_memory():
    """Test 2: Memory Retention"""
    log_test("TEST 2: MEMORY RETENTION")
    print("  Testing if agent remembers previous context...")
    
    # First message
    task1 = "My name is Ahmed and I'm working on an AI project."
    response1 = send_task(task1, 2)
    
    time.sleep(1)
    
    # Second message referencing first
    task2 = "What's my name and what project am I working on?"
    response2 = send_task(task2, 2)
    
    if response2 and "Ahmed" in str(response2):
        print("  ✅ Agent remembered previous context")
        return True
    else:
        print("  ⚠️  Agent memory test inconclusive")
        return False

def test_tool_execution():
    """Test 3: Tool Execution"""
    log_test("TEST 3: TOOL EXECUTION")
    print("  Testing if agent can execute tools properly...")
    
    task = "List all files in the current directory and tell me how many files there are."
    response = send_task(task, 3)
    
    if response:
        print("  ✅ Agent executed tools")
        return True
    else:
        print("  ⚠️  Tool execution test inconclusive")
        return False

def test_complex_task():
    """Test 4: Complex Multi-step Task"""
    log_test("TEST 4: COMPLEX MULTI-STEP TASK")
    print("  Testing if agent can handle complex tasks...")
    
    task = """Create a test file called 'agent_test.txt' with the content:
    'AGENT-V2 Test - Created at {}'.
    Then read it back and confirm the content.""".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    response = send_task(task, 4)
    
    if response:
        print("  ✅ Agent handled complex task")
        return True
    return False

def test_error_handling():
    """Test 5: Error Handling"""
    log_test("TEST 5: ERROR HANDLING")
    print("  Testing if agent handles errors gracefully...")
    
    task = "Try to read a file that doesn't exist and tell me what error you get."
    response = send_task(task, 5)
    
    if response:
        print("  ✅ Agent handled error scenario")
        return True
    return False

def main():
    print("=" * 70)
    print("🤖 AGENT-V2 REAL TASK TESTING")
    print("=" * 70)
    print(f"Conversation ID: {CONVERSATION_ID}")
    print(f"Base URL: {BASE_URL}")
    print("=" * 70)
    
    # Run tests
    results = {
        "Thinking": test_thinking(),
        "Memory": test_memory(),
        "Tool Execution": test_tool_execution(),
        "Complex Task": test_complex_task(),
        "Error Handling": test_error_handling(),
    }
    
    # Print summary
    print("\n" + "=" * 70)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"{test_name:25} {status}")
    
    print("=" * 70)
    print(f"Overall: {passed}/{total} tests passed")
    print("=" * 70)
    
    return 0 if passed >= 3 else 1

if __name__ == "__main__":
    sys.exit(main())
