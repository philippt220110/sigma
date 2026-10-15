import json
import os
import feedparser
from datetime import datetime

print("⚡ SIGMA Weekly Intelligence Agent gestartet...")
print(f"Zeitstempel: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# 1. trends.json laden
DB_FILE = "trends.json"

if os.path.exists(DB_FILE):
    with open(DB_FILE, "r", encoding="utf-8") as f:
        db_data = json.load(f)
    print(f"✅ trends.json erfolgreich geladen ({len(db_data.get('trends', []))} Trends erfasst).")
else:
    print("⚠️ trends.json nicht gefunden.")
    exit(1)

# 2. Relevante RSS Feeds scrapen
RSS_FEEDS = [
    "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
    "http://export.arxiv.org/rss/cs.AI"
]

fetched_news = []
for feed_url in RSS_FEEDS:
    try:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:2]:
            fetched_news.append({
                "date": datetime.now().strftime("%d. %b %Y"),
                "title": entry.title,
                "source": feed.feed.get("title", "Tech Feed"),
                "trend": "General Tech",
                "desc": entry.get("summary", "")[:150] + "..."
            })
    except Exception as e:
        print(f"Fehler beim Lesen von Feed {feed_url}: {e}")

print(f"📰 {len(fetched_news)} aktuelle Nachrichten gesammelt.")

# 3. News-Feed in trends.json aktualisieren (Rollierender 4-Wochen Feed)
if fetched_news:
    # Füge neue News oben an und begrenze auf max 10 Einträge
    updated_feed = fetched_news + db_data.get("news_feed", [])
    db_data["news_feed"] = updated_feed[:10]

db_data["last_updated"] = datetime.now().strftime("%Y-%m-%d")

# 4. Aktualisierte trends.json speichern
with open(DB_FILE, "w", encoding="utf-8") as f:
    json.dump(db_data, f, ensure_ascii=False, indent=2)

print("💾 trends.json wurde erfolgreich aktualisiert!")
