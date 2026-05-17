import os
import requests

# Directly targets OPL's underlying public catalog backend search system
API_URL = "https://ottawa.bibliocommons.com/v2/search?query=formatcode%3A%28VIDEO_GAME%29%20%22playstation%205%22&searchType=smart&f_availability=on_order"
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
    # Masking the request with a standard browser header to pull raw page script components
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }
    try:
        response = requests.get(API_URL, headers=headers, timeout=15)
        text_content = response.text
        
        # OPL embeds data records inside a script tag block named 'pageData' or 'props' 
        # We can extract text chunks directly via simple string isolation without parsing HTML blocks
        chunks = text_content.split('"title":"')
        for chunk in chunks[1:]:
            title = chunk.split('"')[0].strip()
            # Clean out any catalog interface labels or duplicates
            if title and len(title) > 2 and not any(x in title.lower() for x in ['search', 'hold', 'log in', 'cancel']):
                # Clean up escaped unicode spaces if present
                title = title.replace('\\u0020', ' ').replace('\\/','/')
                titles.add(title)
    except Exception as e:
        print(f"Error connecting to OPL data layer: {e}")
        
    return titles

def run():
    current_games = get_on_order_games()
    print(f"Successfully tracked {len(current_games)} titles from the data layer.")
    
    if not current_games:
        print("Data layer check failed or returned an empty payload.")
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
        print("Daily sync complete. No new items listed.")

if __name__ == "__main__":
    run()
