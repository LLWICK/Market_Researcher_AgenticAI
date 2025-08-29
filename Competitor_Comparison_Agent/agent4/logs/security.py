#security.py

import hmac, hashlib, os, time, logging
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
import json

# Configure logging for security events
logging.basicConfig(level=logging.INFO)
security_logger = logging.getLogger(__name__)

# Enhanced shared secret HMAC for message integrity between agents
SHARED_SECRET = os.getenv("AGENTS_SHARED_SECRET", "dev-secret")  # set in your shell
MAX_MESSAGE_AGE = 300  # 5 minutes

class SecurityError(Exception):
    """Custom exception for security-related errors"""
    pass

def generate_hmac(payload_bytes: bytes, timestamp: Optional[str] = None) -> str:
    """Generate HMAC signature with optional timestamp"""
    if timestamp is None:
        timestamp = str(int(time.time()))
    
    # Include timestamp in the signature to prevent replay attacks
    message = timestamp.encode() + b":" + payload_bytes
    mac = hmac.new(SHARED_SECRET.encode(), message, hashlib.sha256).hexdigest()
    return f"{timestamp}:{mac}"

def verify_hmac(payload_bytes: bytes, signature: str) -> bool:
    """Enhanced HMAC verification with timestamp validation"""
    try:
        if ":" not in signature:
            security_logger.warning("Invalid signature format - missing timestamp")
            return False
            
        timestamp_str, mac = signature.split(":", 1)
        timestamp = int(timestamp_str)
        current_time = int(time.time())
        
        # Check if message is too old (replay attack protection)
        if current_time - timestamp > MAX_MESSAGE_AGE:
            security_logger.warning(f"Message too old: {current_time - timestamp} seconds")
            return False
            
        # Verify the HMAC
        expected_message = timestamp_str.encode() + b":" + payload_bytes
        expected_mac = hmac.new(SHARED_SECRET.encode(), expected_message, hashlib.sha256).hexdigest()
        
        if hmac.compare_digest(mac, expected_mac):
            security_logger.info(f"HMAC verification successful for timestamp {timestamp}")
            return True
        else:
            security_logger.warning("HMAC verification failed")
            return False
            
    except (ValueError, IndexError) as e:
        security_logger.error(f"HMAC verification error: {e}")
        return False

def role_allowed(role: str, action: str, resource: Optional[str] = None) -> bool:
    """Enhanced RBAC with resource-based permissions"""
    # Enhanced policy with resource-based access control
    policy: Dict[str, Dict[str, set]] = {
        "agent1": {
            "actions": {"push_market_insights", "read_market_data"},
            "resources": {"market_insights.json", "surveys.json", "reports.json"}
        },
        "agent2": {
            "actions": {"push_raw_data", "scrape_data", "read_raw_data"},
            "resources": {"competitors.json", "scraped_data.json", "raw_feeds.json"}
        },
        "agent3": {
            "actions": {"push_trends", "analyze_trends", "read_trend_data"},
            "resources": {"trends.json", "sentiment.json", "patterns.json"}
        },
        "agent4": {
            "actions": {"compare", "export", "read_comparison_data", "generate_reports"},
            "resources": {"comparison_request.json", "competitor_comparison_result.json"}
        },
        "admin": {
            "actions": {"*"},
            "resources": {"*"}
        }
    }
    
    user_policy = policy.get(role, {"actions": set(), "resources": set()})
    allowed_actions = user_policy.get("actions", set())
    allowed_resources = user_policy.get("resources", set())
    
    # Check action permission
    action_allowed = "*" in allowed_actions or action in allowed_actions
    
    # Check resource permission if specified
    if resource:
        resource_allowed = "*" in allowed_resources or resource in allowed_resources
        result = action_allowed and resource_allowed
    else:
        result = action_allowed
    
    # Log security decisions
    security_logger.info(f"RBAC check: role={role}, action={action}, resource={resource}, allowed={result}")
    
    return result

def sanitize_text(s: str) -> str:
    """Enhanced input sanitization"""
    if not isinstance(s, str):
        raise SecurityError("Input must be a string")
    
    # Remove control characters and limit length
    MAX_TEXT_LENGTH = 10000
    if len(s) > MAX_TEXT_LENGTH:
        security_logger.warning(f"Text truncated from {len(s)} to {MAX_TEXT_LENGTH} characters")
        s = s[:MAX_TEXT_LENGTH]
    
    # Remove control characters but keep newlines and tabs for JSON
    sanitized = "".join(ch for ch in s if ch.isprintable() or ch in '\n\t\r')
    return sanitized.strip()

def validate_json_payload(payload: str) -> bool:
    """Validate that the payload is proper JSON"""
    try:
        json.loads(payload)
        return True
    except json.JSONDecodeError as e:
        security_logger.error(f"Invalid JSON payload: {e}")
        return False

def audit_log(event: str, user: str, details: Optional[Dict] = None):
    """Security audit logging"""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "event": event,
        "user": user,
        "details": details or {}
    }
    security_logger.info(f"AUDIT: {json.dumps(log_entry)}")

def check_rate_limit(user: str, action: str, window_minutes: int = 60, max_requests: int = 100) -> bool:
    """Simple rate limiting (in production, use Redis or similar)"""
    # This is a simple in-memory rate limiter for demo purposes
    # In production, you'd want to use Redis or a database
    from collections import defaultdict, deque
    
    if not hasattr(check_rate_limit, "requests"):
        check_rate_limit.requests = defaultdict(lambda: deque())
    
    now = datetime.utcnow()
    cutoff = now - timedelta(minutes=window_minutes)
    
    # Clean old requests
    user_requests = check_rate_limit.requests[f"{user}:{action}"]
    while user_requests and user_requests[0] < cutoff:
        user_requests.popleft()
    
    # Check if under limit
    if len(user_requests) >= max_requests:
        security_logger.warning(f"Rate limit exceeded for {user}:{action}")
        return False
    
    # Add current request
    user_requests.append(now)
    return True
