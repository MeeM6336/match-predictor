from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from io import StringIO
import undetected_chromedriver as uc
import pandas as pd
import json
from datetime import datetime, timedelta

def loadTeams():
    try:
        with open("src/assets/data/teams.json") as f:
            print("File opened successfully")
            return json.load(f)
            
    except Exception as e:
        print("Error opening file: ", e)

driver = uc.Chrome()
dateNow = datetime.now().strftime('%Y-%m-%d')
dateAgo = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')

teams = loadTeams()

for team_id, team_name in teams.items():
    driver.get(f"https://www.hltv.org/stats/teams/matches/{team_id}/{team_name}?csVersion=CS2&startDate={dateAgo}&endDate={dateNow}&matchType=BigEvents&rankingFilter=Top30")

    try:
        matchTable = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table.stats-table"))
        )
        soup = BeautifulSoup(driver.page_source, "html.parser")

        matchTable = soup.select("table.stats-table")[0]
        matchLinks = matchTable.find_all('a')
        matchLinks = [l.get("href") for l in matchLinks]
        matchLinks = [l for l in matchLinks if "/stats/matches" in l]
        matchUrls = [f"https://www.hltv.org{l}" for l in matchLinks]

        for url in matchUrls:
            driver.get(url)

            try:
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "table.stats-table"))
                )
                htmlData = StringIO(driver.page_source) 
                team1 = pd.read_html(htmlData, flavor="lxml")

                if team1:
                    print(team1[0].head())
            
            except Exception as e:
                print("Error: ", e)

    except Exception as e:
        print("Error reading table data: ", e)

driver.quit()