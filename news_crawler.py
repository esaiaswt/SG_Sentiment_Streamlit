"""
news_crawler.py
Crawls news articles from major Singapore news outlets.
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import feedparser
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def fetch_strait_times():
    url = "https://www.straitstimes.com/news/singapore/rss.xml"
    articles = []
    try:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            articles.append({
                'title': entry.title,
                'url': entry.link,
                'content': entry.get('summary', ''),
                'source': 'The Straits Times',
                'timestamp': entry.get('published', datetime.now().isoformat()),
                'location': 'Singapore'
            })
    except Exception as e:
        print(f"Error fetching The Straits Times: {e}")
    print(f"Fetched {len(articles)} articles from The Straits Times.")
    return articles

def fetch_channel_newsasia():
    url = "https://www.channelnewsasia.com/rssfeeds/8395986"
    articles = []
    try:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            articles.append({
                'title': entry.title,
                'url': entry.link,
                'content': entry.get('summary', ''),
                'source': 'Channel NewsAsia',
                'timestamp': entry.get('published', datetime.now().isoformat()),
                'location': 'Singapore'
            })
    except Exception as e:
        print(f"Error fetching Channel NewsAsia: {e}")
    print(f"Fetched {len(articles)} articles from Channel NewsAsia.")
    return articles

def fetch_today_online():
    url = "https://www.todayonline.com/singapore"
    articles = []
    try:
        resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        seen = set()
        # Try multiple selectors and fallback to <article> links
        for item in soup.select('a.card__link, a.teaser__link, article a'):
            link = item.get('href')
            title = item.get_text(strip=True)
            if link and not link.startswith('http'):
                link = 'https://www.todayonline.com' + link
            if link and link not in seen and title and '/singapore/' in link:
                seen.add(link)
                articles.append({
                    'title': title,
                    'url': link,
                    'content': '',
                    'source': 'Today Online',
                    'timestamp': datetime.now().isoformat(),
                    'location': 'Singapore'
                })
    except Exception as e:
        print(f"Error scraping Today Online: {e}")
    print(f"Fetched {len(articles)} articles from Today Online.")
    return articles

def fetch_mothership():
    """
    Scrape latest news articles from mothership.sg homepage.
    """
    url = "https://mothership.sg/"
    articles = []
    try:
        resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        seen = set()
        # Mothership articles are in <a> tags with hrefs containing '/202'
        for item in soup.find_all('a', href=True):
            link = item['href']
            title = item.get_text(strip=True)
            if link.startswith('/'):
                link = 'https://mothership.sg' + link
            if (
                link not in seen and
                title and
                '/202' in link and  # likely a news article (year in URL)
                len(title) > 10
            ):
                seen.add(link)
                articles.append({
                    'title': title,
                    'url': link,
                    'content': '',
                    'source': 'Mothership',
                    'timestamp': datetime.now().isoformat(),
                    'location': 'Singapore'
                })
    except Exception as e:
        print(f"Error scraping Mothership: {e}")
    print(f"Fetched {len(articles)} articles from Mothership.")
    return articles

def crawl_news():
    """
    Crawl news articles from The Straits Times, Channel NewsAsia, Today Online, Mothership.
    Returns a list of articles with metadata (title, url, content, source, timestamp, location if available).
    """
    articles = []
    articles.extend(fetch_strait_times())
    articles.extend(fetch_channel_newsasia())
    articles.extend(fetch_today_online())
    articles.extend(fetch_mothership())
    print(f"Total articles fetched: {len(articles)}")
    return articles

if __name__ == "__main__":
    crawl_news()
