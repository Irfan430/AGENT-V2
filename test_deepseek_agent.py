#!/usr/bin/env python3
"""
Test AGENT-V2 with DeepSeek API
"""
import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8001"
CONVERSATION_ID = f"deepseek_test_{int(time.time())}"

def log_section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")

def send_task(message):
    """Send a task to the agent"""
    print(f"\n📝 Task: {message[:100]}...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/agent/chat",
            json={
                "user_message": message,
                "conversation_id": CONVERSATION_ID,
                "context": {}
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Response received")
            
            # Check for errors
            if data.get("errors"):
                print(f"❌ Error from agent:")
                for error in data["errors"]:
                    print(f"   - {error.get('error', 'Unknown error')[:100]}")
                return False
            
            # Check for thoughts
            if data.get("thought"):
                print(f"💭 Thought: {data['thought'][:100]}...")
            
            # Check for plan
            if data.get("plan"):
                print(f"📋 Plan: {len(data['plan'])} steps")
            
            # Check for actions
            if data.get("actions"):
                print(f"🔧 Actions: {len(data['actions'])} action(s)")
                for action in data["actions"][:2]:
                    print(f"   - {action[:80]}...")
            
            # Check for observations
            if data.get("observations"):
                print(f"👁️  Observations: {len(data['observations'])} observation(s)")
            
            # Check for reflections
            if data.get("reflections"):
                print(f"🤔 Reflections: {len(data['reflections'])} reflection(s)")
            
            return True
        else:
            print(f"❌ Error: Status {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return False

def main():
    log_section("🤖 AGENT-V2 DEEPSEEK API TEST")
    print(f"Conversation ID: {CONVERSATION_ID}")
    print(f"Base URL: {BASE_URL}")
    
    # Test 1: Simple task
    log_section("TEST 1: Simple Task")
    result1 = send_task("What is 2+2? Think about it step by step.")
    
    # Test 2: File operation
    log_section("TEST 2: File Operation")
    result2 = send_task("Create a file called 'test.txt' with content 'Hello from DeepSeek'")
    
    # Test 3: Planning task
    log_section("TEST 3: Planning & Thinking")
    result3 = send_task("I want to build a Python web scraper. What are the steps I should follow?")
    
    # Test 4: Memory test
    log_section("TEST 4: Memory Test")
    result4 = send_task("My favorite programming language is Python. Remember this.")
    time.sleep(1)
    result4b = send_task("What's my favorite programming language?")
    
    # Test 5: Complex reasoning
    log_section("TEST 5: Complex Reasoning")
    result5 = send_task("Explain how a neural network learns. Be detailed.")
    
    # Summary
    log_section("📊 TEST SUMMARY")
    results = {
        "Simple Task": result1,
        "File Operation": result2,
        "Planning": result3,
        "Memory": result4 and result4b,
        "Complex Reasoning": result5
    }
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"{test_name:25} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    print("="*70)

if __name__ == "__main__":
    main()
