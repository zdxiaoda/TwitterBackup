#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Twitter数据查看器 - Flask Web应用
用于展示备份的Twitter数据
"""

from flask import Flask, render_template, request, send_from_directory, jsonify
from flask_sqlalchemy import SQLAlchemy
import sqlite3
import json
from pathlib import Path
from datetime import datetime
import os
from urllib.parse import urlparse

app = Flask(__name__)
app.config["SECRET_KEY"] = "your-secret-key-here"

# 全局变量存储数据库路径
DB_PATH = None
DATA_ROOT = None


def init_app(db_path):
    """初始化应用配置"""
    global DB_PATH, DATA_ROOT
    DB_PATH = Path(db_path)
    DATA_ROOT = DB_PATH.parent

    if not DB_PATH.exists():
        raise FileNotFoundError(f"数据库文件不存在: {DB_PATH}")

    # 设置静态文件路径
    app.static_folder = str(DATA_ROOT)

    # 添加头像文件夹的静态文件路由
    @app.route("/avatar/<path:filename>")
    def serve_avatar(filename):
        """提供头像文件访问"""
        avatar_dir = DATA_ROOT / "avatar"
        return send_from_directory(str(avatar_dir), filename)

    # 添加媒体文件夹的静态文件路由
    @app.route("/img/<path:filename>")
    def serve_media(filename):
        """提供媒体文件访问"""
        media_dir = DATA_ROOT / "img"
        return send_from_directory(str(media_dir), filename)


def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def convert_avatar_url_to_local(user_id, original_url):
    """
    将Twitter头像URL转换为本地文件路径

    Args:
        user_id: 用户ID
        original_url: 原始Twitter头像URL

    Returns:
        本地头像文件路径，如果文件不存在则返回默认头像
    """
    if not original_url or not user_id:
        return "https://via.placeholder.com/48x48/cccccc/666666?text=?"

    try:
        # 解析原始URL获取文件扩展名
        parsed_url = urlparse(original_url)
        extension = Path(parsed_url.path).suffix

        # 构建本地文件名
        local_filename = f"avatar_{user_id}{extension}"
        local_path = DATA_ROOT / "avatar" / local_filename

        # 检查文件是否存在
        if local_path.exists():
            return f"/avatar/{local_filename}"
        else:
            return "https://via.placeholder.com/48x48/cccccc/666666?text=?"
    except:
        return "https://via.placeholder.com/48x48/cccccc/666666?text=?"


def convert_banner_url_to_local(user_id, original_url):
    """
    将Twitter横幅URL转换为本地文件路径

    Args:
        user_id: 用户ID
        original_url: 原始Twitter横幅URL

    Returns:
        本地横幅文件路径，如果文件不存在则返回None
    """
    if not original_url or not user_id:
        return None

    try:
        # 解析原始URL获取文件扩展名
        parsed_url = urlparse(original_url)
        extension = Path(parsed_url.path).suffix

        # 构建本地文件名
        local_filename = f"banner_{user_id}{extension}"
        local_path = DATA_ROOT / "avatar" / local_filename

        # 检查文件是否存在
        if local_path.exists():
            return f"/avatar/{local_filename}"
        else:
            return None
    except:
        return None


def process_tweet_data(tweet_dict):
    """
    处理推文数据，转换头像URL为本地路径

    Args:
        tweet_dict: 推文字典

    Returns:
        处理后的推文字典
    """
    # 转换作者头像
    if tweet_dict.get("author_avatar"):
        tweet_dict["author_avatar"] = convert_avatar_url_to_local(
            tweet_dict.get("author_id"), tweet_dict["author_avatar"]
        )

    # 转换用户头像
    if tweet_dict.get("user_avatar"):
        tweet_dict["user_avatar"] = convert_avatar_url_to_local(
            tweet_dict.get("user_id"), tweet_dict["user_avatar"]
        )

    # 转换作者横幅
    if tweet_dict.get("author_banner"):
        tweet_dict["author_banner"] = convert_banner_url_to_local(
            tweet_dict.get("author_id"), tweet_dict["author_banner"]
        )

    # 转换用户横幅
    if tweet_dict.get("user_banner"):
        tweet_dict["user_banner"] = convert_banner_url_to_local(
            tweet_dict.get("user_id"), tweet_dict["user_banner"]
        )

    # 处理媒体文件路径
    if tweet_dict.get("media_files"):
        processed_media_files = []
        for media_file in tweet_dict["media_files"]:
            # 清理路径，移除开头的斜杠
            clean_path = media_file.lstrip("/")

            # 如果媒体文件路径已经是相对路径（img/filename），直接使用
            if clean_path.startswith("img/"):
                processed_media_files.append(clean_path)
            else:
                # 否则假设是文件名，添加img/前缀
                processed_media_files.append(f"img/{clean_path}")
        tweet_dict["media_files"] = processed_media_files

    return tweet_dict


def format_date(date_str):
    """格式化日期显示"""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        now = datetime.now()
        diff = now - dt

        if diff.days > 365:
            return f"{diff.days // 365}年前"
        elif diff.days > 30:
            return f"{diff.days // 30}个月前"
        elif diff.days > 0:
            return f"{diff.days}天前"
        elif diff.seconds > 3600:
            return f"{diff.seconds // 3600}小时前"
        elif diff.seconds > 60:
            return f"{diff.seconds // 60}分钟前"
        else:
            return "刚刚"
    except:
        return date_str


@app.template_filter("format_date")
def format_date_filter(date_str):
    """模板过滤器：格式化日期"""
    return format_date(date_str)


@app.template_filter("format_number")
def format_number_filter(num):
    """模板过滤器：格式化数字"""
    if num >= 1000000:
        return f"{num/1000000:.1f}M"
    elif num >= 1000:
        return f"{num/1000:.1f}K"
    return str(num)


@app.route("/")
def index():
    """首页 - 显示所有推文"""
    page = request.args.get("page", 1, type=int)
    per_page = 20

    conn = get_db_connection()
    cursor = conn.cursor()

    # 获取推文总数
    cursor.execute("SELECT COUNT(*) FROM tweets")
    total_tweets = cursor.fetchone()[0]

    # 获取推文列表（分页）
    offset = (page - 1) * per_page
    cursor.execute(
        """
        SELECT 
            t.*,
            a.name as author_name,
            a.nick as author_nick,
            a.profile_image as author_avatar,
            u.name as user_name,
            u.nick as user_nick,
            u.profile_image as user_avatar
        FROM tweets t
        LEFT JOIN users a ON t.author_id = a.user_id
        LEFT JOIN users u ON t.user_id = u.user_id
        ORDER BY t.date DESC
        LIMIT ? OFFSET ?
    """,
        (per_page, offset),
    )

    tweets = []
    for row in cursor.fetchall():
        tweet = dict(row)

        # 解析媒体文件
        if tweet["media_files"]:
            tweet["media_files"] = json.loads(tweet["media_files"])
        else:
            tweet["media_files"] = []

        # 解析hashtags
        if tweet["hashtags"]:
            tweet["hashtags"] = json.loads(tweet["hashtags"])
        else:
            tweet["hashtags"] = []

        # 判断是否为转发
        tweet["is_retweet"] = (
            (tweet["author_id"] != tweet["user_id"])
            if tweet["author_id"] and tweet["user_id"]
            else False
        )

        tweets.append(tweet)

        # 转换头像URL为本地路径
        tweet = process_tweet_data(tweet)

        tweets.append(tweet)

    # 获取统计信息
    cursor.execute("SELECT COUNT(DISTINCT user_id) FROM users")
    total_users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM media_files")
    total_media = cursor.fetchone()[0]

    conn.close()

    # 计算分页信息
    total_pages = (total_tweets + per_page - 1) // per_page

    return render_template(
        "index.html",
        tweets=tweets,
        page=page,
        total_pages=total_pages,
        total_tweets=total_tweets,
        total_users=total_users,
        total_media=total_media,
    )


@app.route("/user/<int:user_id>")
def user_profile(user_id):
    """用户个人主页"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 获取用户信息
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()

    if not user:
        return "用户不存在", 404

    user = dict(user)

    # 获取用户的推文
    cursor.execute(
        """
        SELECT 
            t.*,
            a.name as author_name,
            a.nick as author_nick,
            a.profile_image as author_avatar,
            u.name as user_name,
            u.nick as user_nick,
            u.profile_image as user_avatar
        FROM tweets t
        LEFT JOIN users a ON t.author_id = a.user_id
        LEFT JOIN users u ON t.user_id = u.user_id
        WHERE t.user_id = ? OR t.author_id = ?
        ORDER BY t.date DESC
        LIMIT 50
    """,
        (user_id, user_id),
    )

    tweets = []
    for row in cursor.fetchall():
        tweet = dict(row)

        # 解析媒体文件
        if tweet["media_files"]:
            tweet["media_files"] = json.loads(tweet["media_files"])
        else:
            tweet["media_files"] = []

        # 解析hashtags
        if tweet["hashtags"]:
            tweet["hashtags"] = json.loads(tweet["hashtags"])
        else:
            tweet["hashtags"] = []

        # 判断是否为转发
        tweet["is_retweet"] = (
            (tweet["author_id"] != tweet["user_id"])
            if tweet["author_id"] and tweet["user_id"]
            else False
        )

        tweets.append(tweet)

        # 转换头像URL为本地路径
        tweet = process_tweet_data(tweet)

        tweets.append(tweet)

    conn.close()

    return render_template("profile.html", user=user, tweets=tweets)


