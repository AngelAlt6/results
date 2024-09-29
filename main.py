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
    with open(DATA_FILE, 'w') as file:
        json.dump(data, file, indent=4)

# Remove data older than 24 hours
def remove_old_data(data):
    cutoff_time = datetime.now() - timedelta(hours=24)

    return games

# Function to send the message to Discord
def send_discord_message(content):
    data = {"content": content}
    try:
        response = requests.post(WEBHOOK_URL, json=data)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to send message: {e}")
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
