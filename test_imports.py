import time
import threading
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackContext
import requests
from bs4 import BeautifulSoup
import os

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