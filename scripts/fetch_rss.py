import feedparser
import json
from datetime import datetime,timezone
from dateutil import parser as date_parser

FEEDS = [
    "https://networktocode.com/feed"
]

OUTPUT_FILE = "feeds.json"

def fetch_all_feeds():
    articles = []
    seen_urls = set()  # Track URLs we've already added
    
    for feed_url in FEEDS:
        feed = feedparser.parse(feed_url)
        
        for entry in feed.entries:
            # Skip if we've seen this URL before
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
            
            articles.append({
                'title': entry.title,
                'link': entry.link,
                'published': pub_date,
                'published_parsed': date_iso,
                'source': feed.feed.title,
            })
    
    # Sort by date, newest first
    articles.sort(key=lambda x: x['published_parsed'], reverse=True)
    
    return articles

def main():
    articles = fetch_all_feeds()
    
    output = {
        'last_updated': datetime.now(timezone.utc).isoformat(),
        'article_count': len(articles),
        'articles': articles
    }
    
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(output, f, indent=2, ensure_ascii=False) # No reason to encode and this makes it more readble looking at feeds.json
    
    print(f"Fetched {len(articles)} articles")
    print(f"Written to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()