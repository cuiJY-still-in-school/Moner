from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel

class ToolResult(BaseModel):
    success: bool
    output: Any
    error: Optional[str] = None
    metadata: Dict[str, Any] = {}

class Tool(ABC):
    name: str
    description: str
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        pass
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description
        }