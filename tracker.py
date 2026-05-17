import os
import requests

# Paste your unique Google Web App URL here inside the quotes
GOOGLE_BRIDGE_URL = "https://script.google.com/macros/s/AKfycbwqlqZF-JnzJSstMVCbix7fSqU6uOJcjj1XIN2ZDb8fnYkjIU1hUw9dQWqGvKfQfK8v/exec"
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
        response = requests.get(GOOGLE_BRIDGE_URL, timeout=15)
        if response.status_code == 200 and response.text != "Error":
            # The Google app returns a clean list separated by line breaks
            lines = response.text.split("\n")
            for line in lines:
                if line.strip():
                    titles.add(line.strip())
        else:
            print("Google bridge server encountered an error parsing the page text.")
    except Exception as e:
        print(f"Failed to communicate with Google data bridge: {e}")
        
    return titles

def run():
    current_games = get_on_order_games()
    print(f"Successfully tracked {len(current_games)} titles from the secure data bridge.")
    
    if not current_games:
        print("Data package empty. No current pre-orders found.")
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
        print("Daily check complete. System fully synchronized.")

if __name__ == "__main__":
    run()
