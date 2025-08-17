"""Database connection management for postal code lookups."""

import sqlite3
import os
import threading
import requests
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
    
    def _download_database(self, db_path: Path) -> None:
        """Download the postal code database from Hugging Face."""
        url = "https://huggingface.co/datasets/bott-wa/us-postal-geocoding-db/resolve/main/postal_census_complete.db"
        
        print(f"Downloading postal code database from Hugging Face...")
        print(f"URL: {url}")
        print(f"Destination: {db_path}")
        
        # Ensure the directory exists
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Download with progress indication
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(db_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        progress = (downloaded / total_size) * 100
                        print(f"\rDownload progress: {progress:.1f}%", end='', flush=True)
        
        print(f"\nDownload completed: {db_path}")

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
        
        # If database doesn't exist, try to download it
        print(f"Database not found at {db_path}")
        try:
            self._download_database(db_path)
            return db_path
        except Exception as e:
            raise FileNotFoundError(
                f"Failed to download postal code database from Hugging Face: {e}. "
                f"You can manually download it from: "
                f"https://huggingface.co/datasets/bott-wa/us-postal-geocoding-db/resolve/main/postal_census_complete.db "
                f"and place it at {db_path}, or set POSTAL_DB_PATH environment variable."
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