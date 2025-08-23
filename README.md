# Twitter Backup Processor & Viewer

A Python toolkit to process Twitter backup JSON files into a local SQLite database, and a full-featured web UI to browse and search your data. It can also associate local media files (images/videos) and supports multi-provider translation (OpenAI/Google/Baidu/Youdao/DeepL) via the web UI.

[中文说明](README_zh.md)

## Features

- Data Processor (`twitter_data_processor.py`)

  - Read all JSON files in `twitter-meta/`
  - Store tweets, users, and media references into SQLite
  - Associate files in `img/` with tweets by filename convention
  - Download user `profile_banner` and `profile_image` into `avatar/`
  - Avoid duplicate downloads via URL hash tracking
  - Quick database stats (`--stats`)
  - Automatic DB migration for new columns

- Web Viewer (`twitter_viewer.py`)
  - Timeline browsing with pagination
  - User profile pages with avatar/banner and user stats
  - Tweet detail page with related tweets
  - Powerful search by content/year/month
  - Stats page (overview, top tweets, etc.)
  - Media display (images/videos/avatars/banners)
  - Tweet types: retweet/reply/quote handling
  - Integrated translation with selectable provider and model
  - Modern responsive UI with light/dark theme

## Required directory layout (for your data folder)

```
your_data_folder/
├── twitter-meta/          # JSON metadata files
│   ├── 1448196924784328704.json
│   ├── 1448196924784328705.json
│   └── ...
├── img/                   # Optional: local media files (images/videos)
│   ├── 1448196924784328704_1.jpg
│   ├── 1448196924784328704_2.jpg
│   ├── 1448196924784328704_1.mp4
│   └── ...
└── avatar/                # Created automatically for downloaded avatars/banners
    ├── banner_832500321955962880.jpg
    ├── avatar_832500321955962880.jpg
    └── downloaded_images.txt
```

## Getting data with gallery-dl (optional but recommended)

- Install:

```bash
pip install gallery-dl
# or via your distro package manager
```

- Create `~/.config/gallery-dl/config.json`:

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

- Download examples:

```bash
# User timeline
gallery-dl "https://twitter.com/username"

# A specific tweet
gallery-dl "https://twitter.com/username/status/1234567890"

# Search results
gallery-dl "https://twitter.com/search?q=keyword"

# Lists
gallery-dl "https://twitter.com/username/lists/listname"
```

## Installation

```bash
pip install -r requirements.txt
```

## Usage

- Data processing

```bash
# Build or update the SQLite database in your data folder
python twitter_data_processor.py /path/to/your_data_folder

# Show quick DB statistics
python twitter_data_processor.py /path/to/your_data_folder --stats
```

- Start the web viewer

```bash
# Basic
python twitter_viewer.py /path/to/your_data_folder/twitter_data.db

# With host/port/debug options
python twitter_viewer.py /path/to/your_data_folder/twitter_data.db --host 0.0.0.0 --port 8080 --debug
```

Then open `http://localhost:5000`.

## Web UI highlights

- Responsive, modern layout with dark/light theme
- Infinite-like paging with smart navigation
- Tweet cards show content, user info, media, and type badges
- User profile page with avatar, banner, and counters
- Tweet detail with related conversation
- Search by content/year/month with pagination
- Built-in translation panel per tweet

## Translation

- Providers: `openai`, `google`, `baidu`, `youdao`, `deepl`
- How it works:

  - In the web UI, open the settings panel and choose provider
  - Fill required fields:
    - `translation_service`: one of the providers above
    - `api_key`: required for all providers
    - `api_secret`: required by some providers (e.g., Baidu/Youdao)
    - `api_url`: optional override for custom endpoints
    - `openai_model`: default `gpt-3.5-turbo`; choose preset or `custom`
  - The UI calls backend endpoints:
    - POST `/api/translate` with `{ content, target_lang, translation_service, api_key, api_secret, api_url, openai_model }`
    - POST `/api/detect-language`
    - GET `/api/supported-languages`
  - Note: API keys are sent from browser to server for each translation request; handle them prudently if exposing the app publicly.

- Supported language codes:
  - `zh`, `en`, `ja`, `ko`, `es`, `fr`, `de`, `ru`, `ar`, `hi`, `pt`, `it`

## Database schema

- Table `tweets` (created by `twitter_data_processor.py`)

  - `tweet_id` INTEGER PRIMARY KEY
  - `retweet_id`, `quote_id`, `reply_id` INTEGER
  - `conversation_id`, `source_id` INTEGER
  - `date` TEXT
  - `lang`, `source` TEXT
  - `sensitive` BOOLEAN
  - `sensitive_flags` TEXT (JSON)
  - `favorite_count`, `quote_count`, `reply_count`, `retweet_count`, `bookmark_count`, `view_count` INTEGER
  - `content` TEXT
  - `quote_by` TEXT
  - `count` INTEGER
  - `category`, `subcategory` TEXT
  - `media_files` TEXT (JSON array of associated filenames)
  - `author_id` INTEGER (FK to `users.user_id`)
  - `user_id` INTEGER (FK to `users.user_id`)
  - `hashtags` TEXT (JSON)
  - `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP

- Table `users`

  - `user_id` INTEGER PRIMARY KEY
  - `name`, `nick`, `location` TEXT
  - `date` TEXT
  - `verified`, `protected` BOOLEAN
  - `profile_banner`, `profile_image` TEXT
  - `favourites_count`, `followers_count`, `friends_count`, `listed_count`, `media_count`, `statuses_count` INTEGER
  - `description`, `url` TEXT
  - `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP

- Table `media_files`

  - `id` INTEGER PRIMARY KEY AUTOINCREMENT
  - `tweet_id` INTEGER (FK to `tweets.tweet_id`)
  - `file_name`, `file_type`, `file_path` TEXT
  - `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP

- Insert behavior uses `INSERT OR REPLACE` to avoid duplicates.

## Notes

- Rate limiting: when using gallery-dl, consider setting reasonable rates to avoid throttling.
- Storage: ensure sufficient disk space for media files.
- Legal: make sure your data collection complies with local laws and platform ToS.
- Missing files: the web UI gracefully handles missing media/avatars.

## Logging

- Both processor and viewer emit informative logs. Adjust `logging.basicConfig` in code if needed.

## Examples

```bash
# Process data
python twitter_data_processor.py /home/user/twitter_backup

# Show stats
python twitter_data_processor.py /home/user/twitter_backup --stats

# Start web UI
python twitter_viewer.py /home/user/twitter_backup/twitter_data.db
```
