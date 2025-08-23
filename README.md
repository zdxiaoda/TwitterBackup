# Twitter 数据处理脚本

这是一个用于处理 Twitter 备份数据的 Python 脚本，可以读取 JSON 格式的推文数据，将其存储到 SQLite 数据库中，并下载相关的图片和视频文件。同时提供了一个功能完整的 Web 界面来浏览和搜索数据。

## 功能特性

### 数据处理脚本 (twitter_data_processor.py)

1. **JSON 数据处理**: 读取`twitter-meta`文件夹中的所有 JSON 文件
2. **数据库存储**: 将数据保存到 SQLite 数据库中，包含推文、用户和媒体文件信息
3. **媒体文件关联**: 自动关联`img`文件夹中的图片/视频文件
4. **头像下载**: 自动下载用户的`profile_banner`和`profile_image`到`avatar`文件夹
5. **重复下载避免**: 使用哈希值避免重复下载相同的图片
6. **统计信息**: 提供数据库统计信息查询功能
7. **数据库升级**: 自动升级数据库结构，添加新字段

### Web 查看器 (twitter_viewer.py)

1. **时间线浏览**: 按时间顺序显示所有推文，支持分页
2. **用户资料**: 查看用户详细信息、头像和推文列表
3. **推文详情**: 查看单条推文的完整信息和相关推文
4. **搜索功能**: 支持按内容、年份、月份搜索推文
5. **统计页面**: 显示数据概览、最活跃用户、最受欢迎推文
6. **媒体文件支持**: 自动显示图片、视频、头像和横幅图片
7. **推文类型识别**: 自动识别转发、回复、引用推文并正确显示

## 文件夹结构要求

```
your_data_folder/
├── twitter-meta/          # 包含JSON文件的文件夹
│   ├── 1448196924784328704.json
│   ├── 1448196924784328705.json
│   └── ...
├── img/                   # 包含媒体文件的文件夹（可选）
│   ├── 1448196924784328704_1.jpg
│   ├── 1448196924784328704_2.jpg
│   ├── 1448196924784328704_1.mp4
│   └── ...
└── avatar/                # 头像文件下载文件夹（自动创建）
    ├── banner_832500321955962880.jpg
    ├── avatar_832500321955962880.jpg
    └── downloaded_images.txt
```

## 数据获取

### 使用 gallery-dl 获取 Twitter 数据

在开始处理数据之前，您需要先使用 gallery-dl 工具从 Twitter 获取数据。gallery-dl 是一个强大的媒体下载工具，支持从多个平台下载内容。

#### 1. 安装 gallery-dl

```bash
# 使用 pip 安装
pip install gallery-dl

# 或者使用系统包管理器
# Ubuntu/Debian
sudo apt install gallery-dl

# Arch Linux
sudo pacman -S gallery-dl
```

#### 2. 创建配置文件

在您的主目录下创建 gallery-dl 配置文件：

```bash
mkdir -p ~/.config/gallery-dl
```

创建配置文件 `~/.config/gallery-dl/config.json`：

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

#### 3. 配置说明

- **extractor.twitter**: Twitter 提取器配置

  - `text-tweets`: 下载文本推文
  - `include`: 包含时间线推文
  - `videos`: 下载视频文件
  - `retweets`: 包含转发
  - `quoted`: 包含引用推文

- **downloader.http**: 下载器配置

  - `rate`: 限制下载速度为 1MB/s，避免被限制

- **postprocessors**: 后处理器配置
  - 将推文元数据保存为 JSON 文件到 `twitter-meta` 文件夹
  - 文件名格式为 `{tweet_id}.json`

#### 4. 下载数据

```bash
# 下载指定用户的时间线
gallery-dl "https://twitter.com/username"

# 下载指定推文
gallery-dl "https://twitter.com/username/status/1234567890"

# 下载搜索结果
gallery-dl "https://twitter.com/search?q=keyword"

# 下载列表
gallery-dl "https://twitter.com/username/lists/listname"
```

#### 5. 输出结构

下载完成后，您将得到以下文件夹结构：

```
your_download_folder/
├── twitter-meta/          # JSON 元数据文件
│   ├── 1448196924784328704.json
│   ├── 1448196924784328705.json
│   └── ...
└── img/                   # 媒体文件（图片/视频）
    ├── 1448196924784328704_1.jpg
    ├── 1448196924784328704_2.jpg
    ├── 1448196924784328704_1.mp4
    └── ...
```

### 注意事项

1. **速率限制**: 建议设置合理的下载速率，避免被 Twitter 限制
2. **认证**: 某些内容可能需要登录才能访问，请参考 gallery-dl 的认证文档
3. **法律合规**: 请确保您的数据获取行为符合相关法律法规和 Twitter 的服务条款
4. **存储空间**: 确保有足够的磁盘空间存储下载的数据

## 安装依赖

### 项目依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 数据处理

#### 基本用法

```bash
python twitter_data_processor.py /path/to/your/data/folder
```

#### 查看统计信息

```bash
python twitter_data_processor.py /path/to/your/data/folder --stats
```

### Web 界面展示

项目还提供了一个功能完整的 Web 界面来展示和浏览 Twitter 数据。

#### 启动 Web 服务器

