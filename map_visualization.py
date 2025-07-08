"""
map_visualization.py
Visualizes sentiment/emojis on a Singapore map.
"""

import json
import folium
import requests
from collections import Counter
import yaml
import os
from dotenv import load_dotenv

def get_sg_location_coords(place_name):
    """
    Try OneMap.sg API for Singapore place/building/office first.
    If not found, fallback to Nominatim.
    Returns (lat, lon) or None if not found.
    """
    import requests
    import time
    # 1. Try OneMap.sg API
    try:
        url = f"https://www.onemap.gov.sg/api/common/elastic/search"
        params = {
            'searchVal': place_name,
            'returnGeom': 'Y',
            'getAddrDetails': 'Y',
            'pageNum': 1
        }
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        results = data.get('results', [])
        for r in results:
            if r.get('LATITUDE') and r.get('LONGITUDE'):
                lat, lon = float(r['LATITUDE']), float(r['LONGITUDE'])
                print(f"  OneMap.sg found: {lat}, {lon} for {place_name}")
                return [lat, lon]
    except Exception as e:
        print(f"OneMap.sg geocoding error for '{place_name}': {e}")
    # 2. Fallback: Nominatim
    try:
        url = f"https://nominatim.openstreetmap.org/search"
        params = {
            'q': f"{place_name}, Singapore",
            'format': 'json',
            'limit': 1,
            'addressdetails': 0
        }
        headers = {'User-Agent': 'HappinessIndexBot/1.0'}
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        data = resp.json()
        if data:
            print(f"  Nominatim found: {data[0]['lat']}, {data[0]['lon']} for {place_name}")
            return [float(data[0]['lat']), float(data[0]['lon'])]
    except Exception as e:
        print(f"Nominatim geocoding error for '{place_name}': {e}")
    print(f"  Could not geocode place: {place_name}")
    return None

def load_gemini_api_key():
    load_dotenv()
    return os.getenv('GEMINI_API_KEY')

# Global counters for Gemini token usage
GEMINI_TOTAL_IN_TOKENS = 0
GEMINI_TOTAL_OUT_TOKENS = 0

