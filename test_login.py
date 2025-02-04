import time
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackContext
import requests
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify

# Load environment variables
load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("No BOT_TOKEN provided. Please set the BOT_TOKEN environment variable or create a .env file.")

PORTAL_URL = "https://cuportal.covenantuniversity.edu.ng/studentdashboard.php"
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://cu-portal-bot.onrender.com/webhook")

user_credentials = {}
last_data = {}

# Initialize Flask app
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!"

@app.route("/webhook", methods=['POST'])
def webhook():
    try:
        data = request.json  # Get the JSON data from the request
        print("Webhook received:", data)

        # Process the incoming update
        update = Update.de_json(data, application.bot)
        asyncio.create_task(application.update_queue.put(update))

        # Return a success response
        return jsonify({"status": "success"}), 200
    except Exception as e:
        print("Error processing webhook:", e)
        return jsonify({"status": "error", "message": str(e)}), 500

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
async def check_for_changes(application, chat_id, username, password):
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
                await application.bot.send_message(chat_id=chat_id, text=message)
        last_data[chat_id] = current_data
        await asyncio.sleep(300)  # Check every 5 minutes

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
        asyncio.create_task(check_for_changes(application, chat_id, username, password))
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
    await application.bot.set_webhook(WEBHOOK_URL)

    # Start the Flask app
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))

if __name__ == "__main__":
    try:
        # Run the bot
        asyncio.run(main())
    except RuntimeError as e:
        print(f"RuntimeError: {e}")
    except KeyboardInterrupt:
        print("Bot stopped by user.")