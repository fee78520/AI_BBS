"""
邮件发送服务
支持SMTP协议发送邮件
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import os
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """邮件发送服务类"""

    def __init__(self):
        """初始化邮件服务配置"""
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.example.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "465"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.smtp_ssl = os.getenv("SMTP_SSL", "true").lower() == "true"
        self.from_email = os.getenv("FROM_EMAIL", self.smtp_user)
        self.from_name = os.getenv("FROM_NAME", "BBS论坛")

    def send_verification_code(self, to_email: str, code: str) -> bool:
        """
        发送验证码邮件

        Args:
            to_email: 收件人邮箱
            code: 验证码

        Returns:
            bool: 发送是否成功
        """
        subject = f"【{self.from_name}】邮箱验证码"
        content = f"""
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; font-family: Arial, sans-serif;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0; text-align: center;">{self.from_name}</h1>
            </div>
            <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px;">
                <p style="font-size: 16px; color: #333;">您好！</p>
                <p style="font-size: 16px; color: #333;">您正在注册{self.from_name}账号，验证码如下：</p>
                <div style="background: #fff; border: 2px dashed #667eea; border-radius: 8px; padding: 20px; text-align: center; margin: 20px 0;">
                    <span style="font-size: 32px; font-weight: bold; color: #667eea; letter-spacing: 8px;">{code}</span>
                </div>
                <p style="font-size: 14px; color: #999;">验证码有效期为5分钟，请尽快完成验证。</p>
                <p style="font-size: 14px; color: #999;">如果您没有进行此操作，请忽略此邮件。</p>
                <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                <p style="font-size: 12px; color: #999; text-align: center;">
                    此邮件由系统自动发送，请勿回复。
                </p>
            </div>
        </div>
        """
        return self._send_email(to_email, subject, content)

    def _send_email(self, to_email: str, subject: str, content: str, html: bool = True) -> bool:
        """
        发送邮件（内部方法）

        Args:
            to_email: 收件人邮箱
            subject: 邮件主题
            content: 邮件内容
            html: 是否为HTML格式

        Returns:
            bool: 发送是否成功
        """
        try:
            logger.info(f"self.smtp_user: {self.smtp_user}, self.smtp_password: {self.smtp_password}")
            # 开发模式：仅打印日志
            if not self.smtp_user or not self.smtp_password:
                logger.warning(f"[开发模式] 邮件未发送，验证码: {content}")
                logger.info(f"[模拟邮件] 收件人: {to_email}, 主题: {subject}")
                # 从内容中提取验证码用于显示
                import re
                code_match = re.search(r'letter-spacing: 8px;">(\d+)</span>', content)
                if code_match:
                    logger.info(f"[模拟邮件] 验证码: {code_match.group(1)}")
                return True
            logger.info(f"self.smtp_user: {self.smtp_user}, "
            f"self.smtp_password: {self.smtp_password}, "
            f"self.smtp_host: {self.smtp_host}, "
            f"self.smtp_port: {self.smtp_port}, "
            f"self.smtp_ssl: {self.smtp_ssl}, "
            f"self.from_email: {self.from_email}, "
            f"self.from_name: {self.from_name}, "
            f"to_email: {to_email}")
            # 创建邮件对象
            msg = MIMEMultipart()
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject

            # 添加邮件内容
            if html:
                msg.attach(MIMEText(content, 'html', 'utf-8'))
            else:
                msg.attach(MIMEText(content, 'plain', 'utf-8'))

            # 发送邮件
            if self.smtp_ssl:
                server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port)
            else:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                server.starttls()

            server.login(self.smtp_user, self.smtp_password)
            server.sendmail(self.from_email, to_email, msg.as_string())
            server.quit()

            logger.info(f"邮件发送成功: {to_email}")
            return True

        except Exception as e:
            logger.error(f"邮件发送失败: {str(e)}")
            return False


# 创建全局实例
email_service = EmailService()
