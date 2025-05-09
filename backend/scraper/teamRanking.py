from bs4 import BeautifulSoup
from datetime import datetime
from seleniumbase import Driver
from scraperUtil import db_connect 

def get_teams(cursor):
  driver = Driver(uc=True, page_load_strategy="eager", headless=False)

  today = datetime.today()
  day = today.day
  month = today.strftime("%B").lower()
  year = today.year
  url = f"https://www.hltv.org/ranking/teams/{year}/{month}/{day}"

  try:
      driver.get(url)
      soup = BeautifulSoup(driver.page_source, "html.parser")

      teams_list = soup.find_all("div", "ranked-team standard-box")

      ranking = 1

      for team in teams_list:
        team_link = team.find("a", "moreLink")
        link_string = team_link.get("href")
        parts = link_string.strip("/").split("/")
        team_id = int(parts[1])
        team_name = team.find("span", "name").text.strip()

        cursor.execute("""
          INSERT INTO teams (id, team_name, ranking)
          VALUES (%s, %s, %s)
          ON DUPLICATE KEY UPDATE
          ranking = VALUES(ranking), team_name = VALUES(team_name)
        """, (team_id, team_name, ranking))

        ranking += 1


  except Exception as e:
    print("Error fetching team rankings:", e)

  finally:
        driver.quit()

def main():
  db = db_connect()
  cursor = db.cursor()

  get_teams(cursor)
  db.commit()
  cursor.close()
  db.close()
  
if __name__ == "__main__":
  main()