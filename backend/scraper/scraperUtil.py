from dotenv import load_dotenv
import os
from pathlib import Path
from datetime import datetime, timedelta
import mysql.connector

def load_teams(cursor):
    query = """
        SELECT id, team_name
        FROM teams
        WHERE ranking > 15 # Need to change l8r
        ORDER BY ranking ASC
        LIMIT 50;
    """

    cursor.execute(query)
    return cursor.fetchall()


def get_dates():
    date_now = datetime.now().strftime('%Y-%m-%d')
    date_ago = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')

    return (date_now, date_ago)


def cookie_accept(driver):
    try:
        accept_button = driver.find_element("#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll")
        accept_button.click()

        time_button = driver.find_element("css selector", "div.matches-sort-by-toggle-time")
        time_button.click()
    except Exception as e:
        print("Error accepting cookies:", e)

        
def db_connect():
	try:
		env_path = Path(__file__).resolve().parent.parent / '.env'
		load_dotenv(env_path)

		db = mysql.connector.connect(
			host=os.getenv("DB_HOST"),
			user=os.getenv("DB_USER"),
			password=os.getenv("DB_PASSWORD"),
			database=os.getenv("DB_NAME")
		)
	
		return db

	except mysql.connector.Error as e:
		print("Database connection error:", e)
		return None