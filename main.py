import requests
from bs4 import BeautifulSoup
import os

# Discord Webhook URL from environment variable
WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')

# Scrape the results from the website
def scrape_clan_results():
    url = 'https://territorial.io/clan-results'
    response = requests.get(url)

    if response.status_code != 200:
        print(f"Failed to retrieve data: {response.status_code}")
        return None

    soup = BeautifulSoup(response.content, 'html.parser')
    games = []

    # Find all the relevant data blocks (update with correct tags or classes)
    result_blocks = soup.find_all('div', class_='game-result')  # Example selector, adjust as needed

    for block in result_blocks:
        game_data = {}

        # Extract data from the HTML block
        time = block.find('span', class_='time').text
        mode = block.find('span', class_='mode').text
        map_name = block.find('span', class_='map').text
        player_count = block.find('span', class_='player-count').text

        # Add extracted data to game_data dict
        game_data['Time'] = time
        game_data['Game Mode'] = mode
        game_data['Map'] = map_name
        game_data['Player Count'] = player_count

        # Add any other necessary fields
        games.append(game_data)

    return games

# Function to send the message to Discord
def send_discord_message(content):
    data = {"content": content}
    response = requests.post(WEBHOOK_URL, json=data)
    if response.status_code != 204:
        print(f"Failed to send message: {response.status_code}")

# Format and send the scraped data to Discord
def send_clan_results():
    games = scrape_clan_results()
    if not games:
        print("No game results to send.")
        return

    for game in games:
        content = (
            f"**Time:** {game['Time']}\n"
            f"**Game Mode:** {game['Game Mode']}\n"
            f"**Map:** {game['Map']}\n"
            f"**Player Count:** {game['Player Count']}\n"
        )
        send_discord_message(content)

# Run the function
if __name__ == '__main__':
    send_clan_results()
