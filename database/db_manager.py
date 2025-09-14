"""
Database Management for Korean Reading Comprehension System
Optimized for container environments with connection pooling and migrations
"""

import os
import sqlite3
import psycopg2
from psycopg2 import pool
import threading
import time
from typing import Optional, Dict, Any, List, Tuple
from contextlib import contextmanager
from pathlib import Path
import json
import logging
from datetime import datetime, timedelta

from config.config import get_config
from config.secrets import get_database_url
from utils.logging_config import get_logger

logger = get_logger(__name__)


class DatabaseError(Exception):
    """Base exception for database operations"""
    pass


class ConnectionPoolError(DatabaseError):
    """Exception for connection pool issues"""
    pass


class MigrationError(DatabaseError):
    """Exception for migration issues"""
    pass


class SQLiteManager:
    """SQLite database manager optimized for containers"""
    
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.config = get_config()
        self._local = threading.local()
        self._lock = threading.Lock()
        
        # Ensure database directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize SQLite database with optimizations"""
        with self.get_connection() as conn:
            # Enable WAL mode for better concurrency
            conn.execute("PRAGMA journal_mode=WAL")
            
            # Optimize for container environments
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA cache_size=10000")
            conn.execute("PRAGMA temp_store=MEMORY")
            conn.execute("PRAGMA mmap_size=268435456")  # 256MB
            
            # Set timeout for busy database
            conn.execute("PRAGMA busy_timeout=30000")  # 30 seconds
            
            conn.commit()
        
        logger.info(f"SQLite database initialized: {self.db_path}")
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection for current thread"""
        if not hasattr(self._local, 'connection'):
            self._local.connection = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False,
                timeout=30.0
            )
            
            # Set row factory for dict-like access
            self._local.connection.row_factory = sqlite3.Row
            
            # Enable foreign keys
            self._local.connection.execute("PRAGMA foreign_keys=ON")
        
        return self._local.connection
    
    @contextmanager
    def transaction(self):
        """Context manager for database transactions"""
        conn = self.get_connection()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Transaction rolled back: {e}")
            raise
    
    def backup_database(self, backup_path: str) -> bool:
        """Create database backup"""
        try:
            backup_path = Path(backup_path)
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            
            with self.get_connection() as source:
                backup = sqlite3.connect(str(backup_path))
                source.backup(backup)
                backup.close()
            
            logger.info(f"Database backup created: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            return False
    
    def vacuum_database(self) -> bool:
        """Vacuum database to reclaim space"""
        try:
            with self.get_connection() as conn:
                conn.execute("VACUUM")
            
            logger.info("Database vacuum completed")
            return True
            
        except Exception as e:
            logger.error(f"Database vacuum failed: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            with self.get_connection() as conn:
                # Get page count and size
                page_count = conn.execute("PRAGMA page_count").fetchone()[0]
                page_size = conn.execute("PRAGMA page_size").fetchone()[0]
                
                # Get table info
                tables = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
                
                table_info = {}
                for table in tables:
                    table_name = table[0]
                    count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
                    table_info[table_name] = count
                
                return {
                    "file_size_bytes": self.db_path.stat().st_size,
                    "page_count": page_count,
                    "page_size": page_size,
                    "database_size_bytes": page_count * page_size,
                    "tables": table_info
                }
                
        except Exception as e:
            logger.error(f"Failed to get database statistics: {e}")
            return {}


class PostgreSQLManager:
    """PostgreSQL database manager with connection pooling"""
    
    def __init__(self):
        self.config = get_config()
        self.database_url = get_database_url()
        self._pool: Optional[psycopg2.pool.ThreadedConnectionPool] = None
        self._pool_lock = threading.Lock()
        
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Initialize connection pool"""
        try:
            self._pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=self.config.database.pool_size,
                dsn=self.database_url,
                cursor_factory=psycopg2.extras.RealDictCursor
            )
            
            logger.info(f"PostgreSQL connection pool initialized (max connections: {self.config.database.pool_size})")
            
        except Exception as e:
            logger.error(f"Failed to initialize connection pool: {e}")
            raise ConnectionPoolError(f"Connection pool initialization failed: {e}")
    
    @contextmanager
    def get_connection(self):
        """Get connection from pool"""
        if not self._pool:
            raise ConnectionPoolError("Connection pool not initialized")
        
        connection = None
        try:
            connection = self._pool.getconn()
            yield connection
            
        except Exception as e:
            if connection:
                connection.rollback()
            logger.error(f"Database operation failed: {e}")
            raise
            
        finally:
            if connection:
                self._pool.putconn(connection)
    
    @contextmanager
    def transaction(self):
        """Context manager for database transactions"""
        with self.get_connection() as conn:
            try:
                yield conn
                conn.commit()
            except Exception as e:
                conn.rollback()
                logger.error(f"Transaction rolled back: {e}")
                raise
    
    def execute_query(self, query: str, params: Optional[Tuple] = None) -> List[Dict[str, Any]]:
        """Execute query and return results"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()
    
    def execute_command(self, command: str, params: Optional[Tuple] = None) -> int:
        """Execute command and return affected rows"""
        with self.transaction() as conn:
            with conn.cursor() as cursor:
                cursor.execute(command, params)
                return cursor.rowcount
    
    def get_pool_status(self) -> Dict[str, Any]:
        """Get connection pool status"""
        if not self._pool:
            return {"status": "not_initialized"}
        
        return {
            "status": "active",
            "total_connections": self._pool.maxconn,
            "available_connections": len(self._pool._pool),
            "used_connections": self._pool.maxconn - len(self._pool._pool)
        }
    
    def close_pool(self):
        """Close connection pool"""
        if self._pool:
            self._pool.closeall()
            self._pool = None
            logger.info("PostgreSQL connection pool closed")


class MigrationManager:
    """Database migration manager"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.migrations_dir = Path("/app/database/migrations")
        self.migrations_dir.mkdir(parents=True, exist_ok=True)
    
    def create_migration_table(self):
        """Create migration tracking table"""
        if isinstance(self.db_manager, SQLiteManager):
            with self.db_manager.transaction() as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS migrations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        filename TEXT UNIQUE NOT NULL,
                        applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
        else:  # PostgreSQL
            with self.db_manager.transaction() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS migrations (
                            id SERIAL PRIMARY KEY,
                            filename VARCHAR(255) UNIQUE NOT NULL,
                            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
    
    def get_applied_migrations(self) -> List[str]:
        """Get list of applied migrations"""
        self.create_migration_table()
        
        if isinstance(self.db_manager, SQLiteManager):
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("SELECT filename FROM migrations ORDER BY id")
                return [row[0] for row in cursor.fetchall()]
        else:  # PostgreSQL
            result = self.db_manager.execute_query("SELECT filename FROM migrations ORDER BY id")
            return [row['filename'] for row in result]
    
    def get_pending_migrations(self) -> List[str]:
        """Get list of pending migrations"""
        applied = set(self.get_applied_migrations())
        all_migrations = sorted([
            f.name for f in self.migrations_dir.glob("*.sql")
            if f.is_file()
        ])
        
        return [migration for migration in all_migrations if migration not in applied]
    
    def apply_migration(self, filename: str) -> bool:
        """Apply a single migration"""
        migration_file = self.migrations_dir / filename
        
        if not migration_file.exists():
            logger.error(f"Migration file not found: {filename}")
            return False
        
        try:
            # Read migration SQL
            migration_sql = migration_file.read_text(encoding='utf-8')
            
            # Apply migration
            if isinstance(self.db_manager, SQLiteManager):
                with self.db_manager.transaction() as conn:
                    conn.executescript(migration_sql)
                    conn.execute(
                        "INSERT INTO migrations (filename) VALUES (?)",
                        (filename,)
                    )
            else:  # PostgreSQL
                with self.db_manager.transaction() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute(migration_sql)
                        cursor.execute(
                            "INSERT INTO migrations (filename) VALUES (%s)",
                            (filename,)
                        )
            
            logger.info(f"Migration applied: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to apply migration {filename}: {e}")
            raise MigrationError(f"Migration failed: {e}")
    
    def migrate(self) -> int:
        """Apply all pending migrations"""
        pending = self.get_pending_migrations()
        
        if not pending:
            logger.info("No pending migrations")
            return 0
        
        applied_count = 0
        for migration in pending:
            if self.apply_migration(migration):
                applied_count += 1
            else:
                break
        
        logger.info(f"Applied {applied_count} migrations")
        return applied_count
    
    def create_migration(self, name: str, sql_content: str) -> str:
        """Create a new migration file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{name}.sql"
        migration_file = self.migrations_dir / filename
        
        migration_file.write_text(sql_content, encoding='utf-8')
        logger.info(f"Migration created: {filename}")
        
        return filename


class DatabaseBackupManager:
    """Database backup and recovery manager"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.config = get_config()
        self.backup_dir = Path(self.config.backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def create_backup(self, backup_name: Optional[str] = None) -> str:
        """Create database backup"""
        if not backup_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{timestamp}"
        
        if isinstance(self.db_manager, SQLiteManager):
            backup_path = self.backup_dir / f"{backup_name}.db"
            success = self.db_manager.backup_database(str(backup_path))
            
            if success:
                # Create backup metadata
                metadata = {
                    "backup_name": backup_name,
                    "created_at": datetime.now().isoformat(),
                    "database_type": "sqlite",
                    "size_bytes": backup_path.stat().st_size
                }
                
                metadata_path = self.backup_dir / f"{backup_name}.json"
                metadata_path.write_text(json.dumps(metadata, indent=2))
                
                return str(backup_path)
        
        else:  # PostgreSQL
            # Use pg_dump for PostgreSQL backups
            backup_path = self.backup_dir / f"{backup_name}.sql"
            
            try:
                import subprocess
                
                # Extract connection parameters
                from urllib.parse import urlparse
                parsed = urlparse(self.db_manager.database_url)
                
                cmd = [
                    "pg_dump",
                    "-h", parsed.hostname,
                    "-p", str(parsed.port),
                    "-U", parsed.username,
                    "-d", parsed.path[1:],  # Remove leading /
                    "--no-password",
                    "-f", str(backup_path)
                ]
                
                env = os.environ.copy()
                env["PGPASSWORD"] = parsed.password
                
                result = subprocess.run(cmd, env=env, capture_output=True, text=True)
                
                if result.returncode == 0:
                    # Create backup metadata
                    metadata = {
                        "backup_name": backup_name,
                        "created_at": datetime.now().isoformat(),
                        "database_type": "postgresql",
                        "size_bytes": backup_path.stat().st_size
                    }
                    
                    metadata_path = self.backup_dir / f"{backup_name}.json"
                    metadata_path.write_text(json.dumps(metadata, indent=2))
                    
                    logger.info(f"PostgreSQL backup created: {backup_path}")
                    return str(backup_path)
                
                else:
                    logger.error(f"pg_dump failed: {result.stderr}")
                    raise DatabaseError(f"Backup failed: {result.stderr}")
                    
            except Exception as e:
                logger.error(f"Failed to create PostgreSQL backup: {e}")
                raise DatabaseError(f"Backup failed: {e}")
        
        raise DatabaseError("Backup creation failed")
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """List available backups"""
        backups = []
        
        for metadata_file in self.backup_dir.glob("*.json"):
            try:
                metadata = json.loads(metadata_file.read_text())
                backups.append(metadata)
            except Exception as e:
                logger.warning(f"Failed to read backup metadata {metadata_file}: {e}")
        
        return sorted(backups, key=lambda x: x['created_at'], reverse=True)
    
    def cleanup_old_backups(self, retention_days: int = 30) -> int:
        """Clean up old backups"""
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        deleted_count = 0
        
        for backup in self.list_backups():
            backup_date = datetime.fromisoformat(backup['created_at'])
            
            if backup_date < cutoff_date:
                backup_name = backup['backup_name']
                
                # Delete backup files
                for ext in ['.db', '.sql', '.json']:
                    backup_file = self.backup_dir / f"{backup_name}{ext}"
                    if backup_file.exists():
                        backup_file.unlink()
                
                deleted_count += 1
                logger.info(f"Deleted old backup: {backup_name}")
        
        return deleted_count


# Factory function for database manager
def create_database_manager():
    """Create appropriate database manager based on configuration"""
    config = get_config()
    
    if config.environment == "development" or "sqlite" in get_database_url():
        # Use SQLite for development
        db_path = "/app/data/reading_system.db"
        return SQLiteManager(db_path)
    else:
        # Use PostgreSQL for production
        return PostgreSQLManager()


# Global database manager
_db_manager = None

def get_database_manager():
    """Get global database manager"""
    global _db_manager
    if _db_manager is None:
        _db_manager = create_database_manager()
    return _db_manager


def initialize_database():
    """Initialize database with migrations"""
    db_manager = get_database_manager()
    migration_manager = MigrationManager(db_manager)
    
    # Apply migrations
    migration_manager.migrate()
    
    logger.info("Database initialization completed")


def create_backup():
    """Create database backup"""
    db_manager = get_database_manager()
    backup_manager = DatabaseBackupManager(db_manager)
    
    return backup_manager.create_backup()


if __name__ == "__main__":
    # Test database management
    initialize_database()
    
    db_manager = get_database_manager()
    
    if isinstance(db_manager, SQLiteManager):
        stats = db_manager.get_statistics()
        print(f"Database statistics: {stats}")
    else:
        pool_status = db_manager.get_pool_status()
        print(f"Connection pool status: {pool_status}")
    
    # Test backup
    backup_path = create_backup()
    print(f"Backup created: {backup_path}")