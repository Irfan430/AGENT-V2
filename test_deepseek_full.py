#!/usr/bin/env python3
"""
Full test of AGENT-V2 with DeepSeek API
"""
import asyncio
import os
import json
from datetime import datetime

os.environ['DEEPSEEK_API_KEY'] = 'sk-af8395cfa3a24a6d86247567d8d9715c'
os.environ['DEEPSEEK_MODEL'] = 'deepseek-chat'
os.environ['DEFAULT_LLM_PROVIDER'] = 'deepseek'

from server.agent_orchestrator import get_orchestrator

def print_section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")

async def run_test(task_num, message):
    print(f"\n📝 Task {task_num}: {message[:80]}...")
    
    orch = get_orchestrator()
    state = await orch.run_agent_loop(
        conversation_id=f"test_{task_num}_{int(datetime.now().timestamp())}",
        user_message=message
    )
    
    print(f"✅ Response received")
    print(f"   Success: {state.success}")
    
    if state.thought:
        print(f"   💭 Thinking: {state.thought.reasoning[:100]}...")
        print(f"   📋 Plan: {len(state.thought.plan)} steps")
    
    if state.actions:
        print(f"   🔧 Actions: {len(state.actions)} action(s)")
    
    if state.errors:
        print(f"   ❌ Errors: {len(state.errors)}")
        for err in state.errors[:2]:
            print(f"      - {err.error[:80]}")
    else:
        print(f"   ✅ No errors")
    
    return state.success and len(state.errors) == 0

async def main():
    print_section("🤖 AGENT-V2 DEEPSEEK FULL TEST")
    
    results = {}
    
    # Test 1: Simple math
    print_section("TEST 1: Simple Math")
    results["Simple Math"] = await run_test(1, "What is 2+2? Think step by step.")
    
    # Test 2: Planning
    print_section("TEST 2: Planning & Strategy")
    results["Planning"] = await run_test(2, "How would you build a Python web scraper? List the steps.")
    
    # Test 3: Memory
    print_section("TEST 3: Memory Test")
    await run_test(3, "Remember: My favorite language is Python and I love building AI agents.")
    await asyncio.sleep(1)
    results["Memory"] = await run_test(3, "What's my favorite language and what do I love building?")
    
    # Test 4: Complex reasoning
    print_section("TEST 4: Complex Reasoning")
    results["Reasoning"] = await run_test(4, "Explain how neural networks learn. Be detailed.")
    
    # Test 5: File operations
    print_section("TEST 5: File Operations")
    results["File Ops"] = await run_test(5, "Create a file called 'deepseek_test.txt' with content 'DeepSeek API works!'")
    
    # Summary
    print_section("📊 TEST SUMMARY")
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name:25} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    print("="*70)

if __name__ == "__main__":
    asyncio.run(main())
