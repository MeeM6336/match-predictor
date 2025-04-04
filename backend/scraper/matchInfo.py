from bs4 import BeautifulSoup
from io import StringIO
from seleniumbase import Driver
import pandas as pd
import json
import time
import random
import os
import mysql.connector
from datetime import datetime, timedelta
from dotenv import load_dotenv

'''For future models, implement more features such as type of tournament [online, lan, big_event, major]'''


load_dotenv()

def insert_team_stats(cursor, list_stats): # Given a list of map stats for a particular team
    for stats in list_stats:
        query = "INSERT into map_stats (team_name, map_name, wins, losses) VALUES (%s, %s, %s, %s)"
        val = (stats["team_name"],
               stats["map_name"],
               int(stats["wins"]),
               int(stats["losses"]))
        cursor.execute(query, val)


def insert_match_info(cursor, df):
    query = "INSERT INTO matches (date, tournament, map, team_a, team_b, rounds_team_a, rounds_team_b) VALUES (%s, %s, %s, %s, %s, %s, %s)"
    val = (df["dateTime"].iloc[0], 
           df["tournamentName"].iloc[0], 
           df["mapName"].iloc[0], 
           df["teamNameA"].iloc[0], 
           df["teamNameB"].iloc[0], 
           int(df["teamScoreA"].iloc[0]), 
           int(df["teamScoreB"].iloc[0]))

    cursor.execute(query, val)
    pk = cursor.lastrowid
    
    return pk


def insert_match_statistics(cursor, pk, df):
    query = "INSERT INTO team_stats (team_name, match_id, team_rating, first_kills, clutches_won, avg_kda, avg_kast, avg_adr) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
    val = (df["team_name"].iloc[0], 
    pk, 
    float(df["rating"].iloc[0]), 
    int(df["fk"].iloc[0]), 
    int(df["clutches"].iloc[0]), 
    float(((df["K"].iloc[0] + df["A"].iloc[0])/(df["D"].iloc[0]))), 
    float(df["KAST"].iloc[0]), 
    float(df["ADR"].iloc[0]))
    cursor.execute(query, val)


def get_dates():
    date_now = datetime.now().strftime('%Y-%m-%d')
    date_ago = (datetime.now() - timedelta(days=120)).strftime('%Y-%m-%d')

    return (date_now, date_ago)


def load_teams():
    try:
        with open("assets/data/teams.json") as f:
            print("File opened successfully")
            return json.load(f)
            
    except Exception as e:
        print("Error opening file: ", e)
    
# Need to refactor this
def extract_match_info(soup):
    match_info = soup.select("div.match-info-box-con")[0]
    data = {}

    if match_info:
        current_element = match_info.find("span", {"data-time-format": "yyyy-MM-dd HH:mm"})
        if(current_element):
            data['dateTime'] = current_element.text.strip()

        current_element = match_info.select("a")[0]
        if(current_element):
            data['tournamentName'] = current_element.text.strip()

        current_element = match_info.select("a")[1]
        if(current_element):
            data['teamNameA'] = current_element.text.strip()

        current_element = match_info.select("a")[2]
        if(current_element):
            data['teamNameB'] = current_element.text.strip()
    
    match_info = soup.select("a.stats-match-map:not(.inactive)")[0]

    if match_info:
        current_element = match_info.find("div", "dynamic-map-name-full")
        if current_element:
            data['mapName'] = current_element.text.strip()
        
        current_element = match_info.find("div", "stats-match-map-result-score")
        if current_element:
            score = current_element.text.split("-")
            data['teamScoreA'] = int(score[0])
            data['teamScoreB'] = int(score[1])

    return pd.DataFrame([data])


