#api.py
from fastapi import FastAPI, Header, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from typing import Optional, Dict, Any
import json, base64, time
from datetime import datetime
from .security import (
    verify_hmac, role_allowed, audit_log, check_rate_limit, 
    sanitize_text, validate_json_payload, SecurityError, generate_hmac
)
from .mcp_protocol import AgentMessage, SecureMessageHandler

# Handle import for both direct execution and module import
try:
    from .Competitor_Comparison_Agent import run_compare
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from Competitor_Comparison_Agent import run_compare

app = FastAPI(
    title="Agent 4: Competitor Comparison & Security API",
    description="Secure API for competitor analysis and agent communication",
    version="1.0.0"
)

# Add CORS middleware for secure cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],  # Restrict to known origins
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

security = HTTPBearer()

class PushPayload(BaseModel):
    role: str
    filename: str
    content_b64: str   # base64(JSON)
    sender: Optional[str] = "unknown"
    
    @validator('role')
    def validate_role(cls, v):
        allowed_roles = {'agent1', 'agent2', 'agent3', 'agent4', 'admin'}
        if v not in allowed_roles:
            raise ValueError(f"Role must be one of: {allowed_roles}")
        return v
    
    @validator('filename')
    def validate_filename(cls, v):
        # Only allow specific filenames for security
        allowed_files = {
            'competitors.json', 'trends.json', 'comparison_request.json',
            'market_insights.json', 'raw_data.json'
        }
        if v not in allowed_files:
            raise ValueError(f"Filename must be one of: {allowed_files}")
        return sanitize_text(v)

class CompareRequest(BaseModel):
    requester_role: str = "admin"
    include_llm_summary: bool = True
    
    @validator('requester_role')
    def validate_role(cls, v):
        allowed_roles = {'agent4', 'admin'}
        if v not in allowed_roles:
            raise ValueError(f"Role must be one of: {allowed_roles}")
        return v

# Security middleware
async def verify_authentication(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify bearer token (in production, use proper JWT validation)"""
    if not credentials.token:
        raise HTTPException(status_code=401, detail="Missing authentication token")
    
    # In production, validate JWT token here
    # For now, we'll use a simple token check
    if credentials.token != "agent4-secure-token":
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    
    return credentials.token

@app.middleware("http")
async def security_middleware(request: Request, call_next):
    """Global security middleware"""
    start_time = time.time()
    
    # Log all requests
    audit_log(
        event="api_request",
        user=request.client.host,
        details={
            "method": request.method,
            "url": str(request.url),
            "user_agent": request.headers.get("user-agent", "unknown")
        }
    )
    
    response = await call_next(request)
    
    # Log response time
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    return response

@app.post("/push")
async def push_data(
    pp: PushPayload, 
    request: Request,
    x_signature: Optional[str] = Header(default=None),
    token: str = Depends(verify_authentication)
):
    """Secure endpoint for agents to push data"""
    client_ip = request.client.host
    
    # Rate limiting
    if not check_rate_limit(pp.sender, "push_data", window_minutes=60, max_requests=50):
        audit_log("rate_limit_exceeded", pp.sender, {"action": "push_data", "ip": client_ip})
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    # RBAC check with resource
    if not role_allowed(pp.role, f"push_{pp.filename.split('.')[0]}", pp.filename):
        audit_log("rbac_denied", pp.sender, {"role": pp.role, "filename": pp.filename})
        raise HTTPException(status_code=403, detail="RBAC denied")
    
    # HMAC verification
    if not x_signature:
        audit_log("missing_hmac", pp.sender, {"filename": pp.filename})
        raise HTTPException(status_code=401, detail="Missing HMAC")
    
    try:
        body = base64.b64decode(pp.content_b64)
    except Exception as e:
        audit_log("invalid_base64", pp.sender, {"error": str(e)})
        raise HTTPException(status_code=400, detail="Invalid base64 encoding")
    
    if not verify_hmac(body, x_signature):
        audit_log("hmac_verification_failed", pp.sender, {"filename": pp.filename})
        raise HTTPException(status_code=401, detail="HMAC verification failed")
    
    # Validate JSON content
    try:
        content = body.decode("utf-8")
        if not validate_json_payload(content):
            raise HTTPException(status_code=400, detail="Invalid JSON content")
    except UnicodeDecodeError:
        audit_log("invalid_encoding", pp.sender, {"filename": pp.filename})
        raise HTTPException(status_code=400, detail="Invalid UTF-8 encoding")
    
    # Save to inbound folder
    try:
        from pathlib import Path
        IN = Path(__file__).resolve().parents[1] / "data" / "inbound"
        IN.mkdir(parents=True, exist_ok=True)
        (IN / pp.filename).write_text(content, encoding="utf-8")
        
        audit_log("data_pushed", pp.sender, {
            "filename": pp.filename,
            "size": len(content),
            "ip": client_ip
        })
        
        return {"ok": True, "message": f"Data successfully saved to {pp.filename}"}
        
    except Exception as e:
        audit_log("file_save_error", pp.sender, {"error": str(e), "filename": pp.filename})
        raise HTTPException(status_code=500, detail="Failed to save data")

@app.post("/compare")
async def compare_now(
    request: CompareRequest,
    req: Request,
    token: str = Depends(verify_authentication)
):
    """Secure endpoint to trigger competitor comparison"""
    client_ip = req.client.host
    
    # Rate limiting
    if not check_rate_limit(request.requester_role, "compare", window_minutes=60, max_requests=10):
        audit_log("rate_limit_exceeded", request.requester_role, {"action": "compare", "ip": client_ip})
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    # RBAC check
    if not role_allowed(request.requester_role, "compare"):
        audit_log("rbac_denied", request.requester_role, {"action": "compare"})
        raise HTTPException(status_code=403, detail="RBAC denied")
    
    try:
        audit_log("comparison_started", request.requester_role, {"ip": client_ip})
        out = run_compare()
        
        audit_log("comparison_completed", request.requester_role, {
            "output_file": str(out),
            "ip": client_ip
        })
        
        return {
            "ok": True, 
            "message": "Comparison completed successfully",
            "output": str(out),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        audit_log("comparison_error", request.requester_role, {"error": str(e), "ip": client_ip})
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Agent 4: Competitor Comparison & Security",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/security/status")
async def security_status(token: str = Depends(verify_authentication)):
    """Get security status and metrics"""
    return {
        "hmac_enabled": True,
        "rbac_enabled": True,
        "rate_limiting_enabled": True,
        "audit_logging_enabled": True,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/mcp/message")
async def handle_mcp_message(
    message: AgentMessage,
    req: Request,
    token: str = Depends(verify_authentication)
):
    """Handle MCP protocol messages securely"""
    client_ip = req.client.host
    
    # Rate limiting
    if not check_rate_limit(message.sender, "mcp_message", window_minutes=60, max_requests=100):
        audit_log("rate_limit_exceeded", message.sender, {"action": "mcp_message", "ip": client_ip})
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    # RBAC check
    if not role_allowed(message.role, message.action):
        audit_log("rbac_denied", message.sender, {"role": message.role, "action": message.action})
        raise HTTPException(status_code=403, detail="RBAC denied")
    
    # Process message securely
    if not SecureMessageHandler.process_message(message):
        raise HTTPException(status_code=400, detail="Message processing failed")
    
    audit_log("mcp_message_processed", message.sender, {
        "action": message.action,
        "message_id": message.message_id,
        "ip": client_ip
    })
    
    return {
        "ok": True,
        "message": "MCP message processed successfully",
        "message_id": message.message_id,
        "timestamp": datetime.utcnow().isoformat()
    }
