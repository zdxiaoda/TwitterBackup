#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
推文翻译服务
支持多种翻译API
"""

import os
import re
import json
import requests
import hashlib
import time
from typing import Optional, Dict, Any
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TranslationService:
    """推文翻译服务类"""

    def __init__(
        self,
        service_type: str = "google",
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        api_url: Optional[str] = None,
        openai_model: str = "gpt-3.5-turbo",
    ):
        """
        初始化翻译服务

        Args:
            service_type: 翻译服务类型 (google, baidu, youdao, deepl)
            api_key: API密钥
            api_secret: API密钥（用于百度翻译等需要appid+secret的服务）
            api_url: 自定义API地址
        """
        self.service_type = service_type
        self.api_key = api_key
        self.api_secret = api_secret
        self.api_url = api_url
        self.openai_model = openai_model

        if not self.api_key:
            raise ValueError("API密钥未设置")

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

            # 根据服务类型调用不同的翻译方法
            if self.service_type == "openai":
                translated_text = self._translate_with_openai(
                    clean_content, target_lang, source_lang
                )
            elif self.service_type == "google":
                translated_text = self._translate_with_google(
                    clean_content, target_lang, source_lang
                )
            elif self.service_type == "baidu":
                translated_text = self._translate_with_baidu(
                    clean_content, target_lang, source_lang
                )
            elif self.service_type == "youdao":
                translated_text = self._translate_with_youdao(
                    clean_content, target_lang, source_lang
                )
            elif self.service_type == "deepl":
                translated_text = self._translate_with_deepl(
                    clean_content, target_lang, source_lang
                )
            else:
                return {
                    "success": False,
                    "error": f"不支持的翻译服务: {self.service_type}",
                    "original": content,
                    "translated": "",
                    "source_lang": source_lang,
                    "target_lang": target_lang,
                }

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

    def _translate_with_openai(
        self, content: str, target_lang: str, source_lang: str
    ) -> str:
        """使用OpenAI翻译API"""
        import openai

        # 使用自定义URL或默认URL
        base_url = self.api_url if self.api_url else "https://api.openai.com/v1"
        client = openai.OpenAI(api_key=self.api_key, base_url=base_url)

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

        response = client.chat.completions.create(
            model=self.openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content},
            ],
            max_tokens=500,
            temperature=0.3,
        )

        return response.choices[0].message.content.strip()

    def _translate_with_google(
        self, content: str, target_lang: str, source_lang: str
    ) -> str:
        """使用Google翻译API"""
        # 使用自定义URL或默认URL
        url = (
            self.api_url
            if self.api_url
            else "https://translation.googleapis.com/language/translate/v2"
        )
        params = {
            "key": self.api_key,
            "q": content,
            "target": target_lang,
            "source": source_lang if source_lang != "auto" else None,
            "format": "text",
        }

        response = requests.post(url, data=params)
        response.raise_for_status()

        result = response.json()
        return result["data"]["translations"][0]["translatedText"]

    def _translate_with_baidu(
        self, content: str, target_lang: str, source_lang: str
    ) -> str:
        """使用百度翻译API"""
        # 使用自定义URL或默认URL
        url = (
            self.api_url
            if self.api_url
            else "https://fanyi-api.baidu.com/api/trans/vip/translate"
        )

        # 百度翻译的语言代码映射
        lang_map = {
            "zh": "zh",
            "en": "en",
            "ja": "jp",
            "ko": "kor",
            "es": "spa",
            "fr": "fra",
            "de": "de",
            "ru": "ru",
        }

        salt = str(int(time.time()))
        sign = self.api_key + content + salt + self.api_secret
        sign = hashlib.md5(sign.encode()).hexdigest()

        params = {
            "q": content,
            "from": lang_map.get(source_lang, "auto"),
            "to": lang_map.get(target_lang, "zh"),
            "appid": self.api_key,
            "salt": salt,
            "sign": sign,
        }

        response = requests.get(url, params=params)
        response.raise_for_status()

        result = response.json()
        if "error_code" in result:
            raise Exception(f"百度翻译错误: {result.get('error_msg', '未知错误')}")

        return result["trans_result"][0]["dst"]

    def _translate_with_youdao(
        self, content: str, target_lang: str, source_lang: str
    ) -> str:
        """使用有道翻译API"""
        # 使用自定义URL或默认URL
        url = self.api_url if self.api_url else "https://openapi.youdao.com/api"

        salt = str(int(time.time()))
        input_text = (
            content
            if len(content) <= 20
            else content[:10] + str(len(content)) + content[-10:]
        )
        sign = self.api_key + input_text + salt + self.api_secret
        sign = hashlib.sha256(sign.encode()).hexdigest()

        params = {
            "q": content,
            "from": source_lang if source_lang != "auto" else "auto",
            "to": target_lang,
            "appKey": self.api_key,
            "salt": salt,
            "sign": sign,
            "signType": "v3",
        }

        response = requests.post(url, data=params)
        response.raise_for_status()

        result = response.json()
        if result.get("errorCode") != "0":
            raise Exception(f"有道翻译错误: {result.get('errorMsg', '未知错误')}")

        return result["translation"][0]

    def _translate_with_deepl(
        self, content: str, target_lang: str, source_lang: str
    ) -> str:
        """使用DeepL翻译API"""
        # 使用自定义URL或默认URL
        url = (
            self.api_url if self.api_url else "https://api-free.deepl.com/v2/translate"
        )

        # DeepL的语言代码映射
        lang_map = {
            "zh": "ZH",
            "en": "EN",
            "ja": "JA",
            "ko": "KO",
            "es": "ES",
            "fr": "FR",
            "de": "DE",
            "ru": "RU",
        }

        headers = {
            "Authorization": f"DeepL-Auth-Key {self.api_key}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        data = {
            "text": content,
            "target_lang": lang_map.get(target_lang, "ZH"),
            "source_lang": (
                lang_map.get(source_lang, "AUTO") if source_lang != "auto" else "AUTO"
            ),
        }

        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()

        result = response.json()
        return result["translations"][0]["text"]

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

            # 对于非OpenAI服务，使用简单的语言检测规则
            if self.service_type != "openai":
                detected_lang = self._simple_language_detection(clean_content)
                return {
                    "success": True,
                    "detected_lang": detected_lang,
                    "detected_lang_name": self.supported_languages.get(
                        detected_lang, "未知语言"
                    ),
                }

            # 对于OpenAI服务，使用原来的方法
            import openai

            # 使用自定义URL或默认URL
            base_url = self.api_url if self.api_url else "https://api.openai.com/v1"
            client = openai.OpenAI(api_key=self.api_key, base_url=base_url)

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

            response = client.chat.completions.create(
                model=self.openai_model,
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

    def _simple_language_detection(self, content: str) -> str:
        """简单的语言检测规则"""
        # 检测中文字符
        if re.search(r"[\u4e00-\u9fff]", content):
            return "zh"

        # 检测日文字符
        if re.search(r"[\u3040-\u309f\u30a0-\u30ff]", content):
            return "ja"

        # 检测韩文字符
        if re.search(r"[\uac00-\ud7af]", content):
            return "ko"

        # 检测阿拉伯文字符
        if re.search(r"[\u0600-\u06ff]", content):
            return "ar"

        # 检测印地文字符
        if re.search(r"[\u0900-\u097f]", content):
            return "hi"

        # 检测俄文字符
        if re.search(r"[\u0400-\u04ff]", content):
            return "ru"

        # 默认返回英语
        return "en"

    def get_supported_languages(self) -> Dict[str, str]:
        """
        获取支持的语言列表

        Returns:
            语言代码到语言名称的映射字典
        """
        return self.supported_languages.copy()


# 全局翻译服务实例
_translation_service = None


def get_translation_service(
    service_type: str = "google",
    api_key: str = None,
    api_secret: str = None,
    api_url: str = None,
    openai_model: str = "gpt-3.5-turbo",
) -> TranslationService:
    """
    获取全局翻译服务实例

    Args:
        service_type: 翻译服务类型
        api_key: API密钥
        api_secret: API密钥
        api_url: 自定义API地址

    Returns:
        翻译服务实例
    """
    global _translation_service
    if _translation_service is None:
        _translation_service = TranslationService(
            service_type=service_type,
            api_key=api_key,
            api_secret=api_secret,
            api_url=api_url,
            openai_model=openai_model,
        )
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
