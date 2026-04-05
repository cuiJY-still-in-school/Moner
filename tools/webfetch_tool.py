import aiohttp
import asyncio
from typing import Optional, Dict, Any
from urllib.parse import urlparse

from .base import Tool, ToolResult

class WebFetchTool(Tool):
    name = "webfetch"
    description = "获取网页内容"
    
    def __init__(self):
        self.timeout = 30
        self.max_size = 10 * 1024 * 1024  # 10MB
    
    def _is_url_allowed(self, url: str) -> bool:
        """简单的URL检查"""
        try:
            parsed = urlparse(url)
            # 允许http和https
            if parsed.scheme not in ['http', 'https']:
                return False
            
            # 可以添加黑名单域等
            return True
        except:
            return False
    
    async def execute(self, url: str, method: str = "GET", 
                     headers: Optional[Dict[str, str]] = None,
                     data: Optional[Dict[str, Any]] = None) -> ToolResult:
        
        if not self._is_url_allowed(url):
            return ToolResult(
                success=False,
                output=None,
                error="URL不被允许或格式无效"
            )
        
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                if method.upper() == "GET":
                    async with session.get(url, headers=headers) as response:
                        content = await response.read()
                        status = response.status
                        content_type = response.headers.get('Content-Type', '')
                elif method.upper() == "POST":
                    async with session.post(url, json=data, headers=headers) as response:
                        content = await response.read()
                        status = response.status
                        content_type = response.headers.get('Content-Type', '')
                else:
                    return ToolResult(
                        success=False,
                        output=None,
                        error=f"不支持的HTTP方法: {method}"
                    )
                
                # 检查大小限制
                if len(content) > self.max_size:
                    content = content[:self.max_size]
                    truncated = True
                else:
                    truncated = False
                
                # 尝试解码文本
                if 'text' in content_type or 'json' in content_type or 'xml' in content_type:
                    try:
                        text_content = content.decode('utf-8')
                    except UnicodeDecodeError:
                        text_content = content.decode('latin-1')
                else:
                    text_content = f"[二进制内容，类型: {content_type}, 大小: {len(content)} 字节]"
                
                metadata = {
                    "status_code": status,
                    "content_type": content_type,
                    "size_bytes": len(content),
                    "truncated": truncated,
                    "url": url
                }
                
                return ToolResult(
                    success=200 <= status < 400,
                    output=text_content,
                    error=None if 200 <= status < 400 else f"HTTP状态码: {status}",
                    metadata=metadata
                )
                
        except asyncio.TimeoutError:
            return ToolResult(
                success=False,
                output=None,
                error=f"请求超时 ({self.timeout}秒)"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output=None,
                error=f"请求出错: {str(e)}"
            )