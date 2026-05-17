import os
import requests
import re
import json

URL = "https://ottawa.bibliocommons.com/v2/search?query=formatcode%3A%28VIDEO_GAME%29%20%22playstation%205%22&searchType=smart&f_availability=on_order"
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
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5'
    }
    try:
        response = requests.get(URL, headers=headers, timeout=15)
        html = response.text
        
        # Locate the exact raw bootstrap data object BiblioCommons uses to fill the page
        match = re.search(r'window\.__PRELOADED_STATE__\s*=\s*(\{.*?\});', html)
        if match:
            state_json = json.loads(match.group(1))
            # Drill straight down into the catalog entities dictionary
            entities = state_json.get("entities", {})
            bibs = entities.get("bibs", {})
            
            for bib_id, bib_data in bibs.items():
                title = bib_data.get("title")
                format_code = bib_data.get("format", {}).get("code", "")
                
                # Double check that it's a video game format item
                if title and "VIDEO_GAME" in format_code.upper():
                    titles.add(title.strip())
                    
        # Fallback regex extraction if the JSON layout structure shifts slightly
        if not titles:
            raw_titles = re.findall(r'"title"\s*:\s*"([^"]+)"', html)
            for t in raw_titles:
                if not any(x in t.lower() for x in ['search', 'hold', 'log in', 'ottawa']):
                    titles.add(t.strip())
                    
    except Exception as e:
        print(f"Error extracting data block: {e}")
        
    return titles

def run():
    current_games = get_on_order_games()
    print(f"Successfully tracked {len(current_games)} titles from the layout core.")
    
    if not current_games:
        print("Data core parsing returned zero entries. The layout format may have changed.")
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
        print("Daily sync completed. No new pre-orders found.")

if __name__ == "__main__":
    run()
