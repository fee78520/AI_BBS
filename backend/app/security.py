"""
BBS论坛系统 - 安全防护模块
本文件负责：
1. 敏感词过滤
2. XSS攻击防护
3. 内容验证
4. 垃圾内容检测
5. 数据格式验证
"""
from typing import List, Optional, Tuple
import re
from fastapi import HTTPException, status

# ========== 敏感词列表 ==========
# 可根据需要扩展此列表
# 建议从数据库或配置文件中读取
SENSITIVE_WORDS = [
    "敏感词1", "敏感词2", "敏感词3",
    "违法", "诈骗", "赌博", "色情",
    "暴力", "毒品", "恐怖", "邪教",
]

class SecurityService:
    """安全服务类 - 提供所有安全相关的静态方法"""

    # ========== 敏感词处理 ==========

    @staticmethod
    def check_sensitive_word(content: str) -> Tuple[bool, Optional[str]]:
        """
        检查内容中是否包含敏感词

        参数:
            content: 要检查的文本内容

        返回:
            Tuple[bool, Optional[str]]:
                - 第一个元素: 是否包含敏感词
                - 第二个元素: 如果包含，返回敏感词；否则返回None

        示例:
            >>> contains, word = SecurityService.check_sensitive_word("测试违法内容")
            >>> # contains = True, word = "违法"
        """
        for word in SENSITIVE_WORDS:
            if word in content:
                return True, word
        return False, None

    @staticmethod
    def filter_sensitive_words(content: str) -> str:
        """
        过滤敏感词，替换为***

        参数:
            content: 要过滤的文本内容

        返回:
            str: 过滤后的内容，敏感词被替换为***

        示例:
            >>> filtered = SecurityService.filter_sensitive_words("测试违法内容")
            >>> # filtered = "测试***内容"
        """
        filtered_content = content
        for word in SENSITIVE_WORDS:
            filtered_content = filtered_content.replace(word, "***")
        return filtered_content

    # ========== XSS防护 ==========

    @staticmethod
    def check_xss(content: str) -> bool:
        """
        检查XSS攻击（跨站脚本攻击）

        参数:
            content: 要检查的HTML内容

        返回:
            bool: 是否检测到XSS攻击代码

        检测内容:
            - script标签
            - javascript:协议
            - 事件处理器（onclick, onerror等）
            - iframe, object, embed等危险标签
        """
        xss_patterns = [
            r'<script.*?>.*?</script>',  # script标签
            r'javascript:',  # javascript协议
            r'on\w+\s*=',  # 事件处理器
            r'<iframe.*?>.*?</iframe>',  # iframe标签
            r'<object.*?>.*?</object>',  # object标签
            r'<embed.*?>.*?</embed>',  # embed标签
        ]
        for pattern in xss_patterns:
            if re.search(pattern, content, re.IGNORECASE | re.DOTALL):
                return True
        return False

    @staticmethod
    def sanitize_html(content: str) -> str:
        """
        清理HTML内容，移除危险标签

        参数:
            content: 要清理的HTML内容

        返回:
            str: 清理后的安全HTML内容

        移除内容:
            - script标签
            - iframe, object, embed标签
            - javascript:协议
            - 事件处理器
        """
        dangerous_tags = [
            '<script', '</script>',
            '<iframe', '</iframe>',
            '<object', '</object>',
            '<embed', '</embed>',
            'javascript:',
            'onclick=', 'onerror=', 'onload=',
        ]
        sanitized = content
        for tag in dangerous_tags:
            sanitized = sanitized.replace(tag, '')
        return sanitized

    # ========== 数据格式验证 ==========

    @staticmethod
    def validate_username(username: str) -> bool:
        """
        验证用户名格式

        参数:
            username: 用户名

        返回:
            bool: 用户名格式是否有效

        规则:
            - 长度3-50个字符
            - 只能包含字母、数字、下划线、中文
        """
        if len(username) < 3 or len(username) > 50:
            return False
        if not re.match(r'^[a-zA-Z0-9_\u4e00-\u9fa5]+$', username):
            return False
        return True

    @staticmethod
    def validate_email(email: str) -> bool:
        """
        验证邮箱格式

        参数:
            email: 邮箱地址

        返回:
            bool: 邮箱格式是否有效
        """
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(email_pattern, email) is not None

    @staticmethod
    def validate_password(password: str) -> Tuple[bool, str]:
        """
        验证密码强度

        参数:
            password: 密码

        返回:
            Tuple[bool, str]:
                - 第一个元素: 密码是否有效
                - 第二个元素: 错误信息（如果无效）

        规则:
            - 长度6-50个字符
        """
        if len(password) < 6:
            return False, "密码长度至少6位"
        if len(password) > 50:
            return False, "密码长度不能超过50位"
        return True, ""

    @staticmethod
    def validate_phone(phone: str) -> bool:
        """
        验证手机号格式（中国）

        参数:
            phone: 手机号

        返回:
            bool: 手机号格式是否有效

        规则:
            - 以1开头
            - 第二位3-9
            - 总共11位数字
        """
        phone_pattern = r'^1[3-9]\d{9}$'
        return re.match(phone_pattern, phone) is not None

    # ========== 垃圾内容检测 ==========

    @staticmethod
    def check_content_spam(content: str, user_history: List[str] = None) -> bool:
        """
        检查内容是否为垃圾/灌水

        参数:
            content: 要检查的内容
            user_history: 用户历史内容列表（可选）

        返回:
            bool: 是否为垃圾内容

        检测规则:
            - 内容过短（<2个字符）
            - 重复字符过多（>70%相同）
            - 与历史内容重复
        """
        # 检查内容长度
        if len(content) < 2:
            return True

        # 检查重复字符
        if len(set(content)) < len(content) * 0.3:
            return True

        # 检查历史内容（如果提供）
        if user_history:
            for history_content in user_history[-5:]:  # 检查最近5条
                if content == history_content:
                    return True

        return False

    # ========== 内容验证 ==========

    @staticmethod
    def validate_post_title(title: str) -> Tuple[bool, str]:
        """
        验证帖子标题

        参数:
            title: 帖子标题

        返回:
            tuple[bool, str]:
                - 第一个元素: 标题是否有效
                - 第二个元素: 错误信息（如果无效）

        规则:
            - 长度1-200个字符
            - 不包含敏感词
        """
        if len(title) < 1 or len(title) > 200:
            return False, "标题长度必须在1-200个字符之间"

        # 检查敏感词
        has_sensitive, word = SecurityService.check_sensitive_word(title)
        if has_sensitive:
            return False, f"标题包含敏感词: {word}"

        return True, ""

    @staticmethod
    def validate_post_content(content: str) -> Tuple[bool, str]:
        """
        验证帖子内容

        参数:
            content: 帖子内容

        返回:
            Tuple[bool, str]:
                - 第一个元素: 内容是否有效
                - 第二个元素: 错误信息（如果无效）

        规则:
            - 长度1-100000个字符
            - 不包含敏感词
            - 不包含XSS代码
        """
        if len(content) < 1:
            return False, "内容不能为空"

        if len(content) > 100000:
            return False, "内容长度不能超过100000个字符"

        # 检查敏感词
        has_sensitive, word = SecurityService.check_sensitive_word(content)
        if has_sensitive:
            return False, f"内容包含敏感词: {word}"

        # 检查XSS
        if SecurityService.check_xss(content):
            return False, "内容包含不安全的HTML标签"

        return True, ""

    # ========== 内容提取 ==========

    @staticmethod
    def extract_mentions(content: str) -> List[str]:
        """
        从内容中提取@用户名

        参数:
            content: 文本内容

        返回:
            List[str]: 提取到的用户名列表（已去重）

        示例:
            >>> mentions = SecurityService.extract_mentions("@user1 测试 @user2")
            >>> # mentions = ["user1", "user2"]
        """
        mention_pattern = r'@([a-zA-Z0-9_\u4e00-\u9fa5]+)'
        mentions = re.findall(mention_pattern, content)
        return list(set(mentions))  # 去重

    @staticmethod
    def extract_urls(content: str) -> List[str]:
        """
        从内容中提取URL

        参数:
            content: 文本内容

        返回:
            List[str]: 提取到的URL列表

        示例:
            >>> urls = SecurityService.extract_urls("访问 https://example.com")
            >>> # urls = ["https://example.com"]
        """
        url_pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
        return re.findall(url_pattern, content)

    # ========== 验证码生成 ==========

    @staticmethod
    def generate_captcha_code(length: int = 6) -> str:
        """
        生成验证码

        参数:
            length: 验证码长度（默认6位）

        返回:
            str: 生成的验证码（包含数字和大写字母）

        示例:
            >>> code = SecurityService.generate_captcha_code(6)
            >>> # code = "A1B2C3"
        """
        import random
        import string
        chars = string.digits + string.ascii_uppercase
        return ''.join(random.choice(chars) for _ in range(length))

