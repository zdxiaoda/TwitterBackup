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
from datetime import datetime, timedelta
import os
import re
from urllib.parse import urlparse
from translation_service import get_translation_service

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

    # 设置静态文件路径为项目根目录
    project_root = Path(__file__).parent
    app.static_folder = str(project_root / "static")

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

    # 删除自定义的static/css路由，让Flask自动处理


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

    # 处理引用推文信息
    if tweet_dict.get("quote_info"):
        if tweet_dict["quote_info"].get("author_avatar"):
            tweet_dict["quote_info"]["author_avatar"] = convert_avatar_url_to_local(
                tweet_dict["quote_info"].get("author_id"),
                tweet_dict["quote_info"]["author_avatar"],
            )
    # 处理被引用原推文信息（反向）
    if tweet_dict.get("quoted_info"):
        if tweet_dict["quoted_info"].get("author_avatar"):
            tweet_dict["quoted_info"]["author_avatar"] = convert_avatar_url_to_local(
                tweet_dict["quoted_info"].get("author_id"),
                tweet_dict["quoted_info"]["author_avatar"],
            )

    # 处理转发推文信息
    if tweet_dict.get("retweet_info"):
        if tweet_dict["retweet_info"].get("author_avatar"):
            tweet_dict["retweet_info"]["author_avatar"] = convert_avatar_url_to_local(
                tweet_dict["retweet_info"].get("author_id"),
                tweet_dict["retweet_info"]["author_avatar"],
            )

    # 处理回复推文信息
    if tweet_dict.get("reply_info"):
        if tweet_dict["reply_info"].get("author_avatar"):
            tweet_dict["reply_info"]["author_avatar"] = convert_avatar_url_to_local(
                tweet_dict["reply_info"].get("author_id"),
                tweet_dict["reply_info"]["author_avatar"],
            )

    # 处理被引用推文信息
    if tweet_dict.get("quoted_info"):
        if tweet_dict["quoted_info"].get("author_avatar"):
            tweet_dict["quoted_info"]["author_avatar"] = convert_avatar_url_to_local(
                tweet_dict["quoted_info"].get("author_id"),
                tweet_dict["quoted_info"]["author_avatar"],
            )

    # 处理媒体文件路径（主推文与子对象）
    def _normalize_media_list(media_list):
        normalized = []
        for media_file in media_list or []:
            clean_path = media_file.lstrip("/")
            normalized.append(
                clean_path if clean_path.startswith("img/") else f"img/{clean_path}"
            )
        return normalized

    if tweet_dict.get("media_files"):
        tweet_dict["media_files"] = _normalize_media_list(tweet_dict["media_files"])

    # 同步规范子对象（引用/被引用/回复/被回复/转发）的媒体文件路径
    for related_key in [
        "quote_info",
        "quoted_info",
        "reply_info",
        "replied_info",
        "retweet_info",
    ]:
        if tweet_dict.get(related_key) and tweet_dict[related_key].get("media_files"):
            tweet_dict[related_key]["media_files"] = _normalize_media_list(
                tweet_dict[related_key]["media_files"]
            )

    # 处理推文内容中的Space链接
    def process_space_links(content):
        if not content:
            return content
        # 查找Space链接
        space_link_pattern = r"(https?://(?:x|twitter)\.com/i/spaces/[a-zA-Z0-9_-]+)"

        def replace_space_link(match):
            url = match.group(0)
            return f'<a href="{url}" target="_blank" class="space-link"><i class="fas fa-microphone-alt"></i> Space</a>'

        return re.sub(space_link_pattern, replace_space_link, content)

    # 处理推文内容中的空格和换行
    def clean_tweet_content(content):
        if not content:
            return content

        # 按行分割
        lines = content.split("\n")
        processed_lines = []

        for line in lines:
            # 去除行首和行尾的空格
            line = line.strip()
            # 将多个连续空格替换为单个空格
            line = re.sub(r"\s+", " ", line)
            processed_lines.append(line)

        # 过滤掉空行，并用<br>连接
        non_empty_lines = [line for line in processed_lines if line]
        return "<br>".join(non_empty_lines)

    # 处理推文内容中的链接
    def process_links(content):
        if not content:
            return content

        # 使用一个更精确的正则表达式来匹配所有YouTube链接格式（包括直播）
        youtube_pattern = r'(https?://(?:www\.)?(?:youtube\.com/(?:watch\?v=|embed/|v/|live/)|youtu\.be/)([a-zA-Z0-9_-]+)(?:\?[^"\s]*)?)'

        def replace_youtube_link(match):
            full_url = match.group(1)
            video_id = match.group(2)

            # 返回带有错误处理的HTML嵌入框架
            return f"""<div class="youtube-embed" style="margin-top: 10px;" data-video-id="{video_id}">
                <iframe 
                    width="100%" 
                    height="315" 
                    src="https://www.youtube.com/embed/{video_id}" 
                    frameborder="0" 
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                    allowfullscreen
                    onload="handleYouTubeLoad(this)"
                    onerror="handleYouTubeError(this)"
                ></iframe>
                <div class="youtube-placeholder youtube-loading" style="display: none;">
                    <div class="youtube-placeholder-content">
                        <i class="fas fa-spinner youtube-placeholder-icon"></i>
                        <div class="youtube-placeholder-text no-translate">Loading video...</div>
                        <div class="youtube-placeholder-subtext no-translate">Please wait, connecting to YouTube</div>
                    </div>
                </div>
                <div class="youtube-placeholder youtube-error" style="display: none;">
                    <div class="youtube-placeholder-content">
                        <i class="fas fa-exclamation-triangle youtube-placeholder-icon"></i>
                        <div class="youtube-placeholder-text no-translate">Video loading failed</div>
                        <div class="youtube-placeholder-subtext no-translate">Unable to access this YouTube video, may be network issue or video deleted</div>
                        <button class="youtube-placeholder-button" onclick="retryYouTubeVideo(this)">
                            <i class="fas fa-redo"></i> <span class="no-translate">Retry</span>
                        </button>
                    </div>
                </div>
            </div>"""

        # 替换所有YouTube链接
        content = re.sub(youtube_pattern, replace_youtube_link, content)

        # 处理t.co链接 - 替换为"查看链接"
        tco_pattern = r"(https?://t\.co/[a-zA-Z0-9]+)"

        def replace_tco_link(match):
            return '<span class="tco-link">查看链接</span>'

        content = re.sub(tco_pattern, replace_tco_link, content)

        # 处理其他普通链接 - 高亮显示（排除已处理的YouTube、t.co和Space链接）
        general_link_pattern = r'(https?://(?!t\.co|(?:www\.)?(?:youtube\.com|youtu\.be)|(?:x|twitter)\.com/i/spaces)[^\s<>"]+)'

        def replace_general_link(match):
            url = match.group(1)
            return f'<a href="{url}" target="_blank" class="general-link">{url}</a>'

        content = re.sub(general_link_pattern, replace_general_link, content)

        return content

    # 处理主推文内容
    if tweet_dict.get("content"):
        tweet_dict["content"] = clean_tweet_content(tweet_dict["content"])
        tweet_dict["content"] = process_space_links(tweet_dict["content"])
        tweet_dict["content"] = process_links(tweet_dict["content"])

    # 处理回复推文内容
    if tweet_dict.get("reply_info") and tweet_dict["reply_info"].get("content"):
        tweet_dict["reply_info"]["content"] = clean_tweet_content(
            tweet_dict["reply_info"]["content"]
        )
        tweet_dict["reply_info"]["content"] = process_space_links(
            tweet_dict["reply_info"]["content"]
        )
        tweet_dict["reply_info"]["content"] = process_links(
            tweet_dict["reply_info"]["content"]
        )

    # 处理引用推文内容
    if tweet_dict.get("quote_info") and tweet_dict["quote_info"].get("content"):
        tweet_dict["quote_info"]["content"] = clean_tweet_content(
            tweet_dict["quote_info"]["content"]
        )
        tweet_dict["quote_info"]["content"] = process_space_links(
            tweet_dict["quote_info"]["content"]
        )
        tweet_dict["quote_info"]["content"] = process_links(
            tweet_dict["quote_info"]["content"]
        )

    # 处理被引用原推文内容（quoted_info）
    if tweet_dict.get("quoted_info") and tweet_dict["quoted_info"].get("content"):
        tweet_dict["quoted_info"]["content"] = clean_tweet_content(
            tweet_dict["quoted_info"]["content"]
        )
        tweet_dict["quoted_info"]["content"] = process_space_links(
            tweet_dict["quoted_info"]["content"]
        )
        tweet_dict["quoted_info"]["content"] = process_links(
            tweet_dict["quoted_info"]["content"]
        )

    # 处理被回复原推文内容（replied_info）
    if tweet_dict.get("replied_info") and tweet_dict["replied_info"].get("content"):
        tweet_dict["replied_info"]["content"] = clean_tweet_content(
            tweet_dict["replied_info"]["content"]
        )
        tweet_dict["replied_info"]["content"] = process_space_links(
            tweet_dict["replied_info"]["content"]
        )
        tweet_dict["replied_info"]["content"] = process_links(
            tweet_dict["replied_info"]["content"]
        )

    # 转换被回复原推文头像
    if tweet_dict.get("replied_info") and tweet_dict["replied_info"].get(
        "author_avatar"
    ):
        tweet_dict["replied_info"]["author_avatar"] = convert_avatar_url_to_local(
            tweet_dict["replied_info"].get("author_id"),
            tweet_dict["replied_info"].get("author_avatar"),
        )

    # 处理转发推文内容
    if tweet_dict.get("retweet_info") and tweet_dict["retweet_info"].get("content"):
        tweet_dict["retweet_info"]["content"] = clean_tweet_content(
            tweet_dict["retweet_info"]["content"]
        )
        tweet_dict["retweet_info"]["content"] = process_space_links(
            tweet_dict["retweet_info"]["content"]
        )
        tweet_dict["retweet_info"]["content"] = process_links(
            tweet_dict["retweet_info"]["content"]
        )

    # 处理相关推文的头像URL
    if tweet_dict.get("retweet_info") and tweet_dict["retweet_info"].get(
        "author_avatar"
    ):
        tweet_dict["retweet_info"]["author_avatar"] = convert_avatar_url_to_local(
            tweet_dict["retweet_info"].get("author_id"),
            tweet_dict["retweet_info"]["author_avatar"],
        )

    if tweet_dict.get("quote_info") and tweet_dict["quote_info"].get("author_avatar"):
        tweet_dict["quote_info"]["author_avatar"] = convert_avatar_url_to_local(
            tweet_dict["quote_info"].get("author_id"),
            tweet_dict["quote_info"]["author_avatar"],
        )

    if tweet_dict.get("reply_info") and tweet_dict["reply_info"].get("author_avatar"):
        tweet_dict["reply_info"]["author_avatar"] = convert_avatar_url_to_local(
            tweet_dict["reply_info"].get("author_id"),
            tweet_dict["reply_info"]["author_avatar"],
        )

    return tweet_dict


