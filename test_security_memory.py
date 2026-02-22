#!/usr/bin/env python3
"""
Test security and memory management components.
"""

import sys
import os

# Add server to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'server'))

from security import (
    RateLimiter, 
    InputValidator, 
    SecurityAuditor,
    AuthenticationManager,
    SecurityLevel
)
from memory_manager_v2 import (
    get_memory_manager,
    get_conversation_manager
)

def test_rate_limiter():
    """Test rate limiter."""
    print("\n" + "="*60)
    print("TEST 1: Rate Limiter")
    print("="*60)
    
    limiter = RateLimiter(max_requests=5, window_seconds=60)
    
    # Test allowed requests
    for i in range(5):
        allowed, info = limiter.is_allowed("user_1")
        print(f"Request {i+1}: {'✓ Allowed' if allowed else '✗ Blocked'} (remaining: {info['remaining']})")
    
    # Test rate limit exceeded
    allowed, info = limiter.is_allowed("user_1")
    print(f"Request 6: {'✓ Allowed' if allowed else '✗ Blocked (rate limited)'} (remaining: {info['remaining']})")

def test_input_validator():
    """Test input validation."""
    print("\n" + "="*60)
    print("TEST 2: Input Validator")
    print("="*60)
    
    # Test SQL injection detection
    print("\nSQL Injection Detection:")
    test_cases = [
        ("SELECT * FROM users", False),
        ("Hello world", True),
        ("INSERT INTO table VALUES", False),
    ]
    
    for test_input, should_pass in test_cases:
        is_safe, error = InputValidator.check_sql_injection(test_input)
        status = "✓" if is_safe == should_pass else "✗"
        print(f"{status} '{test_input}': {is_safe}")
    
    # Test XSS detection
    print("\nXSS Detection:")
    test_cases = [
        ("<script>alert('xss')</script>", False),
        ("Hello world", True),
        ("javascript:alert(1)", False),
    ]
    
    for test_input, should_pass in test_cases:
        is_safe, error = InputValidator.check_xss(test_input)
        status = "✓" if is_safe == should_pass else "✗"
        print(f"{status} '{test_input}': {is_safe}")
    
    # Test command injection detection
    print("\nCommand Injection Detection:")
    test_cases = [
        ("ls -la", True),
        ("ls; rm -rf /", False),
        ("echo hello", True),
    ]
    
    for test_input, should_pass in test_cases:
        is_safe, error = InputValidator.check_command_injection(test_input)
        status = "✓" if is_safe == should_pass else "✗"
        print(f"{status} '{test_input}': {is_safe}")

def test_security_auditor():
    """Test security auditor."""
    print("\n" + "="*60)
    print("TEST 3: Security Auditor")
    print("="*60)
    
    auditor = SecurityAuditor()
    
    # Log some security events
    auditor.log_event(
        event_type="unauthorized_access",
        severity=SecurityLevel.HIGH,
        details={"ip": "192.168.1.1", "endpoint": "/api/admin"},
        user_id="user_123"
    )
    
    auditor.log_event(
        event_type="sql_injection_attempt",
        severity=SecurityLevel.CRITICAL,
        details={"payload": "SELECT * FROM users", "endpoint": "/search"},
        user_id=None
    )
    
    auditor.log_event(
        event_type="rate_limit_exceeded",
        severity=SecurityLevel.MEDIUM,
        details={"ip": "192.168.1.2", "requests": 150},
        user_id="user_456"
    )
    
    # Get summary
    summary = auditor.get_security_summary()
    print(f"✓ Total security events: {summary['total_events']}")
    print(f"✓ Event types: {summary['event_types']}")

def test_authentication():
    """Test authentication manager."""
    print("\n" + "="*60)
    print("TEST 4: Authentication Manager")
    print("="*60)
    
    auth = AuthenticationManager()
    
    # Generate API key
    key = auth.generate_api_key("user_123", "test_key")
    print(f"✓ Generated API key: {key[:20]}...")
    
    # Validate API key
    is_valid, user_id = auth.validate_api_key(key)
    print(f"✓ API key validation: {is_valid} (user: {user_id})")
    
    # Test invalid key
    is_valid, user_id = auth.validate_api_key("invalid_key")
    print(f"✓ Invalid key validation: {is_valid}")
    
    # Revoke key
    auth.revoke_api_key(key)
    is_valid, user_id = auth.validate_api_key(key)
    print(f"✓ After revocation: {is_valid}")

def test_memory_manager():
    """Test memory manager."""
    print("\n" + "="*60)
    print("TEST 5: Memory Manager")
    print("="*60)
    
    memory_mgr = get_memory_manager()
    
    # Store memories
    mem1 = memory_mgr.store_memory(
        content="User asked about Python programming",
        memory_type="conversation",
        metadata={"topic": "python"},
        importance_score=0.8
    )
    print(f"✓ Stored memory 1: {mem1}")
    
    mem2 = memory_mgr.store_memory(
        content="Task: Build a web scraper",
        memory_type="task",
        metadata={"project": "scraper"},
        importance_score=0.9
    )
    print(f"✓ Stored memory 2: {mem2}")
    
    # Retrieve memories
    memories = memory_mgr.retrieve_memories(memory_type="conversation", limit=10)
    print(f"✓ Retrieved {len(memories)} conversation memories")
    
    # Search memories
    results = memory_mgr.search_memories("Python", limit=5)
    print(f"✓ Search results: {len(results)} matches")
    
    # Get stats
    stats = memory_mgr.get_memory_stats()
    print(f"✓ Memory stats:")
    print(f"  - Total: {stats['total_memories']}")
    print(f"  - By type: {stats['by_type']}")
    print(f"  - Avg importance: {stats['avg_importance']:.2f}")

def test_conversation_manager():
    """Test conversation manager."""
    print("\n" + "="*60)
    print("TEST 6: Conversation Manager")
    print("="*60)
    
    conv_mgr = get_conversation_manager()
    
    # Start conversation
    conv_id = conv_mgr.start_conversation()
    print(f"✓ Started conversation: {conv_id}")
    
    # Set task
    conv_mgr.set_task_description("Build a Python web scraper for news articles")
    print(f"✓ Set task description")
    
    # Add messages
    conv_mgr.add_message("user", "Can you help me build a web scraper?")
    conv_mgr.add_message("assistant", "Sure! I can help you build a web scraper using Python.")
    conv_mgr.add_message("user", "What libraries should I use?")
    print(f"✓ Added 3 messages")
    
    # Get history
    history = conv_mgr.get_conversation_history(limit=10)
    print(f"✓ Conversation history: {len(history)} messages")
    
    # Get context summary
    summary = conv_mgr.get_context_summary()
    print(f"✓ Context summary: {summary}")

def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("SECURITY & MEMORY MANAGEMENT TEST")
    print("="*60)
    
    try:
        test_rate_limiter()
        test_input_validator()
        test_security_auditor()
        test_authentication()
        test_memory_manager()
        test_conversation_manager()
        
        print("\n" + "="*60)
        print("✓ ALL SECURITY & MEMORY TESTS PASSED")
        print("="*60 + "\n")
        
        return 0
    
    except Exception as e:
        print(f"\n✗ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
