import os
from pathlib import Path
from typing import Optional

from config import settings
from .base import Tool, ToolResult

class EditTool(Tool):
    name = "edit"
    description = "编辑文件内容（替换文本）"
    
    def __init__(self):
        self.allowed_paths = [Path(p).resolve() for p in settings.allowed_edit_paths]
    
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
                     old_string: Optional[str] = None,
                     new_string: Optional[str] = None,
                     content: Optional[str] = None,
                     mode: str = "replace") -> ToolResult:
        """
        编辑文件
        
        参数:
        - file_path: 文件路径
        - old_string: 要替换的字符串（replace模式）
        - new_string: 替换后的字符串（replace模式）
        - content: 整个文件内容（overwrite模式）
        - mode: 'replace' 或 'overwrite'
        """
        
        if not self._is_path_allowed(file_path):
            return ToolResult(
                success=False,
                output=None,
                error="文件路径不在允许的目录内"
            )
        
        try:
            # 检查文件是否存在
            file_exists = os.path.exists(file_path)
            
            if mode == "replace":
                if old_string is None or new_string is None:
                    return ToolResult(
                        success=False,
                        output=None,
                        error="replace模式需要old_string和new_string参数"
                    )
                
                if not file_exists:
                    return ToolResult(
                        success=False,
                        output=None,
                        error="文件不存在，无法替换内容"
                    )
                
                # 读取文件
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_content = f.read()
                
                # 检查old_string是否存在
                if old_string not in file_content:
                    return ToolResult(
                        success=False,
                        output=None,
                        error="old_string在文件中未找到"
                    )
                
                # 执行替换
                new_content = file_content.replace(old_string, new_string)
                
                # 写入文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                changes = file_content.count(old_string)
                
                metadata = {
                    "file_path": file_path,
                    "mode": mode,
                    "changes": changes,
                    "file_existed": True
                }
                
                return ToolResult(
                    success=True,
                    output=f"成功替换 {changes} 处",
                    error=None,
                    metadata=metadata
                )
            
            elif mode == "overwrite":
                if content is None:
                    return ToolResult(
                        success=False,
                        output=None,
                        error="overwrite模式需要content参数"
                    )
                
                # 写入文件（创建或覆盖）
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                metadata = {
                    "file_path": file_path,
                    "mode": mode,
                    "file_existed": file_exists,
                    "new_size": len(content)
                }
                
                return ToolResult(
                    success=True,
                    output=f"成功{'创建' if not file_exists else '覆盖'}文件",
                    error=None,
                    metadata=metadata
                )
            
            else:
                return ToolResult(
                    success=False,
                    output=None,
                    error=f"不支持的模式: {mode}，支持 'replace' 或 'overwrite'"
                )
                
        except PermissionError:
            return ToolResult(
                success=False,
                output=None,
                error="权限不足，无法编辑文件"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output=None,
                error=f"编辑文件时出错: {str(e)}"
            )