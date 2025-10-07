import feedparser
import json
from datetime import datetime, timezone, timedelta
from dateutil import parser as date_parser
from html.parser import HTMLParser
from urllib.parse import urljoin
import re

FEEDS = [
    {
        "url": "https://blog.ipspace.net/atom.xml",
        "title": "ipSpace Blog",
        "manual_tags": ["networking"]
    },
    {
        "url": "https://www.packetcoders.io/rss",
        "title": "Packet Coders",
        "manual_tags": ["networking"]
    },
    {
        "url": "https://www.packetswitch.co.uk/blog/rss",
        "title": "Packet Switch",
        "manual_tags": ["networking"]
    },
    {
        "url": "https://www.netbraintech.com/blog/feed/atom/",
        "title": "NetBrain Blog",
        "manual_tags": ["networking"]
    },
    {
        "url": "https://networkautomation.forum/blog?format=rss",
        "title": "Network Automation Forum",
        "manual_tags": ["networking"]
    },
    {
        "url": "https://feeds.arstechnica.com/arstechnica/technology-lab",
        "title": "Ars Technica - Tech",
        "manual_tags": []
    },
    {
        "url": "https://feeds.arstechnica.com/arstechnica/gadgets",
        "title": "Ars Technica - Gadgets",
        "manual_tags": []
    },
]

OUTPUT_FILE = "feeds.json"
ARCHIVE_FILE = "archive.json"
DAYS_IN_CURRENT = 90  # Articles older than this go to archive

class ImageExtractor(HTMLParser):
    """Extract first image from HTML content"""
    def __init__(self):
        super().__init__()
        self.image_url = None
    
    def handle_starttag(self, tag, attrs):
        if tag == 'img' and self.image_url is None:
            attrs_dict = dict(attrs)
            if 'src' in attrs_dict:
                self.image_url = attrs_dict['src']

class TextExtractor(HTMLParser):
    """Extract plain text from HTML content"""
    def __init__(self):
        super().__init__()
        self.text = []
    
    def handle_data(self, data):
        self.text.append(data)
    
    def get_text(self):
        return ' '.join(self.text)

def extract_first_image(html_content, base_url):
    """Extract first image from HTML and convert to absolute URL"""
    if not html_content:
        return None
    
    parser = ImageExtractor()
    parser.feed(html_content)
    
    if parser.image_url:
        # Convert relative URL to absolute
        return urljoin(base_url, parser.image_url)
    
    return None

def clean_html_to_text(html_content):
    """Convert HTML to plain text and clean it up"""
    if not html_content:
        return ""
    
    parser = TextExtractor()
    parser.feed(html_content)
    text = parser.get_text()
    
    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    return text

def extract_summary(entry, max_length=300):
    """Extract and clean summary from RSS entry"""
    summary_text = ""
    
    # Try to get summary from various fields
    if 'summary' in entry:
        summary_text = clean_html_to_text(entry.summary)
    elif 'description' in entry:
        summary_text = clean_html_to_text(entry.description)
    elif 'content' in entry and entry.content:
        # Use first content block
        summary_text = clean_html_to_text(entry.content[0]['value'])
    
    # Truncate if too long
    if len(summary_text) > max_length:
        summary_text = summary_text[:max_length].rsplit(' ', 1)[0] + '...'
    
    return summary_text

def extract_tags(entry, feed_config):
    """Extract tags/categories from RSS entry, with manual override option"""
    tags = []
    
    # First, check for RSS categories/tags
    if hasattr(entry, 'tags') and entry.tags:
        tags = [tag.term for tag in entry.tags if hasattr(tag, 'term')]
    elif hasattr(entry, 'categories') and entry.categories:
        tags = list(entry.categories)
    
    # If no tags found in RSS and manual tags are defined, use those
    if feed_config.get("manual_tags"):
        if not tags:
            tags = feed_config["manual_tags"]
        else:
            tags.extend(feed_config["manual_tags"])
    
    # Normalize: strip whitespace, convert to lowercase, deduplicate, sort
    normalized_tags = set()
    for tag in tags:
        cleaned = tag.strip().lower()
        if cleaned:  # Only add non-empty tags
            normalized_tags.add(cleaned)
    
    return sorted(list(normalized_tags))

