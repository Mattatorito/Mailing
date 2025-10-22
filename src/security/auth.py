#!/usr/bin/env python3
"""
Система аутентификации для веб-интерфейса.
Поддерживает JWT токены, session-based auth и API ключи.
"""

import os
import jwt
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
import redis
import json
import logging

logger = logging.getLogger(__name__)

# Настройки безопасности
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)

@dataclass
class User:
    """Модель пользователя."""
    username: str
    email: str
    hashed_password: str
    is_active: bool = True
    is_admin: bool = False
    created_at: datetime = None
    last_login: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)

@dataclass
class AuthConfig:
    """Конфигурация аутентификации."""
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    session_expire_hours: int = 24
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15
    require_https: bool = True
    
class AuthenticationError(Exception):
    """Ошибка аутентификации."""
    pass

class AuthorizationError(Exception):
    """Ошибка авторизации."""
    pass

class AccountLockedError(Exception):
    """Аккаунт заблокирован."""
    pass

class AuthManager:
    """Менеджер аутентификации."""
    
    def __init__(self, config: Optional[AuthConfig] = None, redis_client=None):
        self.config = config or self._load_config()
        self.redis_client = redis_client
        self._users: Dict[str, User] = {}
        self._load_default_users()
    
    def _load_config(self) -> AuthConfig:
        """Загружает конфигурацию из переменных окружения."""
        secret_key = os.getenv('AUTH_SECRET_KEY')
        if not secret_key:
            # Генерируем случайный ключ для разработки
            secret_key = secrets.token_urlsafe(32)
            logger.warning("Using generated secret key. Set AUTH_SECRET_KEY in production!")
        
        return AuthConfig(
            secret_key=secret_key,
            algorithm=os.getenv('AUTH_ALGORITHM', 'HS256'),
            access_token_expire_minutes=int(os.getenv('AUTH_ACCESS_TOKEN_EXPIRE_MINUTES', '30')),
            refresh_token_expire_days=int(os.getenv('AUTH_REFRESH_TOKEN_EXPIRE_DAYS', '7')),
            session_expire_hours=int(os.getenv('AUTH_SESSION_EXPIRE_HOURS', '24')),
            max_login_attempts=int(os.getenv('AUTH_MAX_LOGIN_ATTEMPTS', '5')),
            lockout_duration_minutes=int(os.getenv('AUTH_LOCKOUT_DURATION_MINUTES', '15')),
            require_https=os.getenv('AUTH_REQUIRE_HTTPS', 'true').lower() == 'true'
        )
    
    def _load_default_users(self):
        """Загружает пользователей по умолчанию."""
        # Администратор по умолчанию
        admin_username = os.getenv('ADMIN_USERNAME', 'admin')
        admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')
        admin_email = os.getenv('ADMIN_EMAIL', 'admin@example.com')
        
        if admin_password == 'admin123':
            logger.warning("Using default admin password! Change ADMIN_PASSWORD in production!")
        
        self._users[admin_username] = User(
            username=admin_username,
            email=admin_email,
            hashed_password=self.hash_password(admin_password),
            is_admin=True
        )
        
        # Обычный пользователь для демо
        demo_username = os.getenv('DEMO_USERNAME', 'demo')
        demo_password = os.getenv('DEMO_PASSWORD', 'demo123')
        demo_email = os.getenv('DEMO_EMAIL', 'demo@example.com')
        
        self._users[demo_username] = User(
            username=demo_username,
            email=demo_email,
            hashed_password=self.hash_password(demo_password),
            is_admin=False
        )
    
    def hash_password(self, password: str) -> str:
        """Хеширует пароль."""
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Проверяет пароль."""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_user(self, username: str) -> Optional[User]:
        """Получает пользователя по имени."""
        return self._users.get(username)
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Аутентифицирует пользователя."""
        # Проверяем блокировку аккаунта
        if self._is_account_locked(username):
            self._increment_login_attempts(username)
            raise AccountLockedError(f"Account {username} is locked due to too many failed attempts")
        
        user = self.get_user(username)
        if not user:
            self._increment_login_attempts(username)
            return None
        
        if not user.is_active:
            raise AuthenticationError("Account is inactive")
        
        if not self.verify_password(password, user.hashed_password):
            self._increment_login_attempts(username)
            return None
        
        # Успешная аутентификация - сбрасываем счетчик попыток
        self._reset_login_attempts(username)
        user.last_login = datetime.now(timezone.utc)
        
        return user
    
    def _is_account_locked(self, username: str) -> bool:
        """Проверяет заблокирован ли аккаунт."""
        if not self.redis_client:
            return False
        
        try:
            attempts_key = f"login_attempts:{username}"
            lockout_key = f"lockout:{username}"
            
            # Проверяем блокировку
            lockout_time = self.redis_client.get(lockout_key)
            if lockout_time:
                lockout_timestamp = datetime.fromisoformat(lockout_time.decode())
                if datetime.now(timezone.utc) < lockout_timestamp:
                    return True
                else:
                    # Блокировка истекла
                    self.redis_client.delete(lockout_key)
                    self.redis_client.delete(attempts_key)
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking account lock: {e}")
            return False
    
    def _increment_login_attempts(self, username: str):
        """Увеличивает счетчик неудачных попыток входа."""
        if not self.redis_client:
            return
        
        try:
            attempts_key = f"login_attempts:{username}"
            attempts = self.redis_client.incr(attempts_key)
            
            # Устанавливаем TTL для ключа
            self.redis_client.expire(attempts_key, self.config.lockout_duration_minutes * 60)
            
            # Блокируем аккаунт если превышен лимит
            if attempts >= self.config.max_login_attempts:
                lockout_key = f"lockout:{username}"
                lockout_until = datetime.now(timezone.utc) + timedelta(minutes=self.config.lockout_duration_minutes)
                self.redis_client.set(lockout_key, lockout_until.isoformat(), ex=self.config.lockout_duration_minutes * 60)
                logger.warning(f"Account {username} locked due to {attempts} failed login attempts")
                
        except Exception as e:
            logger.error(f"Error incrementing login attempts: {e}")
    
    def _reset_login_attempts(self, username: str):
        """Сбрасывает счетчик неудачных попыток."""
        if not self.redis_client:
            return
        
        try:
            attempts_key = f"login_attempts:{username}"
            lockout_key = f"lockout:{username}"
            self.redis_client.delete(attempts_key)
            self.redis_client.delete(lockout_key)
        except Exception as e:
            logger.error(f"Error resetting login attempts: {e}")
    
    def create_access_token(self, user: User) -> str:
        """Создает JWT access token."""
        expire = datetime.now(timezone.utc) + timedelta(minutes=self.config.access_token_expire_minutes)
        to_encode = {
            "sub": user.username,
            "email": user.email,
            "is_admin": user.is_admin,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "access"
        }
        
        return jwt.encode(to_encode, self.config.secret_key, algorithm=self.config.algorithm)
    
    def create_refresh_token(self, user: User) -> str:
        """Создает JWT refresh token."""
        expire = datetime.now(timezone.utc) + timedelta(days=self.config.refresh_token_expire_days)
        to_encode = {
            "sub": user.username,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "refresh"
        }
        
        token = jwt.encode(to_encode, self.config.secret_key, algorithm=self.config.algorithm)
        
        # Сохраняем refresh token в Redis
        if self.redis_client:
            try:
                token_key = f"refresh_token:{user.username}"
                self.redis_client.set(token_key, token, ex=self.config.refresh_token_expire_days * 24 * 3600)
            except Exception as e:
                logger.error(f"Error storing refresh token: {e}")
        
        return token
    
    def verify_token(self, token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        """Проверяет и декодирует JWT token."""
        try:
            payload = jwt.decode(token, self.config.secret_key, algorithms=[self.config.algorithm])
            
            # Проверяем тип токена
            if payload.get("type") != token_type:
                return None
            
            username = payload.get("sub")
            if not username:
                return None
            
            # Для refresh токенов проверяем что они есть в Redis
            if token_type == "refresh" and self.redis_client:
                try:
                    token_key = f"refresh_token:{username}"
                    stored_token = self.redis_client.get(token_key)
                    if not stored_token or stored_token.decode() != token:
                        return None
                except Exception as e:
                    logger.error(f"Error verifying refresh token: {e}")
                    return None
            
            return payload
            
        except jwt.ExpiredSignatureError:
            return None
        except jwt.JWTError:
            return None
    
    def revoke_refresh_token(self, username: str):
        """Отзывает refresh token пользователя."""
        if self.redis_client:
            try:
                token_key = f"refresh_token:{username}"
                self.redis_client.delete(token_key)
            except Exception as e:
                logger.error(f"Error revoking refresh token: {e}")
    
    def create_session(self, user: User, request: Request) -> str:
        """Создает сессию пользователя."""
        session_id = secrets.token_urlsafe(32)
        expire = datetime.now(timezone.utc) + timedelta(hours=self.config.session_expire_hours)
        
        session_data = {
            "username": user.username,
            "email": user.email,
            "is_admin": user.is_admin,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": expire.isoformat(),
            "ip_address": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent")
        }
        
        if self.redis_client:
            try:
                session_key = f"session:{session_id}"
                self.redis_client.set(session_key, json.dumps(session_data), ex=self.config.session_expire_hours * 3600)
            except Exception as e:
                logger.error(f"Error creating session: {e}")
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Получает данные сессии."""
        if not self.redis_client:
            return None
        
        try:
            session_key = f"session:{session_id}"
            session_data = self.redis_client.get(session_key)
            
            if not session_data:
                return None
            
            data = json.loads(session_data.decode())
            
            # Проверяем срок действия
            expires_at = datetime.fromisoformat(data["expires_at"])
            if datetime.now(timezone.utc) > expires_at:
                self.redis_client.delete(session_key)
                return None
            
            return data
            
        except Exception as e:
            logger.error(f"Error getting session: {e}")
            return None
    
    def revoke_session(self, session_id: str):
        """Отзывает сессию."""
        if self.redis_client:
            try:
                session_key = f"session:{session_id}"
                self.redis_client.delete(session_key)
            except Exception as e:
                logger.error(f"Error revoking session: {e}")
    
    def revoke_all_sessions(self, username: str):
        """Отзывает все сессии пользователя."""
        if not self.redis_client:
            return
        
        try:
            # Ищем все сессии пользователя
            for key in self.redis_client.scan_iter(match="session:*"):
                session_data = self.redis_client.get(key)
                if session_data:
                    data = json.loads(session_data.decode())
                    if data.get("username") == username:
                        self.redis_client.delete(key)
        except Exception as e:
            logger.error(f"Error revoking all sessions: {e}")

# Глобальный экземпляр
auth_manager: Optional[AuthManager] = None

def get_auth_manager() -> AuthManager:
    """Получает экземпляр менеджера аутентификации."""
    global auth_manager
    if not auth_manager:
        # Инициализируем Redis если доступен
        redis_client = None
        try:
            import redis
            redis_host = os.getenv('REDIS_HOST', 'localhost')
            redis_port = int(os.getenv('REDIS_PORT', '6379'))
            redis_db = int(os.getenv('REDIS_DB', '0'))
            redis_client = redis.Redis(host=redis_host, port=redis_port, db=redis_db, decode_responses=False)
            redis_client.ping()  # Проверяем подключение
        except Exception as e:
            logger.warning(f"Redis not available, using in-memory storage: {e}")
            redis_client = None
        
        auth_manager = AuthManager(redis_client=redis_client)
    
    return auth_manager

# Dependency functions для FastAPI
async def get_current_user_token(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[User]:
    """Получает текущего пользователя по JWT токену."""
    if not credentials:
        return None
    
    manager = get_auth_manager()
    payload = manager.verify_token(credentials.credentials, "access")
    
    if not payload:
        return None
    
    username = payload.get("sub")
    user = manager.get_user(username)
    
    if not user or not user.is_active:
        return None
    
    return user

async def get_current_user_session(request: Request) -> Optional[User]:
    """Получает текущего пользователя по сессии."""
    session_id = request.cookies.get("session_id")
    if not session_id:
        return None
    
    manager = get_auth_manager()
    session_data = manager.get_session(session_id)
    
    if not session_data:
        return None
    
    username = session_data.get("username")
    user = manager.get_user(username)
    
    if not user or not user.is_active:
        return None
    
    return user

async def get_current_user(
    request: Request,
    token_user: Optional[User] = Depends(get_current_user_token),
    session_user: Optional[User] = Depends(get_current_user_session)
) -> User:
    """Получает текущего пользователя (токен или сессия)."""
    user = token_user or session_user
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

async def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Проверяет что текущий пользователь - администратор."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return current_user

def require_https(request: Request):
    """Проверяет что используется HTTPS в production."""
    config = get_auth_manager().config
    
    if (
        config.require_https and 
        request.url.scheme != "https" and 
        request.headers.get("x-forwarded-proto") != "https" and
        os.getenv("ENVIRONMENT", "development") == "production"
    ):
        raise HTTPException(
            status_code=status.HTTP_426_UPGRADE_REQUIRED,
            detail="HTTPS required"
        )