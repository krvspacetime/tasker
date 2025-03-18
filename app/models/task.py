from dataclasses import dataclass
from typing import Optional
import uuid

@dataclass
class Task:
    """Represents a command task that can be run"""
    id: str
    title: str
    path: str
    cmd: str
    process: Optional[object] = None

    @classmethod
    def create(cls, path: str, cmd: str, title: str = None) -> 'Task':
        """Create a new task with a unique ID"""
        return cls(
            id=str(uuid.uuid4()),
            title=title or cmd,
            path=path,
            cmd=cmd
        )
