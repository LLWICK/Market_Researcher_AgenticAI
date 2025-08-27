#mcp_protocol.py

from pydantic import BaseModel, validator
from typing import Optional, Dict, Any
from datetime import datetime
import json
# Handle imports for both direct execution and module import
try:
    from .security import sanitize_text, validate_json_payload, SecurityError, audit_log
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from security import sanitize_text, validate_json_payload, SecurityError, audit_log

class AgentMessage(BaseModel):
    sender: str                 # e.g., "agent1" 
    role: str                   # for RBAC
    action: str                 # e.g., "push_trends"
    hmac_sig: Optional[str] = None
    content_type: str = "application/json"
    payload: str = ""           # JSON string; keep it text for generic transport
    timestamp: Optional[str] = None
    message_id: Optional[str] = None
    
    @validator('sender')
    def validate_sender(cls, v):
        if not v or len(v) > 50:
            raise ValueError("Sender must be 1-50 characters")
        return sanitize_text(v)
    
    @validator('role')
    def validate_role(cls, v):
        allowed_roles = {'agent1', 'agent2', 'agent3', 'agent4', 'admin'}
        if v not in allowed_roles:
            raise ValueError(f"Role must be one of: {allowed_roles}")
        return v
    
    @validator('action')
    def validate_action(cls, v):
        allowed_actions = {
            'push_market_insights', 'push_raw_data', 'push_trends', 
            'compare', 'export', 'read_market_data', 'read_raw_data',
            'read_trend_data', 'read_comparison_data', 'generate_reports'
        }
        if v not in allowed_actions:
            raise ValueError(f"Action must be one of: {allowed_actions}")
        return v
    
    @validator('payload')
    def validate_payload(cls, v):
        if not v:
            return v
        # Sanitize and validate JSON
        sanitized = sanitize_text(v)
        if not validate_json_payload(sanitized):
            raise ValueError("Payload must be valid JSON")
        return sanitized

    def safe_payload(self) -> str:
        """Return sanitized payload"""
        return sanitize_text(self.payload)
    
    def get_payload_dict(self) -> Dict[str, Any]:
        """Parse payload as dictionary"""
        try:
            return json.loads(self.safe_payload())
        except json.JSONDecodeError:
            raise SecurityError("Invalid JSON in payload")
    
    def log_message(self, event: str):
        """Log this message for audit purposes"""
        audit_log(
            event=event,
            user=self.sender,
            details={
                "role": self.role,
                "action": self.action,
                "message_id": self.message_id,
                "content_type": self.content_type
            }
        )

class SecureMessageHandler:
    """Handles secure message processing for MCP protocol"""
    
    @staticmethod
    def create_message(sender: str, role: str, action: str, payload: Dict[str, Any], 
                      message_id: Optional[str] = None) -> AgentMessage:
        """Create a secure agent message"""
        import uuid
        
        if message_id is None:
            message_id = str(uuid.uuid4())
        
        timestamp = datetime.utcnow().isoformat()
        
        message = AgentMessage(
            sender=sender,
            role=role,
            action=action,
            payload=json.dumps(payload),
            timestamp=timestamp,
            message_id=message_id
        )
        
        message.log_message("message_created")
        return message
    
    @staticmethod
    def process_message(message: AgentMessage) -> bool:
        """Process and validate an incoming message"""
        try:
            # Log incoming message
            message.log_message("message_received")
            
            # Validate message structure
            if not message.sender or not message.role or not message.action:
                raise SecurityError("Missing required message fields")
            
            # Additional security checks could go here
            # (rate limiting, content scanning, etc.)
            
            message.log_message("message_processed")
            return True
            
        except Exception as e:
            message.log_message(f"message_error: {str(e)}")
            return False
