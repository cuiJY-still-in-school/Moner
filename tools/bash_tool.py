import asyncio
import os
import subprocess
import shlex
from typing import Optional
from pathlib import Path

from config import settings
from .base import Tool, ToolResult

class BashTool(Tool):
    name = "bash"
    description = "执行bash命令，有安全限制"
    
    def __init__(self):
        # 分割逗号分隔的路径字符串
        path_strs = settings.allowed_bash_paths.split(",")
        self.allowed_paths = [Path(p.strip()).resolve() for p in path_strs if p.strip()]
        self.max_timeout = settings.max_bash_timeout
    
    def _is_path_allowed(self, path: Optional[str] = None) -> bool:
        """检查路径是否在允许的目录内"""
        if not path:
            return True
        
        try:
            resolved_path = Path(path).resolve()
            for allowed in self.allowed_paths:
                if resolved_path.is_relative_to(allowed):
                    return True
            return False
        except:
            return False
    
    def _sanitize_command(self, command: str) -> bool:
        """简单命令安全检查"""
        dangerous_patterns = [
            "rm -rf /", "rm -rf /*", "dd if=", "mkfs", "> /dev/sda",
            ":(){ :|:& };:", "forkbomb", "chmod 777 /", "sudo"
        ]
        
        cmd_lower = command.lower()
        for pattern in dangerous_patterns:
            if pattern in cmd_lower:
                return False
        
        # 检查是否尝试更改到不允许的目录
        if cmd_lower.startswith("cd "):
            parts = shlex.split(command)
            if len(parts) >= 2:
                path = parts[1]
                if not self._is_path_allowed(path):
                    return False
        
        return True
    
    async def execute(self, command: str, timeout: Optional[int] = None) -> ToolResult:
        if not self._sanitize_command(command):
            return ToolResult(
                success=False,
                output=None,
                error="命令包含危险模式，被拒绝执行"
            )
        
        # 设置工作目录为第一个允许的路径
        cwd = self.allowed_paths[0] if self.allowed_paths else None
        
        try:
            # 使用asyncio创建子进程
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd
            )
            
            timeout = timeout or self.max_timeout
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
                exit_code = process.returncode
                
                output = stdout.decode('utf-8', errors='ignore')
                error_output = stderr.decode('utf-8', errors='ignore')
                
                combined_output = output + (f"\nSTDERR: {error_output}" if error_output else "")
                
                return ToolResult(
                    success=exit_code == 0,
                    output=combined_output,
                    error=None if exit_code == 0 else f"退出码: {exit_code}",
                    metadata={"exit_code": exit_code, "timeout": timeout}
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return ToolResult(
                    success=False,
                    output=None,
                    error=f"命令执行超时 ({timeout}秒)",
                    metadata={"timeout": timeout}
                )
                
        except Exception as e:
            return ToolResult(
                success=False,
                output=None,
                error=f"执行命令时出错: {str(e)}"
            )