def format_date(date_str):
    """格式化日期显示"""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        now = datetime.now()

        # 如果是今天，显示时间
        if dt.date() == now.date():
            return dt.strftime("%H:%M")
        # 如果是昨天，显示"昨天 时间"
        elif dt.date() == (now.date() - timedelta(days=1)):
            return f"昨天 {dt.strftime('%H:%M')}"
        # 如果是今年，显示"月日 时间"
        elif dt.year == now.year:
            return dt.strftime("%m月%d日 %H:%M")
        # 其他情况显示完整日期时间
        else:
            return dt.strftime("%Y年%m月%d日 %H:%M")
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


def get_pagination_range(current_page, total_pages, max_visible=7):
    """
    生成智能分页范围

    Args:
        current_page: 当前页码
        total_pages: 总页数
        max_visible: 最大可见页码数

    Returns:
        dict: 包含分页信息的字典
    """
    if total_pages <= max_visible:
        # 如果总页数小于等于最大可见数，显示所有页码
        return {
            "pages": list(range(1, total_pages + 1)),
            "show_first": False,
            "show_last": False,
            "show_prev_dots": False,
            "show_next_dots": False,
        }

    # 计算显示的页码范围
    half_visible = max_visible // 2

    if current_page <= half_visible + 1:
        # 当前页在开头附近
        start_page = 1
        end_page = max_visible
        show_first = False
        show_last = total_pages > max_visible
        show_prev_dots = False
        show_next_dots = total_pages > max_visible
    elif current_page >= total_pages - half_visible:
        # 当前页在结尾附近
        start_page = total_pages - max_visible + 1
        end_page = total_pages
        show_first = total_pages > max_visible
        show_last = False
        show_prev_dots = total_pages > max_visible
        show_next_dots = False
    else:
        # 当前页在中间
        start_page = current_page - half_visible
        end_page = current_page + half_visible
        show_first = True
        show_last = True
        show_prev_dots = True
        show_next_dots = True

    pages = list(range(start_page, end_page + 1))

    return {
        "pages": pages,
        "show_first": show_first,
        "show_last": show_last,
        "show_prev_dots": show_prev_dots,
        "show_next_dots": show_next_dots,
    }


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
            u.profile_image as user_avatar,
            -- 转发推文信息
            rt.content as retweet_content,
            rt.author_id as retweet_author_id,
            rt.user_id as retweet_user_id,
            rt.media_files as retweet_media_files,
            rta.name as retweet_author_name,
            rta.nick as retweet_author_nick,
            rta.profile_image as retweet_author_avatar
        FROM tweets t
        LEFT JOIN users a ON t.author_id = a.user_id
        LEFT JOIN users u ON t.user_id = u.user_id
        -- 关联转发推文
        LEFT JOIN tweets rt ON t.retweet_id = rt.tweet_id
        LEFT JOIN users rta ON rt.author_id = rta.user_id
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

        # 判断推文类型
        tweet["is_retweet"] = tweet["retweet_id"] > 0
        tweet["is_quote"] = tweet["quote_id"] > 0
        tweet["is_reply"] = tweet["reply_id"] > 0

        # 处理相关推文信息
        if tweet["is_retweet"] and tweet.get("retweet_content"):
            tweet["retweet_info"] = {
                "content": tweet["retweet_content"],
                "author_id": tweet["retweet_author_id"],
                "user_id": tweet["retweet_user_id"],
                "author_name": tweet.get("retweet_author_name"),
                "author_nick": tweet.get("retweet_author_nick"),
                "author_avatar": tweet.get("retweet_author_avatar"),
            }

        # 反向查找原始被引用推文
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
            WHERE t.quote_id = ?
            LIMIT 1
            """,
            (tweet["tweet_id"],),
        )
        quoted_orig = cursor.fetchone()
        if quoted_orig:
            qo = dict(quoted_orig)
            quote_media_files = []
            if qo.get("media_files"):
                try:
                    quote_media_files = json.loads(qo["media_files"])
                except Exception:
                    quote_media_files = []
            tweet["quoted_info"] = {
                "tweet_id": qo.get("tweet_id"),
                "content": qo.get("content"),
                "author_id": qo.get("author_id"),
                "user_id": qo.get("user_id"),
                "author_name": qo.get("author_name"),
                "author_nick": qo.get("author_nick"),
                "author_avatar": qo.get("author_avatar"),
                "media_files": quote_media_files,
            }

        # 反向查找原始被回复推文
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
            WHERE t.reply_id = ?
            LIMIT 1
            """,
            (tweet["tweet_id"],),
        )
        replied_orig = cursor.fetchone()
        if replied_orig:
            ro = dict(replied_orig)
            reply_media_files = []
            if ro.get("media_files"):
                try:
                    reply_media_files = json.loads(ro["media_files"])
                except Exception:
                    reply_media_files = []
            tweet["replied_info"] = {
                "tweet_id": ro.get("tweet_id"),
                "content": ro.get("content"),
                "author_id": ro.get("author_id"),
                "user_id": ro.get("user_id"),
                "author_name": ro.get("author_name"),
                "author_nick": ro.get("author_nick"),
                "author_avatar": ro.get("author_avatar"),
                "media_files": reply_media_files,
            }

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
    pagination = get_pagination_range(page, total_pages)

    return render_template(
        "index_modern.html",
        tweets=tweets,
        page=page,
        total_pages=total_pages,
        pagination=pagination,
        total_tweets=total_tweets,
        total_users=total_users,
        total_media=total_media,
    )


