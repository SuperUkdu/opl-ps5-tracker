import requests
from bs4 import BeautifulSoup
import os
import re

# Standard OPL search URL targeting PS5 games on order
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
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9'
    }
    try:
        response = requests.get(URL, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        titles = set()
        
        # Strategy A: Target standard title link elements if present
        for link in soup.select("a[href*='/v2/v2/'], .cp-title, a.cp-title-link"):
            text = link.get_text().strip()
            if text and not any(x in text.lower() for x in ['shelf', 'hold', 'log in', 'search']):
                titles.add(text)
                
        # Strategy B: Fallback parsing across the entire page body text layout
        # (Grabs titles listed right next to format markers)
        page_text = soup.get_text()
        raw_matches = re.findall(r'([A-Za-z0-9\s™®©\-\:\!\'\.]+)\,\s*Video\s*Game', page_text)
        for match in raw_matches:
            clean_title = match.strip().split('\n')[-1].strip()
            if len(clean_title) > 2 and not any(x in clean_title.lower() for x in ['skip', 'filter', 'cart']):
                titles.add(clean_title)
                
        return titles
    except Exception as e:
        print(f"Error accessing library webpage: {e}")
        return set()

def run():
    current_games = get_on_order_games()
    print(f"Successfully tracked {len(current_games)} titles from the library catalogue layout.")
    
    if not current_games:
        print("Could not parse records from the current page content.")
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
        print(f"Sent Telegram alert for: {new_games}")
        
        # Append found titles to the baseline memory registry
        with open(TRACKER_FILE, "a", encoding="utf-8") as f:
            for game in new_games:
                f.write(game + "\n")
    else:
        print("Database alignment accurate. No new pre-orders posted.")

if __name__ == "__main__":
    run()
