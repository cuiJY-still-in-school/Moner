import asyncio
import logging
from typing import Dict, Optional, Set
from websockets.server import WebSocketServerProtocol

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocketServerProtocol] = {}
        self.user_connections: Dict[int, WebSocketServerProtocol] = {}
        self.connection_users: Dict[str, int] = {}
    
    async def connect(self, websocket: WebSocketServerProtocol, connection_id: str):
        self.active_connections[connection_id] = websocket
        logger.info(f"连接建立: {connection_id}")
    
    def disconnect(self, connection_id: str):
        websocket = self.active_connections.pop(connection_id, None)
        if connection_id in self.connection_users:
            user_id = self.connection_users.pop(connection_id)
            self.user_connections.pop(user_id, None)
            logger.info(f"用户 {user_id} 断开连接")
        else:
            logger.info(f"连接断开: {connection_id}")
    
    def register_user(self, connection_id: str, user_id: int):
        websocket = self.active_connections.get(connection_id)
        if not websocket:
            return False
        
        self.connection_users[connection_id] = user_id
        self.user_connections[user_id] = websocket
        logger.info(f"用户 {user_id} 注册到连接 {connection_id}")
        return True
    
    def get_user_connection(self, user_id: int) -> Optional[WebSocketServerProtocol]:
        return self.user_connections.get(user_id)
    
    def get_connection_user(self, connection_id: str) -> Optional[int]:
        return self.connection_users.get(connection_id)
    
    async def send_to_user(self, user_id: int, message: str):
        websocket = self.get_user_connection(user_id)
        if websocket:
            try:
                await websocket.send(message)
                return True
            except Exception as e:
                logger.error(f"发送消息给用户 {user_id} 失败: {e}")
                return False
        return False
    
    async def broadcast(self, message: str, exclude: Optional[Set[str]] = None):
        if exclude is None:
            exclude = set()
        
        tasks = []
        for conn_id, websocket in self.active_connections.items():
            if conn_id not in exclude:
                try:
                    tasks.append(websocket.send(message))
                except:
                    pass
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

connection_manager = ConnectionManager()