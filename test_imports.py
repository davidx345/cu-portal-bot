import time
import threading
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackContext
import requests
from bs4 import BeautifulSoup

# Telegram Bot Token (replace with your actual token as a string)
BOT_TOKEN = "7705015733:AAHfQt0Ar2Y7ECVqMhxk45o4xRg9OhFlunQ"  # Replace with your bot token

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
            "academic_planning": soup.find("div", {"id": "academic-planning"}).text.strip(),
            "resumption": soup.find("div", {"id": "resumption"}).text.strip(),
            "student_affairs": soup.find("div", {"id": "student-affairs"}).text.strip(),
            "course_control": soup.find("div", {"id": "course-control"}).text.strip(),
            "attendance": soup.find("div", {"id": "attendance"}).text.strip(),
            "exam_conduct": soup.find("div", {"id": "exam-conduct"}).text.strip(),
            "result_upload": soup.find("div", {"id": "result-upload"}).text.strip(),
            "result_processing": soup.find("div", {"id": "result-processing"}).text.strip(),
        }
        return data
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

# Function to check for changes and notify the user
def check_for_changes(chat_id, username, password):
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
        time.sleep(60)  # Check every minute

# Start command handler
def start(update: Update, context: CallbackContext):
    update.message.reply_text("Welcome! Please provide your portal username and password separated by a space.")

# Handle user input for credentials
def handle_credentials(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    text = update.message.text.strip()
    if " " in text:
        username, password = text.split(" ", 1)
        user_credentials[chat_id] = {"username": username, "password": password}
        update.message.reply_text("Credentials saved. Monitoring started.")
        threading.Thread(target=check_for_changes, args=(chat_id, username, password)).start()
    else:
        update.message.reply_text("Invalid format. Please provide username and password separated by a space.")

# Main function
if __name__ == "__main__":
    # Initialize the Application
    application = Application.builder().token(BOT_TOKEN).build()

    dispatcher = application.dispatcher

    # Add handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(None, handle_credentials))  # Use None instead of Filters.text

    # Start the bot
    application.run_polling()
