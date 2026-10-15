import json
import os
import feedparser
from datetime import datetime
from google import genai

print("⚡ SIGMA Weekly Intelligence Agent mit Gemini AI gestartet...")

# 1. trends.json laden
DB_FILE = "trends.json"
if os.path.exists(DB_FILE):
    with open(DB_FILE, "r", encoding="utf-8") as f:
        db_data = json.load(f)
    print(f"✅ trends.json geladen ({len(db_data.get('trends', []))} Trends verankert).")
else:
    print("⚠️ trends.json nicht gefunden.")
    exit(1)

# 2. Relevante RSS Feeds scrapen
RSS_FEEDS = [
    "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
    "http://export.arxiv.org/rss/cs.AI"
]

raw_articles = []
for feed_url in RSS_FEEDS:
    try:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:3]:
            raw_articles.append({
                "title": entry.title,
                "link": entry.link,
                "summary": entry.get("summary", "")[:200]
            })
    except Exception as e:
        print(f"Fehler beim Scraping ({feed_url}): {e}")

print(f"📰 {len(raw_articles)} neue Artikel gesammelt.")

# 3. Gemini API Prompt mit KI-Reasoning
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("⚠️ Kein GEMINI_API_KEY gefunden!")
    exit(1)

client = genai.Client(api_key=api_key)

prompt = f"""
Du bist der Strategie-KI-Agent für 'SIGMA' (Tech Radar der Schwarz Gruppe).
Deine Aufgabe ist es, aktuelle Nachrichten zu analysieren und sie mit den 11 Core-Trends abzugleichen.

AKTUELLE TREND-BASELINE:
{json.dumps(db_data['trends'], ensure_ascii=False, indent=2)}

NEUE TECH-NACHRICHTEN:
{json.dumps(raw_articles, ensure_ascii=False, indent=2)}

AUFGABEN:
1. Wähle die 2-3 relevantesten Nachrichten aus und ordne sie exakt einem der 11 Trends zu.
2. Prüfe, ob eine der Nachrichten ein starkes Signal ist, das eine Anpassung des Zeithorizonts (z.B. von 5 Jahre auf 2 Jahre) erfordert.

Antworte AUSSCHLIESSLICH in folgendem gültigen JSON-Format (ohne Markdown, ohne ```json Wrap):
{{
  "new_news_items": [
    {{
      "date": "{datetime.now().strftime('%d. %b %Y')}",
      "title": "Titel der Nachricht auf Deutsch",
      "source": "Medium/Quelle",
      "trend": "Name des betroffenen Trends",
      "desc": "Zusammenfassung in 1 Satz auf Deutsch"
    }}
  ],
  "proposed_alert": {{
    "trend_id": "03",
    "reason": "Konkrete Begründung für Anpassung auf Deutsch",
    "sourceNews": "Artikel-Titel als Beleg",
    "suggestedTimeframe": "2 Jahre"
  }}
}}
Wenn KEINE Trend-Anpassung nötig ist, setze "proposed_alert" auf null.
"""

print("🧠 Befrage Gemini API für wöchentliches Trend-Assessment...")

try:
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    
    clean_json_str = response.text.strip().replace("```json", "").replace("```", "")
    ai_output = json.loads(clean_json_str)

    # News Feed aktualisieren
    if "new_news_items" in ai_output and ai_output["new_news_items"]:
        updated_feed = ai_output["new_news_items"] + db_data.get("news_feed", [])
        db_data["news_feed"] = updated_feed[:10]

    # Proposed Alert ins Control Board schreiben
    if ai_output.get("proposed_alert"):
        alert = ai_output["proposed_alert"]
        target_id = alert.get("trend_id")
        for trend in db_data["trends"]:
            if trend["id"] == target_id:
                trend["pendingAlert"] = {
                  "suggestedTimeframe": alert.get("suggestedTimeframe", "2 Jahre"),
                  "reason": alert.get("reason"),
                  "sourceNews": alert.get("sourceNews")
                }
                print(f"⚠️ KI schlägt Alert für Trend {target_id} vor!")

    db_data["last_updated"] = datetime.now().strftime("%Y-%m-%d")

    # In trends.json speichern
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db_data, f, ensure_ascii=False, indent=2)

    print("💾 trends.json erfolgreich mit Gemini AI-Analyse aktualisiert!")

except Exception as e:
    print(f"Fehler bei Gemini API Auswertung: {e}")