def gemini_analyze_article(api_key, title, content, idx=None, total=None):
    global GEMINI_TOTAL_IN_TOKENS, GEMINI_TOTAL_OUT_TOKENS
    """
    Use Google Gemini 2.0 Flash to get best place in Singapore for marker and sentiment analysis.
    Returns (place_name, sentiment, reason, emoji, is_sg_related)
    """
    import google.generativeai as genai
    import time
    import re
    genai.configure(api_key=api_key)
    prompt = f"""
    Given the following news article, respond ONLY with a valid JSON object with these fields (no explanation, no markdown, no extra text):\n
    - is_sg_related: true if the article is about Singapore, false otherwise
    - place: The best Singapore place/building/office to put a map marker for this article (be specific, e.g. 'Changi Airport', 'Orchard Towers', 'Google Asia Pacific', etc.)
    - sentiment: positive, negative, or neutral
    - reason: a short reason for the sentiment
    - emoji: a single emoji that best represents the sentiment
    News title: {title}
    News content: {content}
    """
    model = genai.GenerativeModel('gemini-2.0-flash')  # Use Gemini Pro for best compatibility
    # --- Emoji mapping: map common text/labels to Unicode emoji ---
    def map_to_emoji(emoji_value):
        if not emoji_value:
            return None
        # If it's already a single emoji, return as is
        import re
        emoji_pattern = re.compile(
            r"[\U0001F600-\U0001F64F"  # emoticons
            r"\U0001F300-\U0001F5FF"  # symbols & pictographs
            r"\U0001F680-\U0001F6FF"  # transport & map symbols
            r"\U0001F1E0-\U0001F1FF"  # flags (iOS)
            r"\U00002700-\U000027BF"  # Dingbats
            r"\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
            r"\U00002600-\U000026FF"  # Misc symbols
            r"\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
            r"]+", flags=re.UNICODE)
        if emoji_pattern.fullmatch(str(emoji_value).strip()):
            return emoji_value.strip()
        # Common mappings
        mapping = {
            'happy': '😊', 'smile': '😊', 'smiling': '😊', 'positive': '😊', 'joy': '😊', 'good': '😊',
            'sad': '😞', 'frown': '😞', 'negative': '😞', 'unhappy': '😞', 'cry': '😢', 'angry': '😠',
            'neutral': '😐', 'meh': '😐', 'ok': '😐', 'indifferent': '😐', 'traffic light': '🚦',
            'warning': '⚠️', 'alert': '⚠️', 'danger': '🚨', 'fire': '🔥', 'money': '💰', 'love': '❤️',
            'hospital': '🏥', 'police': '👮', 'school': '🏫', 'rain': '🌧️', 'sun': '☀️', 'cloud': '☁️',
            'storm': '🌩️', 'flood': '🌊', 'accident': '💥', 'virus': '🦠', 'health': '🩺', 'crime': '🚔',
            'protest': '✊', 'celebration': '🎉', 'party': '🥳', 'confused': '😕', 'shocked': '😲',
            'surprised': '😮', 'disappointed': '😞', 'success': '🏆', 'failure': '❌', 'question': '❓',
            'exclamation': '❗', 'star': '⭐', 'earth': '🌏', 'singapore': '🦁', 'lion': '🦁',
            'government': '🏛️', 'airport': '🛫', 'train': '🚆', 'bus': '🚌', 'car': '🚗', 'plane': '✈️',
            'food': '🍲', 'restaurant': '🍽️', 'shopping': '🛍️', 'market': '🛒', 'sports': '🏟️',
            'music': '🎵', 'art': '🎨', 'technology': '💻', 'science': '🔬', 'education': '🎓',
            'environment': '🌳', 'nature': '🌿', 'energy': '⚡', 'water': '💧', 'fireworks': '🎆',
            'award': '🏅', 'medal': '🏅', 'trophy': '🏆', 'winner': '🏆', 'loser': '😞',
        }
        val = str(emoji_value).strip().lower()
        # Try direct mapping
        if val in mapping:
            return mapping[val]
        # Try to extract emoji from text (e.g. "neutral face (😐)")
        match = re.search(r'[\U0001F600-\U0001FAFF\u2600-\u27BF]', emoji_value)
        if match:
            return match.group(0)
        # Try to map by keywords in the value
        for k, v in mapping.items():
            if k in val:
                return v
        # Fallback: neutral face
        return '😐'

    for attempt in range(2):  # Try at most twice
        try:
            response = model.generate_content(prompt)
            # Print Gemini token usage if available
            usage = getattr(response, 'usage_metadata', None)
            if usage:
                in_tokens = usage.prompt_token_count
                out_tokens = usage.candidates_token_count
                if in_tokens is not None:
                    GEMINI_TOTAL_IN_TOKENS += in_tokens
                if out_tokens is not None:
                    GEMINI_TOTAL_OUT_TOKENS += out_tokens
                print(f"Gemini tokens used: in={in_tokens}, out={out_tokens}, total in={GEMINI_TOTAL_IN_TOKENS}, total out={GEMINI_TOTAL_OUT_TOKENS}")
            text = response.text if hasattr(response, 'text') else str(response)
            if not text:
                print(f"Gemini API error: No text in response: {response}")
                continue
            # --- Try to extract JSON object from the response, even with extra text ---
            text_clean = text.strip()
            # Remove Markdown code block if present
            if text_clean.startswith('```'):
                text_clean = re.sub(r'^```[a-zA-Z]*\n?', '', text_clean)
                text_clean = re.sub(r'```$', '', text_clean).strip()
            import json as pyjson
            try:
                # Try direct parse
                parsed = pyjson.loads(text_clean)
                emoji_fixed = map_to_emoji(parsed.get('emoji'))
                return parsed.get('place'), parsed.get('sentiment'), parsed.get('reason'), emoji_fixed, parsed.get('is_sg_related')
            except Exception as e:
                # Try to extract JSON object from within extra text
                import re as _re
                match = _re.search(r'\{[\s\S]*\}', text_clean)
                if match:
                    json_str = match.group(0)
                    # Fix common Gemini mistakes: unquoted values, bad unicode, etc.
                    # 1. Add quotes around unquoted neutral/positive/negative
                    json_str = _re.sub(r'("sentiment"\s*:\s*)(neutral|positive|negative)([\s,}])', r'\1"\2"\3', json_str)
                    # 2. Fix bad unicode (replace \u-style escapes and invalid chars)
                    json_str = json_str.encode('utf-8', 'replace').decode('utf-8', 'replace')
                    try:
                        parsed = pyjson.loads(json_str)
                        emoji_fixed = map_to_emoji(parsed.get('emoji'))
                        return parsed.get('place'), parsed.get('sentiment'), parsed.get('reason'), emoji_fixed, parsed.get('is_sg_related')
                    except Exception as e2:
                        print(f"Gemini API JSON extract error: {e2}\nRaw text: {text}")
                print(f"Gemini API JSON parse error: {e}\nRaw text: {text}")
                continue
        except Exception as e:
            print(f"Gemini API request error: {e}")
            time.sleep(2)
            continue
    print("Gemini API: Exceeded retry attempts after rate limit or errors.")
    return None, None, None, None, None

