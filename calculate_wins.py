import os
import json
import logging
from datetime import datetime, timedelta
import requests

# Set up logging
logging.basicConfig(level=logging.INFO)

# Discord Webhook URL from environment variable
WEBHOOK_URL = os.getenv('DISCORD_WINNER_WEBHOOK_URL')
DATA_FILE = 'clan_results.json'

# Check if the webhook URL is set
if not WEBHOOK_URL:
    logging.error("DISCORD_WINNER_WEBHOOK_URL environment variable is not set.")
    exit(1)

# Load existing data
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as file:
                return json.load(file)
        except json.JSONDecodeError:
            logging.error("JSONDecodeError: The data file is empty or corrupted.")
            return []
    return []

# Sanitize result strings by removing unexpected characters
def sanitize_result(result):
    return ''.join(c for c in result if c.isprintable())

# Calculate wins in the last 24 hours
def calculate_wins(data):
    cutoff_time = datetime.now() - timedelta(hours=24)
    win_counts = {}

    for game in data:
        game_time = datetime.strptime(game['Time'], '%a, %d %b %Y %H:%M:%S %Z')
        if game_time > cutoff_time:
            if not game['Res']:
                continue

            for result in game['Res']:
                result = sanitize_result(result)
                logging.debug(f"Processing sanitized result: {result}")

                clan_name = result.split(' ')[0].strip(':').strip()

                if clan_name not in win_counts:
                    win_counts[clan_name] = 0

                win_counts[clan_name] += 1

    return win_counts

# Send results to Discord as an embed
def send_discord_embed(win_counts):
    if not win_counts:
        logging.info("No wins found in the last 24 hours.")
        return

    # Sort clans by win counts and limit to top 30
    sorted_wins = sorted(win_counts.items(), key=lambda item: item[1], reverse=True)[:30]

    # Prepare fields for the embed
    ranks_list = [str(idx + 1) for idx in range(len(sorted_wins))]
    clans_list = [clan for clan, _ in sorted_wins]
    wins_list = [str(win_count) for _, win_count in sorted_wins]

    # Debugging Output: Print formatted clans
    print("Formatted Clans:")
    for rank, clan, wins in zip(ranks_list, clans_list, wins_list):
        print(f"{rank}. {clan} - Wins: {wins}")

    # Create the embed fields
    fields = [
        {
            "name": "Rank",
            "value": "\n".join(ranks_list),
            "inline": True
        },
        {
            "name": "Clan",
            "value": "\n".join(clans_list]),  # Add brackets to clan names
            "inline": True
        },
        {
            "name": "Wins",
            "value": "\n".join(wins_list),
            "inline": True
        }
    ]

    # Create the embed payload
    embed = {
        "title": "🏆 Top Clans with Most Wins in the Last 24 Hours",
        "description": "Here are the clans that have achieved the most wins recently.",
        "color": int("802929", 16),  # Gold color
        "fields": fields,
        "footer": {
            "text": "Territorial News Headlines",
            "icon_url": "https://i.imgur.com/b7CN3eB.jpeg"  # Your desired image URL
        }
    }

    # Send the embed to Discord
    payload = {
        "embeds": [embed]
    }

    try:
        response = requests.post(WEBHOOK_URL, json=payload)
        response.raise_for_status()  # Raise an error for bad responses
        logging.info("Successfully sent embed to Discord.")
    except requests.exceptions.HTTPError as e:
        logging.error(f"Failed to send embed: {e.response.text}")  # Show detailed error message
    except requests.exceptions.RequestException as e:
        logging.error(f"Request exception: {e}")

if __name__ == '__main__':
    data = load_data()
    win_counts = calculate_wins(data)
    send_discord_embed(win_counts)
