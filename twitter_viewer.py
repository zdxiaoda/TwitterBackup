#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Twitter风格推文展示界面
使用Streamlit创建Web应用，从SQLite数据库读取推文数据
"""

import sqlite3
import pandas as pd
import streamlit as st
from datetime import datetime
import json
from pathlib import Path
import os

# 页面配置
st.set_page_config(
    page_title="Twitter Viewer",
    page_icon="🐦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 自定义CSS样式，模仿Twitter界面
st.markdown(
    """
<style>
    /* Twitter风格的CSS */
    .main {
        background-color: #ffffff;
    }
    
    .tweet-container {
        border: 1px solid #e1e8ed;
        border-radius: 12px;
        padding: 16px;
        margin: 8px 0;
        background-color: #ffffff;
        transition: background-color 0.2s;
    }
    
    .tweet-container:hover {
        background-color: #f7f9fa;
    }
    
    .tweet-header {
        display: flex;
        align-items: center;
        margin-bottom: 8px;
    }
    
    .user-info {
        display: flex;
        align-items: center;
        flex: 1;
    }
    
    .user-avatar {
        width: 48px;
        height: 48px;
        border-radius: 50%;
        margin-right: 12px;
        object-fit: cover;
    }
    
    .user-details {
        flex: 1;
    }
    
    .user-name {
        font-weight: bold;
        color: #14171a;
        font-size: 15px;
        margin: 0;
    }
    
    .user-handle {
        color: #657786;
        font-size: 14px;
        margin: 0;
    }
    
    .tweet-time {
        color: #657786;
        font-size: 14px;
        margin: 0;
    }
    
    .tweet-content {
        color: #14171a;
        font-size: 15px;
        line-height: 1.5;
        margin: 8px 0;
        white-space: pre-wrap;
    }
    
    .tweet-stats {
        display: flex;
        justify-content: space-between;
        margin-top: 12px;
        color: #657786;
        font-size: 13px;
    }
    
    .stat-item {
        display: flex;
        align-items: center;
        gap: 4px;
    }
    
    .media-container {
        margin-top: 12px;
        border-radius: 12px;
        overflow: hidden;
    }
    
    .media-image {
        max-width: 100%;
        border-radius: 12px;
    }
    
    .retweet-indicator {
        color: #657786;
        font-size: 13px;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 4px;
    }
    
    .sidebar {
        background-color: #f7f9fa;
    }
    
    .search-box {
        background-color: #f7f9fa;
        border: 1px solid #e1e8ed;
        border-radius: 20px;
        padding: 8px 16px;
        margin-bottom: 16px;
    }
