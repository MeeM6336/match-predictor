from seleniumbase import Driver
from bs4 import BeautifulSoup
import mysql.connector
import re
from datetime import datetime
from bs4 import BeautifulSoup
from scraperUtil import cookie_accept, db_connect


def insert_upcoming(matches, cursor):
    query = """
        INSERT INTO upcoming_matches 
            (team_a, team_b, date, tournament_name, tournament_type, best_of)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    values = [
        (
            match["team_a"],
            match["team_b"],
            match["date"],
            match["tournament_name"],
            match["tournament_type"],
            match["best_of"]
        )
        for match in matches
    ]
    cursor.executemany(query, values)


def parse_upcoming_matches(soup, driver):
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

        best_of_div = match.find("div", class_="match-meta")
        if best_of_div is not None:
            best_of = int(best_of_div.text.strip()[-1])
            match_data["best_of"] = best_of

        match_rating_div = match.find("div", class_="match-rating")
        if match_rating_div is not None:
            tournament_type = 1
        else:
            tournament_type = 0

        team_names = match.find_all("div", class_="match-teamname")
        if len(team_names) >= 2:
            match_data["team_a"] = team_names[0].text.strip()
            match_data["team_b"] = team_names[1].text.strip()
        else:
            continue

        match_link = match.find("a").get("href", "")
        full_link = f"https://www.hltv.org{match_link}"
        driver.get(full_link)
        match_soup = BeautifulSoup(driver.page_source, "html.parser")
        type_text = match_soup.find("div", class_="padding preformatted-text").text.strip()
        match_type = re.search(r'\((.*?)\)', type_text).group(1)
        if match_type == "LAN":
            tournament_type += 2
        if match_type == "Online":
            tournament_type += 1
        
        match_data["tournament_type"] = tournament_type

        matches_data.append(match_data)
    
    return matches_data
        

def main():
    db = db_connect()
    cursor = db.cursor()
    
    driver = Driver(uc=True, page_load_strategy="eager", headless=True)

    try:
        url = 'https://www.hltv.org/matches'
        driver.get(url)

        try:
            cookie_accept(driver)
        except Exception as e:
            print("No cookies accept found/needed.")

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        matches = parse_upcoming_matches(soup, driver)

        try:
            insert_upcoming(matches, cursor)
            db.commit()

        except mysql.connector.Error as e:
            db.rollback()
            print("Error inserting info:", e)


    except Exception as e:
        print("Error parsing upcoming matches", e)

    finally:
        driver.quit()
        cursor.close()
        db.close()

    
if __name__ == "__main__":
    main()