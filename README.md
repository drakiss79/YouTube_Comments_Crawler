# YouTube Comment Crawler

A Python tool to scrape comments and replies from YouTube videos using the YouTube Data API.

## Features

- Scrape comments and their nested replies from YouTube videos
- Support for both YouTube URLs and video IDs
- Export data to CSV or JSON format
- Clean text formatting and mention symbols
- Handle nested reply structures
- Support for large comment threads

## Installation

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/youtube-comment-scraper.git
cd youtube-comment-scraper
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Get a YouTube Data API key from [Google Cloud Console](https://console.cloud.google.com/)

## Usage

Basic usage:
```bash
python yt_crawler.py "VIDEO_URL" -k YOUR_API_KEY -o output.csv
```

Arguments:
- `video_input`: YouTube video URL or video ID
- `-k, --api-key`: Your YouTube Data API key (required)
- `-m, --max`: Maximum number of comments to retrieve (default: 100)
- `-o, --output`: Output file path (optional, supports .csv and .json)

Example with full options:
```bash
python yt_crawler.py "https://www.youtube.com/watch?v=VIDEO_ID" -k YOUR_API_KEY -m 1000 -o comments.csv
```

## Output Format

The CSV output includes the following columns:
- comment_type (main, reply_level_1, etc.)
- author
- text
- likes
- published
- parent_author
- parent_text

## License

MIT License
