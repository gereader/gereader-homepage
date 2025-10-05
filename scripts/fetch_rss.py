import feedparser
import json
from datetime import datetime, timezone
from dateutil import parser as date_parser
from html.parser import HTMLParser
from urllib.parse import urljoin

FEEDS = [
    {
        "url": "https://blog.ipspace.net/atom.xml",
        "title": "ipSpace Blog",
        "manual_tags": []
    },
    {
        "url": "https://www.packetcoders.io/rss",
        "title": "Packet Coders",
        "manual_tags": []
    },
    {
        "url": "https://www.packetswitch.co.uk/blog/rss",
        "title": "Packet Switch",
        "manual_tags": []
    },
    {
        "url": "https://www.netbraintech.com/blog/feed/atom/",
        "title": "NetBrain Blog",
        "manual_tags": []
    },
    {
        "url": "https://networkautomation.forum/blog?format=rss",
        "title": "Network Automation Forum",
        "manual_tags": []
    },
    {
        "url": "https://hackaday.com/feed/",
        "title": "Hackaday",
        "manual_tags": []
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

def extract_tags(entry, feed_config):
    """Extract tags/categories from RSS entry, with manual override option"""
    tags = []
    
    # First, check for RSS categories/tags
    if hasattr(entry, 'tags') and entry.tags:
        tags = [tag.term for tag in entry.tags if hasattr(tag, 'term')]
    elif hasattr(entry, 'categories') and entry.categories:
        tags = list(entry.categories)
    
    # If no tags found in RSS and manual tags are defined, use those
    if not tags and feed_config.get("manual_tags"):
        tags = feed_config["manual_tags"]
    
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
                'tags': tags,
            })
    
    # Sort by date, newest first
    articles.sort(key=lambda x: x['published_parsed'], reverse=True)
    
    return articles, sorted(list(all_sources)), sorted(list(all_tags))

def main():
    articles, sources, tags = fetch_all_feeds()
    
    output = {
        'last_updated': datetime.now(timezone.utc).isoformat(),
        'article_count': len(articles),
        'sources': sources,
        'tags': tags,
        'articles': articles
    }
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"Fetched {len(articles)} articles")
    print(f"Sources: {', '.join(sources)}")
    print(f"Unique tags: {len(tags)}")
    if tags:
        print(f"Tags: {', '.join(tags[:10])}{'...' if len(tags) > 10 else ''}")
    print(f"Written to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()