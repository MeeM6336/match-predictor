from seleniumbase import Driver
from bs4 import BeautifulSoup
import mysql.connector
import os
import re
from datetime import datetime
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()


def insert_match_outcome(matches, cursor):
    query = f"""
        UPDATE upcoming_matches 
            SET actual_outcome = %s 
        WHERE 
            team_a = %s AND 
            team_b = %s AND 
            DATE(date) = %s AND 
            tournament_name = %s
    """

    values = [
        (
            match["actual_outcome"],
            match['team_a'],
            match['team_b'],
            match['date'],
            match['tournament_name']
        )
        for match in matches
    ]

    cursor.executemany(query, values)



def parse_results(soup):
    matches = []

    try:
        results_container = soup.find("div", class_="results-all")
        results_day = results_container.find_all("div", class_="results-sublist")

        for result_day in results_day:
            date_string = result_day.find("div", class_="standard-headline")
            if date_string is not None:
                date = date_string.text.strip()
                cleaned_date = re.sub(r"Results for\s+", "", date)
                cleaned_date = re.sub(r'(\d{1,2})(st|nd|rd|th)', r'\1', cleaned_date)
                match_date = datetime.strptime(cleaned_date, "%B %d %Y")
            else:
                continue

            results = result_day.find_all("div", class_="result")
            for result in results:
                data = {}
                data["date"] = match_date.date()

                tournament = result.find("span", class_="event-name")
                if tournament is not None:
                    data["tournament_name"] = tournament.text.strip()
                else:
                    continue

                team_names = result.find_all("div", class_="team")
                if len(team_names) >= 2:
                    data["team_a"] = team_names[0].text.strip()
                    data["team_b"] = team_names[1].text.strip()
                else:
                    continue

                team_won = result.find("div", class_="team-won").text.strip()

                score_won = result.find("span", class_="score-won")
                if score_won is not None:
                    score_won = score_won.text.strip()
                else:
                    continue

                score_lost = result.find("span", class_="score-lost")
                if score_lost is not None:
                    score_lost = score_lost.text.strip()
                else:
                    continue
                
                if score_won and score_lost and team_won:
                    if team_won == team_names[0].text.strip():
                        data["actual_outcome"] = 1
                    
                    else:
                        data["actual_outcome"] = 0

                matches.append(data)

    except Exception as e:
        print("Error, results not found:", e)

    return matches


def main():
    try:
        db = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
        )
        cursor = db.cursor()
    
    except mysql.connector.Error as e:
        print("Database connection error:", e)
        return
    
    driver = Driver(uc=True, headless=False)

    try:
        url = 'https://www.hltv.org/results'
        driver.get(url)
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        matches = parse_results(soup)
        
        try:
            insert_match_outcome(matches, cursor)
            db.commit()
        
        except mysql.connector.Error as e:
            db.rollback()
            print("Error inserting info:", e)

    except Exception as e:
        print("Error", e)

    finally:
        driver.quit()
        cursor.close()
        db.close()

if __name__ == "__main__":
    main()