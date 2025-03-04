import requests
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackContext
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask import Flask, request, jsonify
import os

# Load environment variables
load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("No BOT_TOKEN provided. Please set the BOT_TOKEN environment variable or create a .env file.")

# Read the webhook URL from the WEBHOOK_URL file
with open('WEBHOOK_URL', 'r') as file:
    WEBHOOK_URL = file.read().strip()

PORTAL_URL = "https://cuportal.covenantuniversity.edu.ng/studentdashboard.php"

user_credentials = {}
last_data = {}

# Initialize Flask app
app = Flask(__name__)

@app.route("/")
def index():
    return "CU Portal Bot is running."

@app.route("/webhook", methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    application.update_queue.put(update)
    return "ok"

# Function to log in to the portal and fetch data
def fetch_portal_data(username, password):
    session = requests.Session()
    login_page = session.get(PORTAL_URL)
    soup = BeautifulSoup(login_page.content, "html.parser")
    csrf_token = soup.find("input", {"name": "csrf_token"})["value"] if soup.find("input", {"name": "csrf_token"}) else None
    payload = {
        "username": username,
        "password": password,
        "csrf_token": csrf_token
    }
    login_response = session.post(PORTAL_URL, data=payload)
    if "dashboard" in login_response.url:
        dashboard_response = session.get("https://cuportal.covenantuniversity.edu.ng/dashboard.php")
        return dashboard_response.text
    else:
        return None

# Function to check for changes and notify the user
async def check_for_changes(application, chat_id, username, password):
    current_data = fetch_portal_data(username, password)
    if chat_id in last_data:
        if current_data != last_data[chat_id]:
            await application.bot.send_message(chat_id=chat_id, text="There has been a change on your portal!")
        else:
            await application.bot.send_message(chat_id=chat_id, text="No changes detected.")
    else:
        await application.bot.send_message(chat_id=chat_id, text="Initial data fetched.")
    last_data[chat_id] = current_data

# Start command handler
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Welcome! Please send your credentials in the format: /login username password")

# Handle user input for credentials
async def handle_credentials(update: Update, context: CallbackContext):
    try:
        username, password = context.args
        user_credentials[update.message.chat_id] = (username, password)
        await update.message.reply_text("Credentials saved. You will be notified of any changes.")
    except ValueError:
        await update.message.reply_text("Invalid format. Please send your credentials in the format: /login username password")

# Stop command handler
async def stop(update: Update, context: CallbackContext):
    if update.message.chat_id in user_credentials:
        del user_credentials[update.message.chat_id]
        await update.message.reply_text("You have been unsubscribed from notifications.")
    else:
        await update.message.reply_text("You are not subscribed to notifications.")

# Initialize the Telegram bot application
application = Application.builder().token(BOT_TOKEN).build()
bot = application.bot

# Add command handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("login", handle_credentials))
application.add_handler(CommandHandler("stop", stop))

# Set the webhook
application.bot.set_webhook(WEBHOOK_URL)

# Run the Flask app
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)