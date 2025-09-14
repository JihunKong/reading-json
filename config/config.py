"""
Production Configuration Management for Korean Reading Comprehension System
Handles environment-specific configurations and secrets management
"""

import os
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class DatabaseConfig:
    """Database configuration settings"""
    name: str = "reading_db"
    user: str = "postgres"
    password: str = ""
    host: str = "localhost"
    port: int = 5432
    pool_size: int = 20
    max_overflow: int = 30
    pool_timeout: int = 30
    pool_recycle: int = 3600
    
    @property
    def url(self) -> str:
        """Generate database URL"""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


@dataclass
class RedisConfig:
    """Redis configuration settings"""
    host: str = "localhost"
    port: int = 6379
    password: str = ""
    db: int = 0
    pool_max_connections: int = 50
    socket_keepalive: bool = True
    health_check_interval: int = 30
    
    @property
    def url(self) -> str:
        """Generate Redis URL"""
        auth = f"default:{self.password}@" if self.password else ""
        return f"redis://{auth}{self.host}:{self.port}/{self.db}"


@dataclass
class RabbitMQConfig:
    """RabbitMQ configuration settings"""
    host: str = "localhost"
    port: int = 5672
    user: str = "guest"
    password: str = "guest"
    vhost: str = "/"
    heartbeat: int = 600
    connection_attempts: int = 3
    
    @property
    def url(self) -> str:
        """Generate RabbitMQ URL"""
        return f"amqp://{self.user}:{self.password}@{self.host}:{self.port}{self.vhost}"


@dataclass
class LoggingConfig:
    """Logging configuration settings"""
    level: str = "INFO"
    format: str = "json"
    file_path: str = "/app/logs/app.log"
    max_size: str = "100MB"
    backup_count: int = 5
    syslog_enabled: bool = False
    syslog_host: str = "localhost"
    syslog_port: int = 514


@dataclass
class SecurityConfig:
    """Security configuration settings"""
    secret_key: str = ""
    jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 10080
    secure_cookies: bool = True
    https_only: bool = True
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 60
    csrf_protection: bool = True


@dataclass
class PerformanceConfig:
    """Performance configuration settings"""
    max_workers: int = 4
    worker_timeout: int = 120
    worker_connections: int = 1000
    connection_pool_size: int = 50
    cache_ttl_seconds: int = 7200
    async_pool_size: int = 10


@dataclass
class MonitoringConfig:
    """Monitoring configuration settings"""
    prometheus_enabled: bool = False
    prometheus_port: int = 9090
    metrics_export_interval: int = 30
    health_check_enabled: bool = True
    health_check_timeout: int = 5
    sentry_dsn: str = ""


