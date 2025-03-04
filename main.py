import requests
from telegram import Bot
from telegram.ext import Updater
import schedule
import time
from bs4 import BeautifulSoup

# Replace these with your credentials
PORTAL_URL = "https://cuportal.covenantuniversity.edu.ng/login.php"
USERNAME = "your_username"
PASSWORD = "your_password"
TELEGRAM_TOKEN = "7705015733:AAHfQt0Ar2Y7ECVqMhxk45o4xRg9OhFlunQ"
CHAT_ID = "your_chat_id"  # Get this by sending a message to your bot and visiting https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates

# Initialize the Telegram bot
bot = Bot(token=TELEGRAM_TOKEN)

# Function to log in and fetch portal data
def fetch_portal_data():
    session = requests.Session()
    
    # Step 1: Get the login page to retrieve any necessary tokens
    login_page = session.get(PORTAL_URL)
    soup = BeautifulSoup(login_page.content, "html.parser")
    
    # Step 2: Extract CSRF token or other required fields (if any)
    # This depends on the portal's login form. Inspect the HTML to find the field names.
    csrf_token = soup.find("input", {"name": "csrf_token"})["value"] if soup.find("input", {"name": "csrf_token"}) else None
    
    # Step 3: Prepare the login payload
    payload = {
        "username": USERNAME,
        "password": PASSWORD,
        "csrf_token": csrf_token  # Include if required
    }
    
    # Step 4: Submit the login form
    login_response = session.post(PORTAL_URL, data=payload)
    
    # Step 5: Check if login was successful
    if "dashboard" in login_response.url:  # Replace "dashboard" with a keyword in the URL after successful login
        # Fetch the dashboard or any page you want to monitor
        dashboard_response = session.get("https://cuportal.covenantuniversity.edu.ng/dashboard.php")
        return dashboard_response.text
    else:
        return None

# Function to check for changes
def check_for_changes():
    current_data = fetch_portal_data()
    
    # Compare with previous data (you can save this to a file or in-memory)
    if hasattr(check_for_changes, "previous_data"):
        if current_data != check_for_changes.previous_data:
            bot.send_message(chat_id=CHAT_ID, text="There has been a change on your portal!")
        else:
            bot.send_message(chat_id=CHAT_ID, text="No changes detected.")
    else:
        bot.send_message(chat_id=CHAT_ID, text="Initial data fetched.")
    
    # Save the current data for future comparison
    check_for_changes.previous_data = current_data

# Schedule the task to run every 5 minutes
schedule.every(5).minutes.do(check_for_changes)

# Main loop
if __name__ == "__main__":
    # Start the scheduler
    while True:
        schedule.run_pending()
        time.sleep(1)