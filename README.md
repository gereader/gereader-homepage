# Newsfeed

A self-hosted RSS news aggregator built with GitHub Pages and GitHub Actions.
Automatically fetches and displays articles from configured RSS/Atom feeds on a static webpage with filtering, search, and read tracking capabilities.

[Read the project writeup on my blog](https://blog.gereader.xyz/posts/rss-news-aggregator/)

## Features

- **Automated Feed Fetching**: GitHub Actions runs on a schedule to pull latest articles
- **Static Hosting**: No database or server required, this runs entirely on GitHub Pages
- **Client-Side Features**:
  - Filter by source or tag
  - Search articles by title and summary
  - Mark articles as read/unread
  - Hide read articles
  - Light/dark mode toggle
  - Pagination (10 articles per page)
- **Archive System**: Automatically archives articles older than 90 days
- **Image Extraction**: Pulls first image from RSS content for thumbnails
- **Tag Aggregation**: Collects tags from RSS feeds plus manual tagging

## Tech Stack

- **Python 3.11+** - RSS parsing and JSON generation
- **GitHub Actions** - Automated feed fetching
- **GitHub Pages** - Free static hosting
- **Vanilla JavaScript** - Client-side interactivity
- **localStorage** - Read state and filter preferences

## Project Structure

```
gereader-homepage/
├── .github/
│   └── workflows/
│       └── fetch-feeds.yml      # GitHub Actions workflow
├── scripts/
│   ├── fetch_rss.py             # RSS fetching and parsing script
│   └── requirements.txt         # Python dependencies
├── feeds.json                   # Current articles (generated)
├── archive.json                 # Archived articles (generated)
├── index.html                   # Main page
├── archive.html                 # Archive page
└── LICENSE                      # MIT License
```

## Setup

### Prerequisites

- GitHub account
- Python 3.11+ (for local development)
- Optional: Custom domain

### Installation

1. **Fork or clone this repository**

2. **Configure RSS feeds** in `scripts/fetch_rss.py`:
   ```python
   FEEDS = [
       {
           "url": "https://example.com/feed.xml",
           "title": "Example Blog",
           "manual_tags": ["technology"]
       },
       # Add more feeds...
   ]
   ```

3. **Enable GitHub Actions**:
   - Go to repository Settings → Actions → General
   - Under "Workflow permissions", select "Read and write permissions"
   - Save changes

4. **Enable GitHub Pages**:
   - Go to Settings → Pages
   - Under "Source", select "Deploy from a branch"
   - Select your main branch
   - Save

5. **Trigger initial feed fetch**:
   - Go to Actions tab
   - Select "Fetch RSS Feeds" workflow
   - Click "Run workflow" → "Run workflow"

6. **Access your site**:
   - Your site will be available at `https://<username>.github.io/<repository-name>/`

### Custom Domain (Optional)

1. In repository Settings → Pages, add your custom domain
2. Configure DNS with your registrar:
   - Add CNAME record pointing to `<username>.github.io`
3. Wait for DNS propagation and SSL certificate provisioning
4. Enable "Enforce HTTPS" in GitHub Pages settings

## Configuration

### Feed Update Schedule

The workflow runs at these times (Pacific Time):
- Midnight
- 7am
- 11am
- 1pm
- 4pm
- 6pm

Modify the cron schedule in `.github/workflows/fetch-feeds.yml`:
```yaml
schedule:
  - cron: '0 1,7,14,18,23 * * *'  # UTC-7 for Pacific Time
```

### Archive Threshold

Articles older than 90 days are moved to archive. Change this in `scripts/fetch_rss.py`:
```python
DAYS_IN_CURRENT = 90  # Adjust as needed
```

### Articles Per Page

Default is 10 articles per page. Modify in `index.html`:
```javascript
const articlesPerPage = 10;  // Change this value
```

## Local Development

1. **Install dependencies**:
   ```bash
   pip install -r scripts/requirements.txt
   ```

2. **Fetch feeds**:
   ```bash
   python3 scripts/fetch_rss.py
   ```

3. **Run local server**:
   ```bash
   python3 -m http.server 8000
   ```

4. **View in browser**:
   - Navigate to `http://localhost:8000`

## How It Works

### Feed Fetching Process

1. GitHub Actions triggers on schedule or manual dispatch
2. Python script parses each configured RSS/Atom feed
3. Extracts article metadata: title, link, date, source, image, summary, tags
4. Deduplicates articles by URL
5. Sorts by publication date (newest first)
6. Filters articles into current (`feeds.json`) and archive (`archive.json`) based on age
7. Commits updated JSON files to repository

### Client-Side Features

- **Read Tracking**: Article URLs stored in localStorage, persists across sessions
- **Filters**: Applied client-side on the current page's filtered dataset
- **Dark Mode**: Preference saved to localStorage, respects system preference by default
- **Pagination**: Dynamically calculated based on filtered article count

## Dependencies

### Python
- `feedparser` - RSS/Atom feed parsing
- `python-dateutil` - Date parsing and manipulation

### GitHub Actions
- `actions/checkout@v4` - Repository checkout
- `actions/setup-python@v5` - Python environment setup

## Browser Compatibility

Requires modern browser with support for:
- ES6+ JavaScript
- CSS Variables
- localStorage
- Fetch API

## License

MIT License - see [LICENSE](LICENSE) file for details

## Contributing

This is a personal project, but feel free to fork and adapt for your own use. If you find bugs or have suggestions, open an issue.

## Acknowledgments

HTML/CSS/JavaScript structure created with assistance from Claude AI (Anthropic) to accelerate development.