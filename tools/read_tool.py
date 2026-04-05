import os
from pathlib import Path
from typing import Optional

from config import settings
from .base import Tool, ToolResult

class ReadTool(Tool):
    name = "read"
    description = "读取文件内容"
    
    def __init__(self):
        self.allowed_paths = [Path(p).resolve() for p in settings.allowed_read_paths]
    
    def _is_path_allowed(self, file_path: str) -> bool:
        """检查文件路径是否在允许的目录内"""
        try:
            resolved_path = Path(file_path).resolve()
            for allowed in self.allowed_paths:
                if resolved_path.is_relative_to(allowed):
                    return True
            return False
        except:
            return False
    
    async def execute(self, file_path: str, 
                     offset: Optional[int] = None,
                     limit: Optional[int] = None) -> ToolResult:
        
        if not self._is_path_allowed(file_path):
            return ToolResult(
                success=False,
                output=None,
                error="文件路径不在允许的目录内"
            )
        
        try:
            if not os.path.exists(file_path):
                return ToolResult(
                    success=False,
                    output=None,
                    error="文件不存在"
                )
            
            if not os.path.isfile(file_path):
                return ToolResult(
                    success=False,
                    output=None,
                    error="路径不是文件"
                )
            
            # 检查文件大小限制（10MB）
            file_size = os.path.getsize(file_path)
            max_size = 10 * 1024 * 1024  # 10MB
            if file_size > max_size:
                return ToolResult(
                    success=False,
                    output=None,
                    error=f"文件太大 ({file_size} 字节 > {max_size} 字节限制)"
                )
            
            # 读取文件
            encoding = 'utf-8'
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    if offset is not None:
                        # 跳过行
                        lines = []
                        for i, line in enumerate(f):
                            if i >= offset:
                                lines.append(line)
                                if limit and len(lines) >= limit:
                                    break
                        content = ''.join(lines)
                    elif limit is not None:
                        # 读取指定行数
                        lines = []
                        for i, line in enumerate(f):
                            lines.append(line)
                            if i + 1 >= limit:
                                break
                        content = ''.join(lines)
                    else:
                        content = f.read()
            except UnicodeDecodeError:
                # 尝试二进制读取
                with open(file_path, 'rb') as f:
                    binary_content = f.read()
                    # 尝试解码为文本，如果失败则显示为十六进制
                    try:
                        content = binary_content.decode('utf-8')
                    except:
                        content = f"[二进制文件，大小: {len(binary_content)} 字节]"
            
            metadata = {
                "file_path": file_path,
                "file_size": file_size,
                "offset": offset,
                "limit": limit
            }
            
            return ToolResult(
                success=True,
                output=content,
                error=None,
                metadata=metadata
            )
            
        except PermissionError:
            return ToolResult(
                success=False,
                output=None,
                error="权限不足，无法读取文件"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output=None,
                error=f"读取文件时出错: {str(e)}"
            )