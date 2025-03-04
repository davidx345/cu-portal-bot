import asyncio
import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask import Flask, request
import os

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Secure credential retrieval
BOT_TOKEN = os.getenv('BOT_TOKEN')
PORTAL_USERNAME = os.getenv('PORTAL_USERNAME')
PORTAL_PASSWORD = os.getenv('PORTAL_PASSWORD')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')

if not all([BOT_TOKEN, PORTAL_USERNAME, PORTAL_PASSWORD, WEBHOOK_URL]):
    raise ValueError("Missing critical environment variables")

PORTAL_URL = "https://cuportal.covenantuniversity.edu.ng/studentdashboard.php"

# Global state management
user_subscriptions = {}
last_portal_state = {}

# Initialize Flask app
app = Flask(__name__)

# Global application variable
telegram_application = None

def fetch_portal_data():
    """
    Synchronous function to fetch portal data with improved error handling
    """
    try:
        session = requests.Session()
        
        # Fetch login page
        login_page = session.get(PORTAL_URL)
        soup = BeautifulSoup(login_page.content, "html.parser")
        
        # Extract CSRF token if needed
        csrf_token = soup.find("input", {"name": "csrf_token"})
        csrf_token = csrf_token["value"] if csrf_token else None
        
        # Prepare login payload
        payload = {
            "username": PORTAL_USERNAME,
            "password": PORTAL_PASSWORD,
            "csrf_token": csrf_token
        }
        
        # Perform login
        login_response = session.post(PORTAL_URL, data=payload)
        
        # Check login success
        if "dashboard" in login_response.url:
            dashboard_response = session.get("https://cuportal.covenantuniversity.edu.ng/dashboard.php")
            return dashboard_response.text
        else:
            logger.warning("Login failed")
            return None
    
    except Exception as e:
        logger.error(f"Portal data fetch error: {e}")
        return None

async def check_portal_changes(context: ContextTypes.DEFAULT_TYPE):
    """
    Async function to check portal changes and notify subscribers
    """
    try:
        # Use sync function in an async context
        current_data = fetch_portal_data()
        
        if current_data is None:
            logger.error("Failed to fetch portal data")
            return
        
        for chat_id in user_subscriptions:
            if chat_id not in last_portal_state or current_data != last_portal_state[chat_id]:
                try:
                    await context.bot.send_message(
                        chat_id=chat_id, 
                        text="🚨 Portal Update Detected! Check your student dashboard."
                    )
                except Exception as send_error:
                    logger.error(f"Error sending message to {chat_id}: {send_error}")
            
            last_portal_state[chat_id] = current_data
    
    except Exception as e:
        logger.error(f"Error in check_portal_changes: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /start command
    """
    await update.message.reply_text(
        "Welcome to CU Portal Monitor! "
        "Use /subscribe to get portal change notifications."
    )

async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle user subscription
    """
    chat_id = update.effective_chat.id
    user_subscriptions[chat_id] = True
    await update.message.reply_text("Subscribed to portal updates!")

async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle user unsubscription
    """
    chat_id = update.effective_chat.id
    if chat_id in user_subscriptions:
        del user_subscriptions[chat_id]
        await update.message.reply_text("Unsubscribed from portal updates.")
    else:
        await update.message.reply_text("You are not subscribed.")

@app.route("/webhook", methods=['POST'])
async def webhook():
    """
    Async webhook handler
    """
    try:
        # Ensure telegram_application is initialized
        if telegram_application is None:
            logger.error("Telegram application not initialized")
            return "Bot not ready", 500

        # Parse incoming update
        update_data = request.get_json(force=True)
        update = Update.de_json(update_data, telegram_application.bot)
        
        # Put update in queue
        await telegram_application.update_queue.put(update)
        
        return "ok", 200
    
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return "error", 500

def main():
    """
    Initialize and configure the Telegram bot application
    """
    global telegram_application

    # Create application
    telegram_application = Application.builder().token(BOT_TOKEN).build()

    # Add command handlers
    telegram_application.add_handler(CommandHandler("start", start))
    telegram_application.add_handler(CommandHandler("subscribe", subscribe))
    telegram_application.add_handler(CommandHandler("unsubscribe", unsubscribe))

    # Setup periodic portal checking (every 5 minutes)
    telegram_application.job_queue.run_repeating(check_portal_changes, interval=300, first=10)

    # Set webhook
    telegram_application.bot.set_webhook(WEBHOOK_URL)

    return telegram_application

# Main execution
if __name__ == "__main__":
    # Create bot application
    bot_app = main()

    # Run Flask app
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))