import time
import json
from datetime import datetime, timedelta

def load_teams():
    try:
        with open("assets/data/teams.json") as f:
            print("File opened successfully")
            return json.load(f)
            
    except Exception as e:
        print("Error opening file: ", e)

def get_dates():
    date_now = datetime.now().strftime('%Y-%m-%d')
    date_ago = (datetime.now() - timedelta(days=150)).strftime('%Y-%m-%d')

    return (date_now, date_ago)

def cookie_Accept(driver):
    try:
        accept_button = driver.find_element("#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll")
        accept_button.click()

        time_button = driver.find_element("css selector", "div.matches-sort-by-toggle-time")
        time_button.click()
    except Exception as e:
        print("Error accepting cookies:", e)
        