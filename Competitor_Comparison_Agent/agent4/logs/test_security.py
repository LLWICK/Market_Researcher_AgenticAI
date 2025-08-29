#test_security.py
#!/usr/bin/env python3
"""
Security Testing Script for Agent 4: Competitor Comparison & Security

This script tests all the enhanced security features:
- HMAC verification with timestamp
- RBAC (Role-Based Access Control)
- Input sanitization and validation
- Rate limiting
- Audit logging
- MCP protocol security
"""

import json
import base64
import time
from datetime import datetime
from typing import Dict, Any

# Handle imports for both direct execution and module import
import sys
from pathlib import Path

# Add current directory to path for direct execution
sys.path.insert(0, str(Path(__file__).parent))

from security import (
    generate_hmac, verify_hmac, role_allowed, audit_log, 
    check_rate_limit, sanitize_text, validate_json_payload, SecurityError
)
from mcp_protocol import AgentMessage, SecureMessageHandler

def test_hmac_verification():
    """Test enhanced HMAC verification with timestamp"""
    print("\n=== Testing HMAC Verification ===")
    
    # Test valid HMAC
    test_data = b'{"test": "data"}'
    signature = generate_hmac(test_data)
    print(f"Generated signature: {signature}")
    
    result = verify_hmac(test_data, signature)
    print(f"✅ Valid HMAC verification: {result}")
    assert result == True
    
    # Test invalid HMAC
    invalid_sig = "1234567890:invalid_signature"
    result = verify_hmac(test_data, invalid_sig)
    print(f"✅ Invalid HMAC rejection: {not result}")
    assert result == False
    
    # Test old timestamp (simulate replay attack)
    old_timestamp = str(int(time.time()) - 400)  # 400 seconds ago
    old_message = old_timestamp.encode() + b":" + test_data
    import hmac
    import hashlib
    import os
    SHARED_SECRET = os.getenv("AGENTS_SHARED_SECRET", "dev-secret")
    old_mac = hmac.new(SHARED_SECRET.encode(), old_message, hashlib.sha256).hexdigest()
    old_signature = f"{old_timestamp}:{old_mac}"
    
    result = verify_hmac(test_data, old_signature)
    print(f"✅ Replay attack prevention: {not result}")
    assert result == False
    
    print("HMAC verification tests passed! ✅")

def test_rbac_system():
    """Test Role-Based Access Control"""
    print("\n=== Testing RBAC System ===")
    
    # Test valid permissions
    assert role_allowed("agent1", "push_market_insights") == True
    assert role_allowed("agent2", "push_raw_data") == True
    assert role_allowed("agent3", "push_trends") == True
    assert role_allowed("agent4", "compare") == True
    assert role_allowed("admin", "compare") == True
    print("✅ Valid role permissions work")
    
    # Test invalid permissions
    assert role_allowed("agent1", "compare") == False
    assert role_allowed("agent2", "push_trends") == False
    assert role_allowed("agent3", "compare") == False
    print("✅ Invalid role permissions denied")
    
    # Test resource-based permissions
    assert role_allowed("agent1", "read_market_data", "market_insights.json") == True
    assert role_allowed("agent2", "read_raw_data", "competitors.json") == True
    assert role_allowed("agent3", "read_trend_data", "trends.json") == True
    assert role_allowed("agent4", "read_comparison_data", "comparison_request.json") == True
    print("✅ Resource-based permissions work")
    
    # Test admin wildcard
    assert role_allowed("admin", "any_action") == True
    assert role_allowed("admin", "any_action", "any_resource.json") == True
    print("✅ Admin wildcard permissions work")
    
    print("RBAC tests passed! ✅")

def test_input_sanitization():
    """Test input sanitization and validation"""
    print("\n=== Testing Input Sanitization ===")
    
    # Test text sanitization
    malicious_text = "Normal text\x00\x01\x02with control chars"
    sanitized = sanitize_text(malicious_text)
    print(f"Original: {repr(malicious_text)}")
    print(f"Sanitized: {repr(sanitized)}")
    assert "\x00" not in sanitized
    assert "\x01" not in sanitized
    assert "\x02" not in sanitized
    print("✅ Control characters removed")
    
    # Test JSON validation
    valid_json = '{"key": "value", "number": 123}'
    invalid_json = '{"key": "value", "invalid": }'
    
    assert validate_json_payload(valid_json) == True
    assert validate_json_payload(invalid_json) == False
    print("✅ JSON validation works")
    
    # Test long text truncation
    long_text = "A" * 15000  # Exceeds MAX_TEXT_LENGTH
    sanitized_long = sanitize_text(long_text)
    assert len(sanitized_long) <= 10000
    print("✅ Long text truncation works")
    
    print("Input sanitization tests passed! ✅")