@app.route("/user/<int:user_id>")
def user_profile(user_id):
    """用户个人主页"""
    page = request.args.get("page", 1, type=int)
    per_page = 20

    conn = get_db_connection()
    cursor = conn.cursor()

    # 获取用户信息
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()

    if not user:
        return "用户不存在", 404

    user = dict(user)

    # 转换用户头像和横幅URL为本地路径
    if user.get("profile_image"):
        user["profile_image"] = convert_avatar_url_to_local(
            user.get("user_id"), user["profile_image"]
        )

    if user.get("profile_banner"):
        user["profile_banner"] = convert_banner_url_to_local(
            user.get("user_id"), user["profile_banner"]
        )

    # 获取用户推文总数
    cursor.execute(
        "SELECT COUNT(*) FROM tweets WHERE user_id = ? OR author_id = ?",
        (user_id, user_id),
    )
    total_tweets = cursor.fetchone()[0]

    # 获取用户的推文（分页）
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
            u.profile_image as user_avatar,
            -- 相关推文信息
            rt.content as retweet_content,
            rt.author_id as retweet_author_id,
            rt.user_id as retweet_user_id,
            rt.media_files as retweet_media_files,
            rta.name as retweet_author_name,
            rta.nick as retweet_author_nick,
            rta.profile_image as retweet_author_avatar,
            qt.content as quote_content,
            qt.author_id as quote_author_id,
            qt.user_id as quote_user_id,
            qt.media_files as quote_media_files,
            qta.name as quote_author_name,
            qta.nick as quote_author_nick,
            qta.profile_image as quote_author_avatar,
            rp.content as reply_content,
            rp.author_id as reply_author_id,
            rp.user_id as reply_user_id,
            rp.media_files as reply_media_files,
            rpa.name as reply_author_name,
            rpa.nick as reply_author_nick,
            rpa.profile_image as reply_author_avatar
        FROM tweets t
        LEFT JOIN users a ON t.author_id = a.user_id
        LEFT JOIN users u ON t.user_id = u.user_id
        -- 关联转发推文
        LEFT JOIN tweets rt ON t.retweet_id = rt.tweet_id
        LEFT JOIN users rta ON rt.author_id = rta.user_id
        -- 关联引用推文
        LEFT JOIN tweets qt ON t.quote_id = qt.tweet_id
        LEFT JOIN users qta ON qt.author_id = qta.user_id
        -- 关联回复推文
        LEFT JOIN tweets rp ON t.reply_id = rp.tweet_id
        LEFT JOIN users rpa ON rp.author_id = rpa.user_id
        WHERE t.user_id = ? OR t.author_id = ?
        ORDER BY t.date DESC
        LIMIT ? OFFSET ?
    """,
        (user_id, user_id, per_page, offset),
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

        # 判断推文类型
        tweet["is_retweet"] = tweet["retweet_id"] > 0
        tweet["is_quote"] = tweet["quote_id"] > 0
        tweet["is_reply"] = tweet["reply_id"] > 0

        # 处理相关推文信息
        if tweet["is_retweet"] and tweet.get("retweet_content"):
            # 解析转发推文的媒体文件
            retweet_media_files = []
            if tweet.get("retweet_media_files"):
                retweet_media_files = json.loads(tweet["retweet_media_files"])

            tweet["retweet_info"] = {
                "content": tweet["retweet_content"],
                "author_id": tweet["retweet_author_id"],
                "user_id": tweet["retweet_user_id"],
                "author_name": tweet.get("retweet_author_name"),
                "author_nick": tweet.get("retweet_author_nick"),
                "author_avatar": tweet.get("retweet_author_avatar"),
                "media_files": retweet_media_files,
            }

        if tweet["is_quote"] and tweet.get("quote_content"):
            # 解析引用推文的媒体文件
            quote_media_files = []
            if tweet.get("quote_media_files"):
                quote_media_files = json.loads(tweet["quote_media_files"])

            tweet["quote_info"] = {
                "content": tweet["quote_content"],
                "author_id": tweet["quote_author_id"],
                "user_id": tweet["quote_user_id"],
                "author_name": tweet.get("quote_author_name"),
                "author_nick": tweet.get("quote_author_nick"),
                "author_avatar": tweet.get("quote_author_avatar"),
                "media_files": quote_media_files,
            }

        if tweet["is_reply"] and tweet.get("reply_content"):
            # 解析回复推文的媒体文件
            reply_media_files = []
            if tweet.get("reply_media_files"):
                reply_media_files = json.loads(tweet["reply_media_files"])

            tweet["reply_info"] = {
                "content": tweet["reply_content"],
                "author_id": tweet["reply_author_id"],
                "user_id": tweet["reply_user_id"],
                "author_name": tweet.get("reply_author_name"),
                "author_nick": tweet.get("reply_author_nick"),
                "author_avatar": tweet.get("reply_author_avatar"),
                "media_files": reply_media_files,
            }

        # 转换头像URL为本地路径
        tweet = process_tweet_data(tweet)

        tweets.append(tweet)

    conn.close()

    # 计算分页信息
    total_pages = (total_tweets + per_page - 1) // per_page
    pagination = get_pagination_range(page, total_pages)

    return render_template(
        "profile.html",
        user=user,
        tweets=tweets,
        page=page,
        total_pages=total_pages,
        pagination=pagination,
        total_tweets=total_tweets,
    )


@app.route("/tweet/<int:tweet_id>")
def tweet_detail(tweet_id):
    """推文详情页"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 获取推文详情（仅基础信息与转发信息，去掉正向引用/回复关联）
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
            u.profile_banner as user_banner,
            -- 转发推文信息
            rt.content as retweet_content,
            rt.author_id as retweet_author_id,
            rt.user_id as retweet_user_id,
            rt.media_files as retweet_media_files,
            rta.name as retweet_author_name,
            rta.nick as retweet_author_nick,
            rta.profile_image as retweet_author_avatar
        FROM tweets t
        LEFT JOIN users a ON t.author_id = a.user_id
        LEFT JOIN users u ON t.user_id = u.user_id
        LEFT JOIN tweets rt ON t.retweet_id = rt.tweet_id
        LEFT JOIN users rta ON rt.author_id = rta.user_id
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

    # 判断推文类型（仅保留转发标识；引用/回复改为反向查找）
    tweet["is_retweet"] = tweet["retweet_id"] > 0

    # 处理相关推文信息
    if tweet["is_retweet"] and tweet.get("retweet_content"):
        # 解析转发推文的媒体文件
        retweet_media_files = []
        if tweet.get("retweet_media_files"):
            retweet_media_files = json.loads(tweet["retweet_media_files"])

        tweet["retweet_info"] = {
            "content": tweet["retweet_content"],
            "author_id": tweet["retweet_author_id"],
            "user_id": tweet["retweet_user_id"],
            "author_name": tweet.get("retweet_author_name"),
            "author_nick": tweet.get("retweet_author_nick"),
            "author_avatar": tweet.get("retweet_author_avatar"),
            "media_files": retweet_media_files,
        }

    # 反向查找原始推文：如果当前推文是“引用者/回复者”，原始推文会在其他记录中以当前ID作为quote_id/reply_id
    # 原始的被引用推文（quoted original）
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
        WHERE t.quote_id = ?
        LIMIT 1
        """,
        (tweet_id,),
    )
    quoted_orig = cursor.fetchone()
    if quoted_orig:
        qo = dict(quoted_orig)
        qo_media = []
        if qo.get("media_files"):
            try:
                qo_media = json.loads(qo["media_files"])
            except Exception:
                qo_media = []
        tweet["quoted_info"] = {
            "tweet_id": qo.get("tweet_id"),
            "content": qo.get("content"),
            "author_id": qo.get("author_id"),
            "user_id": qo.get("user_id"),
            "author_name": qo.get("author_name"),
            "author_nick": qo.get("author_nick"),
            "author_avatar": qo.get("author_avatar"),
            "media_files": qo_media,
        }

    # 原始的被回复推文（replied original）
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
        WHERE t.reply_id = ?
        LIMIT 1
        """,
        (tweet_id,),
    )
    replied_orig = cursor.fetchone()
    if replied_orig:
        ro = dict(replied_orig)
        ro_media = []
        if ro.get("media_files"):
            try:
                ro_media = json.loads(ro["media_files"])
            except Exception:
                ro_media = []
        tweet["replied_info"] = {
            "tweet_id": ro.get("tweet_id"),
            "content": ro.get("content"),
            "author_id": ro.get("author_id"),
            "user_id": ro.get("user_id"),
            "author_name": ro.get("author_name"),
            "author_nick": ro.get("author_nick"),
            "author_avatar": ro.get("author_avatar"),
            "media_files": ro_media,
        }

    # 转换头像URL为本地路径
    tweet = process_tweet_data(tweet)

    conn.close()

    return render_template("tweet_detail.html", tweet=tweet)


