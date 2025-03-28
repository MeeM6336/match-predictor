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

load_dotenv()

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


def getDates():
    dateNow = datetime.now().strftime('%Y-%m-%d')
    dateAgo = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')

    return (dateNow, dateAgo)


def loadTeams():
    try:
        with open("assets/data/teams.json") as f:
            print("File opened successfully")
            return json.load(f)
            
    except Exception as e:
        print("Error opening file: ", e)
    

def extractMatchInfo(soup):
    matchInfo = soup.select("div.match-info-box-con")[0]
    data = {}

    if matchInfo:
        currentElement = matchInfo.find("span", {"data-time-format": "yyyy-MM-dd HH:mm"})
        if(currentElement):
            data['dateTime'] = currentElement.text.strip()

        currentElement = matchInfo.select("a")[0]
        if(currentElement):
            data['tournamentName'] = currentElement.text.strip()

        currentElement = matchInfo.select("a")[1]
        if(currentElement):
            data['teamNameA'] = currentElement.text.strip()

        currentElement = matchInfo.select("a")[2]
        if(currentElement):
            data['teamNameB'] = currentElement.text.strip()
    
    matchInfo = soup.select("a.stats-match-map:not(.inactive)")[0]

    if matchInfo:
        currentElement = matchInfo.find("div", "dynamic-map-name-full")
        if currentElement:
            data['mapName'] = currentElement.text.strip()
        
        currentElement = matchInfo.find("div", "stats-match-map-result-score")
        if currentElement:
            score = currentElement.text.split("-")
            data['teamScoreA'] = int(score[0])
            data['teamScoreB'] = int(score[1])

    return pd.DataFrame([data])


def extractTeamStats(soup):
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
    
    matchInfo_list = soup.select("div.match-info-box-con")
    if not matchInfo_list:  
        print("Error: No match info found.")
        return {}, {}
    
    matchInfo = matchInfo_list[0]
    team_links = matchInfo.find_all("a", class_="block text-ellipsis")
    if len(team_links) > 1:
        df_teamA["team_name"] = team_links[1].text.strip()
    if len(team_links) > 2:
        df_teamB["team_name"] = team_links[2].text.strip()

    match_rows = matchInfo.find_all("div", class_="match-info-row")

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

    driver = Driver(uc=True, headless=True)
    dateNow, dateAgo = getDates()
    teams = loadTeams()

    try:
        for team_id, team_name in teams.items():
            url = f"https://www.hltv.org/stats/teams/matches/{team_id}/{team_name}?csVersion=CS2&startDate={dateAgo}&endDate={dateNow}&matchType=BigEvents&rankingFilter=Top30"
            driver.get(url)
            print("Scraping data for team:", team_name, "from date range (", dateAgo, "-", dateNow, ")")

            try:
                soup = BeautifulSoup(driver.page_source, "html.parser")
                matchTable = soup.select("table.stats-table")

                if not matchTable:
                    print(f"No match table found for {team_name}")
                    continue
                
                matchLinks = [l.get("href") for l in matchTable[0].find_all('a') if "/stats/matches" in l.get("href", "")]
                matchUrls = [f"https://www.hltv.org{l}" for l in matchLinks]

                for url in matchUrls:
                    try:
                        driver.get(url)
                        time.sleep(random.uniform(2,5))

                        soup = BeautifulSoup(driver.page_source, "html.parser")

                        matchInfo = extractMatchInfo(soup)
                        teamStatA, teamStatB = extractTeamStats(soup)

                        if matchInfo.empty or teamStatA.empty or teamStatB.empty:
                            print("Skipping match due to missing data:", url)
                            continue

                        try:
                            pk = insert_match_info(cursor, matchInfo)
                            insert_match_statistics(cursor, pk, teamStatA)
                            insert_match_statistics(cursor, pk, teamStatB)

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