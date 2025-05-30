from bs4 import BeautifulSoup
from io import StringIO
from seleniumbase import Driver
import pandas as pd
from scraperUtil import get_dates, load_teams, db_connect

def insert_series_info(cursor, match_info_df_list, match_stats_df_list, match_type):
    series_len = len(match_info_df_list)

    team_a_wins = 0
    team_b_wins = 0
    series_outcome = None

    match match_type:
        case "Majors":
            series_match_type = 4

        case "BigEvents":
            series_match_type = 3

        case "Lan":
            series_match_type = 2

        case "Online":
            series_match_type = 1

    for df in match_info_df_list:
        outcome = int(df["outcome"].iloc[0])
        if outcome == 1:
            team_a_wins += 1
        else:
            team_b_wins += 1
    
    if team_a_wins > team_b_wins:
        series_outcome = 1
    elif team_a_wins < team_b_wins:
        series_outcome = 0

    match_diff = abs(team_a_wins - team_b_wins)

    if series_len == 1:
        best_of = 1
    elif series_len == 2:
        best_of = 3
    elif series_len == 3:
        if match_diff == 1:
            best_of = 3
        else:
            best_of = 5
    else:
        best_of= 5

    teamA_dfs = [pair[0] for pair in match_stats_df_list]
    teamB_dfs = [pair[1] for pair in match_stats_df_list]
    avg_teamA = pd.concat(teamA_dfs, ignore_index=True).mean(numeric_only=True)
    avg_teamB = pd.concat(teamB_dfs, ignore_index=True).mean(numeric_only=True)

    avg_kda_teamA = (float(avg_teamA["K"]) + float(avg_teamA["A"])) / float(avg_teamA["D"])
    avg_rating_teamA = float(avg_teamA["rating"])
    avg_adr_teamA = float(avg_teamA["ADR"])
    avg_kast_teamA = float(avg_teamA["KAST"])

    avg_kda_teamB = (float(avg_teamB["K"]) + float(avg_teamB["A"])) / float(avg_teamB["D"])
    avg_rating_teamB = float(avg_teamB["rating"])
    avg_adr_teamB = float(avg_teamB["ADR"])
    avg_kast_teamB = float(avg_teamB["KAST"])


    query = """INSERT INTO matches 
    (date, tournament, tournament_type, best_of, team_a, team_a_rating, team_a_kda, team_a_adr, team_a_kast, team_b, team_b_rating, team_b_kda, team_b_adr, team_b_kast, outcome)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
    val = (match_info_df_list[0]["dateTime"].iloc[0], 
        match_info_df_list[0]["tournamentName"].iloc[0], 
        series_match_type,
        best_of,
        match_info_df_list[0]["teamNameA"].iloc[0], 
        avg_rating_teamA,
        avg_kda_teamA,
        avg_adr_teamA,
        avg_kast_teamA,
        match_info_df_list[0]["teamNameB"].iloc[0],
        avg_rating_teamB,
        avg_kda_teamB,
        avg_adr_teamB,
        avg_kast_teamB,
        series_outcome
    )

    cursor.execute(query, val)

    
def extract_match_info(soup):
    match_info = soup.find("div", class_="match-info-box-con")
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
        tables = soup.find_all("table", class_="totalstats")
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


def scrape_team_data(driver, cursor, mydb, team_id, team_name, date_ago, date_now, match_type):
    print(f"Scraping {match_type} matches for team: {team_name}")
    try:
        url = f"https://www.hltv.org/stats/teams/matches/{team_id}/{team_name}?csVersion=CS2&startDate={date_ago}&endDate={date_now}&matchType={match_type}&rankingFilter=Top50"
        driver.get(url)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        match_table = soup.find("table", class_="stats-table")
        
        if not match_table or not match_table.find("tbody"):
            print(f"No match table found for {team_name}")
            return

        tbody = match_table.find("tbody")

        groupNum = None
        match_info_dataframes = []
        team_stats_data_frames = []
        contains_match = False

        def process_current_group():
            nonlocal match_info_dataframes, team_stats_data_frames
            if contains_match and match_info_dataframes and team_stats_data_frames:
                try:
                    insert_series_info(cursor, match_info_dataframes, team_stats_data_frames, match_type)
                    mydb.commit()
                except Exception as e:
                    mydb.rollback()
                    print(f"Error processing match group: {e}")

        for row in tbody.find_all("tr"):
            currentGroupNum = row.get("class")[0]

            if groupNum != currentGroupNum:
                process_current_group()

                groupNum = currentGroupNum
                match_info_dataframes = []
                team_stats_data_frames = []
                contains_match = False

            links = [a.get("href", "") for a in row.find_all("a")]
            match_link = next((link for link in links if "/stats/matches" in link), None)

            if not match_link:
                continue

            full_link = f"https://www.hltv.org{match_link}"
            driver.get(full_link)
            soup = BeautifulSoup(driver.page_source, "html.parser")

            match_info = extract_match_info(soup)
            team_stats_A, team_stats_B = extract_match_team_stats(soup)

            if (
                match_info is None or team_stats_A is None or team_stats_B is None
                or match_info.empty or team_stats_A.empty or team_stats_B.empty
            ):
                print("Skipping match due to missing data:", match_link)
                continue

            contains_match = True
            match_info_dataframes.append(match_info)
            team_stats_data_frames.append((team_stats_A, team_stats_B))

        process_current_group()

    except Exception as e:
        print(f"Error retrieving match list for {team_name}: {e}")


def main():
    db = db_connect()
    cursor = db.cursor()

    driver = Driver(uc=True, page_load_strategy="eager", headless=True)
    date_now, date_ago = get_dates(delta=365)
    teams = load_teams(cursor)
    match_types = ["Majors", "BigEvents","Lan", "Online"]

    try:
        for team_id, team_name in teams:
            for match_type in match_types:
                scrape_team_data(driver, cursor, db, team_id, team_name, date_ago, date_now, match_type)
    finally:
        driver.quit()
        cursor.close()
        db.close()


if __name__ == "__main__":
    main()