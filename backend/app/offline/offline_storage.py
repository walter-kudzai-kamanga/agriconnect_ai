import json
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import os

class OfflineStorage:
    """Local storage for offline requests"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Use project root directory
            base_dir = Path(__file__).parent.parent.parent
            db_path = str(base_dir / "offline_requests.db")
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize offline database"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS offline_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_type TEXT NOT NULL,
                data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                synced BOOLEAN DEFAULT 0,
                sync_attempts INTEGER DEFAULT 0,
                last_sync_attempt TIMESTAMP,
                synced_at TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()
    
    def store_request(self, request_type: str, data: Dict) -> int:
        """Store request for later sync"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO offline_requests (request_type, data)
            VALUES (?, ?)
        """, (request_type, json.dumps(data)))
        request_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return request_id
    
    def get_pending_requests(self, limit: int = 50) -> List[Dict]:
        """Get requests pending sync"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM offline_requests
            WHERE synced = 0
            ORDER BY created_at ASC
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def mark_synced(self, request_id: int):
        """Mark request as synced"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            UPDATE offline_requests
            SET synced = 1, synced_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (request_id,))
        conn.commit()
        conn.close()
    
    def get_stats(self) -> Dict:
        """Get offline storage statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM offline_requests WHERE synced = 0")
        pending = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM offline_requests WHERE synced = 1")
        synced = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM offline_requests")
        total = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "pending": pending,
            "synced": synced,
            "total": total
        }

