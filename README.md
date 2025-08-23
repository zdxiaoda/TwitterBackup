# Twitter 数据处理脚本

这是一个用于处理 Twitter 备份数据的 Python 脚本，可以读取 JSON 格式的推文数据，将其存储到 SQLite 数据库中，并下载相关的图片和视频文件。

## 功能特性

1. **JSON 数据处理**: 读取`twitter-meta`文件夹中的所有 JSON 文件
2. **数据库存储**: 将数据保存到 SQLite 数据库中，包含推文、用户和媒体文件信息
3. **媒体文件关联**: 自动关联`img`文件夹中的图片/视频文件
4. **头像下载**: 自动下载用户的`profile_banner`和`profile_image`到`avatar`文件夹
5. **重复下载避免**: 使用哈希值避免重复下载相同的图片
6. **统计信息**: 提供数据库统计信息查询功能

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

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 基本用法

```bash
python twitter_data_processor.py /path/to/your/data/folder
```

### 查看统计信息

```bash
python twitter_data_processor.py /path/to/your/data/folder --stats
```

## 数据库结构

脚本会创建以下三个表：

### tweets 表

存储推文的基本信息，包括：

- tweet_id: 推文 ID（主键）
- content: 推文内容
- date: 发布时间
- favorite_count, retweet_count 等统计信息
- media_files: 关联的媒体文件列表（JSON 格式）

### users 表

存储用户信息，包括：

- user_id: 用户 ID（主键）
- name, nick: 用户名和昵称
- profile_banner, profile_image: 头像和横幅图片 URL
- followers_count, friends_count 等统计信息

### media_files 表

存储媒体文件信息，包括：

- tweet_id: 关联的推文 ID
- file_name: 文件名
- file_type: 文件类型
- file_path: 文件路径

## 示例

假设你有一个包含 Twitter 备份数据的文件夹：

```bash
# 处理数据
python twitter_data_processor.py /home/user/twitter_backup

# 查看处理结果统计
python twitter_data_processor.py /home/user/twitter_backup --stats
```

## 注意事项

1. 脚本会自动创建`avatar`文件夹和`downloaded_images.txt`文件来跟踪已下载的图片
2. 为了避免重复下载，脚本使用 URL 的 MD5 哈希值来判断图片是否已下载
3. 下载图片时会添加适当的请求头，模拟浏览器行为
4. 处理大量文件时，脚本会在每个文件处理后添加小延迟，避免请求过于频繁
5. 所有操作都有详细的日志记录，方便调试和监控

## 错误处理

- 如果 JSON 文件格式不正确，脚本会记录错误并继续处理其他文件
- 如果图片下载失败，脚本会记录错误但不会中断整个处理过程
- 数据库操作使用`INSERT OR REPLACE`，确保数据不会重复

## 日志

脚本会输出详细的日志信息，包括：

- 处理进度
- 成功/失败的文件数量
- 下载的图片信息
- 错误详情

日志级别可以通过修改代码中的`logging.basicConfig`来调整。