```bash
# 基本启动
python twitter_viewer.py /path/to/your/data/folder/twitter_data.db

# 指定主机和端口
python twitter_viewer.py /path/to/your/data/folder/twitter_data.db --host 0.0.0.0 --port 8080

# 调试模式
python twitter_viewer.py /path/to/your/data/folder/twitter_data.db --debug
```

#### Web 界面功能

启动后，您可以通过浏览器访问 `http://localhost:5000` 来使用以下功能：

1. **首页时间线**

   - 按时间顺序显示所有推文
   - 支持分页浏览（每页 20 条）
   - 显示推文内容、用户信息、媒体文件
   - 支持转发、回复、引用推文的展示
   - 智能分页导航

2. **用户资料页面**

   - 查看用户详细信息
   - 显示用户头像和横幅图片
   - 查看用户的推文列表（分页）
   - 显示用户统计信息

3. **推文详情页面**

   - 查看单条推文的详细信息
   - 显示完整的推文内容
   - 查看关联的媒体文件
   - 显示推文的互动数据（点赞、转发、回复数）
   - 显示相关推文（回复、引用等）

4. **搜索功能**

   - 搜索推文内容
   - 按年份筛选
   - 按月份筛选
   - 支持组合搜索
   - 搜索结果分页

5. **统计页面**

   - 显示总体统计信息
   - 最活跃用户排行（前 10 名）
   - 最受欢迎推文排行（按点赞数，前 10 名）
   - 数据概览（推文数、用户数、媒体文件数等）

6. **媒体文件支持**
   - 自动显示图片和视频
   - 支持头像和横幅图片
   - 本地文件路径映射
   - 自动处理媒体文件路径

#### 界面特性

- **响应式设计**: 支持桌面和移动设备
- **深色/浅色主题**: 可切换的界面主题
- **现代化 UI**: 类似 Twitter 的界面设计
- **快速加载**: 优化的数据库查询和页面渲染
- **智能分页**: 自动计算分页信息，支持大量数据

## 数据库结构

脚本会创建以下三个表：

### tweets 表

存储推文的基本信息，包括：

- `tweet_id`: 推文 ID（主键）
- `retweet_id`, `quote_id`, `reply_id`: 关联推文 ID
- `conversation_id`, `source_id`: 对话和来源 ID
- `date`: 发布时间
- `lang`, `source`: 语言和来源
- `sensitive`, `sensitive_flags`: 敏感内容标记
- `favorite_count`, `retweet_count`, `reply_count`, `quote_count`, `bookmark_count`, `view_count`: 互动统计
- `content`: 推文内容
- `quote_by`: 引用来源
- `category`, `subcategory`: 分类信息
- `media_files`: 关联的媒体文件列表（JSON 格式）
- `author_id`, `user_id`: 作者和用户 ID
- `hashtags`: 话题标签（JSON 格式）
- `created_at`: 记录创建时间

### users 表

存储用户信息，包括：

- `user_id`: 用户 ID（主键）
- `name`, `nick`: 用户名和昵称
- `location`: 位置信息
- `date`: 注册日期
- `verified`, `protected`: 认证和保护状态
- `profile_banner`, `profile_image`: 头像和横幅图片 URL
- `favourites_count`, `followers_count`, `friends_count`, `listed_count`, `media_count`, `statuses_count`: 用户统计
- `description`: 用户描述
- `url`: 用户网站
- `created_at`: 记录创建时间

### media_files 表

存储媒体文件信息，包括：

- `id`: 自增主键
- `tweet_id`: 关联的推文 ID
- `file_name`: 文件名
- `file_type`: 文件类型
- `file_path`: 文件路径
- `created_at`: 记录创建时间

## 示例

假设你有一个包含 Twitter 备份数据的文件夹：

```bash
# 处理数据
python twitter_data_processor.py /home/user/twitter_backup

# 查看处理结果统计
python twitter_data_processor.py /home/user/twitter_backup --stats

# 启动Web界面
python twitter_viewer.py /home/user/twitter_backup/twitter_data.db
```

## 注意事项

1. 脚本会自动创建`avatar`文件夹和`downloaded_images.txt`文件来跟踪已下载的图片
2. 为了避免重复下载，脚本使用 URL 的 MD5 哈希值来判断图片是否已下载
3. 下载图片时会添加适当的请求头，模拟浏览器行为
4. 处理大量文件时，脚本会在每个文件处理后添加小延迟，避免请求过于频繁
5. 所有操作都有详细的日志记录，方便调试和监控
6. 数据库使用`INSERT OR REPLACE`，确保数据不会重复
7. 支持数据库结构自动升级，添加新字段

## 错误处理

- 如果 JSON 文件格式不正确，脚本会记录错误并继续处理其他文件
- 如果图片下载失败，脚本会记录错误但不会中断整个处理过程
- 数据库操作使用`INSERT OR REPLACE`，确保数据不会重复
- Web 界面会自动处理文件不存在的情况，显示默认头像

## 日志

脚本会输出详细的日志信息，包括：

- 处理进度
- 成功/失败的文件数量
- 下载的图片信息
- 错误详情
- 数据库升级信息

日志级别可以通过修改代码中的`logging.basicConfig`来调整。

## 性能优化

1. **批量处理**: 使用事务批量提交数据库操作
2. **索引优化**: 数据库表已针对查询进行了优化
3. **分页加载**: Web 界面使用分页减少内存占用
4. **缓存机制**: 避免重复下载相同的图片
5. **延迟控制**: 添加适当延迟避免请求过于频繁
