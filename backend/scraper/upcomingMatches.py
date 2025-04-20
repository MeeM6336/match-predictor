from seleniumbase import Driver
from bs4 import BeautifulSoup
import mysql.connector
import os
from datetime import datetime
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from scraperUtil import cookie_Accept

load_dotenv()

def insert_upcoming(matches, cursor):
    query = """
        INSERT INTO upcoming_matches 
            (team_a, team_b, date, tournament_name)
        VALUES (%s, %s, %s, %s)
    """
    values = [
        (
            match["team_a"],
            match['team_b'],
            match['date'],
            match['tournament_name']
        )
        for match in matches
    ]

    cursor.executemany(query, values)


def parse_upcoming_matches(soup):
    day = soup.find("div", "matches-list-section")
    matches = day.find_all("div", "match")

    matches_data = []

    for match in matches:
        match_data = {}
        tournement_div = match.find("div", class_="match-event")
        if tournement_div is not None:
            match_data["tournament_name"] = tournement_div["data-event-headline"]
        else:
            continue

        time_div = match.find("div", class_="match-time")
        if time_div is not None:
            time_unix = int(time_div["data-unix"])
            seconds = time_unix / 1000
            match_data["date"] = datetime.fromtimestamp(seconds)
        else:
            continue

        team_names = match.find_all("div", class_="match-teamname")
        if len(team_names) >= 2:
            match_data["team_a"] = team_names[0].text.strip()
            match_data["team_b"] = team_names[1].text.strip()
        else:
            continue

        matches_data.append(match_data)

    return matches_data
        

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
    
    driver = Driver(uc=True, page_load_strategy="eager", headless=False)

    try:
        url = 'https://www.hltv.org/matches'
        driver.get(url)

        cookie_Accept(driver)
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        matches = parse_upcoming_matches(soup)

        try:
            insert_upcoming(matches, cursor)
            mydb.commit()

        except mysql.connector.Error as e:
            mydb.rollback()
            print("Error inserting info:", e)


    except Exception as e:
        print("Error parsing upcoming matches", e)

    finally:
        driver.quit()
        cursor.close()
        mydb.close()

    
if __name__ == "__main__":
    main()