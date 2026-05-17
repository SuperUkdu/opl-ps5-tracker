import os
import requests
import xml.etree.ElementTree as ET

# Native BiblioCommons RSS data feed targeting OPL's PS5 "On Order" catalog list
FEED_URL = "https://ottawa.bibliocommons.com/search.rss?t=smart&q=formatcode%3A%28VIDEO_GAME%29+AND+%22playstation+5%22+AND+oo%3A%28true%29"
TRACKER_FILE = "seen_games.txt"

def send_telegram_message(message):
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if token and chat_id:
        telegram_url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": message}
        try:
            requests.post(telegram_url, json=payload, timeout=10)
        except Exception as e:
            print(f"Failed to send Telegram message: {e}")

def get_on_order_games():
    titles = set()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) OPL-Game-Tracker-Bot'
    }
    try:
        response = requests.get(FEED_URL, headers=headers, timeout=15)
        if response.status_code == 200:
            # Parse the raw feed text data directly using Python's built-in fast XML processor
            root = ET.fromstring(response.content)
            for item in root.findall('.//item'):
                title_elem = item.find('title')
                if title_elem is not None and title_elem.text:
                    title_text = title_elem.text.strip()
                    # Drop the generic feed header name if it loops into the item layout
                    if not title_text.startswith("Ottawa Public Library"):
                        titles.add(title_text)
        else:
            print(f"Library feed responded with status code: {response.status_code}")
    except Exception as e:
        print(f"Error accessing public library feed: {e}")
        
    return titles

def run():
    current_games = get_on_order_games()
    print(f"Successfully tracked {len(current_games)} titles from the native library feed.")
    
    if not current_games:
        print("The library data feed is currently empty or pending update.")
        return
    
    if os.path.exists(TRACKER_FILE):
        with open(TRACKER_FILE, "r", encoding="utf-8") as f:
            seen_games = set(line.strip() for line in f if line.strip())
    else:
        seen_games = set()

    new_games = current_games - seen_games

    if new_games:
        message = "🚨 New PS5 Game(s) On Order at OPL!:\n\n" + "\n".join(f"• {game}" for game in new_games)
        send_telegram_message(message)
        print(f"Sent Telegram notification for: {new_games}")
        
        with open(TRACKER_FILE, "a", encoding="utf-8") as f:
            for game in new_games:
                f.write(game + "\n")
    else:
        print("Daily sync verified. No new arrivals posted to feed.")

if __name__ == "__main__":
    run()
