"""
BBS论坛系统 - 认证授权模块
本文件负责：
1. 密码加密和验证
2. JWT令牌生成和验证
3. 用户身份认证
4. 权限验证依赖
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.schemas import TokenData
import os

# ========== JWT配置 ==========
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")  # JWT密钥（生产环境必须修改）
REFRESH_SECRET_KEY = os.getenv("REFRESH_SECRET_KEY", "your-refresh-secret-key-change-in-production")  # 刷新令牌密钥
ALGORITHM = "HS256"  # JWT加密算法
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # Token有效期：7天
REFRESH_TOKEN_EXPIRE_DAYS = 30  # 刷新令牌有效期：30天

# ========== 密码加密配置 ==========
# 使用bcrypt算法进行密码哈希
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ========== OAuth2配置 ==========
# 定义Token获取的URL路径
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

# ========== 密码处理函数 ==========

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码是否正确

    参数:
        plain_password: 明文密码
        hashed_password: 数据库存储的哈希密码

    返回:
        bool: 密码是否匹配
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    生成密码的哈希值

    参数:
        password: 明文密码

    返回:
        str: 哈希后的密码
    """
    return pwd_context.hash(password)

# ========== JWT令牌函数 ==========

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    创建JWT访问令牌

    参数:
        data: 要编码的数据（通常包含用户名和用户ID）
        expires_delta: 自定义过期时间（可选）

    返回:
        str: JWT令牌字符串
    """
    to_encode = data.copy()  # 复制数据避免修改原始字典
    if expires_delta:
        # 使用自定义过期时间
        expire = datetime.utcnow() + expires_delta
    else:
        # 使用默认过期时间（7天）
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})  # 添加过期时间到payload
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)  # 生成JWT
    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    创建刷新令牌

    参数:
        data: 要编码的数据（通常包含用户名和用户ID）
        expires_delta: 自定义过期时间（可选）

    返回:
        str: 刷新令牌字符串
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})  # 添加过期时间和令牌类型
    encoded_jwt = jwt.encode(to_encode, REFRESH_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# ========== 用户认证函数 ==========

def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """
    验证用户身份（仅用户名+密码）

    参数:
        db: 数据库会话
        username: 用户名
        password: 明文密码

    返回:
        User: 认证成功返回用户对象，失败返回None
    """
    # 根据用户名查询用户
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None  # 用户不存在
    # 验证密码
    if not verify_password(password, user.password_hash):
        return None  # 密码错误
    # 检查账号状态
    if not user.is_active or user.is_banned:
        return None  # 账号未激活或被封禁
    return user  # 认证成功

def authenticate_user_by_phone_or_email(db: Session, identifier: str, password: str) -> Optional[User]:
    """
    验证用户身份（支持用户名/手机号/邮箱+密码）

    参数:
        db: 数据库会话
        identifier: 用户名/手机号/邮箱
        password: 明文密码

    返回:
        User: 认证成功返回用户对象，失败返回None
    """
    # 尝试通过用户名、手机号或邮箱查询用户
    user = db.query(User).filter(
        (User.username == identifier) |
        (User.phone == identifier) |
        (User.email == identifier)
    ).first()

    if not user:
        return None  # 用户不存在

    # 验证密码
    if not verify_password(password, user.password_hash):
        return None  # 密码错误

    # 检查账号状态
    if not user.is_active or user.is_banned:
        return None  # 账号未激活或被封禁

    return user  # 认证成功

# ========== FastAPI依赖函数 ==========

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    获取当前登录用户的依赖函数

    参数:
        token: JWT令牌（从Authorization头中自动提取）
        db: 数据库会话

    返回:
        User: 当前用户对象

    异常:
        HTTPException: Token无效或用户不存在时抛出401错误
    """
    # 定义认证失败的异常
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # 解码JWT令牌
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # 从payload中提取用户名和用户ID
        username: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        if username is None or user_id is None:
            raise credentials_exception  # Token中缺少必要信息
        token_data = TokenData(username=username, user_id=user_id)
    except JWTError:
        raise credentials_exception  # Token解码失败

    # 根据用户ID查询用户
    user = db.query(User).filter(User.id == token_data.user_id).first()
    if user is None:
        raise credentials_exception  # 用户不存在
    # 检查账号状态
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    if user.is_banned:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User is banned. Reason: {user.ban_reason or 'Not specified'}"
        )
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    获取当前活跃用户的依赖函数

    参数:
        current_user: 当前用户（通过get_current_user获取）

    返回:
        User: 活跃用户对象

    异常:
        HTTPException: 用户未激活时抛出400错误
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_optional_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> Optional[User]:
    """
    获取可选的当前用户（未登录返回None）

    用于需要区分登录/未登录用户的接口
    """
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        if username is None or user_id is None:
            return None
        user = db.query(User).filter(User.id == user_id).first()
        if user and user.is_active and not user.is_banned:
            return user
    except JWTError:
        pass
    return None

# ========== 装饰器方式鉴权 ==========

from functools import wraps
from typing import Callable, List

def auth_required(required_roles: List[str] = None):
    """
    认证装饰器 - 验证用户身份和权限

    参数:
        required_roles: 需要的角色列表，None表示只需要登录

    使用示例:
        @auth_required()  # 需要登录
        @auth_required(required_roles=["user"])  # 需要登录
        @auth_required(required_roles=["moderator", "admin"])  # 需要版主或管理员
        @auth_required(required_roles=["admin"])  # 需要管理员
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 从kwargs中获取current_user（由FastAPI依赖注入）
            current_user = kwargs.get('current_user')

            # 如果没有current_user，说明缺少鉴权依赖
            if current_user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )

            # 检查角色权限（比较枚举值）
            if required_roles and current_user.role.value not in required_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Required roles: {', '.join(required_roles)}"
                )

            # 执行原函数
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# 便捷装饰器
def require_auth(func: Callable) -> Callable:
    """需要登录的装饰器"""
    return auth_required()(func)

def require_moderator(func: Callable) -> Callable:
    """需要版主或管理员权限的装饰器"""
    return auth_required(required_roles=["moderator", "admin"])(func)

def require_admin(func: Callable) -> Callable:
    """需要管理员权限的装饰器"""
    return auth_required(required_roles=["admin"])(func)

# ========== 刷新令牌验证函数 ==========

def verify_refresh_token(token: str) -> Optional[TokenData]:
    """
    验证刷新令牌

    参数:
        token: 刷新令牌字符串

    返回:
        TokenData: 令牌数据对象，验证失败返回None
    """
    try:
        payload = jwt.decode(token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        token_type: str = payload.get("type")

        # 验证令牌类型是否为refresh
        if token_type != "refresh" or username is None or user_id is None:
            return None

        return TokenData(username=username, user_id=user_id)
    except JWTError:
        return None
