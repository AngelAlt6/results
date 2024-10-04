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
    return ''.join(c for c in result if c.isprintable() and c not in ('\n', '\r'))

# Calculate wins in the last 24 hours
def calculate_wins(data):
    cutoff_time = datetime.now() - timedelta(hours=24)
    win_counts = {}

    for game in data:
        game_time = datetime.strptime(game['Time'], '%a, %d %b %Y %H:%M:%S %Z')
        if game_time > cutoff_time:
            for result in game['Res']:
                # Sanitize the result
                result = sanitize_result(result)
                logging.debug(f"Processing sanitized result: {result}")

                # Ensure the result is in the expected format
                parts = result.split('=')
                if len(parts) < 2:
                    logging.warning(f"Unexpected format in result: {result}")
                    continue
                
                try:
                    clan_name = result.split(':')[0].strip('[] ')
                    percentage_str = parts[1].split(',')[0].strip()
                    percentage = float(percentage_str)

                    if clan_name not in win_counts:
                        win_counts[clan_name] = 0

                    # Check for win
                    if percentage > 50:  # Modify based on your winning criteria
                        win_counts[clan_name] += 1
                
                except ValueError as e:
                    logging.warning(f"Could not process result: {result}, error: {e}")
                    continue

    return win_counts

# Send results to Discord
def send_discord_message(content):
    data = {"content": content}
    try:
        response = requests.post(WEBHOOK_URL, json=data)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to send message: {e}")

# Format and send the top clans' win results
def report_wins():
    data = load_data()
    win_counts = calculate_wins(data)

    if not win_counts:
        logging.info("No wins found in the last 24 hours.")
        return

    # Sort clans by win counts and limit to top 30
    sorted_wins = sorted(win_counts.items(), key=lambda item: item[1], reverse=True)[:30]

    # Create message content
    content = "Top 30 Clans with Most Wins in the Last 24 Hours:\n"
    for clan, wins in sorted_wins:
        content += f"{clan}: {wins} wins\n"

    send_discord_message(content)

if __name__ == '__main__':
    report_wins()
