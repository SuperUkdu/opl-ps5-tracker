import os
import requests
from bs4 import BeautifulSoup

# A pre-generated RSS feed layout matching OPL's "Playstation 5 On Order" search query
RSS_FEED_URL = "https://fetchrss.com/rss/6647953258c707bf040669c2664794fc7d620580970a0492.xml"
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
    try:
        # Fetching raw XML text structure from the RSS mirror proxy
        response = requests.get(RSS_FEED_URL, timeout=15)
        soup = BeautifulSoup(response.content, features="xml")
        
        # Every game listed on order will be inside an <item> tag block
        items = soup.find_all('item')
        for item in items:
            title_element = item.find('title')
            if title_element:
                title_text = title_element.text.strip()
                # Clean up any generic interface headers attached by the feed generator
                if title_text and not title_text.startswith("Ottawa Public Library"):
                    titles.add(title_text)
    except Exception as e:
        print(f"Error parsing the proxy RSS feed layer: {e}")
        
    return titles

def run():
    current_games = get_on_order_games()
    print(f"Successfully tracked {len(current_games)} titles from the RSS feed layer.")
    
    if not current_games:
        print("Could not pull records. The proxy feed source returned zero entries.")
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
        print("Daily check complete. No new pre-orders posted today.")

if __name__ == "__main__":
    run()
