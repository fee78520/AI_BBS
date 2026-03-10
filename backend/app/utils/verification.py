"""
验证码服务
负责验证码的生成、存储、验证
"""
import random
import string
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional, Tuple
import os
import logging

from app.models import VerificationCode
from app.schemas import VerificationCodeType
from app.utils.email_service import email_service
from app.utils.sms_service import sms_service

logger = logging.getLogger(__name__)

# 验证码配置
CODE_LENGTH = 6  # 验证码长度
CODE_EXPIRE_MINUTES = 5  # 验证码有效期（分钟）
CODE_SEND_INTERVAL = 60  # 发送间隔（秒）


class VerificationService:
    """验证码服务类"""

    @staticmethod
    def generate_code(length: int = CODE_LENGTH) -> str:
        """
        生成随机验证码

        Args:
            length: 验证码长度

        Returns:
            str: 验证码
        """
        return ''.join(random.choices(string.digits, k=length))

    @staticmethod
    def can_send(db: Session, target: str) -> Tuple[bool, Optional[str]]:
        """
        检查是否可以发送验证码

        Args:
            db: 数据库会话
            target: 邮箱或手机号

        Returns:
            Tuple[bool, Optional[str]]: (是否可以发送, 错误信息)
        """
        # 查询最近一条验证码记录
        latest_code = db.query(VerificationCode).filter(
            VerificationCode.target == target
        ).order_by(VerificationCode.created_at.desc()).first()

        if latest_code:
            # 检查发送间隔
            time_passed = (datetime.utcnow() - latest_code.created_at).total_seconds()
            if time_passed < CODE_SEND_INTERVAL:
                remaining = int(CODE_SEND_INTERVAL - time_passed)
                return False, f"请等待 {remaining} 秒后再试"

        return True, None

    @staticmethod
    def send_code(db: Session, target: str, code_type: str) -> Tuple[bool, Optional[str]]:
        """
        发送验证码

        Args:
            db: 数据库会话
            target: 邮箱或手机号
            code_type: 验证码类型 (email/phone)

        Returns:
            Tuple[bool, Optional[str]]: (是否成功, 错误信息)
        """
        logger.info(f"[VerificationService] send_code 开始: target={target}, type={code_type}")
        
        # 检查是否可以发送
        can_send, error_msg = VerificationService.can_send(db, target)
        logger.info(f"[VerificationService] can_send 检查结果: can_send={can_send}, error_msg={error_msg}")
        if not can_send:
            return False, error_msg

        # 生成验证码
        code = VerificationService.generate_code()
        logger.info(f"[VerificationService] 生成验证码: {code}")

        # 设置过期时间
        expires_at = datetime.utcnow() + timedelta(minutes=CODE_EXPIRE_MINUTES)

        # 确定验证码类型
        vtype = VerificationCodeType.EMAIL if code_type == "email" else VerificationCodeType.PHONE

        # 保存到数据库
        verification_code = VerificationCode(
            target=target,
            code=code,
            type=vtype,
            expires_at=expires_at
        )
        db.add(verification_code)
        db.commit()
        logger.info(f"[VerificationService] 验证码已保存到数据库")

        # 发送验证码
        logger.info(f"[VerificationService] 开始调用发送服务: type={code_type}")
        if code_type == "email":
            success = email_service.send_verification_code(target, code)
        else:
            success = sms_service.send_verification_code(target, code)
        logger.info(f"[VerificationService] 发送服务返回: success={success}")

        if success:
            logger.info(f"验证码发送成功: {target}, 类型: {code_type}")
            return True, None
        else:
            logger.error(f"验证码发送失败: {target}, 类型: {code_type}")
            return False, "验证码发送失败，请稍后重试"

    @staticmethod
    def verify_code(db: Session, target: str, code: str, code_type: str) -> Tuple[bool, Optional[str]]:
        """
        验证验证码

        Args:
            db: 数据库会话
            target: 邮箱或手机号
            code: 验证码
            code_type: 验证码类型 (email/phone)

        Returns:
            Tuple[bool, Optional[str]]: (是否验证成功, 错误信息)
        """
        # 确定验证码类型
        vtype = VerificationCodeType.EMAIL if code_type == "email" else VerificationCodeType.PHONE

        # 查询验证码记录
        verification = db.query(VerificationCode).filter(
            and_(
                VerificationCode.target == target,
                VerificationCode.code == code,
                VerificationCode.type == vtype,
                VerificationCode.used == False,
                VerificationCode.expires_at > datetime.utcnow()
            )
        ).first()

        if not verification:
            return False, "验证码无效或已过期"

        # 标记为已使用
        verification.used = True
        db.commit()

        logger.info(f"验证码验证成功: {target}")
        return True, None

    @staticmethod
    def get_expires_in() -> int:
        """获取验证码有效期（秒）"""
        return CODE_EXPIRE_MINUTES * 60


# 创建全局实例
verification_service = VerificationService()
