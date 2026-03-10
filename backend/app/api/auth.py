from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from pydantic import BaseModel
from app.database import get_db
from app.models import User, Log
from app.schemas import (
    UserCreate, UserResponse, Token, UserLogin,
    SendVerificationCodeRequest, RegisterWithCodeRequest, VerificationCodeResponse,
    ChangePasswordRequest, ResetPasswordRequest
)
from app.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    authenticate_user,
    authenticate_user_by_phone_or_email,
    get_current_active_user,
    verify_refresh_token
)
from app.security import SecurityService
from app.utils.verification import verification_service
import os
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", str(60 * 24 * 7)))

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    """用户注册"""
    # 检查用户名是否已存在
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )

    # 检查邮箱是否已存在
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已被注册"
        )

    # 验证用户名格式
    if not SecurityService.validate_username(user.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名格式不正确"
        )

    # 验证密码
    is_valid, msg = SecurityService.validate_password(user.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg
        )

    # 验证邮箱格式
    if not SecurityService.validate_email(user.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱格式不正确"
        )

    # 验证手机号（如果提供）
    if user.phone and not SecurityService.validate_phone(user.phone):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="手机号格式不正确"
        )

    # 创建新用户
    db_user = User(
        username=user.username,
        email=user.email,
        phone=user.phone,
        password_hash=get_password_hash(user.password)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # 记录日志
    log = Log(
        user_id=db_user.id,
        action="user_register",
        extra_data={"username": user.username}
    )
    db.add(log)
    db.commit()

    return db_user

@router.post("/login", response_model=Token)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    用户登录（支持用户名/手机号/邮箱登录）
    使用OAuth2标准的表单格式，适用于传统的登录表单
    """
    # 尝试通过用户名/手机号/邮箱登录
    user = authenticate_user_by_phone_or_email(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="账号或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 更新最后登录时间和IP
    user.last_login_at = datetime.utcnow()
    client_host = request.client.host if request.client else None
    user.last_login_ip = client_host
    db.commit()

    # 创建访问令牌和刷新令牌
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id},
        expires_delta=access_token_expires
    )

    # 创建刷新令牌（有效期30天）
    refresh_token_expires = timedelta(days=30)
    refresh_token = create_refresh_token(
        data={"sub": user.username, "user_id": user.id},
        expires_delta=refresh_token_expires
    )

    # 记录登录日志
    log = Log(
        user_id=user.id,
        action="user_login",
        ip_address=client_host,
        extra_data={"login_method": "form", "username": user.username}
    )
    db.add(log)
    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/login/json", response_model=Token)
async def login_json(
    user_login: UserLogin,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    用户登录（JSON格式）
    支持用户名/手机号/邮箱登录，适用于前后端分离的API调用
    """
    # 尝试通过用户名/手机号/邮箱登录
    user = authenticate_user_by_phone_or_email(db, user_login.username, user_login.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="账号或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 更新最后登录时间和IP
    user.last_login_at = datetime.utcnow()
    client_host = request.client.host if request.client else None
    user.last_login_ip = client_host
    db.commit()

    # 创建访问令牌和刷新令牌
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id},
        expires_delta=access_token_expires
    )

    # 创建刷新令牌（有效期30天）
    refresh_token_expires = timedelta(days=30)
    refresh_token = create_refresh_token(
        data={"sub": user.username, "user_id": user.id},
        expires_delta=refresh_token_expires
    )

    # 记录登录日志
    log = Log(
        user_id=user.id,
        action="user_login",
        ip_address=client_host,
        extra_data={"login_method": "json", "username": user.username}
    )
    db.add(log)
    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """获取当前用户信息"""
    return current_user

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """
    用户登出
    前端应该删除存储的token
    """
    # 记录日志
    log = Log(
        user_id=current_user.id,
        action="user_logout",
        extra_data={"username": current_user.username}
    )
    db.add(log)
    db.commit()

    return {"message": "登出成功"}

class RefreshTokenRequest(BaseModel):
    refresh_token: str