@dataclass
class AppConfig:
    """Main application configuration"""
    environment: str = "development"
    debug: bool = False
    testing: bool = False
    
    # Configuration objects
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    redis: RedisConfig = field(default_factory=RedisConfig)
    rabbitmq: RabbitMQConfig = field(default_factory=RabbitMQConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    
    # File paths
    content_output_dir: str = "/app/data/content"
    report_output_dir: str = "/app/data/reports"
    backup_dir: str = "/app/data/backups"
    static_dir: str = "/app/static"
    
    # Korean NLP settings
    konlpy_backend: str = "mecab"
    korean_stopwords_path: str = "/app/data/korean_stopwords.txt"
    nlp_cache_size: int = 1000
    nlp_workers: int = 4
    
    # Content generation
    default_paragraph_count: int = 5
    default_article_count: int = 3
    max_generation_batch: int = 100
    generation_timeout_seconds: int = 600
    
    # Grading settings
    default_similarity_threshold: float = 0.68
    require_pos_check: bool = True
    required_pos_tags: str = "NOUN,VERB"
    
    def __post_init__(self):
        """Post-initialization validation"""
        if not self.security.secret_key:
            raise ValueError("SECRET_KEY must be set")
        
        if self.environment == "production" and self.debug:
            logger.warning("Debug mode enabled in production environment")
        
        # Ensure directories exist
        for dir_path in [self.content_output_dir, self.report_output_dir, self.backup_dir]:
            Path(dir_path).mkdir(parents=True, exist_ok=True)


class ConfigManager:
    """Configuration manager for loading and validating settings"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file
        self._config: Optional[AppConfig] = None
    
    def load_config(self) -> AppConfig:
        """Load configuration from environment variables and files"""
        if self._config is not None:
            return self._config
        
        # Determine environment
        environment = os.getenv("ENVIRONMENT", "development")
        
        # Load base configuration
        config_data = self._load_environment_config(environment)
        
        # Override with environment variables
        config_data.update(self._load_env_vars())
        
        # Load secrets
        config_data.update(self._load_secrets())
        
        # Create configuration object
        self._config = self._create_config_object(config_data)
        
        return self._config
    
    def _load_environment_config(self, environment: str) -> Dict[str, Any]:
        """Load environment-specific configuration file"""
        config_file = f"/app/config/{environment}.env"
        config_data = {}
        
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        config_data[key.strip()] = value.strip()
        
        return config_data
    
    def _load_env_vars(self) -> Dict[str, Any]:
        """Load configuration from environment variables"""
        config_data = {}
        
        # Define environment variable mappings
        env_mappings = {
            # Database
            "DB_NAME": "database.name",
            "DB_USER": "database.user",
            "DB_PASSWORD": "database.password",
            "DB_HOST": "database.host",
            "DB_PORT": "database.port",
            
            # Redis
            "REDIS_HOST": "redis.host",
            "REDIS_PORT": "redis.port",
            "REDIS_PASSWORD": "redis.password",
            "REDIS_DB": "redis.db",
            
            # RabbitMQ
            "RABBITMQ_HOST": "rabbitmq.host",
            "RABBITMQ_PORT": "rabbitmq.port",
            "RABBITMQ_USER": "rabbitmq.user",
            "RABBITMQ_PASSWORD": "rabbitmq.password",
            
            # Security
            "SECRET_KEY": "security.secret_key",
            "JWT_SECRET_KEY": "security.jwt_secret",
            "JWT_ALGORITHM": "security.jwt_algorithm",
            
            # Application
            "DEBUG": "debug",
            "ENVIRONMENT": "environment",
            
            # Logging
            "LOG_LEVEL": "logging.level",
            "LOG_FORMAT": "logging.format",
            "LOG_FILE_PATH": "logging.file_path",
            
            # Performance
            "MAX_WORKERS": "performance.max_workers",
            "WORKER_TIMEOUT": "performance.worker_timeout",
            
            # Monitoring
            "PROMETHEUS_ENABLED": "monitoring.prometheus_enabled",
            "SENTRY_DSN": "monitoring.sentry_dsn",
        }
        
        for env_var, config_path in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                config_data[config_path] = self._parse_value(value)
        
        return config_data
    
    def _load_secrets(self) -> Dict[str, Any]:
        """Load secrets from Docker secrets or secure files"""
        secrets_data = {}
        secrets_dir = Path("/run/secrets")
        
        if secrets_dir.exists():
            for secret_file in secrets_dir.iterdir():
                if secret_file.is_file():
                    secret_name = secret_file.name.upper()
                    try:
                        secret_value = secret_file.read_text().strip()
                        secrets_data[secret_name] = secret_value
                    except Exception as e:
                        logger.warning(f"Failed to read secret {secret_name}: {e}")
        
        return secrets_data
    
    def _parse_value(self, value: str) -> Any:
        """Parse configuration value to appropriate type"""
        # Boolean values
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        # Integer values
        try:
            return int(value)
        except ValueError:
            pass
        
        # Float values
        try:
            return float(value)
        except ValueError:
            pass
        
        # JSON values
        if value.startswith('{') or value.startswith('['):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                pass
        
        # String values
        return value
    
    def _create_config_object(self, config_data: Dict[str, Any]) -> AppConfig:
        """Create AppConfig object from configuration data"""
        # Parse nested configuration
        nested_config = {}
        flat_config = {}
        
        for key, value in config_data.items():
            if '.' in key:
                parts = key.split('.')
                current = nested_config
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                current[parts[-1]] = value
            else:
                flat_config[key] = value
        
        # Create configuration objects
        db_config = DatabaseConfig(**nested_config.get('database', {}))
        redis_config = RedisConfig(**nested_config.get('redis', {}))
        rabbitmq_config = RabbitMQConfig(**nested_config.get('rabbitmq', {}))
        logging_config = LoggingConfig(**nested_config.get('logging', {}))
        security_config = SecurityConfig(**nested_config.get('security', {}))
        performance_config = PerformanceConfig(**nested_config.get('performance', {}))
        monitoring_config = MonitoringConfig(**nested_config.get('monitoring', {}))
        
        # Create main config
        app_config = AppConfig(
            database=db_config,
            redis=redis_config,
            rabbitmq=rabbitmq_config,
            logging=logging_config,
            security=security_config,
            performance=performance_config,
            monitoring=monitoring_config,
            **flat_config
        )
        
        return app_config
    
    def validate_config(self, config: AppConfig) -> bool:
        """Validate configuration settings"""
        try:
            # Check required settings
            if not config.security.secret_key:
                logger.error("SECRET_KEY is required")
                return False
            
            if config.environment == "production":
                if config.debug:
                    logger.warning("Debug mode should be disabled in production")
                
                if not config.security.https_only:
                    logger.warning("HTTPS should be enabled in production")
                
                if not config.security.secure_cookies:
                    logger.warning("Secure cookies should be enabled in production")
            
            # Check database connectivity (basic validation)
            if not config.database.host or not config.database.name:
                logger.error("Database configuration is incomplete")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            return False


# Global configuration manager
config_manager = ConfigManager()

def get_config() -> AppConfig:
    """Get application configuration"""
    return config_manager.load_config()


def validate_environment() -> bool:
    """Validate current environment configuration"""
    config = get_config()
    return config_manager.validate_config(config)


if __name__ == "__main__":
    # Test configuration loading
    config = get_config()
    print(f"Environment: {config.environment}")
    print(f"Database URL: {config.database.url}")
    print(f"Redis URL: {config.redis.url}")
    print(f"Valid configuration: {validate_environment()}")