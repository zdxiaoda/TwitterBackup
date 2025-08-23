#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Twitter数据处理脚本
功能：
1. 读取twitter-meta文件夹中的所有JSON文件
2. 将数据保存到SQLite数据库
3. 检查img文件夹中的图片/视频文件
4. 下载profile_banner和profile_image到avatar文件夹
"""

import json
import sqlite3
import os
import requests
import hashlib
from pathlib import Path
from urllib.parse import urlparse
import time
from typing import Dict, List, Optional
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TwitterDataProcessor:
    def __init__(self, base_path: str):
        """
        初始化处理器

        Args:
            base_path: 包含twitter-meta、img、avatar文件夹的基础路径
        """
        self.base_path = Path(base_path)
        self.twitter_meta_path = self.base_path / "twitter-meta"
        self.img_path = self.base_path / "img"
        self.avatar_path = self.base_path / "avatar"
        self.db_path = self.base_path / "twitter_data.db"

        # 确保文件夹存在
        self.avatar_path.mkdir(exist_ok=True)

        # 初始化数据库
        self.init_database()

        # 用于跟踪已下载的图片，避免重复下载
        self.downloaded_images = set()
        self.load_downloaded_images()

    def load_downloaded_images(self):
        """加载已下载的图片记录"""
        record_file = self.avatar_path / "downloaded_images.txt"
        if record_file.exists():
            with open(record_file, "r", encoding="utf-8") as f:
                for line in f:
                    self.downloaded_images.add(line.strip())

    def save_downloaded_images(self):
        """保存已下载的图片记录"""
        record_file = self.avatar_path / "downloaded_images.txt"
        with open(record_file, "w", encoding="utf-8") as f:
            for img_hash in self.downloaded_images:
                f.write(f"{img_hash}\n")

    def init_database(self):
        """初始化SQLite数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 创建推文表
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tweets (
                tweet_id INTEGER PRIMARY KEY,
                retweet_id INTEGER,
                quote_id INTEGER,
                reply_id INTEGER,
                conversation_id INTEGER,
                source_id INTEGER,
                date TEXT,
                lang TEXT,
                source TEXT,
                sensitive BOOLEAN,
                sensitive_flags TEXT,
                favorite_count INTEGER,
                quote_count INTEGER,
                reply_count INTEGER,
                retweet_count INTEGER,
                bookmark_count INTEGER,
                view_count INTEGER,
                content TEXT,
                quote_by TEXT,
                count INTEGER,
                category TEXT,
                subcategory TEXT,
                media_files TEXT,
                author_id INTEGER,
                user_id INTEGER,
                hashtags TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (author_id) REFERENCES users (user_id),
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """
        )

        # 检查是否需要升级数据库（添加新字段）
        self.upgrade_database(cursor)

        # 创建用户表
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                name TEXT,
                nick TEXT,
                location TEXT,
                date TEXT,
                verified BOOLEAN,
                protected BOOLEAN,
                profile_banner TEXT,
                profile_image TEXT,
                favourites_count INTEGER,
                followers_count INTEGER,
                friends_count INTEGER,
                listed_count INTEGER,
                media_count INTEGER,
                statuses_count INTEGER,
                description TEXT,
                url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # 创建媒体文件表
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS media_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tweet_id INTEGER,
                file_name TEXT,
                file_type TEXT,
                file_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (tweet_id) REFERENCES tweets (tweet_id)
            )
        """
        )

        conn.commit()
        conn.close()
        logger.info("数据库初始化完成")

    def upgrade_database(self, cursor):
        """升级数据库结构，添加新字段"""
        try:
            # 检查是否需要添加新字段
            cursor.execute("PRAGMA table_info(tweets)")
            columns = [column[1] for column in cursor.fetchall()]

            # 添加新字段（如果不存在）
            if "author_id" not in columns:
                cursor.execute("ALTER TABLE tweets ADD COLUMN author_id INTEGER")
                logger.info("添加 author_id 字段")

            if "user_id" not in columns:
                cursor.execute("ALTER TABLE tweets ADD COLUMN user_id INTEGER")
                logger.info("添加 user_id 字段")

            if "hashtags" not in columns:
                cursor.execute("ALTER TABLE tweets ADD COLUMN hashtags TEXT")
                logger.info("添加 hashtags 字段")

        except Exception as e:
            logger.warning(f"数据库升级过程中出现警告: {e}")

    def get_media_files(self, tweet_id: int) -> List[str]:
        """
        获取指定推文的媒体文件列表

        Args:
            tweet_id: 推文ID

        Returns:
            媒体文件列表
        """
        media_files = []
        if not self.img_path.exists():
            return media_files

        # 查找所有以tweet_id开头的文件
        for file_path in self.img_path.glob(f"{tweet_id}_*"):
            if file_path.is_file():
                media_files.append(file_path.name)

        return sorted(media_files)

    def download_image(self, url: str, filename: str) -> bool:
        """
        下载图片到avatar文件夹

        Args:
            url: 图片URL
            filename: 保存的文件名

        Returns:
            是否下载成功
        """
        # 计算URL的哈希值，用于避免重复下载
        url_hash = hashlib.md5(url.encode()).hexdigest()

        if url_hash in self.downloaded_images:
            # 静默跳过，不输出日志避免刷屏
            return True

        try:
            # 添加请求头，模拟浏览器
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }

            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            # 保存文件
            file_path = self.avatar_path / filename
            with open(file_path, "wb") as f:
                f.write(response.content)

            # 记录已下载
            self.downloaded_images.add(url_hash)
            logger.info(f"成功下载图片: {filename}")
            return True

        except Exception as e:
            logger.error(f"下载图片失败 {url}: {e}")
            return False

    def process_profile_images(self, user_data: Dict) -> List[str]:
        """
        处理用户头像和横幅图片

        Args:
            user_data: 用户数据字典

        Returns:
            下载的图片文件名列表
        """
        downloaded_files = []

        # 处理profile_banner
        if user_data.get("profile_banner"):
            url = user_data["profile_banner"]
            parsed_url = urlparse(url)
            filename = f"banner_{user_data['id']}{Path(parsed_url.path).suffix}"
            if self.download_image(url, filename):
                downloaded_files.append(filename)

        # 处理profile_image
        if user_data.get("profile_image"):
            url = user_data["profile_image"]
            parsed_url = urlparse(url)
            filename = f"avatar_{user_data['id']}{Path(parsed_url.path).suffix}"
            if self.download_image(url, filename):
                downloaded_files.append(filename)

        return downloaded_files

    def insert_user(self, cursor, user_data: Dict):
        """插入用户数据到数据库"""
        cursor.execute(
            """
            INSERT OR REPLACE INTO users (
                user_id, name, nick, location, date, verified, protected,
                profile_banner, profile_image, favourites_count, followers_count,
                friends_count, listed_count, media_count, statuses_count,
                description, url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                user_data["id"],
                user_data.get("name"),
                user_data.get("nick"),
                user_data.get("location"),
                user_data.get("date"),
                user_data.get("verified", False),
                user_data.get("protected", False),
                user_data.get("profile_banner"),
                user_data.get("profile_image"),
                user_data.get("favourites_count", 0),
                user_data.get("followers_count", 0),
                user_data.get("friends_count", 0),
                user_data.get("listed_count", 0),
                user_data.get("media_count", 0),
                user_data.get("statuses_count", 0),
                user_data.get("description"),
                user_data.get("url"),
            ),
        )

    def insert_media_files(self, cursor, tweet_id: int, media_files: List[str]):
        """插入媒体文件信息到数据库"""
        for filename in media_files:
            file_type = Path(filename).suffix.lower()
            # 使用相对路径：img/filename
            relative_path = f"img/{filename}"
            cursor.execute(
                """
                INSERT OR REPLACE INTO media_files (tweet_id, file_name, file_type, file_path)
                VALUES (?, ?, ?, ?)
            """,
                (tweet_id, filename, file_type, relative_path),
            )

    def process_json_file(self, file_path: Path) -> bool:
        """
        处理单个JSON文件

        Args:
            file_path: JSON文件路径

        Returns:
            是否处理成功
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 处理作者信息
            if "author" in data:
                self.insert_user(cursor, data["author"])
                self.process_profile_images(data["author"])

            # 处理用户信息（如果存在）
            if "user" in data:
                self.insert_user(cursor, data["user"])
                self.process_profile_images(data["user"])

            # 获取媒体文件
            tweet_id = data["tweet_id"]
            media_files = self.get_media_files(tweet_id)

            # 获取作者和用户ID
            author_id = data.get("author", {}).get("id") if data.get("author") else None
            user_id = data.get("user", {}).get("id") if data.get("user") else None

            # 插入推文数据
            cursor.execute(
                """
                INSERT OR REPLACE INTO tweets (
                    tweet_id, retweet_id, quote_id, reply_id, conversation_id,
                    source_id, date, lang, source, sensitive, sensitive_flags,
                    favorite_count, quote_count, reply_count, retweet_count,
                    bookmark_count, view_count, content, quote_by, count,
                    category, subcategory, media_files, author_id, user_id, hashtags
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    data["tweet_id"],
                    data.get("retweet_id", 0),
                    data.get("quote_id", 0),
                    data.get("reply_id", 0),
                    data.get("conversation_id", 0),
                    data.get("source_id", 0),
                    data.get("date"),
                    data.get("lang"),
                    data.get("source"),
                    data.get("sensitive", False),
                    json.dumps(data.get("sensitive_flags", [])),
                    data.get("favorite_count", 0),
                    data.get("quote_count", 0),
                    data.get("reply_count", 0),
                    data.get("retweet_count", 0),
                    data.get("bookmark_count", 0),
                    data.get("view_count", 0),
                    data.get("content"),
                    data.get("quote_by"),
                    data.get("count", 0),
                    data.get("category"),
                    data.get("subcategory"),
                    json.dumps(media_files),
                    author_id,
                    user_id,
                    json.dumps(data.get("hashtags", [])),
                ),
            )

            # 插入媒体文件信息
            if media_files:
                self.insert_media_files(cursor, tweet_id, media_files)

            conn.commit()
            conn.close()

            logger.info(f"成功处理文件: {file_path.name}")
            return True

        except Exception as e:
            logger.error(f"处理文件失败 {file_path.name}: {e}")
            return False

    def process_all_files(self):
        """处理所有JSON文件"""
        if not self.twitter_meta_path.exists():
            logger.error(f"twitter-meta文件夹不存在: {self.twitter_meta_path}")
            return

        json_files = list(self.twitter_meta_path.glob("*.json"))
        if not json_files:
            logger.warning("未找到JSON文件")
            return

        logger.info(f"找到 {len(json_files)} 个JSON文件")

        success_count = 0
        start_time = time.time()
        last_progress_time = start_time

        for i, file_path in enumerate(json_files):
            if self.process_json_file(file_path):
                success_count += 1

            # 每分钟输出一次进度
            current_time = time.time()
            if current_time - last_progress_time >= 60:  # 60秒 = 1分钟
                elapsed_minutes = (current_time - start_time) / 60
                progress_percent = (i + 1) / len(json_files) * 100
                logger.info(
                    f"处理进度: {i + 1}/{len(json_files)} ({progress_percent:.1f}%) - 已用时 {elapsed_minutes:.1f} 分钟"
                )
                last_progress_time = current_time

            # 添加小延迟，避免请求过于频繁
            time.sleep(0.1)

        # 保存下载记录
        self.save_downloaded_images()

        total_time = (time.time() - start_time) / 60
        logger.info(
            f"处理完成: {success_count}/{len(json_files)} 个文件成功处理，总用时 {total_time:.1f} 分钟"
        )

    def get_statistics(self):
        """获取数据库统计信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 推文数量
        cursor.execute("SELECT COUNT(*) FROM tweets")
        tweet_count = cursor.fetchone()[0]

        # 用户数量
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]

        # 媒体文件数量
        cursor.execute("SELECT COUNT(*) FROM media_files")
        media_count = cursor.fetchone()[0]

        # 有媒体文件的推文数量
        cursor.execute("SELECT COUNT(*) FROM tweets WHERE media_files != '[]'")
        tweets_with_media = cursor.fetchone()[0]

        # 转发推文数量（author_id != user_id）
        cursor.execute(
            "SELECT COUNT(*) FROM tweets WHERE author_id IS NOT NULL AND user_id IS NOT NULL AND author_id != user_id"
        )
        retweet_count = cursor.fetchone()[0]

        # 原创推文数量（author_id = user_id 或 author_id IS NULL）
        cursor.execute(
            "SELECT COUNT(*) FROM tweets WHERE author_id IS NULL OR author_id = user_id"
        )
        original_tweet_count = cursor.fetchone()[0]

        conn.close()

        return {
            "tweets": tweet_count,
            "users": user_count,
            "media_files": media_count,
            "tweets_with_media": tweets_with_media,
            "retweets": retweet_count,
            "original_tweets": original_tweet_count,
        }


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="Twitter数据处理脚本")
    parser.add_argument("path", help="包含twitter-meta、img、avatar文件夹的基础路径")
    parser.add_argument("--stats", action="store_true", help="显示统计信息")

    args = parser.parse_args()

    processor = TwitterDataProcessor(args.path)

    if args.stats:
        stats = processor.get_statistics()
        print("\n=== 数据库统计信息 ===")
        print(f"推文数量: {stats['tweets']}")
        print(f"原创推文: {stats['original_tweets']}")
        print(f"转发推文: {stats['retweets']}")
        print(f"用户数量: {stats['users']}")
        print(f"媒体文件数量: {stats['media_files']}")
        print(f"包含媒体文件的推文数量: {stats['tweets_with_media']}")
    else:
        processor.process_all_files()


if __name__ == "__main__":
    main()