@app.route("/search")
def search():
    """搜索功能"""
    query = request.args.get("q", "")
    year = request.args.get("year", "")
    month = request.args.get("month", "")
    page = request.args.get("page", 1, type=int)
    per_page = 20

    if not query and not year and not month:
        return render_template(
            "search.html",
            tweets=[],
            query="",
            year="",
            month="",
            page=1,
            total_pages=0,
            pagination=None,
        )

    conn = get_db_connection()
    cursor = conn.cursor()

    # 构建搜索条件
    conditions = []
    params = []

    if query:
        conditions.append("t.content LIKE ?")
        params.append(f"%{query}%")

    if year:
        conditions.append("strftime('%Y', t.date) = ?")
        params.append(year)

    if month:
        conditions.append("strftime('%m', t.date) = ?")
        params.append(month.zfill(2))

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    # 获取搜索结果总数
    count_sql = f"""
        SELECT COUNT(*) FROM tweets t WHERE {where_clause}
    """
    cursor.execute(count_sql, params)
    total_tweets = cursor.fetchone()[0]

    # 计算分页信息
    total_pages = (total_tweets + per_page - 1) // per_page
    offset = (page - 1) * per_page

    # 搜索推文内容
    cursor.execute(
        f"""
        SELECT 
            t.*,
            a.name as author_name,
            a.nick as author_nick,
            a.profile_image as author_avatar,
            u.name as user_name,
            u.nick as user_nick,
            u.profile_image as user_avatar,
            -- 相关推文信息
            rt.content as retweet_content,
            rt.author_id as retweet_author_id,
            rt.user_id as retweet_user_id,
            rt.media_files as retweet_media_files,
            rta.name as retweet_author_name,
            rta.nick as retweet_author_nick,
            rta.profile_image as retweet_author_avatar,
            qt.content as quote_content,
            qt.author_id as quote_author_id,
            qt.user_id as quote_user_id,
            qt.media_files as quote_media_files,
            qta.name as quote_author_name,
            qta.nick as quote_author_nick,
            qta.profile_image as quote_author_avatar,
            rp.content as reply_content,
            rp.author_id as reply_author_id,
            rp.user_id as reply_user_id,
            rp.media_files as reply_media_files,
            rpa.name as reply_author_name,
            rpa.nick as reply_author_nick,
            rpa.profile_image as reply_author_avatar
        FROM tweets t
        LEFT JOIN users a ON t.author_id = a.user_id
        LEFT JOIN users u ON t.user_id = u.user_id
        -- 关联转发推文
        LEFT JOIN tweets rt ON t.retweet_id = rt.tweet_id
        LEFT JOIN users rta ON rt.author_id = rta.user_id
        -- 关联引用推文
        LEFT JOIN tweets qt ON t.quote_id = qt.tweet_id
        LEFT JOIN users qta ON qt.author_id = qta.user_id
        -- 关联回复推文
        LEFT JOIN tweets rp ON t.reply_id = rp.tweet_id
        LEFT JOIN users rpa ON rp.author_id = rpa.user_id
        WHERE {where_clause}
        ORDER BY t.date DESC
        LIMIT ? OFFSET ?
    """,
        params + [per_page, offset],
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

        # 判断推文类型
        tweet["is_retweet"] = tweet["retweet_id"] > 0
        tweet["is_quote"] = tweet["quote_id"] > 0
        tweet["is_reply"] = tweet["reply_id"] > 0

        # 处理相关推文信息
        if tweet["is_retweet"] and tweet.get("retweet_content"):
            # 解析转发推文的媒体文件
            retweet_media_files = []
            if tweet.get("retweet_media_files"):
                retweet_media_files = json.loads(tweet["retweet_media_files"])

            tweet["retweet_info"] = {
                "content": tweet["retweet_content"],
                "author_id": tweet["retweet_author_id"],
                "user_id": tweet["retweet_user_id"],
                "author_name": tweet.get("retweet_author_name"),
                "author_nick": tweet.get("retweet_author_nick"),
                "author_avatar": tweet.get("retweet_author_avatar"),
                "media_files": retweet_media_files,
            }

        if tweet["is_quote"] and tweet.get("quote_content"):
            # 解析引用推文的媒体文件
            quote_media_files = []
            if tweet.get("quote_media_files"):
                quote_media_files = json.loads(tweet["quote_media_files"])

            tweet["quote_info"] = {
                "content": tweet["quote_content"],
                "author_id": tweet["quote_author_id"],
                "user_id": tweet["quote_user_id"],
                "author_name": tweet.get("quote_author_name"),
                "author_nick": tweet.get("quote_author_nick"),
                "author_avatar": tweet.get("quote_author_avatar"),
                "media_files": quote_media_files,
            }

        if tweet["is_reply"] and tweet.get("reply_content"):
            # 解析回复推文的媒体文件
            reply_media_files = []
            if tweet.get("reply_media_files"):
                reply_media_files = json.loads(tweet["reply_media_files"])

            tweet["reply_info"] = {
                "content": tweet["reply_content"],
                "author_id": tweet["reply_author_id"],
                "user_id": tweet["reply_user_id"],
                "author_name": tweet.get("reply_author_name"),
                "author_nick": tweet.get("reply_author_nick"),
                "author_avatar": tweet.get("reply_author_avatar"),
                "media_files": reply_media_files,
            }

        # 转换头像URL为本地路径
        tweet = process_tweet_data(tweet)

        tweets.append(tweet)

    conn.close()

    # 生成分页信息
    pagination = get_pagination_range(page, total_pages) if total_pages > 0 else None

    return render_template(
        "search.html",
        tweets=tweets,
        query=query,
        year=year,
        month=month,
        page=page,
        total_pages=total_pages,
        pagination=pagination,
    )


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
            a.name as author_name,
            a.nick as author_nick,
            a.profile_image as author_avatar
        FROM tweets t
        LEFT JOIN users a ON t.author_id = a.user_id
        ORDER BY t.favorite_count DESC
        LIMIT 10
    """
    )
    top_tweets = []
    for row in cursor.fetchall():
        tweet = dict(row)
        # 解析媒体文件JSON
        if tweet.get("media_files"):
            try:
                tweet["media_files"] = json.loads(tweet["media_files"])
            except (json.JSONDecodeError, TypeError):
                tweet["media_files"] = []
        else:
            tweet["media_files"] = []
        # 解析话题标签JSON
        if tweet.get("hashtags"):
            try:
                tweet["hashtags"] = json.loads(tweet["hashtags"])
            except (json.JSONDecodeError, TypeError):
                tweet["hashtags"] = []
        else:
            tweet["hashtags"] = []
        # 转换推文头像URL为本地路径
        tweet = process_tweet_data(tweet)
        top_tweets.append(tweet)
    stats["top_tweets"] = top_tweets

    conn.close()

    return render_template("stats.html", stats=stats)


@app.route("/api/translate", methods=["POST"])
def api_translate():
    """翻译API接口"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "请求数据为空"}), 400

        content = data.get("content", "")
        target_lang = data.get("target_lang", "zh")
        translation_service = data.get("translation_service", "google")
        openai_model = data.get("openai_model", "gpt-3.5-turbo")
        # 如果模型名称为空，使用默认值
        if not openai_model:
            openai_model = "gpt-3.5-turbo"
        api_key = data.get("api_key", "")
        api_secret = data.get("api_secret", "")
        api_url = data.get("api_url", "")

        if not content:
            return jsonify({"success": False, "error": "翻译内容为空"}), 400

        if not api_key:
            return jsonify({"success": False, "error": "API密钥未设置"}), 400

        # 创建翻译服务实例
        from translation_service import TranslationService

        service = TranslationService(
            service_type=translation_service,
            api_key=api_key,
            api_secret=api_secret,
            api_url=api_url,
            openai_model=openai_model,
        )

        # 执行翻译
        result = service.translate_tweet(content, target_lang)

        return jsonify(result)

    except Exception as e:
        return jsonify({"success": False, "error": f"翻译失败: {str(e)}"}), 500


@app.route("/api/detect-language", methods=["POST"])
def api_detect_language():
    """语言检测API接口"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "请求数据为空"}), 400

        content = data.get("content", "")
        translation_service = data.get("translation_service", "google")
        openai_model = data.get("openai_model", "gpt-3.5-turbo")
        # 如果模型名称为空，使用默认值
        if not openai_model:
            openai_model = "gpt-3.5-turbo"
        api_key = data.get("api_key", "")
        api_secret = data.get("api_secret", "")
        api_url = data.get("api_url", "")

        if not content:
            return jsonify({"success": False, "error": "检测内容为空"}), 400

        if not api_key:
            return jsonify({"success": False, "error": "API密钥未设置"}), 400

        # 创建翻译服务实例
        from translation_service import TranslationService

        service = TranslationService(
            service_type=translation_service,
            api_key=api_key,
            api_secret=api_secret,
            api_url=api_url,
            openai_model=openai_model,
        )

        # 执行语言检测
        result = service.detect_language(content)

        return jsonify(result)

    except Exception as e:
        return jsonify({"success": False, "error": f"语言检测失败: {str(e)}"}), 500


@app.route("/api/supported-languages")
def api_supported_languages():
    """获取支持的语言列表"""
    try:
        # 创建一个默认的翻译服务实例来获取支持的语言
        from translation_service import TranslationService

        service = TranslationService(service_type="google", api_key="dummy")
        languages = service.get_supported_languages()
        return jsonify({"success": True, "languages": languages})

    except Exception as e:
        return jsonify({"success": False, "error": f"获取语言列表失败: {str(e)}"}), 500


@app.route("/api/user/<int:user_id>/media")
def api_user_media(user_id: int):
    """获取用户媒体推文（后端筛选），返回HTML片段"""
    try:
        media_type = request.args.get("type", "all")  # all|images|videos
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)

        conn = get_db_connection()
        cursor = conn.cursor()

        # 基于 profile 页相同的查询，拿到该用户的所有推文（含相关信息）
        cursor.execute(
            """
        SELECT 
            t.*,
            a.name as author_name,
            a.nick as author_nick,
            a.profile_image as author_avatar,
            u.name as user_name,
            u.nick as user_nick,
            u.profile_image as user_avatar,
            -- 相关推文信息
            rt.content as retweet_content,
            rt.author_id as retweet_author_id,
            rt.user_id as retweet_user_id,
            rt.media_files as retweet_media_files,
            rta.name as retweet_author_name,
            rta.nick as retweet_author_nick,
            rta.profile_image as retweet_author_avatar,
            qt.content as quote_content,
            qt.author_id as quote_author_id,
            qt.user_id as quote_user_id,
            qt.media_files as quote_media_files,
            qta.name as quote_author_name,
            qta.nick as quote_author_nick,
            qta.profile_image as quote_author_avatar,
            rp.content as reply_content,
            rp.author_id as reply_author_id,
            rp.user_id as reply_user_id,
            rp.media_files as reply_media_files,
            rpa.name as reply_author_name,
            rpa.nick as reply_author_nick,
            rpa.profile_image as reply_author_avatar
        FROM tweets t
        LEFT JOIN users a ON t.author_id = a.user_id
        LEFT JOIN users u ON t.user_id = u.user_id
        LEFT JOIN tweets rt ON t.retweet_id = rt.tweet_id
        LEFT JOIN users rta ON rt.author_id = rta.user_id
        LEFT JOIN tweets qt ON t.quote_id = qt.tweet_id
        LEFT JOIN users qta ON qt.author_id = qta.user_id
        LEFT JOIN tweets rp ON t.reply_id = rp.tweet_id
        LEFT JOIN users rpa ON rp.author_id = rpa.user_id
        WHERE t.user_id = ? OR t.author_id = ?
        ORDER BY t.date DESC
        """,
            (user_id, user_id),
        )

        all_rows = cursor.fetchall()
        conn.close()

        tweets = []
        for row in all_rows:
            tweet = dict(row)

            # 解析媒体文件
            if tweet.get("media_files"):
                tweet["media_files"] = json.loads(tweet["media_files"]) or []
            else:
                tweet["media_files"] = []

            # 解析hashtags
            if tweet.get("hashtags"):
                try:
                    tweet["hashtags"] = json.loads(tweet["hashtags"]) or []
                except Exception:
                    tweet["hashtags"] = []
            else:
                tweet["hashtags"] = []

            # 标记类型
            tweet["is_retweet"] = tweet.get("retweet_id", 0) > 0
            tweet["is_quote"] = tweet.get("quote_id", 0) > 0
            tweet["is_reply"] = tweet.get("reply_id", 0) > 0

            # 相关推文媒体
            def parse_media_field(value):
                if not value:
                    return []
                try:
                    return json.loads(value) or []
                except Exception:
                    return []

            if tweet["is_retweet"] and tweet.get("retweet_content") is not None:
                tweet["retweet_info"] = {
                    "content": tweet.get("retweet_content"),
                    "author_id": tweet.get("retweet_author_id"),
                    "user_id": tweet.get("retweet_user_id"),
                    "author_name": tweet.get("retweet_author_name"),
                    "author_nick": tweet.get("retweet_author_nick"),
                    "author_avatar": tweet.get("retweet_author_avatar"),
                    "media_files": parse_media_field(tweet.get("retweet_media_files")),
                }

            if tweet["is_quote"] and tweet.get("quote_content") is not None:
                tweet["quote_info"] = {
                    "content": tweet.get("quote_content"),
                    "author_id": tweet.get("quote_author_id"),
                    "user_id": tweet.get("quote_user_id"),
                    "author_name": tweet.get("quote_author_name"),
                    "author_nick": tweet.get("quote_author_nick"),
                    "author_avatar": tweet.get("quote_author_avatar"),
                    "media_files": parse_media_field(tweet.get("quote_media_files")),
                }

            if tweet["is_reply"] and tweet.get("reply_content") is not None:
                tweet["reply_info"] = {
                    "content": tweet.get("reply_content"),
                    "author_id": tweet.get("reply_author_id"),
                    "user_id": tweet.get("reply_user_id"),
                    "author_name": tweet.get("reply_author_name"),
                    "author_nick": tweet.get("reply_author_nick"),
                    "author_avatar": tweet.get("reply_author_avatar"),
                    "media_files": parse_media_field(tweet.get("reply_media_files")),
                }

            # 转换头像/横幅URL等
            tweet = process_tweet_data(tweet)

            tweets.append(tweet)

        # 后端媒体筛选：按根推文媒体和 retweet/quote/reply 的媒体综合判断
        def is_video(path: str) -> bool:
            p = path.lower()
            return (
                p.endswith(".mp4")
                or p.endswith(".mov")
                or p.endswith(".avi")
                or p.endswith(".mkv")
                or p.endswith(".webm")
            )

        def match_tweet_media(tw: dict) -> bool:
            media_paths = []
            media_paths += tw.get("media_files", [])
            if tw.get("retweet_info"):
                media_paths += tw["retweet_info"].get("media_files", [])
            if tw.get("quote_info"):
                media_paths += tw["quote_info"].get("media_files", [])
            if tw.get("reply_info"):
                media_paths += tw["reply_info"].get("media_files", [])
            if not media_paths:
                return False
            if media_type == "images":
                return any(not is_video(p) for p in media_paths)
            if media_type == "videos":
                return any(is_video(p) for p in media_paths)
            return True  # all

        filtered = [tw for tw in tweets if match_tweet_media(tw)]

        # 分页
        start = (page - 1) * per_page
        end = start + per_page
        page_items = filtered[start:end]

        # 渲染为HTML片段（复用宏）
        from flask import render_template_string

        html = render_template_string(
            '{% from "tweet_conversation.html" import render_tweet_conversation %}'
            "{% for t in tweets %}{{ render_tweet_conversation(t) }}{% endfor %}",
            tweets=page_items,
        )

        return jsonify({"success": True, "html": html, "total": len(filtered)})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


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
