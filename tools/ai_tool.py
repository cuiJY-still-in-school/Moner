"""
AI工具包装器
"""

from typing import Dict, Any, Optional
from .base import Tool, ToolResult

class SimpleAITool(Tool):
    """简单的AI工具（占位符）"""
    name = "ai"
    description = "AI推理和生成工具（需要配置）"
    
    def __init__(self):
        self.available = False
        self.ai_tool = None
        self._try_init_ai()
    
    def _try_init_ai(self):
        """尝试初始化AI工具"""
        try:
            from ai.tools import OpenAITool
            # 这里应该从配置或数据库加载API密钥
            # 目前只是一个占位符
            self.ai_tool = None  # 实际使用时需要初始化
            self.available = False
            self.description = "AI推理和生成工具（未配置API密钥）"
        except ImportError:
            self.available = False
            self.description = "AI推理和生成工具（缺少依赖）"
    
    def set_api_key(self, api_key: str, provider: str = "openai"):
        """设置API密钥"""
        try:
            if provider == "openai":
                from ai.tools import OpenAITool
                self.ai_tool = OpenAITool(api_key=api_key)
                self.available = True
                self.description = "OpenAI AI推理和生成工具"
            elif provider == "anthropic":
                from ai.tools import AnthropicTool
                self.ai_tool = AnthropicTool(api_key=api_key)
                self.available = True
                self.description = "Anthropic Claude AI推理和生成工具"
        except ImportError:
            self.available = False
    
    async def execute(self, 
                     prompt: str,
                     model: Optional[str] = None,
                     max_tokens: Optional[int] = None,
                     temperature: Optional[float] = None,
                     **kwargs) -> ToolResult:
        """执行AI补全"""
        if not self.available or not self.ai_tool:
            return ToolResult(
                success=False,
                output=None,
                error="AI工具未配置或不可用。请设置API密钥。"
            )
        
        return await self.ai_tool.execute(
            prompt=prompt,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs
        )
    
    async def chat(self,
                  messages: list,
                  model: Optional[str] = None,
                  max_tokens: Optional[int] = None,
                  temperature: Optional[float] = None,
                  **kwargs) -> ToolResult:
        """执行AI聊天"""
        if not self.available or not self.ai_tool:
            return ToolResult(
                success=False,
                output=None,
                error="AI工具未配置或不可用。请设置API密钥。"
            )
        
        return await self.ai_tool.chat(
            messages=messages,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs
        )


class DynamicAITool(Tool):
    """动态AI工具，每次调用时提供完整配置"""
    name = "ai_dynamic"
    description = "动态AI推理工具（支持OpenAI、Anthropic等，使用时提供完整配置）"
    
    def __init__(self):
        self.available = True  # 总是可用，因为配置是动态的
    
    async def execute(self, 
                     prompt: str,
                     provider: str,
                     api_key: str,
                     model_name: str,
                     base_url: Optional[str] = None,
                     max_tokens: Optional[int] = 1000,
                     temperature: Optional[float] = 0.7,
                     **kwargs) -> ToolResult:
        """执行AI补全（动态配置）"""
        try:
            if provider.lower() == "openai":
                from ai.tools import OpenAITool
                ai_tool = OpenAITool(api_key=api_key, base_url=base_url)
                return await ai_tool.execute(
                    prompt=prompt,
                    model=model_name,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    **kwargs
                )
            elif provider.lower() == "anthropic":
                from ai.tools import AnthropicTool
                ai_tool = AnthropicTool(api_key=api_key)
                return await ai_tool.execute(
                    prompt=prompt,
                    model=model_name,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    **kwargs
                )
            else:
                return ToolResult(
                    success=False,
                    output=None,
                    error=f"不支持的AI提供商: {provider}。支持: openai, anthropic"
                )
        except ImportError as e:
            return ToolResult(
                success=False,
                output=None,
                error=f"缺少依赖: {str(e)}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output=None,
                error=f"AI调用失败: {str(e)}"
            )
    
    async def chat(self,
                  messages: list,
                  provider: str,
                  api_key: str,
                  model_name: str,
                  base_url: Optional[str] = None,
                  max_tokens: Optional[int] = 1000,
                  temperature: Optional[float] = 0.7,
                  **kwargs) -> ToolResult:
        """执行AI聊天（动态配置）"""
        try:
            if provider.lower() == "openai":
                from ai.tools import OpenAITool
                ai_tool = OpenAITool(api_key=api_key, base_url=base_url)
                return await ai_tool.chat(
                    messages=messages,
                    model=model_name,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    **kwargs
                )
            elif provider.lower() == "anthropic":
                from ai.tools import AnthropicTool
                ai_tool = AnthropicTool(api_key=api_key)
                return await ai_tool.chat(
                    messages=messages,
                    model=model_name,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    **kwargs
                )
            else:
                return ToolResult(
                    success=False,
                    output=None,
                    error=f"不支持的AI提供商: {provider}。支持: openai, anthropic"
                )
        except ImportError as e:
            return ToolResult(
                success=False,
                output=None,
                error=f"缺少依赖: {str(e)}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output=None,
                error=f"AI聊天失败: {str(e)}"
            )