def fetch_all_feeds():
    articles = []
    seen_urls = set()
    all_sources = set()
    all_tags = set()
    
    for feed_config in FEEDS:
        feed_url = feed_config["url"]
        custom_title = feed_config["title"]
        
        feed = feedparser.parse(feed_url)
        all_sources.add(custom_title)
        
        for entry in feed.entries:
            # Deduplicate by URL
            if entry.link in seen_urls:
                continue
            seen_urls.add(entry.link)
            
            # Parse the date so we can sort
            pub_date = entry.get('published', '')
            try:
                parsed_date = date_parser.parse(pub_date)
                date_iso = parsed_date.isoformat()
            except:
                date_iso = pub_date
            
            # Try to extract image from content or summary
            image_url = None
            if 'content' in entry:
                image_url = extract_first_image(entry.content[0]['value'], entry.link)
            elif 'summary' in entry:
                image_url = extract_first_image(entry.summary, entry.link)
            
            # Extract summary
            summary = extract_summary(entry)
            
            # Extract tags/categories
            tags = extract_tags(entry, feed_config)
            all_tags.update(tags)
            
            articles.append({
                'title': entry.title,
                'link': entry.link,
                'published': pub_date,
                'published_parsed': date_iso,
                'source': custom_title,
                'image': image_url,
                'summary': summary,
                'tags': tags,
            })
    
    # Sort by date, newest first
    articles.sort(key=lambda x: x['published_parsed'], reverse=True)
    
    return articles, sorted(list(all_sources)), sorted(list(all_tags))

def load_archive():
    """Load existing archive or return empty dict"""
    try:
        with open(ARCHIVE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return {article['link']: article for article in data.get('articles', [])}
    except FileNotFoundError:
        return {}

def save_archive(archive_dict):
    """Save archive with all articles sorted by date"""
    articles = list(archive_dict.values())
    articles.sort(key=lambda x: x['published_parsed'], reverse=True)
    
    output = {
        'last_updated': datetime.now(timezone.utc).isoformat(),
        'article_count': len(articles),
        'articles': articles
    }
    
    with open(ARCHIVE_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

def main():
    # Load existing archive
    archive = load_archive()
    
    # Fetch current articles from feeds
    all_fetched_articles, sources, tags = fetch_all_feeds()
    
    # Calculate cutoff date (90 days ago)
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=DAYS_IN_CURRENT)
    
    current_articles = []
    current_urls = set()
    
    for article in all_fetched_articles:
        current_urls.add(article['link'])
        
        try:
            article_date = date_parser.parse(article['published_parsed'])
            # Make timezone-aware if naive
            if article_date.tzinfo is None:
                article_date = article_date.replace(tzinfo=timezone.utc)
        except:
            article_date = datetime.now(timezone.utc)
        
        if article_date >= cutoff_date:
            # Recent article - goes to feeds.json
            current_articles.append(article)
        else:
            # Old article - goes to archive
            if article['link'] not in archive:
                archive[article['link']] = article
    
    # Move articles that disappeared from feeds to archive
    # (This preserves articles from feeds with limited history)
    for url, article in list(archive.items()):
        if url not in current_urls:
            # Article not in current fetch - keep in archive
            continue
    
    # Add any current articles to archive that aren't there yet
    for article in current_articles:
        if article['link'] not in archive:
            archive[article['link']] = article
    
    # Save archive
    save_archive(archive)
    
    # Save current feeds.json
    output = {
        'last_updated': datetime.now(timezone.utc).isoformat(),
        'article_count': len(current_articles),
        'sources': sources,
        'tags': tags,
        'articles': current_articles
    }
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"Current articles (last {DAYS_IN_CURRENT} days): {len(current_articles)}")
    print(f"Archive total: {len(archive)}")
    print(f"Sources:")
    print("\n".join(f"    - {source_item}" for source_item in sources))


if __name__ == "__main__":
    main()