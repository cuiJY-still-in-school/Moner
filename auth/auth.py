from datetime import datetime, timedelta
from typing import Optional
import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from config import settings
from models.user import User
from auth.schemas import TokenData

pwd_context = CryptContext(schemes=["pbkdf2_sha256", "bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    # bcrypt限制密码为72字节，需要截断
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password = password_bytes[:72].decode('utf-8', 'ignore')
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt

def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

def get_current_user(token: str, db: Session) -> Optional[User]:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        token_data = TokenData(user_id=int(user_id))
    except jwt.InvalidTokenError:
        return None
    
    user = db.query(User).filter(User.id == token_data.user_id).first()
    return user