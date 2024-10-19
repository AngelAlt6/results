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
            # Check if there are results
            if not game['Res']:
                continue

            # Iterate over each result in the Res section
            for result in game['Res']:
                # Sanitize the result
                result = sanitize_result(result)
                logging.debug(f"Processing sanitized result: {result}")

                # Extract clan names from the result and sanitize
                clan_name = result.split(' ')[0].strip(':').strip()  # Remove ':' and spaces

                if clan_name not in win_counts:
                    win_counts[clan_name] = 0

                # Count each entry as a win
                win_counts[clan_name] += 1

    return win_counts

# Send results to Discord as an embed
def send_discord_embed(wins):
    # Create fields for the embed
    fields = [
        {"name": f"{idx + 1}. {clan}", "value": f"Wins: {win_count}", "inline": True}
        for idx, (clan, win_count) in enumerate(wins)
    ]

    embed = {
        "title": "🏆 Top Clans with Most Wins in the Last 24 Hours",
        "description": "Here are the clans that have achieved the most wins recently.",
        "color": int("FFD700", 16),  # Gold color
        "fields": fields,
        "footer": {
            "text": "Data updated every 24 hours",
        }
    }

    payload = {
        "embeds": [embed]
    }

    try:
        response = requests.post(WEBHOOK_URL, json=payload)
        response.raise_for_status()
        logging.info("Successfully sent embed to Discord.")
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to send embed: {e}")

# Format and send the top clans' win results
def report_wins():
    data = load_data()
    win_counts = calculate_wins(data)

    if not win_counts:
        logging.info("No wins found in the last 24 hours.")
        return

    # Sort clans by win counts and limit to top 30
    sorted_wins = sorted(win_counts.items(), key=lambda item: item[1], reverse=True)[:30]

    send_discord_embed(sorted_wins)

if __name__ == '__main__':
    report_wins()