def extract_team_stats(soup):
    try:
        htmlString = str(soup.select("table.totalstats")[0])
        htmlData = StringIO(htmlString)
        df_teamA = pd.read_html(htmlData)[0]

        htmlString = str(soup.select("table.totalstats")[1])
        htmlData = StringIO(htmlString)
        df_teamB = pd.read_html(htmlData)[0]

    except IndexError:
        print("Error: Could not find both team stats tables.")
        return None, None
    
    # Modify dataframe structure
    df_teamA.drop(df_teamA.columns[0], axis=1, inplace=True)
    df_teamA.drop('K-D Diff', axis=1, inplace=True)
    df_teamA.drop('FK Diff', axis=1, inplace=True)

    df_teamA[['K', 'hs']] = df_teamA['K (hs)'].str.split(' ', expand=True)
    df_teamA['K'] = df_teamA['K'].astype(int)
    df_teamA.drop('hs', axis=1, inplace=True)
    df_teamA[['A', 'f']] = df_teamA['A (f)'].str.split(' ', expand=True)
    df_teamA['A'] = df_teamA['A'].astype(int)
    df_teamA.drop('f', axis=1, inplace=True)
    df_teamA.drop(['K (hs)', 'A (f)'], axis=1, inplace=True)

    df_teamA['KAST'] = df_teamA['KAST'].str.replace('%', '').astype(float)

    df_teamA = df_teamA.mean()
    df_teamA = df_teamA.to_frame().T

    df_teamB.drop(df_teamB.columns[0], axis=1, inplace=True)
    df_teamB.drop('K-D Diff', axis=1, inplace=True)
    df_teamB.drop('FK Diff', axis=1, inplace=True)

    df_teamB[['K', 'hs']] = df_teamB['K (hs)'].str.split(' ', expand=True)
    df_teamB['K'] = df_teamB['K'].astype(int)
    df_teamB.drop('hs', axis=1, inplace=True)
    df_teamB[['A', 'f']] = df_teamB['A (f)'].str.split(' ', expand=True)
    df_teamB['A'] = df_teamB['A'].astype(int)
    df_teamB.drop('f', axis=1, inplace=True)
    df_teamB.drop(['K (hs)', 'A (f)'], axis=1, inplace=True)

    df_teamB['KAST'] = df_teamB['KAST'].str.replace('%', '').astype(float)

    df_teamB = df_teamB.mean()
    df_teamB = df_teamB.to_frame().T
    
    match_info_list = soup.select("div.match-info-box-con")
    if not match_info_list:  
        print("Error: No match info found.")
        return {}, {}
    
    match_info = match_info_list[0]
    team_links = match_info.find_all("a", class_="block text-ellipsis")
    if len(team_links) > 1:
        df_teamA["team_name"] = team_links[1].text.strip()
    if len(team_links) > 2:
        df_teamB["team_name"] = team_links[2].text.strip()

    match_rows = match_info.find_all("div", class_="match-info-row")

    if len(match_rows) > 1:
        children = [child for child in list(match_rows[1].children) if child.name]
        if children:
            rating = children[0].text.split(":")
            if len(rating) == 2:
                df_teamA["rating"] = float(rating[0])
                df_teamB["rating"] = float(rating[1])

    if len(match_rows) > 2:
        children = [child for child in list(match_rows[2].children) if child.name]
        if children:
            fk = children[0].text.split(":")
            if len(fk) == 2:
                df_teamA["fk"] = int(fk[0])
                df_teamB["fk"] = int(fk[1])

    if len(match_rows) > 3:
        children = [child for child in list(match_rows[3].children) if child.name]
        if children:
            clutches = children[0].text.split(":")
            if len(clutches) == 2:
                df_teamA["clutches"] = int(clutches[0])
                df_teamB["clutches"] = int(clutches[1])

    df_teamA.fillna(pd.NA, inplace=True)
    df_teamB.fillna(pd.NA, inplace=True)

    return df_teamA, df_teamB


def extract_team_map_stats(soup):
    try:
        team_name = soup.find("span", class_="context-item-name").text.strip()

        map_stats_grid = soup.find("div", class_="two-grid").select("div.stats-rows.standard-box")
        team_map_stats = []

        for i, map_stat in enumerate(map_stats_grid):
            data = {}
            data["team_name"] = team_name
            
            data["map_name"] = map_stat.parent.find("div", class_="map-pool-map-name").text.strip()
            wdl = map_stat.find_all("div", class_="stats-row")[0].find_all("span")[1].text.strip()
            w, _, l = map(int, [x.strip() for x in wdl.split('/')])
            data["wins"] = w
            data["losses"] = l
            team_map_stats.append(data)

        return team_map_stats

    except Exception as e:
        print(f"Map stats not found for {team_name}:", e)
        return []


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
            url = f"https://www.hltv.org/stats/teams/maps/{team_id}/{team_name}?startDate={date_ago}&endDate={date_now}&rankingFilter=Top50"
            driver.get(url)
            print("Scraping data for team:", team_name, "from date range (", date_ago, "-", date_now, ")")

            try:
                soup = BeautifulSoup(driver.page_source, "html.parser")
                map_team_stats = extract_team_map_stats(soup)

                try:
                    insert_team_stats(cursor, map_team_stats)
                    mydb.commit()
                except mysql.connector.Error as e:
                    mydb.rollback()
                    print("Error inserting info:", e)

            except Exception as e:
                print("Error:", e)

            url = f"https://www.hltv.org/stats/teams/matches/{team_id}/{team_name}?csVersion=CS2&startDate={date_ago}&endDate={date_now}&rankingFilter=Top50"
            driver.get(url)

            try:
                soup = BeautifulSoup(driver.page_source, "html.parser")
                match_table = soup.select("table.stats-table")

                if not match_table:
                    print(f"No match table found for {team_name}")
                    continue
                
                match_links = [l.get("href") for l in match_table[0].find_all('a') if "/stats/matches" in l.get("href", "")]
                match_urls = [f"https://www.hltv.org{l}" for l in match_links]

                for url in match_urls:
                    try:
                        driver.get(url)
                        time.sleep(random.uniform(2,5))

                        soup = BeautifulSoup(driver.page_source, "html.parser")

                        match_info = extract_match_info(soup)
                        team_stat_A, team_stat_B = extract_team_stats(soup)

                        if match_info.empty or team_stat_A.empty or team_stat_B.empty:
                            print("Skipping match due to missing data:", url)
                            continue

                        try:
                            pk = insert_match_info(cursor, match_info)
                            insert_match_statistics(cursor, pk, team_stat_A)
                            insert_match_statistics(cursor, pk, team_stat_B)

                            mydb.commit()
                    
                        except mysql.connector.Error as e:
                            mydb.rollback()
                            print("Error inserting info:", e)

                    except Exception as e:
                        print(f"Error processing match {url}: {e}")
                        continue

            except Exception as e:
                print("Error reading table data:", e)

    finally:
        driver.quit()
        cursor.close()
        mydb.close()

if __name__ == "__main__":
    main()