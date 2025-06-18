"""
run_pipeline.py
Automates the full pipeline: crawl news, analyze sentiment, and visualize on map.
"""

import importlib
import json
import datetime

# Import modules
news_crawler = importlib.import_module('news_crawler')
sentiment_analysis = importlib.import_module('sentiment_analysis')
map_visualization = importlib.import_module('map_visualization')

def remove_old_articles(json_path, date_key="timestamp", days=3):
    from dateutil import parser as date_parser
    import os
    if not os.path.exists(json_path):
        return
    with open(json_path, 'r', encoding='utf-8') as f:
        try:
            articles = json.load(f)
        except Exception:
            return
    now = datetime.datetime.now()
    filtered = []
    for article in articles:
        ts = article.get(date_key)
        if not ts:
            filtered.append(article)
            continue
        try:
            # Try parsing both ISO and non-ISO formats
            try:
                dt = date_parser.parse(ts)
            except Exception:
                dt = datetime.datetime.strptime(ts, "%a, %d %b %Y %H:%M:%S %z")
            if (now - dt).days <= days:
                filtered.append(article)
        except Exception:
            filtered.append(article)
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(filtered, f, ensure_ascii=False, indent=2)

# Remove old articles before pipeline runs
remove_old_articles('latest_articles.json')
remove_old_articles('articles_with_sentiment.json')

# Step 1: Crawl news
print("Crawling news...")
articles = news_crawler.crawl_news()
print(f"Crawled {len(articles)} articles.")
with open('latest_articles.json', 'w', encoding='utf-8') as f:
    json.dump(articles, f, ensure_ascii=False, indent=2)
print(f"Saved {len(articles)} articles to latest_articles.json.")

# Step 2: Sentiment analysis
print("Analyzing sentiment...")
results = sentiment_analysis.analyze_sentiment(articles)
print(f"Processed sentiment for {len(results)} articles.")
with open('articles_with_sentiment.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print(f"Saved sentiment results to articles_with_sentiment.json.")

# Step 2.5: Gemini Singapore relevance & place analysis
print("Running Gemini Singapore relevance & place analysis...")
results_with_gemini = map_visualization.process_articles_with_gemini(results)
with open('articles_with_sentiment.json', 'w', encoding='utf-8') as f:
    json.dump(results_with_gemini, f, ensure_ascii=False, indent=2)
print(f"Saved Gemini-processed results to articles_with_sentiment.json.")

# Step 3: Map visualization
print("Generating map visualization...")
map_visualization.plot_emojis_on_map(results_with_gemini)
print("Pipeline complete. Open singapore_news_sentiment_map.html to view the map.")