@router.post("/refresh", response_model=Token)
async def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    刷新访问令牌
    使用刷新令牌获取新的访问令牌
    """
    # 验证刷新令牌
    token_data = verify_refresh_token(request.refresh_token)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="刷新令牌无效或已过期",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 查询用户
    user = db.query(User).filter(User.id == token_data.user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或未激活"
        )

    # 创建新的访问令牌
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id},
        expires_delta=access_token_expires
    )

    # 创建新的刷新令牌
    refresh_token_expires = timedelta(days=30)
    new_refresh_token = create_refresh_token(
        data={"sub": user.username, "user_id": user.id},
        expires_delta=refresh_token_expires
    )

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }

# ========== 验证码相关接口 ==========

@router.post("/send-code", response_model=VerificationCodeResponse)
async def send_verification_code(
    request: SendVerificationCodeRequest,
    db: Session = Depends(get_db)
):
    """
    发送验证码
    支持邮箱和手机号两种方式
    """
    logger.info(f"收到发送验证码请求: target={request.target}, type={request.type}")
    target = request.target
    code_type = request.type

    # 验证邮箱/手机号格式
    if code_type == "email":
        if not SecurityService.validate_email(target):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱格式不正确"
            )
        # 检查邮箱是否已被注册
        if db.query(User).filter(User.email == target).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该邮箱已被注册"
            )
    elif code_type == "phone":
        if not SecurityService.validate_phone(target):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="手机号格式不正确"
            )
        # 检查手机号是否已被注册
        if db.query(User).filter(User.phone == target).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该手机号已被注册"
            )

    # 发送验证码
    logger.info(f"开始发送验证码: target={target}, type={code_type}")
    try:
        success, error_msg = verification_service.send_code(db, target, code_type)
        logger.info(f"验证码发送结果: success={success}, error_msg={error_msg}")
    except Exception as e:
        logger.error(f"验证码发送异常: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"验证码发送失败: {str(e)}"
        )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=error_msg
        )

    return VerificationCodeResponse(
        message="验证码发送成功",
        expires_in=verification_service.get_expires_in()
    )

@router.post("/register-with-code", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_with_code(
    data: RegisterWithCodeRequest,
    db: Session = Depends(get_db)
):
    """
    验证码注册
    用户输入验证码后完成注册
    """
    # 验证验证码
    success, error_msg = verification_service.verify_code(
        db, data.target, data.code, data.type
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )

    # 检查用户名是否已存在
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )

    # 验证用户名格式
    if not SecurityService.validate_username(data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名格式不正确"
        )

    # 验证密码
    is_valid, msg = SecurityService.validate_password(data.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg
        )

    # 根据类型设置邮箱或手机号
    email = None
    phone = None
    if data.type == "email":
        email = data.target
    else:
        phone = data.target

    # 创建新用户
    db_user = User(
        username=data.username,
        email=email,
        phone=phone,
        password_hash=get_password_hash(data.password)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # 记录日志
    log = Log(
        user_id=db_user.id,
        action="user_register_with_code",
        extra_data={"username": data.username, "type": data.type}
    )
    db.add(log)
    db.commit()

    return db_user

# ========== 密码管理接口 ==========

@router.post("/change-password")
async def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    修改密码（需要登录）
    验证旧密码后设置新密码
    """
    # 验证旧密码
    if not verify_password(data.old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="旧密码错误"
        )

    # 验证新密码强度
    is_valid, msg = SecurityService.validate_password(data.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg
        )

    # 新密码不能与旧密码相同
    if data.old_password == data.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="新密码不能与旧密码相同"
        )

    # 更新密码
    current_user.password_hash = get_password_hash(data.new_password)
    db.commit()

    # 记录日志
    log = Log(
        user_id=current_user.id,
        action="change_password",
        extra_data={"username": current_user.username}
    )
    db.add(log)
    db.commit()

    return {"message": "密码修改成功"}

@router.post("/send-reset-code", response_model=VerificationCodeResponse)
async def send_reset_code(
    request: SendVerificationCodeRequest,
    db: Session = Depends(get_db)
):
    """
    发送重置密码验证码（无需登录）
    通过邮箱或手机号发送验证码
    """
    target = request.target
    code_type = request.type

    # 验证邮箱/手机号格式并检查是否已注册
    if code_type == "email":
        if not SecurityService.validate_email(target):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱格式不正确"
            )
        # 检查邮箱是否已注册（重置密码需要已注册的邮箱）
        if not db.query(User).filter(User.email == target).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该邮箱未注册"
            )
    elif code_type == "phone":
        if not SecurityService.validate_phone(target):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="手机号格式不正确"
            )
        # 检查手机号是否已注册
        if not db.query(User).filter(User.phone == target).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该手机号未注册"
            )

    # 发送验证码
    try:
        success, error_msg = verification_service.send_code(db, target, code_type)
    except Exception as e:
        logger.error(f"重置密码验证码发送异常: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"验证码发送失败: {str(e)}"
        )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=error_msg
        )

    return VerificationCodeResponse(
        message="验证码发送成功",
        expires_in=verification_service.get_expires_in()
    )

@router.post("/reset-password")
async def reset_password(
    data: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    重置密码（无需登录）
    验证验证码后重置密码
    """
    # 验证验证码
    success, error_msg = verification_service.verify_code(
        db, data.target, data.code, data.type
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )

    # 查找用户
    user = None
    if data.type == "email":
        user = db.query(User).filter(User.email == data.target).first()
    else:
        user = db.query(User).filter(User.phone == data.target).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户不存在"
        )

    # 验证新密码强度
    is_valid, msg = SecurityService.validate_password(data.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg
        )

    # 更新密码
    user.password_hash = get_password_hash(data.new_password)
    db.commit()

    # 记录日志
    log = Log(
        user_id=user.id,
        action="reset_password",
        extra_data={"username": user.username, "type": data.type}
    )
    db.add(log)
    db.commit()

    return {"message": "密码重置成功"}