def test_rate_limiting():
    """Test rate limiting functionality"""
    print("\n=== Testing Rate Limiting ===")
    
    user = "test_user"
    action = "test_action"
    
    # Test within limits
    for i in range(5):
        result = check_rate_limit(user, action, window_minutes=1, max_requests=10)
        assert result == True
    print("✅ Requests within limit allowed")
    
    # Test exceeding limits
    for i in range(10):
        check_rate_limit(user, action, window_minutes=1, max_requests=10)
    
    # This should be rejected
    result = check_rate_limit(user, action, window_minutes=1, max_requests=10)
    assert result == False
    print("✅ Requests exceeding limit rejected")
    
    print("Rate limiting tests passed! ✅")

def test_mcp_protocol_security():
    """Test MCP protocol security features"""
    print("\n=== Testing MCP Protocol Security ===")
    
    # Test valid message creation
    payload = {"test": "data", "value": 123}
    message = SecureMessageHandler.create_message(
        sender="agent1",
        role="agent1", 
        action="push_market_insights",
        payload=payload
    )
    
    assert message.sender == "agent1"
    assert message.role == "agent1"
    assert message.action == "push_market_insights"
    assert message.message_id is not None
    print("✅ Valid message creation works")
    
    # Test message validation
    try:
        invalid_message = AgentMessage(
            sender="agent1",
            role="invalid_role",  # Invalid role
            action="push_market_insights",
            payload='{"test": "data"}'
        )
        assert False, "Should have raised validation error"
    except ValueError:
        print("✅ Invalid role rejected")
    
    try:
        invalid_action = AgentMessage(
            sender="agent1",
            role="agent1",
            action="invalid_action",  # Invalid action
            payload='{"test": "data"}'
        )
        assert False, "Should have raised validation error"
    except ValueError:
        print("✅ Invalid action rejected")
    
    # Test message processing
    valid_message = AgentMessage(
        sender="agent1",
        role="agent1",
        action="push_market_insights",
        payload='{"test": "data"}'
    )
    
    result = SecureMessageHandler.process_message(valid_message)
    assert result == True
    print("✅ Valid message processing works")
    
    print("MCP protocol security tests passed! ✅")

def test_audit_logging():
    """Test audit logging functionality"""
    print("\n=== Testing Audit Logging ===")
    
    # Test basic audit logging
    audit_log("test_event", "test_user", {"detail": "test_detail"})
    print("✅ Basic audit logging works")
    
    # Test audit logging with complex data
    complex_details = {
        "timestamp": datetime.utcnow().isoformat(),
        "ip_address": "192.168.1.1",
        "user_agent": "test-agent/1.0",
        "action_result": "success"
    }
    audit_log("complex_test_event", "test_user", complex_details)
    print("✅ Complex audit logging works")
    
    print("Audit logging tests passed! ✅")

def test_end_to_end_security():
    """Test end-to-end security workflow"""
    print("\n=== Testing End-to-End Security Workflow ===")
    
    # Simulate agent-to-agent communication
    sender = "agent2"
    role = "agent2"
    action = "push_raw_data"
    
    # Step 1: Create secure message
    payload = {
        "competitors": [
            {"name": "TestComp", "kpis": {"MAU": 1.0}}
        ]
    }
    
    message = SecureMessageHandler.create_message(
        sender=sender,
        role=role,
        action=action,
        payload=payload
    )
    print("✅ Step 1: Secure message created")
    
    # Step 2: Generate HMAC for payload
    payload_bytes = message.payload.encode('utf-8')
    hmac_sig = generate_hmac(payload_bytes)
    message.hmac_sig = hmac_sig
    print("✅ Step 2: HMAC signature generated")
    
    # Step 3: Verify RBAC
    if not role_allowed(role, action):
        print("❌ RBAC check failed")
        return False
    print("✅ Step 3: RBAC check passed")
    
    # Step 4: Verify HMAC
    if not verify_hmac(payload_bytes, hmac_sig):
        print("❌ HMAC verification failed")
        return False
    print("✅ Step 4: HMAC verification passed")
    
    # Step 5: Process message
    if not SecureMessageHandler.process_message(message):
        print("❌ Message processing failed")
        return False
    print("✅ Step 5: Message processed successfully")
    
    # Step 6: Audit log
    audit_log("end_to_end_test", sender, {
        "message_id": message.message_id,
        "action": action,
        "result": "success"
    })
    print("✅ Step 6: Audit logged")
    
    print("End-to-end security workflow test passed! ✅")

def main():
    """Run all security tests"""
    print("🔒 Starting Agent 4 Security Tests")
    print("=" * 50)
    
    try:
        test_hmac_verification()
        test_rbac_system()
        test_input_sanitization()
        test_rate_limiting()
        test_mcp_protocol_security()
        test_audit_logging()
        test_end_to_end_security()
        
        print("\n" + "=" * 50)
        print("🎉 ALL SECURITY TESTS PASSED! 🎉")
        print("Agent 4 security features are working correctly.")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    main()
