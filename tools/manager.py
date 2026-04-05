from typing import Dict, Any, Optional
import importlib
from .bash_tool import BashTool
from .webfetch_tool import WebFetchTool
from .read_tool import ReadTool
from .edit_tool import EditTool
from .base import Tool, ToolResult

class ToolManager:
    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        self._register_default_tools()
    
    def _register_default_tools(self):
        self.register_tool(BashTool())
        self.register_tool(WebFetchTool())
        self.register_tool(ReadTool())
        self.register_tool(EditTool())
        
        # 尝试注册AI工具
        try:
            from .ai_tool import SimpleAITool, DynamicAITool
            self.register_tool(SimpleAITool())
            self.register_tool(DynamicAITool())
        except ImportError:
            # AI工具不可用
            pass
    
    def register_tool(self, tool: Tool):
        self.tools[tool.name] = tool
    
    def get_tool(self, name: str) -> Optional[Tool]:
        return self.tools.get(name)
    
    def list_tools(self) -> Dict[str, str]:
        return {name: tool.description for name, tool in self.tools.items()}
    
    async def execute_tool(self, tool_name: str, **kwargs) -> ToolResult:
        tool = self.get_tool(tool_name)
        if not tool:
            return ToolResult(
                success=False,
                output=None,
                error=f"工具 '{tool_name}' 不存在"
            )
        
        try:
            return await tool.execute(**kwargs)
        except Exception as e:
            return ToolResult(
                success=False,
                output=None,
                error=f"工具执行异常: {str(e)}"
            )
    
    def get_tool_schema(self, tool_name: str) -> Optional[Dict[str, Any]]:
        tool = self.get_tool(tool_name)
        if not tool:
            return None
        return tool.get_schema()

# 全局工具管理器实例
tool_manager = ToolManager()