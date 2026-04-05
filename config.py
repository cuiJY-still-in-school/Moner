import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # 服务器配置
    server_host: str = os.getenv("SERVER_HOST", "0.0.0.0")
    server_port: int = int(os.getenv("SERVER_PORT", "8000"))
    ws_host: str = os.getenv("WS_HOST", "0.0.0.0")
    ws_port: int = int(os.getenv("WS_PORT", "8765"))
    
    # 数据库
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./moner.db")
    
    # JWT
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    jwt_access_token_expire_minutes: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # 工具安全限制
    allowed_bash_paths: list[str] = os.getenv("ALLOWED_BASH_PATHS", "/home/jayson2013/moner,/tmp").split(",")
    max_bash_timeout: int = int(os.getenv("MAX_BASH_TIMEOUT", "30"))
    allowed_read_paths: list[str] = os.getenv("ALLOWED_READ_PATHS", "/home/jayson2013/moner").split(",")
    allowed_edit_paths: list[str] = os.getenv("ALLOWED_EDIT_PATHS", "/home/jayson2013/moner").split(",")
    
    # AI配置
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY", None)
    anthropic_api_key: Optional[str] = os.getenv("ANTHROPIC_API_KEY", None)
    openai_base_url: Optional[str] = os.getenv("OPENAI_BASE_URL", None)
    default_ai_model: str = os.getenv("DEFAULT_AI_MODEL", "gpt-3.5-turbo")
    
    # 应用
    app_name: str = "Moner"
    app_version: str = "0.1.0"
    
    class Config:
        env_file = ".env"

settings = Settings()