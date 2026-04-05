"""
AI工具实现
"""

import asyncio
import json
from typing import Dict, Any, Optional, List
import openai
import anthropic
from openai import OpenAI, AsyncOpenAI
import tiktoken

from tools.base import Tool, ToolResult
from config import settings

class AITool(Tool):
    """AI工具基类"""
    name = "ai"
    description = "调用AI模型进行推理和生成"
    
    def __init__(self):
        self.default_model = "gpt-3.5-turbo"
        self.default_max_tokens = 1000
        self.default_temperature = 0.7
    
    async def execute(self, 
                     prompt: str,
                     model: Optional[str] = None,
                     max_tokens: Optional[int] = None,
                     temperature: Optional[float] = None,
                     **kwargs) -> ToolResult:
        """执行AI补全"""
        raise NotImplementedError("子类必须实现execute方法")
    
    async def chat(self,
                  messages: List[Dict[str, str]],
                  model: Optional[str] = None,
                  max_tokens: Optional[int] = None,
                  temperature: Optional[float] = None,
                  **kwargs) -> ToolResult:
        """执行AI聊天"""
        raise NotImplementedError("子类必须实现chat方法")

class OpenAITool(AITool):
    """OpenAI工具"""
    name = "openai"
    description = "调用OpenAI API进行AI推理"
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        super().__init__()
        self.api_key = api_key or settings.get("OPENAI_API_KEY", "")
        self.base_url = base_url or settings.get("OPENAI_BASE_URL", None)
        self.client = None
        self.async_client = None
        
        if self.api_key:
            self._init_clients()
    
    def _init_clients(self):
        """初始化客户端"""
        client_kwargs = {"api_key": self.api_key}
        if self.base_url:
            client_kwargs["base_url"] = self.base_url
        
        self.client = OpenAI(**client_kwargs)
        self.async_client = AsyncOpenAI(**client_kwargs)
    
    def set_api_key(self, api_key: str):
        """设置API密钥"""
        self.api_key = api_key
        self._init_clients()
    
    async def execute(self, 
                     prompt: str,
                     model: Optional[str] = None,
                     max_tokens: Optional[int] = None,
                     temperature: Optional[float] = None,
                     **kwargs) -> ToolResult:
        """执行OpenAI补全"""
        if not self.async_client:
            return ToolResult(
                success=False,
                output=None,
                error="OpenAI客户端未初始化，请设置API密钥"
            )
        
        try:
            response = await self.async_client.completions.create(
                model=model or self.default_model,
                prompt=prompt,
                max_tokens=max_tokens or self.default_max_tokens,
                temperature=temperature or self.default_temperature,
                **kwargs
            )
            
            completion = response.choices[0].text
            usage = response.usage
            
            metadata = {
                "model": response.model,
                "tokens_used": usage.total_tokens if usage else 0,
                "finish_reason": response.choices[0].finish_reason
            }
            
            return ToolResult(
                success=True,
                output=completion,
                error=None,
                metadata=metadata
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                output=None,
                error=f"OpenAI API错误: {str(e)}"
            )
    
    async def chat(self,
                  messages: List[Dict[str, str]],
                  model: Optional[str] = None,
                  max_tokens: Optional[int] = None,
                  temperature: Optional[float] = None,
                  **kwargs) -> ToolResult:
        """执行OpenAI聊天"""
        if not self.async_client:
            return ToolResult(
                success=False,
                output=None,
                error="OpenAI客户端未初始化，请设置API密钥"
            )
        
        try:
            response = await self.async_client.chat.completions.create(
                model=model or "gpt-3.5-turbo",
                messages=messages,
                max_tokens=max_tokens or self.default_max_tokens,
                temperature=temperature or self.default_temperature,
                **kwargs
            )
            
            message = response.choices[0].message
            usage = response.usage
            
            result = {
                "role": message.role,
                "content": message.content,
                "tool_calls": message.tool_calls
            }
            
            metadata = {
                "model": response.model,
                "tokens_used": usage.total_tokens if usage else 0,
                "finish_reason": response.choices[0].finish_reason
            }
            
            return ToolResult(
                success=True,
                output=result,
                error=None,
                metadata=metadata
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                output=None,
                error=f"OpenAI API错误: {str(e)}"
            )
    
    def count_tokens(self, text: str, model: str = "gpt-3.5-turbo") -> int:
        """计算token数量"""
        try:
            encoding = tiktoken.encoding_for_model(model)
            return len(encoding.encode(text))
        except:
            # 简单估算
            return len(text) // 4

class AnthropicTool(AITool):
    """Anthropic工具"""
    name = "anthropic"
    description = "调用Anthropic Claude API进行AI推理"
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__()
        self.api_key = api_key or settings.get("ANTHROPIC_API_KEY", "")
        self.client = None
        
        if self.api_key:
            self.client = anthropic.Anthropic(api_key=self.api_key)
    
    def set_api_key(self, api_key: str):
        """设置API密钥"""
        self.api_key = api_key
        self.client = anthropic.Anthropic(api_key=api_key)
    
    async def execute(self, 
                     prompt: str,
                     model: Optional[str] = None,
                     max_tokens: Optional[int] = None,
                     temperature: Optional[float] = None,
                     **kwargs) -> ToolResult:
        """执行Anthropic补全"""
        if not self.client:
            return ToolResult(
                success=False,
                output=None,
                error="Anthropic客户端未初始化，请设置API密钥"
            )
        
        try:
            response = self.client.completions.create(
                model=model or "claude-2",
                prompt=f"{anthropic.HUMAN_PROMPT} {prompt} {anthropic.AI_PROMPT}",
                max_tokens_to_sample=max_tokens or self.default_max_tokens,
                temperature=temperature or self.default_temperature,
                **kwargs
            )
            
            completion = response.completion
            metadata = {
                "model": response.model,
                "stop_reason": response.stop_reason
            }
            
            return ToolResult(
                success=True,
                output=completion,
                error=None,
                metadata=metadata
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                output=None,
                error=f"Anthropic API错误: {str(e)}"
            )
    
    async def chat(self,
                  messages: List[Dict[str, str]],
                  model: Optional[str] = None,
                  max_tokens: Optional[int] = None,
                  temperature: Optional[float] = None,
                  **kwargs) -> ToolResult:
        """执行Anthropic聊天（消息格式转换）"""
        if not self.client:
            return ToolResult(
                success=False,
                output=None,
                error="Anthropic客户端未初始化，请设置API密钥"
            )
        
        try:
            # 转换消息格式为Anthropic格式
            prompt = ""
            for msg in messages:
                if msg["role"] == "user":
                    prompt += f"{anthropic.HUMAN_PROMPT} {msg['content']}"
                elif msg["role"] == "assistant":
                    prompt += f"{anthropic.AI_PROMPT} {msg['content']}"
            
            prompt += f"{anthropic.AI_PROMPT}"
            
            response = self.client.completions.create(
                model=model or "claude-2",
                prompt=prompt,
                max_tokens_to_sample=max_tokens or self.default_max_tokens,
                temperature=temperature or self.default_temperature,
                **kwargs
            )
            
            result = {
                "role": "assistant",
                "content": response.completion
            }
            
            metadata = {
                "model": response.model,
                "stop_reason": response.stop_reason
            }
            
            return ToolResult(
                success=True,
                output=result,
                error=None,
                metadata=metadata
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                output=None,
                error=f"Anthropic API错误: {str(e)}"
            )