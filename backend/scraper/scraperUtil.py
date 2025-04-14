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