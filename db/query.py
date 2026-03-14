"""Database Query - 数据库查询"""
import sqlite3
from typing import Dict, List, Optional, Any
from pathlib import Path

class Database:
    """数据库"""
    
    def __init__(self, db_path: str = "data.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = None
        
    def connect(self):
        """连接"""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        
    def close(self):
        """关闭"""
        if self.conn:
            self.conn.close()
            
    def execute(self, sql: str, params: tuple = ()):
        """执行"""
        if not self.conn:
            self.connect()
        return self.conn.execute(sql, params)
        
    def commit(self):
        """提交"""
        if self.conn:
            self.conn.commit()
            
    def create_tables(self):
        """创建表"""
        self.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE,
                email TEXT,
                role TEXT DEFAULT 'user',
                created_at TEXT,
                updated_at TEXT
            )
        """)
        
        self.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                title TEXT,
                description TEXT,
                status TEXT DEFAULT 'pending',
                priority INTEGER DEFAULT 5,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        
        self.commit()
