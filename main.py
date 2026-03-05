import time
import requests
import tweepy
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
from nba_api.stats.endpoints import scoreboardv2

# --- 1. YOUR CREDENTIALS ---
# Fixed the Syntax Error: Only one set of quotes!
API_KEY = "zQpIu4UhNcUqbcYaOg0oP0yMQ"
API_SECRET = "TXc8cM941xjCmrPbnrRUcYjpzYoxXm6tBgyNvAYiPyQJ8Rg5Db"
ACCESS_TOKEN = "2011467923400126464-C1pVqVYSiOO6tqCayi0i1m55NhI3i0"
ACCESS_TOKEN_SECRET = "aVnCJlDrAPqHkGv8uuMWaJetT8EvAv61GgF5nePZVXntI"

client = tweepy.Client(
    consumer_key=API_KEY, consumer_secret=API_SECRET,
    access_token=ACCESS_TOKEN, access_token_secret=ACCESS_TOKEN_SECRET
)

# --- 2. SCRAPER: GET BEST PROP FROM WAGERWISE ---
def get_wagerwise_prop():
    try:
        url = "https://wagerwise.win/nba"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Finds the first row in the table (usually the highest edge)
        rows = soup.find_all('tr')
        for row in rows[1:3]: # Checking top entries
            cols = row.find_all('td')
            if len(cols) >= 4:
                player = cols[0].get_text(strip=True)
                prop = cols[1].get_text(strip=True)
                line = cols[2].get_text(strip=True)
                edge = cols[3].get_text(strip=True)
                return f"🔥 TOP NBA PROP\n👤 {player}\n🏀 {prop}: {line}\n🎯 Edge: {edge}"
    except Exception as e:
        print(f"Scraper error: {e}")
    return None

# --- 3. SCHEDULER: CHECK FOR GAMES 10 HOURS AWAY ---
posted_games = set()

def run_bot():
    print("🤖 Bot is active and scanning schedule...")
    while True:
        try:
            # Get today's games
            sb = scoreboardv2.ScoreboardV2()
            games = sb.get_dict()['resultSets'][0]['rowSet']
            
            now = datetime.now(timezone.utc)
            
            for g in games:
                game_id = g[2]
                # NBA API times are usually formatted as "2024-03-25T19:00:00"
                # We assume the API returns ET, so adjust if needed
                game_time = datetime.fromisoformat(g[4].replace('Z', '')).replace(tzinfo=timezone.utc)
                
                # Check if game is roughly 10 hours away (within a 10-minute window)
                time_diff = game_time - now
                if timedelta(hours=9, minutes=55) < time_diff < timedelta(hours=10, minutes=5):
                    if game_id not in posted_games:
                        prop_msg = get_wagerwise_prop()
                        if prop_msg:
                            tweet_text = f"{prop_msg}\n\n🕒 Tip-off in 10 hours!\n#NBAProps #WagerWise"
                            client.create_tweet(text=tweet_text)
                            posted_games.add(game_id)
                            print(f"✅ Posted for Game {game_id}")
            
        except Exception as e:
            print(f"Loop error: {e}")
        
        time.sleep(300) # Check every 5 minutes

if __name__ == "__main__":
    run_bot()