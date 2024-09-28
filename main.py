import requests
import os
import logging
import json
from datetime import datetime, timedelta
from time import sleep

# Set up logging
logging.basicConfig(level=logging.INFO)

# Discord Webhook URL from environment variable
WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
DATA_FILE = 'clan_results.json'

# Check if the webhook URL is set
if not WEBHOOK_URL:
    logging.error("DISCORD_WEBHOOK_URL environment variable is not set.")
    exit(1)

# Load existing data
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as file:
                return json.load(file)
        except json.JSONDecodeError:
            logging.error("JSONDecodeError: The data file is empty or corrupted. Initializing with an empty list.")
            return []
    return []

# Save data to JSON file
def save_data(data):
    with open(DATA_FILE, 'w') as file:
        json.dump(data, file, indent=4)

# Remove data older than 24 hours
def remove_old_data(data):
    cutoff_time = datetime.now() - timedelta(hours=24)
    return [game for game in data if datetime.strptime(game['Time'], '%a, %d %b %Y %H:%M:%S %Z') > cutoff_time]

# Scrape the results from the website
def scrape_clan_results():
    url = 'https://territorial.io/clan-results'
    retries = 3
    for _ in range(retries):
        try:
            response = requests.get(url)
            response.raise_for_status()
            break
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to retrieve data: {e}")
            sleep(5)
    else:
        logging.error("Max retries exceeded. Exiting.")
        return None

    text = response.text
    games = []
    game_data = {}

    for line in text.splitlines():
        if line.startswith("Time:"):
            if game_data:
                games.append(game_data)
                game_data = {}
            game_data['Time'] = line.split("Time:")[1].strip()
        elif line.startswith("Game Mode:"):
            game_data['Game Mode'] = line.split("Game Mode:")[1].strip()
        elif line.startswith("Map:"):
            game_data['Map'] = line.split("Map:")[1].strip()
        elif line.startswith("Player Count:"):
            game_data['Player Count'] = line.split("Player Count:")[1].strip()
        elif line.startswith("Team T:"):
            game_data['Team T'] = line.split("Team T:")[1].strip()
        elif line.startswith("Percentage L:"):
            game_data['Percentage L'] = line.split("Percentage L:")[1].strip()
        elif line.startswith("Res:"):
            game_data['Res'] = []
        elif line.startswith("   ["):
            game_data['Res'].append(line.strip())

    if game_data:
        games.append(game_data)

    return games

# Function to send the message to Discord
def send_discord_message(content):
    data = {"content": content}
    try:
        response = requests.post(WEBHOOK_URL, json=data)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to send message: {e}")

# Split the message into smaller parts if it exceeds Discord's limit
def split_message(content, limit=2000):
    parts = []
    while len(content) > limit:
        split_index = content.rfind('\n', 0, limit)
        if split_index == -1:
            split_index = limit
        parts.append(content[:split_index])
        content = content[split_index:]
    parts.append(content)
    return parts

# Format and send the scraped data to Discord
def send_clan_results():
    existing_data = load_data()
    existing_data = remove_old_data(existing_data)
    games = scrape_clan_results()
    if not games:
        logging.info("No game results to send.")
        return

    new_games = [game for game in games if game not in existing_data]
    if not new_games:
        logging.info("No new game results to send.")
        return

    content = ""
    count = 0
    for game in reversed(new_games):  # Post in reverse order
        game_info = (
            f"```\n"
            f"Time: {game['Time']}\n"
            f"Game Mode: {game['Game Mode']}\n"
            f"Map: {game['Map']}\n"
            f"Player Count: {game['Player Count']}\n"
            f"Team T: {game['Team T']}\n"
            f"Percentage L: {game['Percentage L']}\n"
            f"Res:\n" + "\n".join(game['Res']) + "\n"
            f"```\n"
        )
        content += game_info
        count += 1

        if count == 6:
            messages = split_message(content)
            for message in messages:
                send_discord_message(message)
            content = ""
            count = 0

    if content:
        messages = split_message(content)
        for message in messages:
            send_discord_message(message)

    save_data(existing_data + new_games)

# Run the function
if __name__ == '__main__':
    try:
        send_clan_results()
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        send_discord_message(f"An error occurred while running the scraper: {e}")