def is_in_singapore(lat, lon):
    """Return True if coordinates are within Singapore's bounding box."""
    return 1.130 <= lat <= 1.480 and 103.6 <= lon <= 104.1

def plot_emojis_on_map(articles_with_sentiment):
    # --- Emoji mapping: map common text/labels to Unicode emoji ---
    def map_to_emoji(emoji_value):
        if not emoji_value:
            return None
        import re
        emoji_pattern = re.compile(
            r"[\U0001F600-\U0001F64F"  # emoticons
            r"\U0001F300-\U0001F5FF"  # symbols & pictographs
            r"\U0001F680-\U0001F6FF"  # transport & map symbols
            r"\U0001F1E0-\U0001F1FF"  # flags (iOS)
            r"\U00002700-\U000027BF"  # Dingbats
            r"\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
            r"\U00002600-\U000026FF"  # Misc symbols
            r"\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
            r"]+", flags=re.UNICODE)
        if emoji_pattern.fullmatch(str(emoji_value).strip()):
            return emoji_value.strip()
        mapping = {
            'happy': '😊', 'smile': '😊', 'smiling': '😊', 'positive': '😊', 'joy': '😊', 'good': '😊',
            'sad': '😞', 'frown': '😞', 'negative': '😞', 'unhappy': '😞', 'cry': '😢', 'angry': '😠',
            'neutral': '😐', 'meh': '😐', 'ok': '😐', 'indifferent': '😐', 'traffic light': '🚦',
            'warning': '⚠️', 'alert': '⚠️', 'danger': '🚨', 'fire': '🔥', 'money': '💰', 'love': '❤️',
            'hospital': '🏥', 'police': '👮', 'school': '🏫', 'rain': '🌧️', 'sun': '☀️', 'cloud': '☁️',
            'storm': '🌩️', 'flood': '🌊', 'accident': '💥', 'virus': '🦠', 'health': '🩺', 'crime': '🚔',
            'protest': '✊', 'celebration': '🎉', 'party': '🥳', 'confused': '😕', 'shocked': '😲',
            'surprised': '😮', 'disappointed': '😞', 'success': '🏆', 'failure': '❌', 'question': '❓',
            'exclamation': '❗', 'star': '⭐', 'earth': '🌏', 'singapore': '🦁', 'lion': '🦁',
            'government': '🏛️', 'airport': '🛫', 'train': '🚆', 'bus': '🚌', 'car': '🚗', 'plane': '✈️',
            'food': '🍲', 'restaurant': '🍽️', 'shopping': '🛍️', 'market': '🛒', 'sports': '🏟️',
            'music': '🎵', 'art': '🎨', 'technology': '💻', 'science': '🔬', 'education': '🎓',
            'environment': '🌳', 'nature': '🌿', 'energy': '⚡', 'water': '💧', 'fireworks': '🎆',
            'award': '🏅', 'medal': '🏅', 'trophy': '🏆', 'winner': '🏆', 'loser': '😞',
        }
        val = str(emoji_value).strip().lower()
        if val in mapping:
            return mapping[val]
        match = re.search(r'[\U0001F600-\U0001FAFF\u2600-\u27BF]', emoji_value)
        if match:
            return match.group(0)
        for k, v in mapping.items():
            if k in val:
                return v
        return '😐'
    api_key = load_gemini_api_key()
    overall_coords = [1.285, 103.905]  # Approx. sea below Marine Parade
    sg_coords = [1.3521, 103.8198]
    m = folium.Map(location=sg_coords, zoom_start=12)
    sentiments = []
    marker_count = 0
    outlet_sentiment = {}
    # Track marker positions to avoid overlap
    marker_positions = {}
    # Debug: count articles with valid Gemini fields
    valid_articles = [a for a in articles_with_sentiment if a.get('place') and a.get('sentiment') and a.get('emoji')]
    print(f"Articles with valid Gemini fields: {len(valid_articles)} / {len(articles_with_sentiment)}")
    if len(valid_articles) == 0 and len(articles_with_sentiment) > 0:
        print("No articles with valid Gemini fields found. Forcing reprocessing with Gemini...")
        articles_with_sentiment = process_articles_with_gemini(articles_with_sentiment)
    total_articles = len(articles_with_sentiment)
    for idx, article in enumerate(articles_with_sentiment, 1):
        print(f"Processing article {idx} of {total_articles}: {article.get('title', '')[:60]}")
        title = article.get('title', '')
        content = article.get('content', '')
        url = article.get('url', '')
        # Use Gemini results from cache (do NOT call Gemini here)
        place_name = article.get('place')
        sentiment = article.get('sentiment')
        reason = article.get('reason')
        emoji = map_to_emoji(article.get('emoji'))
        is_sg_related = article.get('is_sg_related')
        if is_sg_related is not True:
            print(f"  Skipping non-Singapore related article: {title}")
            continue
        missing_fields = []
        if not place_name:
            missing_fields.append('place')
        if not sentiment:
            missing_fields.append('sentiment')
        if not emoji:
            missing_fields.append('emoji')
        if missing_fields:
            print(f"  Gemini result missing fields {missing_fields} for: {title}")
            # Optionally log the problematic article for debugging
            try:
                with open('gemini_missing_results.log', 'a', encoding='utf-8') as logf:
                    import json as _json
                    logf.write(_json.dumps({'title': title, 'missing_fields': missing_fields, 'article': article}, ensure_ascii=False) + '\n')
            except Exception as log_exc:
                print(f"    (Could not log missing Gemini result: {log_exc})")
            continue
        # Geocode the place_name
        coord = get_sg_location_coords(place_name)
        # Check if coordinates are in Singapore
        if coord and not is_in_singapore(coord[0], coord[1]):
            print(f"  Geocoded place out of Singapore: {coord} for {place_name}. Retrying with 'Singapore' appended.")
            coord = get_sg_location_coords(f"{place_name} Singapore")
            if coord and not is_in_singapore(coord[0], coord[1]):
                print(f"  Still out of Singapore: {coord}. Skipping marker.")
                continue
        if not coord:
            print(f"  Could not geocode place: {place_name}")
            continue
        # --- Overlap avoidance logic ---
        coord_key = (round(coord[0], 6), round(coord[1], 6))
        count = marker_positions.get(coord_key, 0)
        marker_positions[coord_key] = count + 1
        # Offset each marker slightly if there are overlaps
        offset_distance = 0.00015  # ~15 meters
        angle = (count * 45) % 360  # Spread out in a circle
        import math
        lat_offset = offset_distance * math.cos(math.radians(angle))
        lon_offset = offset_distance * math.sin(math.radians(angle))
        marker_lat = coord[0] + lat_offset
        marker_lon = coord[1] + lon_offset
        print(f"  Placing marker at: {[marker_lat, marker_lon]} for {place_name} (offset {count})")
        # Add news source URL to popup if available
        url_html = f'<br><a href="{url}" target="_blank">Read full article</a>' if url else ''
        popup = folium.Popup(f"<b>{article['source']}</b><br>{title}<br>{reason}<br>Sentiment: {sentiment} {emoji}{url_html}", max_width=300)
        folium.Marker(
            location=[marker_lat, marker_lon],
            popup=popup,
            icon=folium.DivIcon(html=f"""
                <div style='font-size:32px; line-height:32px; text-align:center; background: white; border-radius: 50%; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; border: 1px solid #888; font-family: 'Segoe UI Emoji', 'Apple Color Emoji', 'Noto Color Emoji', 'Twemoji Mozilla', 'Arial';'>
                    {emoji}<span style='font-size:10px; color:#888;'>(news)</span>
                </div>
            """.strip())
        ).add_to(m)
        # Track sentiment counts by outlet
        source = article.get('source', 'Unknown')
        if source not in outlet_sentiment:
            outlet_sentiment[source] = {'positive': 0, 'negative': 0, 'neutral': 0}
        if sentiment in outlet_sentiment[source]:
            outlet_sentiment[source][sentiment] += 1
        sentiments.append(sentiment)
        marker_count += 1
    # Overall sentiment
    if sentiments:
        from collections import Counter
        from datetime import datetime
        import pytz
        overall = Counter(sentiments).most_common(1)[0][0]
        overall_emoji = {'positive': '😊', 'negative': '😞', 'neutral': '😐'}.get(overall, '😐')
        # Build HTML table for outlet sentiment counts
        table_html = '<table border="1" style="border-collapse:collapse;font-size:12px;margin-top:6px;">'
        table_html += '<tr><th>News Outlet</th><th>Positive</th><th>Neutral</th><th>Negative</th></tr>'
        pos_total = neg_total = neu_total = 0
        for outlet, counts in outlet_sentiment.items():
            table_html += f'<tr><td>{outlet}</td><td>{counts["positive"]}</td><td>{counts["neutral"]}</td><td>{counts["negative"]}</td></tr>'
            pos_total += counts["positive"]
            neg_total += counts["negative"]
            neu_total += counts["neutral"]
        total_articles = pos_total + neg_total + neu_total
        table_html += f'<tr style="font-weight:bold;background:#f0f0f0;"><td>Subtotal</td><td>{pos_total}</td><td>{neu_total}</td><td>{neg_total}</td></tr>'
        table_html += f'<tr style="font-weight:bold;background:#e0e0e0;"><td colspan="4">Total News Articles: {total_articles}</td></tr>'
        table_html += '</table>'
        # Add last updated date and time (Singapore time)
        now = datetime.now(pytz.timezone('Asia/Singapore'))
        last_updated = now.strftime('%d-%m-%Y %I:%M:%S %p')
        last_updated_html = f'<div style="font-size:11px;color:#555;margin-top:4px;">Last updated: {last_updated}</div>'
        # Format last updated date in DD-MM-YYYY and style it below "Overview"
        last_updated_ddmmyyyy = now.strftime('%d-%m-%Y')
        folium.Marker(
            location=overall_coords,
            popup=folium.Popup(f"<b>Overall Singapore Sentiment</b><br>{overall.title()} {overall_emoji}{table_html}{last_updated_html}", max_width=400),
            icon=folium.DivIcon(html=f"""
                <div style='font-size:40px; line-height:40px; text-align:center; background: white; border: 2px solid #0000FF; border-radius: 12px; width: 260px; height: 110px; display: flex; flex-direction: column; align-items: center; justify-content: center; box-shadow: 0 0 8px #0003; font-family: 'Segoe UI Emoji', 'Apple Color Emoji', 'Noto Color Emoji', 'Twemoji Mozilla', 'Arial';'>
                    <div style='display: flex; align-items: center; justify-content: center; margin-top: 8px;'>
                        {overall_emoji}<span style='font-size:28px; font-weight:bold; color:#111; margin-left:14px;'>Overview</span>
                    </div>
                    <div style='font-size:20px; color:#333; margin-top:8px; font-weight:normal;'>{last_updated_ddmmyyyy}</div>
                </div>
            """.strip())
        ).add_to(m)
    # --- Inject JS to expose Leaflet map as window.map for Home button ---
    from branca.element import Element, MacroElement, Template
    # --- Inject JS to expose Leaflet map as window.map for Home button ---
    class ExposeMapMacro(MacroElement):
        def __init__(self):
            super().__init__()
            self._template = Template("""
                <script>
                setTimeout(function() {
                    for (var key in window) {
                        if (window[key] && window[key].setView && window[key].fitBounds && window[key].addLayer) {
                            window.map = window[key];
                            break;
                        }
                    }
                }, 500);
                </script>
            """)
    m.get_root().add_child(ExposeMapMacro())
    # --- Home button (top right, reloads the map HTML) ---
    home_button_html = '''
        <div id="home-btn" style="position: absolute; top: 10px; right: 10px; z-index: 9999;">
            <button onclick="window.location.reload();" style="background: #fff; border: 2px solid #0078A8; border-radius: 6px; padding: 6px 16px; font-size: 16px; font-weight: bold; color: #0078A8; cursor: pointer; box-shadow: 0 2px 6px #0002;">🏠 Home</button>
        </div>
    '''
    m.get_root().html.add_child(Element(home_button_html))
    print(f"Actually added {marker_count} Gemini markers to the map.")
    m.save('singapore_news_sentiment_map.html')
    print("Map saved to singapore_news_sentiment_map.html")

