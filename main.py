#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Twitter备份查看器
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from twitter_viewer import app, init_app


def main():
    """主函数"""
    # 检查命令行参数
    if len(sys.argv) < 2:
        print("使用方法: python run_optimized.py <数据库文件路径>")
        print("示例: python run_optimized.py ./data/twitter.db")
        sys.exit(1)

    db_path = sys.argv[1]

    # 检查数据库文件是否存在
    if not os.path.exists(db_path):
        print(f"错误: 数据库文件不存在: {db_path}")
        sys.exit(1)

    try:
        # 初始化应用
        init_app(db_path)

        # 启动Flask应用
        app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=True)

    except Exception as e:
        print(f"启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
