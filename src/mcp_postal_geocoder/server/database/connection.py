"""Database connection management for postal code lookups."""

import sqlite3
import os
import threading
from pathlib import Path
from typing import Optional


class DatabaseConnection:
    """Singleton database connection manager with connection pooling."""
    
    _instance: Optional['DatabaseConnection'] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> 'DatabaseConnection':
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self) -> None:
        if hasattr(self, '_initialized'):
            return
            
        self._initialized = True
        self._db_path = self._get_database_path()
        self._connection: Optional[sqlite3.Connection] = None
        self._lock = threading.Lock()
    
    def _get_database_path(self) -> Path:
        """Get the path to the postal codes database."""
        # Try to find the database relative to this file
        current_dir = Path(__file__).parent
        
        # Look for database in data directory
        data_dir = current_dir.parent.parent.parent.parent / "data"
        db_path = data_dir / "postal_census_complete.db"
        
        if db_path.exists():
            return db_path
        
        # Fallback to environment variable
        env_path = os.getenv('POSTAL_DB_PATH')
        if env_path and Path(env_path).exists():
            return Path(env_path)
        
        raise FileNotFoundError(
            f"Postal code database not found at {db_path}. "
            f"Set POSTAL_DB_PATH environment variable to specify location."
        )
    
    def connect(self) -> sqlite3.Connection:
        """Get or create database connection."""
        if self._connection is None:
            with self._lock:
                if self._connection is None:
                    self._connection = sqlite3.connect(
                        self._db_path,
                        check_same_thread=False
                    )
                    self._connection.row_factory = sqlite3.Row
                    
                    # Enable WAL mode for better concurrent access
                    self._connection.execute("PRAGMA journal_mode = WAL")
                    
                    # Optimize for read performance
                    self._connection.execute("PRAGMA temp_store = memory")
                    self._connection.execute("PRAGMA mmap_size = 268435456")  # 256MB
                    
                    print(f"Connected to postal database: {self._db_path}")
        
        return self._connection
    
    def close(self) -> None:
        """Close database connection."""
        if self._connection:
            with self._lock:
                if self._connection:
                    self._connection.close()
                    self._connection = None
                    print("Database connection closed")
    
    def get_connection(self) -> sqlite3.Connection:
        """Get the current database connection."""
        if self._connection is None:
            return self.connect()
        return self._connection