"""
数据库管理工具类
提供数据库连接和查询的封装
"""

import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager


class DatabaseManager:
    """数据库管理器"""

    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(f"数据库文件不存在: {db_path}")

    @contextmanager
    def get_connection(self):
        """获取数据库连接的上下文管理器"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """执行查询并返回结果"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def execute_one(self, query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        """执行查询并返回单条结果"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            row = cursor.fetchone()
            return dict(row) if row else None

    def execute_update(self, query: str, params: tuple = ()) -> int:
        """执行更新操作并返回影响的行数"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount

    def get_tweets(
        self, page: int = 1, per_page: int = 20, user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取推文列表"""
        offset = (page - 1) * per_page

        if user_id:
            query = """
                SELECT t.*, u.nick as author_nick, u.name as author_name, u.avatar as author_avatar
                FROM tweets t
                LEFT JOIN users u ON t.author_id = u.id
                WHERE t.author_id = ?
                ORDER BY t.date DESC
                LIMIT ? OFFSET ?
            """
            params = (user_id, per_page, offset)
        else:
            query = """
                SELECT t.*, u.nick as author_nick, u.name as author_name, u.avatar as author_avatar
                FROM tweets t
                LEFT JOIN users u ON t.author_id = u.id
                ORDER BY t.date DESC
                LIMIT ? OFFSET ?
            """
            params = (per_page, offset)

        return self.execute_query(query, params)

    def get_tweet_by_id(self, tweet_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取推文"""
        query = """
            SELECT t.*, u.nick as author_nick, u.name as author_name, u.avatar as author_avatar
            FROM tweets t
            LEFT JOIN users u ON t.author_id = u.id
            WHERE t.tweet_id = ?
        """
        return self.execute_one(query, (tweet_id,))

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取用户信息"""
        query = "SELECT * FROM users WHERE id = ?"
        return self.execute_one(query, (user_id,))

    def search_tweets(
        self, query: str, page: int = 1, per_page: int = 20
    ) -> List[Dict[str, Any]]:
        """搜索推文"""
        offset = (page - 1) * per_page
        search_pattern = f"%{query}%"

        sql_query = """
            SELECT t.*, u.nick as author_nick, u.name as author_name, u.avatar as author_avatar
            FROM tweets t
            LEFT JOIN users u ON t.author_id = u.id
            WHERE t.content LIKE ? OR u.nick LIKE ? OR u.name LIKE ?
            ORDER BY t.date DESC
            LIMIT ? OFFSET ?
        """
        params = (search_pattern, search_pattern, search_pattern, per_page, offset)

        return self.execute_query(sql_query, params)

    def get_stats(self) -> Dict[str, int]:
        """获取统计信息"""
        stats = {}

        # 推文总数
        result = self.execute_one("SELECT COUNT(*) as count FROM tweets")
        stats["total_tweets"] = result["count"] if result else 0

        # 用户总数
        result = self.execute_one("SELECT COUNT(*) as count FROM users")
        stats["total_users"] = result["count"] if result else 0

        # 媒体文件总数
        result = self.execute_one(
            "SELECT COUNT(*) as count FROM tweets WHERE media_files IS NOT NULL AND media_files != ''"
        )
        stats["total_media"] = result["count"] if result else 0

        return stats

    def get_pagination_info(
        self, page: int, per_page: int, user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取分页信息"""
        if user_id:
            result = self.execute_one(
                "SELECT COUNT(*) as count FROM tweets WHERE author_id = ?", (user_id,)
            )
        else:
            result = self.execute_one("SELECT COUNT(*) as count FROM tweets")

        total_count = result["count"] if result else 0
        total_pages = (total_count + per_page - 1) // per_page

        return {
            "current_page": page,
            "total_pages": total_pages,
            "total_count": total_count,
            "per_page": per_page,
        }
