"""Database Models - 数据模型"""
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional

@dataclass
class BaseModel:
    """基类模型"""
    id: str = ""
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
            
    def to_dict(self) -> Dict:
        result = {}
        for k, v in self.__dict__.items():
            if isinstance(v, datetime):
                result[k] = v.isoformat()
            else:
                result[k] = v
        return result

@dataclass
class User(BaseModel):
    """用户"""
    username: str = ""
    email: str = ""
    role: str = "user"

@dataclass
class Task(BaseModel):
    """任务"""
    title: str = ""
    description: str = ""
    status: str = "pending"
    priority: int = 5

@dataclass
class Agent(BaseModel):
    """智能体"""
    name: str = ""
    type: str = ""
    status: str = "idle"
    config: Dict = None
    
    def __post_init__(self):
        super().__post_init__()
        if self.config is None:
            self.config = {}
