import requests
import os

# Directly targeting the OPL BiblioCommons data API feed for PS5 games on order
API_URL = "https://gateway.bibliocommons.com/v2/libraries/ottawa/results?query=formatcode%3A%28VIDEO_GAME%29%20%22playstation%205%22%20f_availability%3A%28on_order%29&searchType=smart"
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
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Accept': 'application/json',
        'X-Client-Id': '8a9ad0b3-ecae-4f9a-8b83-ffdf49ec1c12' # Standard BiblioCommons app key
    }
    try:
        response = requests.get(API_URL, headers=headers, timeout=15)
        data = response.json()
        
        # Dig into the data layout to extract raw titles
        titles = []
        results = data.get("results", [])
        for item in results:
            bib = item.get("bib", {})
            title = bib.get("title")
            if title:
                titles.append(title.strip())
                
        return set(titles)
    except Exception as e:
        print(f"Error calling OPL catalog backend: {e}")
        return set()

def run():
    current_games = get_on_order_games()
    print(f"Successfully scraped {len(current_games)} titles from library database.")
    
    if not current_games:
        print("Database returned zero entries or request timed out.")
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
        print(f"Sent Telegram update for: {new_games}")
        
        # Save baseline to list so it won't send repeats
        with open(TRACKER_FILE, "a", encoding="utf-8") as f:
            for game in new_games:
                f.write(game + "\n")
    else:
        print("Database sync verified. No new titles to report.")

if __name__ == "__main__":
    run()
