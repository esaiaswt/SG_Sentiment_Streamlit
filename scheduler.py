"""
scheduler.py
Runs the news crawler every hour and saves results for further processing.
"""

import time
import importlib
import json

# Import the crawl_news function from news_crawler
news_crawler = importlib.import_module('news_crawler')

def run_hourly():
    while True:
        print("Crawling news...")
        articles = news_crawler.crawl_news()
        # Save articles to a file for sentiment analysis
        with open('latest_articles.json', 'w', encoding='utf-8') as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)
        print(f"Saved {len(articles)} articles to latest_articles.json.")
        print("Sleeping for 1 hour...")
        time.sleep(3600)

if __name__ == "__main__":
    run_hourly()
