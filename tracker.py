import os
import time
import requests
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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
    options = uc.ChromeOptions()
    options.add_argument("--headless") # Runs silently in the background
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    titles = set()
    
    try:
        # Initialize the stealth undetected chrome driver
        driver = uc.Chrome(options=options)
        driver.get(URL)
        
        # Give the heavy page up to 25 seconds to render past protection screens
        WebDriverWait(driver, 25).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a.cp-title-link, .cp-title, [data-test-id='title']"))
        )
        time.sleep(5) # Safe buffer for text synchronization
        
        elements = driver.find_elements(By.CSS_SELECTOR, "a.cp-title-link, .cp-title, [data-test-id='title']")
        for el in elements:
            text = el.text.strip()
            if text and len(text) > 2 and not any(x in text.lower() for x in ['hold', 'shelf', 'log in', 'search', 'filter']):
                titles.add(text)
                
        driver.quit()
    except Exception as e:
        print(f"Stealth browser encountered a layout delay or timeout: {e}")
        try:
            driver.quit()
        except:
            pass
            
    return titles

def run():
    current_games = get_on_order_games()
    print(f"Successfully tracked {len(current_games)} titles from the live browser environment.")
    
    if not current_games:
        print("Could not pull records via browser. Page layer did not render.")
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
        print("Database sync complete. No new pre-orders listed.")

if __name__ == "__main__":
    run()
