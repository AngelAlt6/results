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
    
    filtered_data = []
    for game in data:
        try:
            game_time = datetime.strptime(game['Time'], '%a, %d %b %Y %H:%M:%S %Z')
            if game_time > cutoff_time:
                filtered_data.append(game)
        except ValueError:
            try:
                # Attempt to parse with the new format
                game_time = datetime.strptime(game['Time'], '%Y-%m-%d %H:%M:%S')
                if game_time > cutoff_time:
                    filtered_data.append(game)
            except ValueError:
                logging.warning(f"Could not parse game time for entry: {game}")
                
    return filtered_data

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
    lines = text.splitlines()
    i = 0

    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("Time:"):
            if game_data:
                games.append(game_data)
            game_data = {}
            game_data['Time'] = line.split("Time:")[1].strip()
            i += 1
            game_data['Contest'] = lines[i].split("Contest:")[1].strip()
            i += 1
            game_data['Map'] = lines[i].split("Map:")[1].strip()
            i += 1
            game_data['Player Count'] = lines[i].split("Player Count:")[1].strip()
            i += 1
            game_data['Diminisher'] = lines[i].split("Diminisher:")[1].strip()
            i += 1
            game_data['Winning Clan'] = lines[i].split("Winning Clan:")[1].strip()
            i += 1
            game_data['Prev. Points'] = lines[i].split("Prev. Points:")[1].strip()
            i += 1
            game_data['Gain'] = lines[i].split("Gain:")[1].strip()
            i += 1
            game_data['Curr. Points'] = lines[i].split("Curr. Points:")[1].strip()
            i += 1
        else:
            i += 1

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
    for game in reversed(new_games):
        game_info = (
            f"```\n"
            f"Time: {game['Time']}\n"
            f"Contest: {game['Contest']}\n"
            f"Map: {game['Map']}\n"
            f"Player Count: {game['Player Count']}\n"
            f"Diminisher: {game['Diminisher']}\n"
            f"Winning Clan: {game['Winning Clan']}\n"
            f"Prev. Points: {game['Prev. Points']}\n"
            f"Gain: {game['Gain']}\n"
            f"Curr. Points: {game['Curr. Points']}\n"
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

if __name__ == '__main__':
    try:
        send_clan_results()
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        send_discord_message(f"An error occurred while running the scraper: {e}")
