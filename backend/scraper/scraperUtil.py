import time
from pathlib import Path
import json
from datetime import datetime, timedelta

def load_teams():
    try:
        teams_path = Path(__file__).resolve().parent / 'assets/data/teams.json'
        
        with open(teams_path) as f:
            print("File opened successfully")
            return json.load(f)
    except Exception as e:
        print(f"Failed to open file: {e}")

def get_dates():
    date_now = datetime.now().strftime('%Y-%m-%d')
    date_ago = (datetime.now() - timedelta(days=160)).strftime('%Y-%m-%d')

    return (date_now, date_ago)

def cookie_Accept(driver):
    try:
        accept_button = driver.find_element("#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll")
        accept_button.click()

        time_button = driver.find_element("css selector", "div.matches-sort-by-toggle-time")
        time_button.click()
    except Exception as e:
        print("Error accepting cookies:", e)
        