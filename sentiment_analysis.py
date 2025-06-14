"""
sentiment_analysis.py
Performs sentiment analysis on news articles.
"""

import json
from textblob import TextBlob
from datetime import datetime

def analyze_sentiment(articles):
    """
    Takes a list of articles and returns a list with sentiment scores and reasons.
    """
    results = []
    for article in articles:
        text = article.get('content') or article.get('title')
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        if polarity > 0.2:
            sentiment = 'positive'
            emoji = '😊'
            reason = 'Positive sentiment detected.'
        elif polarity < -0.2:
            sentiment = 'negative'
            emoji = '😞'
            reason = 'Negative sentiment detected.'
        else:
            sentiment = 'neutral'
            emoji = '😐'
            reason = 'Neutral sentiment detected.'
        results.append({
            **article,
            'sentiment': sentiment,
            'emoji': emoji,
            'sentiment_score': polarity,
            'sentiment_reason': reason
        })
    return results

if __name__ == "__main__":
    # Load articles from latest_articles.json
    with open('latest_articles.json', 'r', encoding='utf-8') as f:
        articles = json.load(f)
    results = analyze_sentiment(articles)
    # Save results to a new file
    with open('articles_with_sentiment.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Analyzed sentiment for {len(results)} articles. Results saved to articles_with_sentiment.json.")