def load_processed_articles(path='processed_articles.json'):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

def save_processed_articles(processed, path='processed_articles.json'):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(processed, f, ensure_ascii=False, indent=2)

def process_articles_with_gemini(articles):
    processed = load_processed_articles()
    api_key = load_gemini_api_key()
    updated = False
    results = []
    total_articles = len(articles)
    for idx, article in enumerate(articles, 1):
        article_id = article.get('url') or article.get('title')
        if not article_id:
            continue
        title = article.get('title', '')
        content = article.get('content', '')
        location = article.get('location', '')
        category = article.get('category', '')
        # If 'Singapore' is mentioned in title/content, or location is Singapore, or category is Singapore/local, set is_sg_related = True
        if (
            'singapore' in title.lower() or
            'singapore' in content.lower() or
            location.lower() == 'singapore' or
            ('singapore' in category.lower() if isinstance(category, str) else False) or
            ('local' in category.lower() if isinstance(category, str) else False)
        ):
            is_sg_related = True
            # Optionally, use previous Gemini result for place/sentiment if available
            if article_id in processed:
                gemini_result = processed[article_id]
                gemini_result['is_sg_related'] = True
            else:
                # Only run Gemini for place/sentiment, but force is_sg_related True
                place_name, sentiment, reason, emoji, _ = gemini_analyze_article(api_key, title, content, idx, total_articles)
                gemini_result = {
                    'place': place_name,
                    'sentiment': sentiment,
                    'reason': reason,
                    'emoji': emoji,
                    'is_sg_related': True
                }
                processed[article_id] = gemini_result
                updated = True
        else:
            # Only call Gemini if not already cached
            if article_id in processed and 'is_sg_related' in processed[article_id]:
                gemini_result = processed[article_id]
            else:
                place_name, sentiment, reason, emoji, is_sg_related = gemini_analyze_article(api_key, title, content, idx, total_articles)
                gemini_result = {
                    'place': place_name,
                    'sentiment': sentiment,
                    'reason': reason,
                    'emoji': emoji,
                    'is_sg_related': is_sg_related
                }
                processed[article_id] = gemini_result
                updated = True
        # Merge Gemini result into article
        article.update(gemini_result)
        results.append(article)
    if updated:
        save_processed_articles(processed)
    return results

if __name__ == "__main__":
    from datetime import datetime
    import pytz
    # Load all articles
    with open('articles_with_sentiment.json', 'r', encoding='utf-8') as f:
        articles = json.load(f)
    # Filter for today's news only (assume 'published' or 'date' field in ISO format)
    today = datetime.now(pytz.timezone('Asia/Singapore')).date()
    def is_today(article):
        for key in ['published', 'date', 'datetime']:
            if key in article:
                try:
                    dt = datetime.fromisoformat(article[key])
                    return dt.date() == today
                except Exception:
                    continue
        return False
    today_articles = [a for a in articles if is_today(a)]
    print(f"Found {len(today_articles)} articles for today.")
    # Only call Gemini for new articles, use cache for others
    today_articles_with_gemini = process_articles_with_gemini(today_articles)
    # Ensure processed_articles.json is always updated with the latest cache
    # (process_articles_with_gemini already saves if updated, but force save here for safety)
    processed_cache = load_processed_articles()
    save_processed_articles(processed_cache)
    plot_emojis_on_map(today_articles_with_gemini)
