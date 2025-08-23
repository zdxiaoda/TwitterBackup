#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
推文翻译服务
使用OpenAI API进行推文翻译
"""

import os
import re
import openai
from typing import Optional, Dict, Any
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TranslationService:
    """推文翻译服务类"""

    def __init__(self, api_key: Optional[str] = None):
        """
        初始化翻译服务

        Args:
            api_key: OpenAI API密钥，如果为None则从环境变量获取
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API密钥未设置，请设置OPENAI_API_KEY环境变量或在初始化时传入"
            )

        # 配置OpenAI客户端
        self.client = openai.OpenAI(api_key=self.api_key)

        # 支持的目标语言
        self.supported_languages = {
            "zh": "中文",
            "en": "English",
            "ja": "日本語",
            "ko": "한국어",
            "es": "Español",
            "fr": "Français",
            "de": "Deutsch",
            "ru": "Русский",
            "ar": "العربية",
            "hi": "हिन्दी",
            "pt": "Português",
            "it": "Italiano",
        }

    def clean_tweet_content(self, content: str) -> str:
        """
        清理推文内容，移除HTML标签和特殊字符

        Args:
            content: 原始推文内容

        Returns:
            清理后的推文内容
        """
        if not content:
            return ""

        # 移除HTML标签
        content = re.sub(r"<[^>]+>", "", content)

        # 移除多余的空白字符
        content = re.sub(r"\s+", " ", content).strip()

        return content

    def translate_tweet(
        self, content: str, target_lang: str = "zh", source_lang: str = "auto"
    ) -> Dict[str, Any]:
        """
        翻译推文内容

        Args:
            content: 要翻译的推文内容
            target_lang: 目标语言代码
            source_lang: 源语言代码，'auto'表示自动检测

        Returns:
            包含翻译结果的字典
        """
        try:
            # 清理推文内容
            clean_content = self.clean_tweet_content(content)

            if not clean_content:
                return {
                    "success": False,
                    "error": "推文内容为空",
                    "original": content,
                    "translated": "",
                    "source_lang": source_lang,
                    "target_lang": target_lang,
                }

            # 获取目标语言名称
            target_lang_name = self.supported_languages.get(target_lang, "中文")

            # 构建翻译提示
            system_prompt = f"""你是一个专业的推文翻译助手。请将以下推文翻译成{target_lang_name}。

翻译要求：
1. 保持推文的原始语气和风格
2. 保留推文中的表情符号、标签和链接
3. 确保翻译准确、自然、符合目标语言的表达习惯
4. 如果是网络用语或流行语，请使用目标语言中对应的表达
5. 保持推文的简洁性和可读性

请只返回翻译结果，不要添加任何解释或额外内容。"""

            # 调用OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": clean_content},
                ],
                max_tokens=500,
                temperature=0.3,
            )

            translated_text = response.choices[0].message.content.strip()

            return {
                "success": True,
                "original": content,
                "translated": translated_text,
                "source_lang": source_lang,
                "target_lang": target_lang,
                "target_lang_name": target_lang_name,
            }

        except Exception as e:
            logger.error(f"翻译失败: {str(e)}")
            return {
                "success": False,
                "error": f"翻译失败: {str(e)}",
                "original": content,
                "translated": "",
                "source_lang": source_lang,
                "target_lang": target_lang,
            }

    def detect_language(self, content: str) -> Dict[str, Any]:
        """
        检测文本语言

        Args:
            content: 要检测的文本内容

        Returns:
            包含语言检测结果的字典
        """
        try:
            clean_content = self.clean_tweet_content(content)

            if not clean_content:
                return {
                    "success": False,
                    "error": "文本内容为空",
                    "detected_lang": "unknown",
                }

            system_prompt = """你是一个语言检测专家。请检测以下文本的语言，并返回对应的语言代码。

支持的语言代码：
- zh: 中文
- en: 英语
- ja: 日语
- ko: 韩语
- es: 西班牙语
- fr: 法语
- de: 德语
- ru: 俄语
- ar: 阿拉伯语
- hi: 印地语
- pt: 葡萄牙语
- it: 意大利语

请只返回语言代码，不要添加任何其他内容。"""

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": clean_content},
                ],
                max_tokens=10,
                temperature=0.1,
            )

            detected_lang = response.choices[0].message.content.strip().lower()

            return {
                "success": True,
                "detected_lang": detected_lang,
                "detected_lang_name": self.supported_languages.get(
                    detected_lang, "未知语言"
                ),
            }

        except Exception as e:
            logger.error(f"语言检测失败: {str(e)}")
            return {
                "success": False,
                "error": f"语言检测失败: {str(e)}",
                "detected_lang": "unknown",
            }

    def get_supported_languages(self) -> Dict[str, str]:
        """
        获取支持的语言列表

        Returns:
            语言代码到语言名称的映射字典
        """
        return self.supported_languages.copy()


# 全局翻译服务实例
_translation_service = None


def get_translation_service() -> TranslationService:
    """
    获取全局翻译服务实例

    Returns:
        翻译服务实例
    """
    global _translation_service
    if _translation_service is None:
        _translation_service = TranslationService()
    return _translation_service


def translate_tweet_content(content: str, target_lang: str = "zh") -> Dict[str, Any]:
    """
    翻译推文内容的便捷函数

    Args:
        content: 要翻译的推文内容
        target_lang: 目标语言代码

    Returns:
        翻译结果字典
    """
    service = get_translation_service()
    return service.translate_tweet(content, target_lang)


def detect_tweet_language(content: str) -> Dict[str, Any]:
    """
    检测推文语言的便捷函数

    Args:
        content: 要检测的推文内容

    Returns:
        语言检测结果字典
    """
    service = get_translation_service()
    return service.detect_language(content)
