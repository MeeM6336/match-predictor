from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from seleniumbase import Driver
from scraperUtil import db_connect, get_date_range
from io import StringIO
import time
import pandas as pd

def get_team_ranking(driver, day, month, year):
  url = f"https://www.hltv.org/ranking/teams/{year}/{month}/{day}"

  try:
    driver.get(url)
    soup = BeautifulSoup(driver.page_source, "html.parser")

    teams_list = soup.find_all("div", "ranked-team standard-box")

    team_rankings = []
    ranking = 1

    for team in teams_list:
      team_link = team.find("a", "moreLink")
      link_string = team_link.get("href")
      parts = link_string.strip("/").split("/")
      team_id = int(parts[1])
      team_name = team.find("span", "name").text.strip()

      current_ranking = {
        "team_name": team_name,
        "team_id": team_id,
        "ranking": ranking
      }

      team_rankings.append(current_ranking)

      ranking += 1

    return team_rankings

  except Exception as e:
    print("Error fetching team rankings:", e)


def get_table_stats(driver, type, date_ago):
  date_before = date_ago - timedelta(days=50)
  year = date_ago.year
  month = date_ago.strftime('%m')
  day = date_ago.strftime('%d')

  year_before = date_before.year
  month_before = date_before.strftime('%m')
  day_before = date_before.strftime('%d')

  url = f"https://www.hltv.org/stats/teams/{type}?startDate={year_before}-{month_before}-{day_before}&endDate={year}-{month}-{day}&rankingFilter=Top50"

  try:
    driver.get(url)
    table = pd.read_html(StringIO(driver.page_source))
    return table[0]

  except Exception as e:
    print("Error fetching ftu/pistol table", e)
    return []
  

def insert_team_stat(cursor, date_ago, current_date_rankings, ftu_table, pistol_table):
  for team in current_date_rankings:
    team_name = team["team_name"]
    ranking = team["ranking"]
    id = team["team_id"]

    try:
      ftu_row = ftu_table[ftu_table['Team'] == team_name].iloc[0]
      pistols_row = pistol_table[pistol_table['Team'] == team_name].iloc[0]
    except:
      continue

    query = """
      INSERT INTO team_stats_by_date (
        id, date, team_name, ranking, round_wr, opening_kill_rate, multikill_rate, 5v4_wr, 4v5_wr, trade_rate, utility_adr, flash_assists, pistol_wr, round2_conv, round2_break
      )
      VALUES (
      %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
      )
    """
    val = (
      id,
      date_ago,
      team_name,
      ranking,
      float(ftu_row["RW%"].strip('%')) / 100,
      float(ftu_row["OpK"].strip('%')) / 100,
      ftu_row["MultiK"],
      float(ftu_row["5v4%"].strip('%')) / 100,
      float(ftu_row["4v5%"].strip('%')) / 100,
      float(ftu_row["Traded%"].strip('%')) / 100,
      ftu_row["ADR"],
      ftu_row["FA"],
      float(pistols_row["Pistol win %"].strip('%')) / 100,
      float(pistols_row["Round 2 convR2 conv"].strip('%')) / 100,
      float(pistols_row["Round 2 breakR2 break"].strip('%')) / 100
    )

    cursor.execute(query, val)


def main():
  db = db_connect()
  cursor = db.cursor()
  driver = Driver(uc=True, page_load_strategy="eager", headless=False)

  today = "2025-05-26 00:00:00"

  date_now, date_ago = get_date_range(today, delta=364)

  date_ago_dt = datetime.strptime(date_ago, '%Y-%m-%d')
  date_now_dt = datetime.strptime(date_now, '%Y-%m-%d')

  while (date_ago_dt <= date_now_dt):
    year = date_ago_dt.year
    month_str = date_ago_dt.strftime("%B").lower()
    day = date_ago_dt.day

    current_date_rankings = get_team_ranking(driver, day, month_str, year)

    ftu_table = get_table_stats(driver, "ftu", date_ago_dt)
    ftu_table.columns = [col[1] for col in ftu_table.columns]
    pistol_table = get_table_stats(driver, "pistols", date_ago_dt)

    

    try:
      insert_team_stat(cursor, date_ago_dt, current_date_rankings, ftu_table, pistol_table)
      db.commit()
    except Exception as e:
      db.rollback()
      print(f"Error processing team_stats_by_date: {e}")

    date_ago_dt = date_ago_dt + timedelta(days=7)
    time.sleep(5)

  cursor.close()
  db.close()
  
if __name__ == "__main__":
  main()