@app.route("/tweet/<int:tweet_id>")
def tweet_detail(tweet_id):
    """推文详情页"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 获取推文详情
    cursor.execute(
        """
        SELECT 
            t.*,
            a.name as author_name,
            a.nick as author_nick,
            a.profile_image as author_avatar,
            a.profile_banner as author_banner,
            u.name as user_name,
            u.nick as user_nick,
            u.profile_image as user_avatar,
            u.profile_banner as user_banner
        FROM tweets t
        LEFT JOIN users a ON t.author_id = a.user_id
        LEFT JOIN users u ON t.user_id = u.user_id
        WHERE t.tweet_id = ?
    """,
        (tweet_id,),
    )

    tweet = cursor.fetchone()

    if not tweet:
        return "推文不存在", 404

    tweet = dict(tweet)

    # 解析媒体文件
    if tweet["media_files"]:
        tweet["media_files"] = json.loads(tweet["media_files"])
    else:
        tweet["media_files"] = []

    # 解析hashtags
    if tweet["hashtags"]:
        tweet["hashtags"] = json.loads(tweet["hashtags"])
    else:
        tweet["hashtags"] = []

    # 判断是否为转发
    tweet["is_retweet"] = (
        (tweet["author_id"] != tweet["user_id"])
        if tweet["author_id"] and tweet["user_id"]
        else False
    )

    # 转换头像URL为本地路径
    tweet = process_tweet_data(tweet)

    # 获取相关推文（回复、引用等）
    cursor.execute(
        """
        SELECT 
            t.*,
            a.name as author_name,
            a.nick as author_nick,
            a.profile_image as author_avatar,
            u.name as user_name,
            u.nick as user_nick,
            u.profile_image as user_avatar
        FROM tweets t
        LEFT JOIN users a ON t.author_id = a.user_id
        LEFT JOIN users u ON t.user_id = u.user_id
        WHERE t.reply_id = ? OR t.quote_id = ?
        ORDER BY t.date DESC
        LIMIT 20
    """,
        (tweet_id, tweet_id),
    )

    related_tweets = []
    for row in cursor.fetchall():
        related = dict(row)
        if related["media_files"]:
            related["media_files"] = json.loads(related["media_files"])
        else:
            related["media_files"] = []

        # 转换头像URL为本地路径
        related = process_tweet_data(related)

        related_tweets.append(related)

    conn.close()

    return render_template(
        "tweet_detail.html", tweet=tweet, related_tweets=related_tweets
    )


@app.route("/search")
def search():
    """搜索功能"""
    query = request.args.get("q", "")
    if not query:
        return render_template("search.html", tweets=[], query="")

    conn = get_db_connection()
    cursor = conn.cursor()

    # 搜索推文内容
    cursor.execute(
        """
        SELECT 
            t.*,
            a.name as author_name,
            a.nick as author_nick,
            a.profile_image as author_avatar,
            u.name as user_name,
            u.nick as user_nick,
            u.profile_image as user_avatar
        FROM tweets t
        LEFT JOIN users a ON t.author_id = a.user_id
        LEFT JOIN users u ON t.user_id = u.user_id
        WHERE t.content LIKE ?
        ORDER BY t.date DESC
        LIMIT 50
    """,
        (f"%{query}%",),
    )

    tweets = []
    for row in cursor.fetchall():
        tweet = dict(row)

        # 解析媒体文件
        if tweet["media_files"]:
            tweet["media_files"] = json.loads(tweet["media_files"])
        else:
            tweet["media_files"] = []

        # 解析hashtags
        if tweet["hashtags"]:
            tweet["hashtags"] = json.loads(tweet["hashtags"])
        else:
            tweet["hashtags"] = []

        # 判断是否为转发
        tweet["is_retweet"] = (
            (tweet["author_id"] != tweet["user_id"])
            if tweet["author_id"] and tweet["user_id"]
            else False
        )

        # 转换头像URL为本地路径
        tweet = process_tweet_data(tweet)

        tweets.append(tweet)

    conn.close()

    return render_template("search.html", tweets=tweets, query=query)


@app.route("/stats")
def stats():
    """统计页面"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 获取各种统计数据
    stats = {}

    cursor.execute("SELECT COUNT(*) FROM tweets")
    stats["total_tweets"] = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT user_id) FROM users")
    stats["total_users"] = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM media_files")
    stats["total_media"] = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tweets WHERE author_id != user_id")
    stats["total_retweets"] = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tweets WHERE reply_id > 0")
    stats["total_replies"] = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tweets WHERE quote_id > 0")
    stats["total_quotes"] = cursor.fetchone()[0]

    # 获取最活跃用户
    cursor.execute(
        """
        SELECT u.*, COUNT(t.tweet_id) as tweet_count
        FROM users u
        JOIN tweets t ON u.user_id = t.user_id
        GROUP BY u.user_id
        ORDER BY tweet_count DESC
        LIMIT 10
    """
    )
    top_users = []
    for row in cursor.fetchall():
        user = dict(row)
        # 转换用户头像URL为本地路径
        if user.get("profile_image"):
            user["profile_image"] = convert_avatar_url_to_local(
                user.get("user_id"), user["profile_image"]
            )
        top_users.append(user)
    stats["top_users"] = top_users

    # 获取最受欢迎的推文
    cursor.execute(
        """
        SELECT 
            t.*,
            u.name as user_name,
            u.nick as user_nick,
            u.profile_image as user_avatar
        FROM tweets t
        LEFT JOIN users u ON t.user_id = u.user_id
        ORDER BY t.favorite_count DESC
        LIMIT 10
    """
    )
    top_tweets = []
    for row in cursor.fetchall():
        tweet = dict(row)
        # 转换推文头像URL为本地路径
        tweet = process_tweet_data(tweet)
        top_tweets.append(tweet)
    stats["top_tweets"] = top_tweets

    conn.close()

    return render_template("stats.html", stats=stats)


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="Twitter数据查看器")
    parser.add_argument("db_path", help="SQLite数据库文件路径")
    parser.add_argument("--host", default="127.0.0.1", help="监听地址")
    parser.add_argument("--port", default=5000, type=int, help="监听端口")
    parser.add_argument("--debug", action="store_true", help="调试模式")

    args = parser.parse_args()

    # 初始化应用
    init_app(args.db_path)

    print(f"启动Twitter数据查看器...")
    print(f"数据库: {DB_PATH}")
    print(f"数据目录: {DATA_ROOT}")
    print(f"访问地址: http://{args.host}:{args.port}")

    # 运行应用
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
