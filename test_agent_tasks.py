#!/usr/bin/env python3
"""
Test script to verify AGENT-V2 functionality with real tasks.
"""
import requests
import json
import time
import sys

BASE_URL = "http://localhost:8001"
CONVERSATION_ID = f"test_conv_{int(time.time())}"

def test_health():
    """Test agent health endpoint"""
    print("\n🏥 Testing Agent Health...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Agent is healthy")
            return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
    return False

def test_settings():
    """Test settings endpoint"""
    print("\n⚙️  Testing Settings...")
    try:
        response = requests.get(f"{BASE_URL}/settings")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Settings retrieved")
            print(f"   - Agent: {data.get('agent', {}).get('name')}")
            print(f"   - LLM Provider: {data.get('llm', {}).get('provider')}")
            return True
    except Exception as e:
        print(f"❌ Settings retrieval failed: {e}")
    return False

def test_github_user():
    """Test GitHub user info"""
    print("\n🐙 Testing GitHub Integration...")
    try:
        response = requests.post(
            f"{BASE_URL}/chat",
            json={
                "conversation_id": CONVERSATION_ID,
                "message": "Who am I on GitHub? Use the get_github_user tool.",
                "tools_enabled": ["get_github_user"]
            }
        )
        if response.status_code == 200:
            print("✅ GitHub integration working")
            return True
    except Exception as e:
        print(f"❌ GitHub test failed: {e}")
    return False

def test_llm_connection():
    """Test LLM connection"""
    print("\n🧠 Testing LLM Connection...")
    try:
        response = requests.post(
            f"{BASE_URL}/settings/test",
            json={
                "provider": "openai",
                "api_key": "sk-test",
                "model": "gpt-4.1-mini",
                "base_url": "https://api.manus.im/api/llm-proxy/v1"
            }
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print("✅ LLM connection successful")
                return True
    except Exception as e:
        print(f"⚠️  LLM test skipped: {e}")
    return False

def main():
    print("=" * 60)
    print("🤖 AGENT-V2 Functionality Tests")
    print("=" * 60)
    
    results = {
        "Health": test_health(),
        "Settings": test_settings(),
        "GitHub": test_github_user(),
        "LLM": test_llm_connection(),
    }
    
    print("\n" + "=" * 60)
    print("📊 Test Results:")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"{test_name:20} {status}")
    
    print("=" * 60)
    print(f"Overall: {passed}/{total} tests passed")
    print("=" * 60)
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
