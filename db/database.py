"""Database Module - 数据库模块"""
import sqlite3
import json
from typing import Dict, List, Optional, Type
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass
import hashlib

@dataclass
class Model:
    """数据模型基类"""
    id: str = ""
    created_at: datetime = None
    updated_at: datetime = None

class QueryBuilder:
    """查询构建器"""
    def __init__(self, table: str):
        self.table = table
        self.where_clauses = []
        self.order_by = []
        self.limit_val = None
        self.offset_val = None
        
    def where(self, field: str, op: str, value):
        self.where_clauses.append(f"{field} {op} ?")
        return self
        
    def order(self, field: str, desc=False):
        direction = "DESC" if desc else "ASC"
        self.order_by.append(f"{field} {direction}")
        return self
        
    def limit(self, n: int):
        self.limit_val = n
        return self
        
    def offset(self, n: int):
        self.offset_val = n
        return self

class Database:
    """数据库管理器"""
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.connection = None
        
    def connect(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(str(self.db_path))
        self.connection.row_factory = sqlite3.Row
        
    def close(self):
        if self.connection:
            self.connection.close()
            
    def execute(self, sql: str, params=()):
        if not self.connection:
            self.connect()
        return self.connection.execute(sql, params)
        
    def commit(self):
        if self.connection:
            self.connection.commit()
            
    def create_table(self, table: str, fields: Dict):
        """创建表"""
        cols = []
        for name, t in fields.items():
            if name == "id":
                cols.append(f"{name} TEXT PRIMARY KEY")
            elif name in ["created_at", "updated_at"]:
                cols.append(f"{name} TEXT")
            else:
                cols.append(f"{name} {t}")
        sql = f"CREATE TABLE IF NOT EXISTS {table} ({', '.join(cols)})"
        self.execute(sql)
        self.commit()
        
    def insert(self, table: str, data: Dict) -> bool:
        """插入数据"""
        if "id" not in data:
            data["id"] = hashlib.md5(f"{datetime.now().isoformat()}".encode()).hexdigest()[:16]
        data["created_at"] = datetime.now().isoformat()
        data["updated_at"] = datetime.now().isoformat()
        
        cols = list(data.keys())
        placeholders = ["?"] * len(cols)
        sql = f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({', '.join(placeholders)})"
        
        try:
            self.execute(sql, tuple(str(v) for v in data.values()))
            self.commit()
            return True
        except Exception as e:
            print(f"Insert error: {e}")
            return False
            
    def update(self, table: str, data: Dict, id: str) -> bool:
        """更新数据"""
        data["updated_at"] = datetime.now().isoformat()
        
        updates = [f"{k} = ?" for k in data.keys()]
        sql = f"UPDATE {table} SET {', '.join(updates)} WHERE id = ?"
        
        try:
            self.execute(sql, tuple(str(v) for v in data.values()) + (id,))
            self.commit()
            return True
        except Exception as e:
            print(f"Update error: {e}")
            return False
            
    def delete(self, table: str, id: str) -> bool:
        """删除数据"""
        sql = f"DELETE FROM {table} WHERE id = ?"
        try:
            self.execute(sql, (id,))
            self.commit()
            return True
        except:
            return False
            
    def find_one(self, table: str, id: str) -> Optional[Dict]:
        """查找单条"""
        sql = f"SELECT * FROM {table} WHERE id = ?"
        cursor = self.execute(sql, (id,))
        row = cursor.fetchone()
        return dict(row) if row else None
        
    def find_all(self, table: str, limit: int = 100) -> List[Dict]:
        """查找所有"""
        sql = f"SELECT * FROM {table} LIMIT {limit}"
        cursor = self.execute(sql)
        return [dict(row) for row in cursor.fetchall()]
