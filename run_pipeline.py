"""
run_pipeline.py
Automates the full pipeline: crawl news, analyze sentiment, and visualize on map.
"""

import importlib
import json

# Import modules
news_crawler = importlib.import_module('news_crawler')
sentiment_analysis = importlib.import_module('sentiment_analysis')
map_visualization = importlib.import_module('map_visualization')

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
