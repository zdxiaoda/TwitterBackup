# Twitter 数据处理与查看器 (中文)

一个用于将 Twitter 备份 JSON 文件导入到本地 SQLite，并通过 Web 界面浏览/搜索数据的工具集。可关联本地媒体文件（图片/视频），并在 Web 端集成多翻译服务（OpenAI/Google/百度/有道/DeepL）。

## 功能特性

- 数据处理器（`twitter_data_processor.py`）

  - 读取 `twitter-meta/` 中的 JSON
  - 写入 SQLite：推文、用户、媒体引用
  - 依据文件名规则关联 `img/` 媒体
  - 下载 `profile_banner` 与 `profile_image` 到 `avatar/`
  - 通过 URL 哈希避免重复下载
  - 快速统计 `--stats`
  - 自动数据库结构升级

- Web 查看器（`twitter_viewer.py`）
  - 时间线分页浏览
  - 用户页（头像/横幅/统计）
  - 推文详情与相关推文
  - 内容/年份/月份搜索
  - 统计页（概览、热门等）
  - 媒体显示（图片/视频/头像/横幅）
  - 转发/回复/引用识别与展示
  - 集成翻译（选择服务与模型）
  - 响应式现代 UI，支持明暗主题

## 数据目录结构

```
your_data_folder/
├── twitter-meta/          # JSON 元数据文件
│   ├── 1448196924784328704.json
│   ├── 1448196924784328705.json
│   └── ...
├── img/                   # 可选：本地媒体文件（图片/视频）
│   ├── 1448196924784328704_1.jpg
│   ├── 1448196924784328704_2.jpg
│   ├── 1448196924784328704_1.mp4
│   └── ...
└── avatar/                # 自动创建，用于下载的头像/横幅
    ├── banner_832500321955962880.jpg
    ├── avatar_832500321955962880.jpg
    └── downloaded_images.txt
```

## 使用 gallery-dl 获取数据（可选但推荐）

- 安装：

```bash
pip install gallery-dl
# 或通过系统包管理器
```

- 创建 `~/.config/gallery-dl/config.json`：

```json
{
  "extractor": {
    "twitter": {
      "text-tweets": true,
      "include": "timeline",
      "videos": true,
      "retweets": true,
      "quoted": true
    }
  },
  "downloader": {
    "http": {
      "rate": "1M"
    }
  },
  "output": {
    "mode": "terminal",
    "progress": true
  },
  "postprocessors": [
    {
      "name": "metadata",
      "mode": "json",
      "extension": "json",
      "directory": ["twitter-meta"],
      "indent": 4,
      "event": "post",
      "filename": "{tweet_id}.json"
    }
  ]
}
```

- 下载示例：

```bash
# 用户时间线
gallery-dl "https://twitter.com/username"

# 特定推文
gallery-dl "https://twitter.com/username/status/1234567890"

# 搜索结果
gallery-dl "https://twitter.com/search?q=keyword"

# 列表
gallery-dl "https://twitter.com/username/lists/listname"
```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

- 数据处理

```bash
# 在数据文件夹中构建或更新 SQLite 数据库
python twitter_data_processor.py /path/to/your_data_folder

# 显示快速数据库统计
python twitter_data_processor.py /path/to/your_data_folder --stats
```

- 启动 Web 查看器

```bash
# 基本启动
python twitter_viewer.py /path/to/your_data_folder/twitter_data.db

# 指定主机/端口/调试选项
python twitter_viewer.py /path/to/your_data_folder/twitter_data.db --host 0.0.0.0 --port 8080 --debug
```

然后打开 `http://localhost:5000`。

## Web UI 亮点

- 响应式现代布局，支持明暗主题
- 类似无限滚动的智能分页导航
- 推文卡片显示内容、用户信息、媒体和类型徽章
- 用户资料页，包含头像、横幅和计数器
- 推文详情与相关对话
- 按内容/年份/月份搜索，支持分页
- 每条推文内置翻译面板

## 翻译功能

- 支持服务：`openai`、`google`、`baidu`、`youdao`、`deepl`
- 工作原理：

  - 在 Web UI 中，打开设置面板并选择服务
  - 填写必需字段：
    - `translation_service`：上述服务之一
    - `api_key`：所有服务均必需
    - `api_secret`：部分服务需要（如百度/有道）
    - `api_url`：可选的自定义端点覆盖
    - `openai_model`：默认 `gpt-3.5-turbo`；选择预设或 `custom`
  - UI 调用后端端点：
    - POST `/api/translate` 携带 `{ content, target_lang, translation_service, api_key, api_secret, api_url, openai_model }`
    - POST `/api/detect-language`
    - GET `/api/supported-languages`
  - 注意：API 密钥会随每次翻译请求从浏览器发送到服务器；如果公开暴露应用，请谨慎处理。

- 支持的语言代码：
  - `zh`、`en`、`ja`、`ko`、`es`、`fr`、`de`、`ru`、`ar`、`hi`、`pt`、`it`

## 数据库结构

- `tweets` 表（由 `twitter_data_processor.py` 创建）

  - `tweet_id` INTEGER PRIMARY KEY
  - `retweet_id`、`quote_id`、`reply_id` INTEGER
  - `conversation_id`、`source_id` INTEGER
  - `date` TEXT
  - `lang`、`source` TEXT
  - `sensitive` BOOLEAN
  - `sensitive_flags` TEXT (JSON)
  - `favorite_count`、`quote_count`、`reply_count`、`retweet_count`、`bookmark_count`、`view_count` INTEGER
  - `content` TEXT
  - `quote_by` TEXT
  - `count` INTEGER
  - `category`、`subcategory` TEXT
  - `media_files` TEXT (关联文件名的 JSON 数组)
  - `author_id` INTEGER (FK 到 `users.user_id`)
  - `user_id` INTEGER (FK 到 `users.user_id`)
  - `hashtags` TEXT (JSON)
  - `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP

- `users` 表

  - `user_id` INTEGER PRIMARY KEY
  - `name`、`nick`、`location` TEXT
  - `date` TEXT
  - `verified`、`protected` BOOLEAN
  - `profile_banner`、`profile_image` TEXT
  - `favourites_count`、`followers_count`、`friends_count`、`listed_count`、`media_count`、`statuses_count` INTEGER
  - `description`、`url` TEXT
  - `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP

- `media_files` 表

  - `id` INTEGER PRIMARY KEY AUTOINCREMENT
  - `tweet_id` INTEGER (FK 到 `tweets.tweet_id`)
  - `file_name`、`file_type`、`file_path` TEXT
  - `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP

- 插入行为使用 `INSERT OR REPLACE` 避免重复。

## 注意事项

- 速率限制：使用 gallery-dl 时，考虑设置合理的速率以避免被限制。
- 存储：确保有足够的磁盘空间存储媒体文件。
- 法律合规：确保您的数据收集符合当地法律和平台服务条款。
- 缺失文件：Web UI 优雅地处理缺失的媒体/头像。

## 日志

- 处理器和查看器都会输出信息性日志。如需调整，可修改代码中的 `logging.basicConfig`。

## 示例

```bash
# 处理数据
python twitter_data_processor.py /home/user/twitter_backup

# 显示统计
python twitter_data_processor.py /home/user/twitter_backup --stats

# 启动 Web UI
python twitter_viewer.py /home/user/twitter_backup/twitter_data.db
```
