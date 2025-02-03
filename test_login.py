import time
import threading
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackContext
import requests
from bs4 import BeautifulSoup
import sys
import os
import asyncio

# Load the bot token from the environment variable or from the BOT_TOKEN.env file
BOT_TOKEN = os.getenv('BOT_TOKEN')

if not BOT_TOKEN:
    try:
        with open('BOT_TOKEN.env', 'r') as file:
            BOT_TOKEN = file.read().strip()
    except FileNotFoundError:
        raise ValueError("No BOT_TOKEN provided. Please set the BOT_TOKEN environment variable or create a BOT_TOKEN.env file.")

# Portal URL
PORTAL_URL = "https://cuportal.covenantuniversity.edu.ng/studentdashboard.php"

# User credentials storage (for demonstration purposes; use a secure method in production)
user_credentials = {}
last_data = {}

# Function to log in to the portal and fetch data
def fetch_portal_data(username, password):
    try:
        session = requests.Session()
        # Simulate login (adjust based on the actual login mechanism of the portal)
        login_payload = {
            "username": username,
            "password": password
        }
        response = session.post(PORTAL_URL, data=login_payload)

        # Check if login was successful
        if "studentdashboard.php" not in response.url:
            return None  # Login failed

        # Parse the dashboard content
        soup = BeautifulSoup(response.text, 'html.parser')
        data = {
            "academic_planning": soup.find("div", {"id": "academic-planning"}).text.strip() if soup.find("div", {"id": "academic-planning"}) else "N/A",
            "resumption": soup.find("div", {"id": "resumption"}).text.strip() if soup.find("div", {"id": "resumption"}) else "N/A",
            "student_affairs": soup.find("div", {"id": "student-affairs"}).text.strip() if soup.find("div", {"id": "student-affairs"}) else "N/A",
            "course_control": soup.find("div", {"id": "course-control"}).text.strip() if soup.find("div", {"id": "course-control"}) else "N/A",
            "attendance": soup.find("div", {"id": "attendance"}).text.strip() if soup.find("div", {"id": "attendance"}) else "N/A",
            "exam_conduct": soup.find("div", {"id": "exam-conduct"}).text.strip() if soup.find("div", {"id": "exam-conduct"}) else "N/A",
            "result_upload": soup.find("div", {"id": "result-upload"}).text.strip() if soup.find("div", {"id": "result-upload"}) else "N/A",
            "result_processing": soup.find("div", {"id": "result-processing"}).text.strip() if soup.find("div", {"id": "result-processing"}) else "N/A",
        }
        return data
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

# Function to check for changes and notify the user
def check_for_changes(application, chat_id, username, password):
    global last_data
    while True:
        current_data = fetch_portal_data(username, password)
        if current_data and chat_id in last_data:
            if current_data != last_data[chat_id]:
                changes = []
                for key, value in current_data.items():
                    if last_data[chat_id].get(key) != value:
                        changes.append(f"{key.replace('_', ' ').title()}: {value}")
                message = "Changes detected:\n" + "\n".join(changes)
                application.bot.send_message(chat_id=chat_id, text=message)
        last_data[chat_id] = current_data
        time.sleep(300)  # Check every 5 minutes

# Start command handler
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Welcome! Please provide your portal username and password separated by a space.")

# Handle user input for credentials
async def handle_credentials(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    text = update.message.text.strip()
    if " " in text:
        username, password = text.split(" ", 1)
        user_credentials[chat_id] = {"username": username, "password": password}
        await update.message.reply_text("Credentials saved. Monitoring started.")
        threading.Thread(target=check_for_changes, args=(application, chat_id, username, password)).start()
    else:
        await update.message.reply_text("Invalid format. Please provide username and password separated by a space.")

# Stop command handler
async def stop(update: Update, context: CallbackContext):
    await update.message.reply_text("Bot is stopping...")
    await application.stop()

# Main function
async def main():
    global application
    # Initialize the Application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stop", stop))
    application.add_handler(MessageHandler(None, handle_credentials))  # Use None instead of Filters.text

    # Set webhook
    WEBHOOK_URL = "https://cu-portal-bot.onrender.com/webhook"
    await application.bot.set_webhook(WEBHOOK_URL)

    # Start the bot
    application.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        url_path="/webhook",
        webhook_url=WEBHOOK_URL
    )

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())