#config.py
#!/usr/bin/env python3
"""
Configuration Manager for Agent 4: Competitor Comparison & Security

This module provides centralized configuration management using environment variables
and .env files, with sensible defaults and validation.
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Union
from dataclasses import dataclass, field
import logging
from dotenv import load_dotenv

# Load .env file if it exists
env_path = Path(__file__).resolve().parents[2] / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ Loaded environment from: {env_path}")
else:
    print(f"⚠️  No .env file found at: {env_path}")
    print("💡 Using default environment variables")

@dataclass
class OllamaConfig:
    """Ollama LLM configuration"""
    base_url: str = field(default_factory=lambda: os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
    model: str = field(default_factory=lambda: os.getenv("OLLAMA_MODEL", "llama3.2:latest"))
    timeout: int = field(default_factory=lambda: int(os.getenv("OLLAMA_TIMEOUT", "120")))
    temperature: float = field(default_factory=lambda: float(os.getenv("OLLAMA_TEMPERATURE", "0.1")))
    top_p: float = field(default_factory=lambda: float(os.getenv("OLLAMA_TOP_P", "0.9")))
    max_tokens: int = field(default_factory=lambda: int(os.getenv("OLLAMA_MAX_TOKENS", "300")))

@dataclass
class SecurityConfig:
    """Security configuration"""
    shared_secret: str = field(default_factory=lambda: os.getenv("AGENTS_SHARED_SECRET", "agent4-default-secret"))
    log_level: str = field(default_factory=lambda: os.getenv("SECURITY_LOG_LEVEL", "INFO"))
    enable_hmac: bool = field(default_factory=lambda: os.getenv("ENABLE_HMAC_VERIFICATION", "true").lower() == "true")
    enable_rbac: bool = field(default_factory=lambda: os.getenv("ENABLE_RBAC", "true").lower() == "true")
    enable_sanitization: bool = field(default_factory=lambda: os.getenv("ENABLE_INPUT_SANITIZATION", "true").lower() == "true")
    enable_audit: bool = field(default_factory=lambda: os.getenv("ENABLE_AUDIT_LOGGING", "true").lower() == "true")
    enable_rate_limiting: bool = field(default_factory=lambda: os.getenv("ENABLE_RATE_LIMITING", "true").lower() == "true")
    
    # Rate limiting
    rate_limit_requests: int = field(default_factory=lambda: int(os.getenv("RATE_LIMIT_REQUESTS", "100")))
    rate_limit_window: int = field(default_factory=lambda: int(os.getenv("RATE_LIMIT_WINDOW", "3600")))
    
    # HMAC
    hmac_algorithm: str = field(default_factory=lambda: os.getenv("HMAC_ALGORITHM", "SHA256"))
    hmac_expiry: int = field(default_factory=lambda: int(os.getenv("HMAC_EXPIRY_SECONDS", "300")))

@dataclass
class DashboardConfig:
    """Dashboard configuration"""
    port: int = field(default_factory=lambda: int(os.getenv("DASHBOARD_PORT", "8501")))
    host: str = field(default_factory=lambda: os.getenv("DASHBOARD_HOST", "localhost"))
    theme: str = field(default_factory=lambda: os.getenv("DASHBOARD_THEME", "light"))
    layout: str = field(default_factory=lambda: os.getenv("DASHBOARD_LAYOUT", "wide"))
    sidebar_state: str = field(default_factory=lambda: os.getenv("DASHBOARD_SIDEBAR_STATE", "expanded"))
    
    # Security
    enable_auth: bool = field(default_factory=lambda: os.getenv("DASHBOARD_ENABLE_AUTH", "false").lower() == "true")
    enable_cors: bool = field(default_factory=lambda: os.getenv("DASHBOARD_ENABLE_CORS", "true").lower() == "true")
    allowed_origins: str = field(default_factory=lambda: os.getenv("DASHBOARD_ALLOWED_ORIGINS", "*"))

@dataclass
class AgentConfig:
    """Agent configuration"""
    name: str = field(default_factory=lambda: os.getenv("AGENT4_NAME", "Competitor_Comparison_Agent"))
    version: str = field(default_factory=lambda: os.getenv("AGENT4_VERSION", "1.0.0"))
    environment: str = field(default_factory=lambda: os.getenv("AGENT4_ENVIRONMENT", "development"))
    role: str = field(default_factory=lambda: os.getenv("AGENT4_ROLE", "agent4"))
    permissions: str = field(default_factory=lambda: os.getenv("AGENT4_PERMISSIONS", "compare,analyze,export,security_audit"))
    
    # Permission matrix
    compare_permission: bool = field(default_factory=lambda: os.getenv("AGENT4_COMPARE_PERMISSION", "true").lower() == "true")
    analyze_permission: bool = field(default_factory=lambda: os.getenv("AGENT4_ANALYZE_PERMISSION", "true").lower() == "true")
    export_permission: bool = field(default_factory=lambda: os.getenv("AGENT4_EXPORT_PERMISSION", "true").lower() == "true")
    security_audit_permission: bool = field(default_factory=lambda: os.getenv("AGENT4_SECURITY_AUDIT_PERMISSION", "true").lower() == "true")

@dataclass
class DataConfig:
    """Data configuration"""
    inbound_path: str = field(default_factory=lambda: os.getenv("DATA_INBOUND_PATH", "data/inbound"))
    outbound_path: str = field(default_factory=lambda: os.getenv("DATA_OUTBOUND_PATH", "data/outbound"))
    retention_days: int = field(default_factory=lambda: int(os.getenv("DATA_RETENTION_DAYS", "30")))
    backup_enabled: bool = field(default_factory=lambda: os.getenv("DATA_BACKUP_ENABLED", "true").lower() == "true")

@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    format: str = field(default_factory=lambda: os.getenv("LOG_FORMAT", "json"))
    file: str = field(default_factory=lambda: os.getenv("LOG_FILE", "logs/agent4.log"))
    max_size: str = field(default_factory=lambda: os.getenv("LOG_MAX_SIZE", "10MB"))
    backup_count: int = field(default_factory=lambda: int(os.getenv("LOG_BACKUP_COUNT", "5")))

@dataclass
class APIConfig:
    """API configuration"""
    host: str = field(default_factory=lambda: os.getenv("API_HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: int(os.getenv("API_PORT", "8000")))
    workers: int = field(default_factory=lambda: int(os.getenv("API_WORKERS", "4")))
    timeout: int = field(default_factory=lambda: int(os.getenv("API_TIMEOUT", "30")))
    max_requests: int = field(default_factory=lambda: int(os.getenv("API_MAX_REQUESTS", "1000")))
    
    # Security
    enable_cors: bool = field(default_factory=lambda: os.getenv("API_ENABLE_CORS", "true").lower() == "true")
    enable_rate_limiting: bool = field(default_factory=lambda: os.getenv("API_ENABLE_RATE_LIMITING", "true").lower() == "true")
    enable_auth: bool = field(default_factory=lambda: os.getenv("API_ENABLE_AUTHENTICATION", "true").lower() == "true")
    enable_logging: bool = field(default_factory=lambda: os.getenv("API_ENABLE_LOGGING", "true").lower() == "true")

@dataclass
class MCPConfig:
    """MCP Protocol configuration"""
    enabled: bool = field(default_factory=lambda: os.getenv("MCP_ENABLED", "true").lower() == "true")
    version: str = field(default_factory=lambda: os.getenv("MCP_VERSION", "1.0"))
    timeout: int = field(default_factory=lambda: int(os.getenv("MCP_TIMEOUT", "30")))
    max_message_size: int = field(default_factory=lambda: int(os.getenv("MCP_MAX_MESSAGE_SIZE", "1048576")))

@dataclass
class PerformanceConfig:
    """Performance configuration"""
    enable_caching: bool = field(default_factory=lambda: os.getenv("ENABLE_CACHING", "true").lower() == "true")
    cache_ttl: int = field(default_factory=lambda: int(os.getenv("CACHE_TTL", "300")))
    enable_compression: bool = field(default_factory=lambda: os.getenv("ENABLE_COMPRESSION", "true").lower() == "true")
    enable_async: bool = field(default_factory=lambda: os.getenv("ENABLE_ASYNC_PROCESSING", "true").lower() == "true")

@dataclass
class MonitoringConfig:
    """Monitoring configuration"""
    enable_health_checks: bool = field(default_factory=lambda: os.getenv("ENABLE_HEALTH_CHECKS", "true").lower() == "true")
    health_check_interval: int = field(default_factory=lambda: int(os.getenv("HEALTH_CHECK_INTERVAL", "60")))
    enable_metrics: bool = field(default_factory=lambda: os.getenv("ENABLE_METRICS", "true").lower() == "true")
    metrics_port: int = field(default_factory=lambda: int(os.getenv("METRICS_PORT", "9090")))

@dataclass
class DevelopmentConfig:
    """Development configuration"""
    debug_mode: bool = field(default_factory=lambda: os.getenv("DEBUG_MODE", "false").lower() == "true")
    enable_hot_reload: bool = field(default_factory=lambda: os.getenv("ENABLE_HOT_RELOAD", "false").lower() == "true")
    enable_profiling: bool = field(default_factory=lambda: os.getenv("ENABLE_PROFILING", "false").lower() == "true")
    enable_testing: bool = field(default_factory=lambda: os.getenv("ENABLE_TESTING", "true").lower() == "true")

@dataclass
class ComplianceConfig:
    """Compliance and governance configuration"""
    enable_encryption: bool = field(default_factory=lambda: os.getenv("ENABLE_DATA_ENCRYPTION", "true").lower() == "true")
    enable_pii_detection: bool = field(default_factory=lambda: os.getenv("ENABLE_PII_DETECTION", "true").lower() == "true")
    enable_compliance_logging: bool = field(default_factory=lambda: os.getenv("ENABLE_COMPLIANCE_LOGGING", "true").lower() == "true")
    enable_audit_trail: bool = field(default_factory=lambda: os.getenv("ENABLE_AUDIT_TRAIL", "true").lower() == "true")

class ConfigManager:
    """Centralized configuration manager for Agent 4"""
    
    def __init__(self):
        self.ollama = OllamaConfig()
        self.security = SecurityConfig()
        self.dashboard = DashboardConfig()
        self.agent = AgentConfig()
        self.data = DataConfig()
        self.logging = LoggingConfig()
        self.api = APIConfig()
        self.mcp = MCPConfig()
        self.performance = PerformanceConfig()
        self.monitoring = MonitoringConfig()
        self.development = DevelopmentConfig()
        self.compliance = ComplianceConfig()
        
        # Setup logging
        self._setup_logging()
        
        # Validate configuration
        self._validate_config()
    
    def _setup_logging(self):
        """Setup logging configuration"""
        log_level = getattr(logging, self.logging.level.upper(), logging.INFO)
        
        # Create logs directory if it doesn't exist
        log_file_path = Path(self.logging.file)
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file_path),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Configuration loaded - Environment: {self.agent.environment}")
    
    def _validate_config(self):
        """Validate configuration values"""
        try:
            # Validate Ollama configuration
            if not self.ollama.base_url.startswith(('http://', 'https://')):
                raise ValueError(f"Invalid Ollama base URL: {self.ollama.base_url}")
            
            if self.ollama.timeout <= 0:
                raise ValueError(f"Invalid Ollama timeout: {self.ollama.timeout}")
            
            if not (0 <= self.ollama.temperature <= 2):
                raise ValueError(f"Invalid Ollama temperature: {self.ollama.temperature}")
            
            # Validate security configuration
            if len(self.security.shared_secret) < 16:
                self.logger.warning("Security shared secret is too short - consider using a longer key")
            
            # Validate dashboard configuration
            if not (1 <= self.dashboard.port <= 65535):
                raise ValueError(f"Invalid dashboard port: {self.dashboard.port}")
            
            # Validate API configuration
            if not (1 <= self.api.port <= 65535):
                raise ValueError(f"Invalid API port: {self.api.port}")
            
            self.logger.info("Configuration validation passed")
            
        except Exception as e:
            self.logger.error(f"Configuration validation failed: {e}")
            raise
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key"""
        try:
            # Support nested keys like "ollama.base_url"
            keys = key.split('.')
            value = self
            
            for k in keys:
                value = getattr(value, k)
            
            return value
        except AttributeError:
            return default
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            'ollama': self.ollama.__dict__,
            'security': self.security.__dict__,
            'dashboard': self.dashboard.__dict__,
            'agent': self.agent.__dict__,
            'data': self.data.__dict__,
            'logging': self.logging.__dict__,
            'api': self.api.__dict__,
            'mcp': self.mcp.__dict__,
            'performance': self.performance.__dict__,
            'monitoring': self.monitoring.__dict__,
            'development': self.development.__dict__,
            'compliance': self.compliance.__dict__
        }
    
    def print_config(self):
        """Print current configuration"""
        print("\n🔒 Agent 4 Configuration")
        print("=" * 50)
        
        config_dict = self.to_dict()
        for section, settings in config_dict.items():
            print(f"\n📋 {section.upper()}:")
            for key, value in settings.items():
                # Mask sensitive values
                if 'secret' in key.lower() or 'key' in key.lower():
                    value = '*' * 8
                print(f"   {key}: {value}")
        
        print("\n" + "=" * 50)

# Global configuration instance
config = ConfigManager()

# Convenience functions
def get_config() -> ConfigManager:
    """Get global configuration instance"""
    return config

def get_ollama_config() -> OllamaConfig:
    """Get Ollama configuration"""
    return config.ollama

def get_security_config() -> SecurityConfig:
    """Get security configuration"""
    return config.security

def get_dashboard_config() -> DashboardConfig:
    """Get dashboard configuration"""
    return config.dashboard

def get_agent_config() -> AgentConfig:
    """Get agent configuration"""
    return config.agent

if __name__ == "__main__":
    # Print configuration when run directly
    config.print_config()





