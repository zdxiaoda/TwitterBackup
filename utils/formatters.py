"""
文本格式化工具类
提供各种文本格式化功能
"""

import re
from datetime import datetime
from typing import List, Optional
from urllib.parse import urlparse


class TextFormatter:
    """文本格式化器"""

    @staticmethod
    def format_date(date_str: str) -> str:
        """格式化日期显示"""
        try:
            if isinstance(date_str, str):
                dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            else:
                dt = date_str

            now = datetime.now()
            diff = now - dt.replace(tzinfo=None) if dt.tzinfo else now - dt

            if diff.days > 0:
                if diff.days == 1:
                    return "昨天"
                elif diff.days < 7:
                    return f"{diff.days}天前"
                else:
                    return dt.strftime("%m月%d日")
            else:
                hours = diff.seconds // 3600
                if hours > 0:
                    return f"{hours}小时前"
                else:
                    minutes = diff.seconds // 60
                    if minutes > 0:
                        return f"{minutes}分钟前"
                    else:
                        return "刚刚"
        except:
            return date_str

    @staticmethod
    def format_number(num: int) -> str:
        """格式化数字显示"""
        if num < 1000:
            return str(num)
        elif num < 10000:
            return f"{num/1000:.1f}K".replace(".0", "")
        elif num < 1000000:
            return f"{num/1000:.0f}K"
        else:
            return f"{num/1000000:.1f}M".replace(".0", "")

    @staticmethod
    def extract_hashtags(text: str) -> List[str]:
        """提取文本中的标签"""
        hashtags = re.findall(r"#(\w+)", text)
        return list(set(hashtags))

    @staticmethod
    def extract_links(text: str) -> List[str]:
        """提取文本中的链接"""
        url_pattern = r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
        return re.findall(url_pattern, text)

    @staticmethod
    def format_tweet_content(content: str) -> str:
        """格式化推文内容"""
        if not content:
            return ""

        # 处理链接
        content = re.sub(
            r"(https?://[^\s]+)",
            r'<a href="\1" class="tco-link" target="_blank">\1</a>',
            content,
        )

        # 处理标签
        content = re.sub(
            r"#(\w+)", r'<a href="/search?q=%23\1" class="hashtag">#\1</a>', content
        )

        # 处理@用户
        content = re.sub(
            r"@(\w+)", r'<a href="/user/\1" class="username-link">@\1</a>', content
        )

        return content

    @staticmethod
    def truncate_text(text: str, max_length: int = 100) -> str:
        """截断文本"""
        if len(text) <= max_length:
            return text
        return text[: max_length - 3] + "..."

    @staticmethod
    def clean_html_tags(text: str) -> str:
        """清理HTML标签"""
        clean = re.compile("<.*?>")
        return re.sub(clean, "", text)

    @staticmethod
    def is_valid_url(url: str) -> bool:
        """验证URL是否有效"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False

    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """格式化文件大小"""
        if size_bytes == 0:
            return "0B"

        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1

        return f"{size_bytes:.1f}{size_names[i]}"

    @staticmethod
    def format_duration(seconds: int) -> str:
        """格式化时长"""
        if seconds < 60:
            return f"{seconds}秒"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"{minutes}分钟"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}小时{minutes}分钟"
