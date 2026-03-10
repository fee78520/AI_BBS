"""
短信发送服务
开发环境使用模拟模式，验证码输出到控制台
生产环境可接入阿里云/腾讯云短信服务
"""
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


class SMSService:
    """短信发送服务类"""

    def __init__(self):
        """初始化短信服务配置"""
        # 阿里云短信配置
        self.aliyun_access_key = os.getenv("ALIYUN_ACCESS_KEY", "")
        self.aliyun_access_secret = os.getenv("ALIYUN_ACCESS_SECRET", "")
        self.aliyun_sign_name = os.getenv("ALIYUN_SIGN_NAME", "")
        self.aliyun_template_code = os.getenv("ALIYUN_TEMPLATE_CODE", "")

        # 腾讯云短信配置
        self.tencent_secret_id = os.getenv("TENCENT_SECRET_ID", "")
        self.tencent_secret_key = os.getenv("TENCENT_SECRET_KEY", "")
        self.tencent_app_id = os.getenv("TENCENT_APP_ID", "")
        self.tencent_sign_name = os.getenv("TENCENT_SIGN_NAME", "")
        self.tencent_template_id = os.getenv("TENCENT_TEMPLATE_ID", "")

        # 模拟模式（开发环境）
        self.mock_mode = os.getenv("SMS_MOCK_MODE", "true").lower() == "true"

    def send_verification_code(self, phone: str, code: str) -> bool:
        """
        发送验证码短信

        Args:
            phone: 手机号
            code: 验证码

        Returns:
            bool: 发送是否成功
        """
        # 模拟模式：直接打印验证码
        if self.mock_mode:
            return self._mock_send(phone, code)

        # 阿里云短信
        if self.aliyun_access_key and self.aliyun_access_secret:
            return self._send_via_aliyun(phone, code)

        # 腾讯云短信
        if self.tencent_secret_id and self.tencent_secret_key:
            return self._send_via_tencent(phone, code)

        # 默认使用模拟模式
        logger.warning("未配置短信服务商，使用模拟模式")
        return self._mock_send(phone, code)

    def _mock_send(self, phone: str, code: str) -> bool:
        """
        模拟发送短信（开发测试用）

        Args:
            phone: 手机号
            code: 验证码

        Returns:
            bool: 始终返回True
        """
        logger.info(f"=" * 50)
        logger.info(f"[模拟短信] 收件人: {phone}")
        logger.info(f"[模拟短信] 验证码: {code}")
        logger.info(f"[模拟短信] 有效期: 5分钟")
        logger.info(f"=" * 50)
        print(f"\n{'='*50}")
        print(f"[模拟短信] 手机号: {phone}")
        print(f"[模拟短信] 验证码: {code}")
        print(f"[模拟短信] 有效期: 5分钟")
        print(f"{'='*50}\n")
        return True

    def _send_via_aliyun(self, phone: str, code: str) -> bool:
        """
        通过阿里云短信服务发送

        Args:
            phone: 手机号
            code: 验证码

        Returns:
            bool: 发送是否成功
        """
        try:
            from aliyunsdkcore.client import AcsClient
            from aliyunsdkcore.acs_exception.exceptions import ServerException
            from aliyunsdkdysmsapi.request.v20170525 import SendSmsRequest

            client = AcsClient(self.aliyun_access_key, self.aliyun_access_secret, 'cn-hangzhou')

            request = SendSmsRequest.SendSmsRequest()
            request.set_PhoneNumbers(phone)
            request.set_SignName(self.aliyun_sign_name)
            request.set_TemplateCode(self.aliyun_template_code)
            request.set_TemplateParam(f'{{"code":"{code}"}}')

            response = client.do_action_with_exception(request)

            import json
            result = json.loads(response.decode('utf-8'))
            if result.get('Code') == 'OK':
                logger.info(f"阿里云短信发送成功: {phone}")
                return True
            else:
                logger.error(f"阿里云短信发送失败: {result}")
                return False

        except ImportError:
            logger.warning("未安装阿里云SDK，请运行: pip install aliyun-python-sdk-core aliyun-python-sdk-dysmsapi")
            return self._mock_send(phone, code)
        except Exception as e:
            logger.error(f"阿里云短信发送异常: {str(e)}")
            return False

    def _send_via_tencent(self, phone: str, code: str) -> bool:
        """
        通过腾讯云短信服务发送

        Args:
            phone: 手机号
            code: 验证码

        Returns:
            bool: 发送是否成功
        """
        try:
            from tencentcloud.common import credential
            from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
            from tencentcloud.sms.v20210111 import sms_client, models

            cred = credential.Credential(self.tencent_secret_id, self.tencent_secret_key)
            client = sms_client.SmsClient(cred, "ap-guangzhou")

            req = models.SendSmsRequest()
            req.SmsSdkAppId = self.tencent_app_id
            req.SignName = self.tencent_sign_name
            req.TemplateId = self.tencent_template_id
            req.PhoneNumberSet = [f"+86{phone}"]
            req.TemplateParamSet = [code]

            response = client.SendSms(req)

            if response.SendStatusSet and response.SendStatusSet[0].Code == "Ok":
                logger.info(f"腾讯云短信发送成功: {phone}")
                return True
            else:
                logger.error(f"腾讯云短信发送失败: {response}")
                return False

        except ImportError:
            logger.warning("未安装腾讯云SDK，请运行: pip install tencentcloud-sdk-python")
            return self._mock_send(phone, code)
        except Exception as e:
            logger.error(f"腾讯云短信发送异常: {str(e)}")
            return False


# 创建全局实例
sms_service = SMSService()
