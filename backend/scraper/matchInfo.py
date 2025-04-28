from bs4 import BeautifulSoup
from io import StringIO
from seleniumbase import Driver
import pandas as pd
import time
import random
import os
import mysql.connector
from dotenv import load_dotenv   
from scraperUtil import get_dates, load_teams

'''For future models, implement more features such as type of tournament [online, lan, big_event, major]'''
load_dotenv()

def insert_match_info(cursor, df):
    query = "INSERT INTO matches (date, tournament, map, team_a, team_b, outcome) VALUES (%s, %s, %s, %s, %s, %s)"
    val = (df["dateTime"].iloc[0], 
           df["tournamentName"].iloc[0], 
           df["map"].iloc[0],
           df["teamNameA"].iloc[0], 
           df["teamNameB"].iloc[0], 
           int(df["outcome"].iloc[0]))

    cursor.execute(query, val)
    pk = cursor.lastrowid
    
    return pk


def insert_match_team_stats(cursor, pk, df):
    query = "INSERT INTO match_team_stats (team_name, match_id, team_rating, avg_kda, avg_kast, avg_adr) VALUES (%s, %s, %s, %s, %s, %s)"
    val = (df["team_name"].iloc[0], 
    pk, 
    float(df["rating"].iloc[0]), 
    float(((df["K"].iloc[0] + df["A"].iloc[0])/(df["D"].iloc[0]))), 
    float(df["KAST"].iloc[0]), 
    float(df["ADR"].iloc[0]))
    cursor.execute(query, val)
    
def extract_match_info(soup):
    match_info = soup.select("div.match-info-box-con")[0]
    data = {}

    if match_info:
        time_span = match_info.find("span", {"data-time-format": "yyyy-MM-dd HH:mm"})
        if(time_span):
            data["dateTime"] = time_span.text.strip()
        else:
            data["dateTime"] = None
            print("No date found")

        map_name = match_info.find("div", class_="small-text").next_sibling.text.strip()
        if map_name:
            data["map"] = map_name
        else:
            data["map"] = None
            print("No map found")

        score_A = match_info.find("div", class_="team-left").find("div", class_="bold").text.strip()
        score_B = match_info.find("div", class_="team-right").find("div", class_="bold").text.strip()
        if score_A and score_B:
            data["outcome"] = 1 if int(score_A) > int(score_B) else 0
        else:
            data["outcome"] = None
            print("No outcome found")

        links_list = match_info.find_all("a")

        if len(links_list) > 2:
            data["tournamentName"] = links_list[0].text.strip() if links_list[0] else None
            data["teamNameA"] = links_list[1].text.strip() if links_list[1] else None
            data["teamNameB"] = links_list[2].text.strip() if links_list[2] else None

    return pd.DataFrame([data])


def extract_match_team_stats(soup):
    try:
        tables = soup.select("table.totalstats")
        if len(tables) < 2:
            print("Error: Could not find both team stats tables.")
            return None, None

        df_teamA = pd.read_html(StringIO(str(tables[0])))[0]
        df_teamB = pd.read_html(StringIO(str(tables[1])))[0]

        df_teamA.drop(columns=[df_teamA.columns[0], 'K-D Diff', 'FK Diff'], inplace=True, errors='ignore')
        df_teamA[['K', '_']] = df_teamA['K (hs)'].str.split(' ', expand=True)
        df_teamA['K'] = df_teamA['K'].astype(int)
        df_teamA.drop(columns=['K (hs)', '_'], inplace=True)
        df_teamA[['A', '_']] = df_teamA['A (f)'].str.split(' ', expand=True)
        df_teamA['A'] = df_teamA['A'].astype(int)
        df_teamA.drop(columns=['A (f)', '_'], inplace=True)
        df_teamA['KAST'] = df_teamA['KAST'].str.replace('%', '', regex=False).astype(float)
        df_teamA = df_teamA.mean().to_frame().T
        df_teamA['ADR'] = df_teamA['ADR'].astype(float)

        df_teamB.drop(columns=[df_teamB.columns[0], 'K-D Diff', 'FK Diff'], inplace=True, errors='ignore')
        df_teamB[['K', '_']] = df_teamB['K (hs)'].str.split(' ', expand=True)
        df_teamB['K'] = df_teamB['K'].astype(int)
        df_teamB.drop(columns=['K (hs)', '_'], inplace=True)
        df_teamB[['A', '_']] = df_teamB['A (f)'].str.split(' ', expand=True)
        df_teamB['A'] = df_teamB['A'].astype(int)
        df_teamB.drop(columns=['A (f)', '_'], inplace=True)
        df_teamB['KAST'] = df_teamB['KAST'].str.replace('%', '', regex=False).astype(float)
        df_teamB = df_teamB.mean().to_frame().T
        df_teamB['ADR'] = df_teamB['ADR'].astype(float)

    except Exception as e:
        print(f"Error extracting team stats: {e}")
        return None, None

    match_info = soup.select_one("div.match-info-box-con")
    if not match_info:
        print("Error: No match info found.")
        return None, None

    team_links = match_info.select("a.block.text-ellipsis")
    if len(team_links) > 1:
        df_teamA["team_name"] = team_links[1].text.strip()
    if len(team_links) > 2:
        df_teamB["team_name"] = team_links[2].text.strip()

    match_rows = match_info.select("div.match-info-row")
    if len(match_rows) > 1:
        rating_text = match_rows[1].text.strip().split(":")
        if len(rating_text) == 2:
            df_teamA["rating"] = float(rating_text[0].strip().split()[0])
            df_teamB["rating"] = float(rating_text[1].strip().split()[0])

    df_teamA.fillna(pd.NA, inplace=True)
    df_teamB.fillna(pd.NA, inplace=True)

    return df_teamA, df_teamB


def scrape_team_data(driver, cursor, mydb, team_id, team_name, date_ago, date_now):
    print(f"Scraping matches for team: {team_name}")
    try:
        url = f"https://www.hltv.org/stats/teams/matches/{team_id}/{team_name}?csVersion=CS2&startDate={date_ago}&endDate={date_now}&rankingFilter=Top50"
        driver.get(url)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        match_table = soup.select("table.stats-table")

        if not match_table:
            print(f"No match table found for {team_name}")
            return

        match_links = [l.get("href") for l in match_table[0].find_all('a') if "/stats/matches" in l.get("href", "")]
        match_urls = [f"https://www.hltv.org{l}" for l in match_links]

        for match_url in match_urls:
            try:
                driver.get(match_url)
                time.sleep(random.uniform(2, 5))

                soup = BeautifulSoup(driver.page_source, "html.parser")
                match_info = extract_match_info(soup)
                team_stat_A, team_stat_B = extract_match_team_stats(soup)

                if match_info.empty or team_stat_A.empty or team_stat_B.empty:
                    print("Skipping match due to missing data:", match_url)
                    continue

                pk = insert_match_info(cursor, match_info)
                insert_match_team_stats(cursor, pk, team_stat_A)
                insert_match_team_stats(cursor, pk, team_stat_B)
                mydb.commit()

            except Exception as e:
                mydb.rollback()
                print(f"Error processing match {match_url}: {e}")

    except Exception as e:
        print(f"Error retrieving match list for {team_name}: {e}")

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

    driver = Driver(uc=True, page_load_strategy="eager", headless=True)
    date_now, date_ago = get_dates()
    teams = load_teams()

    try:
        for team_id, team_name in teams.items():
            scrape_team_data(driver, cursor, mydb, team_id, team_name, date_ago, date_now)
    finally:
        driver.quit()
        cursor.close()
        mydb.close()


if __name__ == "__main__":
    main()