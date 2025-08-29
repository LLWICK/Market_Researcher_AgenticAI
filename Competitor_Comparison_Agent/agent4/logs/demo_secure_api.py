#demo_secure_api.py
#!/usr/bin/env python3
"""
Demonstration of Secure API Usage for Agent 4: Competitor Comparison & Security

This script demonstrates how to use the enhanced security features:
- Secure agent-to-agent communication
- HMAC-signed data transmission
- MCP protocol messaging
- Authentication and authorization

To run the API server:
    uvicorn api:app --host 0.0.0.0 --port 8000

To test the secure endpoints:
    python demo_secure_api.py
"""

import json
import base64
import time
import requests
from datetime import datetime
from typing import Dict, Any

# Handle imports for both direct execution and module import
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from security import generate_hmac, SecurityError
from mcp_protocol import AgentMessage, SecureMessageHandler

# API Configuration
API_BASE_URL = "http://localhost:8000"
API_TOKEN = "agent4-secure-token"  # In production, use proper JWT tokens

def create_auth_headers():
    """Create authentication headers"""
    return {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }

def demo_secure_data_push():
    """Demonstrate secure data push with HMAC verification"""
    print("\n=== Demo: Secure Data Push ===")
    
    # Sample competitor data from Agent 2
    competitor_data = [
        {
            "name": "SecureComp",
            "website": "https://securecomp.example",
            "kpis": {"MAU": 3.2, "NPS": 68},
            "pricing": {"basic": 25, "pro": 65},
            "features": {"api": True, "sso": True, "analytics": True}
        }
    ]
    
    # Convert to JSON and encode
    json_data = json.dumps(competitor_data, indent=2)
    encoded_data = base64.b64encode(json_data.encode('utf-8')).decode('utf-8')
    
    # Generate HMAC signature
    hmac_signature = generate_hmac(json_data.encode('utf-8'))
    
    # Prepare payload
    payload = {
        "role": "agent2",
        "filename": "competitors.json",
        "content_b64": encoded_data,
        "sender": "agent2"
    }
    
    headers = create_auth_headers()
    headers["X-Signature"] = hmac_signature
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/push",
            json=payload,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Secure data push successful!")
            print(f"Response: {response.json()}")
        else:
            print(f"❌ Data push failed: {response.status_code} - {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        print("💡 Make sure the API server is running: uvicorn api:app --host 0.0.0.0 --port 8000")

def demo_secure_comparison():
    """Demonstrate secure comparison request"""
    print("\n=== Demo: Secure Comparison ===")
    
    payload = {
        "requester_role": "admin",
        "include_llm_summary": True
    }
    
    headers = create_auth_headers()
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/compare",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            print("✅ Secure comparison successful!")
            result = response.json()
            print(f"Message: {result.get('message')}")
            print(f"Output: {result.get('output')}")
            print(f"Timestamp: {result.get('timestamp')}")
        else:
            print(f"❌ Comparison failed: {response.status_code} - {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")

def demo_mcp_message():
    """Demonstrate MCP protocol secure messaging"""
    print("\n=== Demo: MCP Protocol Messaging ===")
    
    # Create a secure MCP message
    payload_data = {
        "action": "request_comparison",
        "market": "AI-Security",
        "priority": "high"
    }
    
    message = SecureMessageHandler.create_message(
        sender="agent3",
        role="agent3",
        action="push_trends",
        payload=payload_data
    )
    
    headers = create_auth_headers()
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/mcp/message",
            json=message.dict(),
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ MCP message processed successfully!")
            result = response.json()
            print(f"Message ID: {result.get('message_id')}")
            print(f"Timestamp: {result.get('timestamp')}")
        else:
            print(f"❌ MCP message failed: {response.status_code} - {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")

def demo_security_status():
    """Check security status of the API"""
    print("\n=== Demo: Security Status Check ===")
    
    headers = create_auth_headers()
    
    try:
        # Health check
        response = requests.get(f"{API_BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            print("✅ API Health Check: OK")
            print(f"Service: {response.json().get('service')}")
        
        # Security status
        response = requests.get(
            f"{API_BASE_URL}/security/status",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Security Status Check: OK")
            status = response.json()
            print(f"HMAC Enabled: {status.get('hmac_enabled')}")
            print(f"RBAC Enabled: {status.get('rbac_enabled')}")
            print(f"Rate Limiting: {status.get('rate_limiting_enabled')}")
            print(f"Audit Logging: {status.get('audit_logging_enabled')}")
        else:
            print(f"❌ Security status check failed: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")

def demo_rate_limiting():
    """Demonstrate rate limiting protection"""
    print("\n=== Demo: Rate Limiting Protection ===")
    
    headers = create_auth_headers()
    success_count = 0
    rate_limited_count = 0
    
    print("Sending multiple requests to test rate limiting...")
    
    for i in range(15):  # Send more requests than the limit
        try:
            response = requests.get(
                f"{API_BASE_URL}/security/status",
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 200:
                success_count += 1
            elif response.status_code == 429:
                rate_limited_count += 1
                break
            
        except requests.exceptions.RequestException:
            break
    
    print(f"✅ Successful requests: {success_count}")
    if rate_limited_count > 0:
        print(f"✅ Rate limiting activated after {success_count} requests")
    else:
        print("ℹ️ Rate limit not reached (may need more requests)")

def demo_authentication_failure():
    """Demonstrate authentication failure protection"""
    print("\n=== Demo: Authentication Protection ===")
    
    # Try request without authentication
    try:
        response = requests.get(f"{API_BASE_URL}/security/status", timeout=10)
        if response.status_code == 401:
            print("✅ Unauthenticated request properly rejected")
        else:
            print(f"❌ Expected 401, got {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
    
    # Try request with invalid token
    invalid_headers = {
        "Authorization": "Bearer invalid-token",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/security/status",
            headers=invalid_headers,
            timeout=10
        )
        if response.status_code == 401:
            print("✅ Invalid token properly rejected")
        else:
            print(f"❌ Expected 401, got {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")

def main():
    """Run all security demonstrations"""
    print("🔒 Agent 4: Secure API Demonstration")
    print("=" * 50)
    print("This demo shows the enhanced security features of Agent 4")
    print("Make sure the API server is running: uvicorn api:app --host 0.0.0.0 --port 8000")
    print("=" * 50)
    
    # Check if API is available
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("❌ API server not available. Please start it first.")
            return
    except requests.exceptions.RequestException:
        print("❌ Cannot connect to API server.")
        print("💡 Start the server with: uvicorn api:app --host 0.0.0.0 --port 8000")
        return
    
    print("✅ API server is available")
    
    # Run demonstrations
    demo_security_status()
    demo_authentication_failure()
    demo_secure_data_push()
    demo_secure_comparison()
    demo_mcp_message()
    demo_rate_limiting()
    
    print("\n" + "=" * 50)
    print("🎉 Security demonstration completed!")
    print("Agent 4 security features are fully functional.")

if __name__ == "__main__":
    main()





