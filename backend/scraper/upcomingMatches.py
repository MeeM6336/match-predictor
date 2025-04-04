from seleniumbase import Driver
from bs4 import BeautifulSoup
import mysql.connector
import time
import os
from datetime import datetime
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

def insert_upcoming(soup, cursor):
    try:
        tournement_div = soup.find("div", class_="match-event")
        tournement_name = tournement_div["data-event-headline"]

        time_div = soup.find("div", class_="match-time")
        time_unix = int(time_div["data-unix"])
        seconds = time_unix / 1000
        time = datetime.fromtimestamp(seconds)

        team_names = soup.find_all("div", class_="match-teamname")

        if len(team_names) >= 2:
            team_a = team_names[0].text.strip()
            team_b = team_names[1].text.strip()

        else:
            print("Insufficient data. Aborting insert since")
            return

        query = "INSERT INTO upcoming_matches (team_a, team_b, date, tournament_name) Values (%s, %s, %s, %s)"
        val = (team_a,
        team_b,
        time,
        tournement_name
        )

        cursor.execute(query, val)

    except Exception as e:
        print("Error", e)
    

def main():
    try:
        mydb = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
        )
        cursor = mydb.cursor()
    
    except mysql.connector.Error as e:
        print("Database connection error:", e)
        return
    
    driver = Driver(uc=True, headless=False)

    try:
        url = 'https://www.hltv.org/matches'
        driver.get(url)

        try:
            accept_button = driver.find_element("#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll")
            accept_button.click()

            time_button = driver.find_element("css selector", "div.matches-sort-by-toggle-time")
            time_button.click()

            days = driver.find_elements("css selector", "div.matches-list-section")
            for day in days[:1]:
                matches = day.find_elements("css selector", "div.match")

                for match in matches:
                    table_html = match.get_attribute("outerHTML")
                    soup = BeautifulSoup(table_html, 'html.parser')

                    try:
                        insert_upcoming(soup, cursor)
                        mydb.commit()

                    except mysql.connector.Error as e:
                        mydb.rollback()
                        print("Error inserting info:", e)

        except Exception as e:
            print("Error", e)


    except Exception as e:
        print("Error", e)

    finally:
        driver.quit()
        cursor.close()
        mydb.close()

    
if __name__ == "__main__":
    main()