</style>
""",
    unsafe_allow_html=True,
)


def load_database(db_path):
    """加载数据库连接"""
    try:
        conn = sqlite3.connect(db_path)
        return conn
    except Exception as e:
        st.error(f"数据库连接失败: {e}")
        return None


def get_tweets_data(conn, limit=50, offset=0, search_query=""):
    """获取推文数据"""
    try:
        # 构建查询语句
        base_query = """
        SELECT 
            t.tweet_id,
            t.content,
            t.date,
            t.favorite_count,
            t.retweet_count,
            t.reply_count,
            t.quote_count,
            t.media_files,
            t.author_id,
            t.user_id,
            t.hashtags,
            a.name as author_name,
            a.nick as author_nick,
            a.profile_image as author_avatar,
            u.name as user_name,
            u.nick as user_nick,
            u.profile_image as user_avatar
        FROM tweets t
        LEFT JOIN users a ON t.author_id = a.user_id
        LEFT JOIN users u ON t.user_id = u.user_id
        """

        if search_query:
            base_query += f" WHERE t.content LIKE '%{search_query}%'"

        base_query += " ORDER BY t.date DESC LIMIT ? OFFSET ?"

        df = pd.read_sql_query(base_query, conn, params=(limit, offset))
        return df
    except Exception as e:
        st.error(f"查询数据失败: {e}")
        return pd.DataFrame()


def format_time(date_str):
    """格式化时间显示"""
    try:
        if pd.isna(date_str):
            return "未知时间"

        # 解析时间字符串
        if isinstance(date_str, str):
            dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        else:
            dt = date_str

        now = datetime.now()
        diff = now - dt

        if diff.days > 0:
            return f"{diff.days}天前"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours}小时前"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes}分钟前"
        else:
            return "刚刚"
    except:
        return "未知时间"


def display_tweet(tweet_data, base_path):
    """显示单条推文"""
    # 判断是否为转发推文
    is_retweet = (
        tweet_data["author_id"] != tweet_data["user_id"]
        and not pd.isna(tweet_data["author_id"])
        and not pd.isna(tweet_data["user_id"])
    )

    # 确定显示的用户信息
    if is_retweet:
        display_name = tweet_data["user_name"] or tweet_data["user_nick"]
        display_nick = tweet_data["user_nick"]
        display_avatar = tweet_data["user_avatar"]
        original_author = tweet_data["author_name"] or tweet_data["author_nick"]
    else:
        display_name = tweet_data["author_name"] or tweet_data["author_nick"]
        display_nick = tweet_data["author_nick"]
        display_avatar = tweet_data["author_avatar"]
        original_author = None

    # 解析媒体文件
    media_files = []
    if tweet_data["media_files"] and tweet_data["media_files"] != "[]":
        try:
            media_files = json.loads(tweet_data["media_files"])
        except:
            media_files = []

    # 解析标签
    hashtags = []
    if tweet_data["hashtags"] and tweet_data["hashtags"] != "[]":
        try:
            hashtags = json.loads(tweet_data["hashtags"])
        except:
            hashtags = []

    # 创建推文HTML
    tweet_html = f"""
    <div class="tweet-container">
        {f'<div class="retweet-indicator">🔄 {original_author} 转发了</div>' if is_retweet else ''}
        <div class="tweet-header">
            <div class="user-info">
                <img src="{display_avatar or 'https://abs.twimg.com/sticky/default_profile_images/default_profile_normal.png'}" 
                     class="user-avatar" alt="头像">
                <div class="user-details">
                    <div class="user-name">{display_name or '未知用户'}</div>
                    <div class="user-handle">@{display_nick or 'unknown'}</div>
                </div>
            </div>
            <div class="tweet-time">{format_time(tweet_data['date'])}</div>
        </div>
        <div class="tweet-content">{tweet_data['content'] or ''}</div>
    """

    # 添加媒体文件
    if media_files:
        tweet_html += '<div class="media-container">'
        for media_file in media_files[:4]:  # 最多显示4个媒体文件
            media_path = Path(base_path) / media_file
            if media_path.exists():
                if media_file.lower().endswith((".jpg", ".jpeg", ".png", ".gif")):
                    tweet_html += f'<img src="data:image/jpeg;base64,{get_image_base64(media_path)}" class="media-image">'
                elif media_file.lower().endswith((".mp4", ".avi", ".mov")):
                    tweet_html += f'<video controls class="media-image"><source src="file://{media_path}"></video>'
        tweet_html += "</div>"

    # 添加标签
    if hashtags:
        hashtag_html = " ".join(
            [f'<span style="color: #1da1f2;">#{tag}</span>' for tag in hashtags]
        )
        tweet_html += f'<div style="margin-top: 8px;">{hashtag_html}</div>'

    # 添加统计信息
    tweet_html += f"""
        <div class="tweet-stats">
            <div class="stat-item">💬 {tweet_data['reply_count'] or 0}</div>
            <div class="stat-item">🔄 {tweet_data['retweet_count'] or 0}</div>
            <div class="stat-item">❤️ {tweet_data['favorite_count'] or 0}</div>
            <div class="stat-item">📊 {tweet_data['quote_count'] or 0}</div>
        </div>
    </div>
    """

    return tweet_html


def get_image_base64(image_path):
    """获取图片的base64编码（简化版本）"""
    try:
        import base64

        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except:
        return ""


def main():
    """主函数"""
    st.title("🐦 Twitter Viewer")

    # 侧边栏配置
    with st.sidebar:
        st.header("设置")

        # 数据库路径选择
        db_path = st.text_input(
            "数据库路径", value="twitter_data.db", help="输入SQLite数据库文件的路径"
        )

        # 搜索功能
        search_query = st.text_input(
            "搜索推文", placeholder="输入关键词搜索...", help="在推文内容中搜索关键词"
        )

        # 每页显示数量
        tweets_per_page = st.slider(
            "每页显示推文数", min_value=10, max_value=100, value=20, step=10
        )

        # 数据路径（用于媒体文件）
        base_path = st.text_input(
            "数据根目录", value=".", help="包含img文件夹的数据根目录路径"
        )

        # 统计信息
        if st.button("显示统计信息"):
            conn = load_database(db_path)
            if conn:
                try:
                    stats_query = """
                    SELECT 
                        COUNT(*) as total_tweets,
                        COUNT(CASE WHEN author_id != user_id THEN 1 END) as retweets,
                        COUNT(CASE WHEN media_files != '[]' THEN 1 END) as tweets_with_media
                    FROM tweets
                    """
                    stats_df = pd.read_sql_query(stats_query, conn)
                    st.write("### 统计信息")
                    st.write(f"总推文数: {stats_df.iloc[0]['total_tweets']}")
                    st.write(f"转发推文: {stats_df.iloc[0]['retweets']}")
                    st.write(f"包含媒体: {stats_df.iloc[0]['tweets_with_media']}")
                except Exception as e:
                    st.error(f"获取统计信息失败: {e}")
                finally:
                    conn.close()

    # 主内容区域
    if db_path:
        conn = load_database(db_path)
        if conn:
            try:
                # 分页
                page = st.session_state.get("page", 0)
                offset = page * tweets_per_page

                # 获取推文数据
                tweets_df = get_tweets_data(conn, tweets_per_page, offset, search_query)

                if not tweets_df.empty:
                    st.write(f"### 显示第 {page + 1} 页，共 {len(tweets_df)} 条推文")

                    # 显示推文
                    for _, tweet in tweets_df.iterrows():
                        tweet_html = display_tweet(tweet, base_path)
                        st.markdown(tweet_html, unsafe_allow_html=True)

                    # 分页控制
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col1:
                        if st.button("上一页") and page > 0:
                            st.session_state.page = page - 1
                            st.rerun()

                    with col2:
                        st.write(f"第 {page + 1} 页")

                    with col3:
                        if len(tweets_df) == tweets_per_page:
                            if st.button("下一页"):
                                st.session_state.page = page + 1
                                st.rerun()
                else:
                    st.info("没有找到推文数据")

            except Exception as e:
                st.error(f"加载数据失败: {e}")
            finally:
                conn.close()
        else:
            st.error("无法连接到数据库，请检查数据库路径是否正确")
    else:
        st.info("请在侧边栏输入数据库路径")


if __name__ == "__main__":
    main()
