from seleniumbase import Driver
import mysql.connector
import pandas as pd
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

def main():
    '''try:
        mydb = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
        )
        cursor = mydb.cursor()
    
    except mysql.connector.Error as e:
        print("Database connection error:", e)
        return'''
    

    driver = Driver(uc=True, headless=True)

    try:
        url = 'https://www.hltv.org/events'
        driver.get(url)


    except Exception as e:


    
if __name__ == "__main__":
    main()