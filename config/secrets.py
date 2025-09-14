"""
Secrets Management for Korean Reading Comprehension System
Handles Docker secrets, environment variables, and secure configuration
"""

import os
import json
import base64
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, Union
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


class SecretsManager:
    """Manages application secrets with multiple sources and encryption"""
    
    def __init__(self, encryption_key: Optional[str] = None):
        self.encryption_key = encryption_key
        self._cipher = None
        self._secrets_cache: Dict[str, str] = {}
        
        if encryption_key:
            self._setup_encryption(encryption_key)
    
    def _setup_encryption(self, password: str):
        """Setup encryption for sensitive secrets"""
        try:
            password_bytes = password.encode()
            salt = hashlib.sha256(password_bytes).digest()[:16]
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password_bytes))
            self._cipher = Fernet(key)
        except Exception as e:
            logger.error(f"Failed to setup encryption: {e}")
            self._cipher = None
    
    def get_secret(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get secret value from multiple sources in priority order"""
        # Check cache first
        if key in self._secrets_cache:
            return self._secrets_cache[key]
        
        # 1. Docker secrets (highest priority)
        docker_secret = self._get_docker_secret(key)
        if docker_secret:
            self._secrets_cache[key] = docker_secret
            return docker_secret
        
        # 2. Environment variables
        env_secret = os.getenv(key)
        if env_secret:
            self._secrets_cache[key] = env_secret
            return env_secret
        
        # 3. Encrypted secrets file
        file_secret = self._get_file_secret(key)
        if file_secret:
            self._secrets_cache[key] = file_secret
            return file_secret
        
        # 4. Default value
        return default
    
    def _get_docker_secret(self, key: str) -> Optional[str]:
        """Get secret from Docker secrets"""
        secrets_dir = Path("/run/secrets")
        secret_file = secrets_dir / key.lower()
        
        if secret_file.exists() and secret_file.is_file():
            try:
                return secret_file.read_text().strip()
            except Exception as e:
                logger.warning(f"Failed to read Docker secret {key}: {e}")
        
        return None
    
    def _get_file_secret(self, key: str) -> Optional[str]:
        """Get secret from encrypted file"""
        secrets_file = Path("/app/config/secrets.json")
        
        if not secrets_file.exists():
            return None
        
        try:
            with open(secrets_file, 'r') as f:
                secrets_data = json.load(f)
            
            encrypted_value = secrets_data.get(key)
            if encrypted_value and self._cipher:
                try:
                    decrypted_bytes = self._cipher.decrypt(encrypted_value.encode())
                    return decrypted_bytes.decode()
                except Exception as e:
                    logger.warning(f"Failed to decrypt secret {key}: {e}")
            
            # Return plain text if not encrypted
            return secrets_data.get(key)
            
        except Exception as e:
            logger.warning(f"Failed to read secrets file: {e}")
        
        return None
    
    def set_secret(self, key: str, value: str, encrypt: bool = True) -> bool:
        """Set secret value in encrypted file"""
        secrets_file = Path("/app/config/secrets.json")
        
        try:
            # Load existing secrets
            secrets_data = {}
            if secrets_file.exists():
                with open(secrets_file, 'r') as f:
                    secrets_data = json.load(f)
            
            # Encrypt value if cipher is available and encryption is requested
            if encrypt and self._cipher:
                try:
                    encrypted_bytes = self._cipher.encrypt(value.encode())
                    secrets_data[key] = encrypted_bytes.decode()
                except Exception as e:
                    logger.warning(f"Failed to encrypt secret {key}: {e}")
                    secrets_data[key] = value
            else:
                secrets_data[key] = value
            
            # Write back to file
            secrets_file.parent.mkdir(parents=True, exist_ok=True)
            with open(secrets_file, 'w') as f:
                json.dump(secrets_data, f, indent=2)
            
            # Update cache
            self._secrets_cache[key] = value
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to set secret {key}: {e}")
            return False
    
    def get_database_url(self) -> str:
        """Get complete database URL with credentials"""
        db_name = self.get_secret("DB_NAME", "reading_db")
        db_user = self.get_secret("DB_USER", "postgres")
        db_password = self.get_secret("DB_PASSWORD", "")
        db_host = self.get_secret("DB_HOST", "localhost")
        db_port = self.get_secret("DB_PORT", "5432")
        
        if not db_password:
            logger.warning("Database password not set")
        
        return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    def get_redis_url(self) -> str:
        """Get complete Redis URL with credentials"""
        redis_host = self.get_secret("REDIS_HOST", "localhost")
        redis_port = self.get_secret("REDIS_PORT", "6379")
        redis_password = self.get_secret("REDIS_PASSWORD", "")
        redis_db = self.get_secret("REDIS_DB", "0")
        
        auth = f"default:{redis_password}@" if redis_password else ""
        return f"redis://{auth}{redis_host}:{redis_port}/{redis_db}"
    
    def get_rabbitmq_url(self) -> str:
        """Get complete RabbitMQ URL with credentials"""
        rabbitmq_host = self.get_secret("RABBITMQ_HOST", "localhost")
        rabbitmq_port = self.get_secret("RABBITMQ_PORT", "5672")
        rabbitmq_user = self.get_secret("RABBITMQ_USER", "guest")
        rabbitmq_password = self.get_secret("RABBITMQ_PASSWORD", "guest")
        rabbitmq_vhost = self.get_secret("RABBITMQ_VHOST", "/")
        
        return f"amqp://{rabbitmq_user}:{rabbitmq_password}@{rabbitmq_host}:{rabbitmq_port}{rabbitmq_vhost}"
    
    def get_jwt_secret(self) -> str:
        """Get JWT secret key"""
        jwt_secret = self.get_secret("JWT_SECRET_KEY")
        if not jwt_secret:
            logger.warning("JWT_SECRET_KEY not set, generating random key")
            import secrets
            jwt_secret = secrets.token_urlsafe(32)
            self.set_secret("JWT_SECRET_KEY", jwt_secret)
        
        return jwt_secret
    
    def get_session_secret(self) -> str:
        """Get session secret key"""
        session_secret = self.get_secret("SESSION_SECRET")
        if not session_secret:
            logger.warning("SESSION_SECRET not set, generating random key")
            import secrets
            session_secret = secrets.token_urlsafe(32)
            self.set_secret("SESSION_SECRET", session_secret)
        
        return session_secret
    
    def validate_secrets(self) -> Dict[str, bool]:
        """Validate that all required secrets are available"""
        required_secrets = [
            "DB_PASSWORD",
            "REDIS_PASSWORD", 
            "RABBITMQ_PASSWORD",
            "JWT_SECRET_KEY",
            "SESSION_SECRET"
        ]
        
        validation_results = {}
        
        for secret in required_secrets:
            value = self.get_secret(secret)
            validation_results[secret] = value is not None and len(value) > 0
            
            if not validation_results[secret]:
                logger.warning(f"Required secret {secret} is missing or empty")
        
        return validation_results
    
    def rotate_secrets(self) -> bool:
        """Rotate sensitive secrets (for security maintenance)"""
        try:
            import secrets
            
            # Generate new secrets
            new_jwt_secret = secrets.token_urlsafe(32)
            new_session_secret = secrets.token_urlsafe(32)
            
            # Update secrets
            self.set_secret("JWT_SECRET_KEY", new_jwt_secret)
            self.set_secret("SESSION_SECRET", new_session_secret)
            
            # Clear cache to force reload
            self._secrets_cache.clear()
            
            logger.info("Secrets rotated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to rotate secrets: {e}")
            return False
    
    def export_secrets_template(self, output_path: str) -> bool:
        """Export a template file for setting up secrets"""
        template = {
            "DB_PASSWORD": "your-database-password-here",
            "REDIS_PASSWORD": "your-redis-password-here",
            "RABBITMQ_USER": "your-rabbitmq-username",
            "RABBITMQ_PASSWORD": "your-rabbitmq-password",
            "JWT_SECRET_KEY": "your-jwt-secret-key-here",
            "SESSION_SECRET": "your-session-secret-here",
            "OPENAI_API_KEY": "your-openai-api-key-here",
            "ANTHROPIC_API_KEY": "your-anthropic-api-key-here",
            "UPSTAGE_API_KEY": "your-upstage-api-key-here",
            "SMTP_USER": "your-smtp-username",
            "SMTP_PASSWORD": "your-smtp-password",
            "SENTRY_DSN": "your-sentry-dsn-here"
        }
        
        try:
            with open(output_path, 'w') as f:
                json.dump(template, f, indent=2)
            
            logger.info(f"Secrets template exported to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export secrets template: {e}")
            return False


# Global secrets manager
secrets_manager = SecretsManager(os.getenv("SECRETS_ENCRYPTION_KEY"))


def get_secret(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get secret value - convenience function"""
    return secrets_manager.get_secret(key, default)


def get_database_url() -> str:
    """Get database URL - convenience function"""
    return secrets_manager.get_database_url()


def get_redis_url() -> str:
    """Get Redis URL - convenience function"""
    return secrets_manager.get_redis_url()


def get_rabbitmq_url() -> str:
    """Get RabbitMQ URL - convenience function"""
    return secrets_manager.get_rabbitmq_url()


def validate_all_secrets() -> bool:
    """Validate all required secrets are present"""
    results = secrets_manager.validate_secrets()
    return all(results.values())


if __name__ == "__main__":
    # Test secrets management
    print("Testing secrets management...")
    
    # Test getting secrets
    db_url = get_database_url()
    redis_url = get_redis_url()
    rabbitmq_url = get_rabbitmq_url()
    
    print(f"Database URL configured: {bool(db_url)}")
    print(f"Redis URL configured: {bool(redis_url)}")
    print(f"RabbitMQ URL configured: {bool(rabbitmq_url)}")
    
    # Validate secrets
    validation_results = secrets_manager.validate_secrets()
    print(f"Secrets validation: {validation_results}")
    
    # Export template
    secrets_manager.export_secrets_template("/tmp/secrets-template.json")
    print("Secrets template exported to /tmp/secrets-template.json")