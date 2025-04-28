import mysql.connector
import pandas as pd
import os
import datetime
import joblib
from dotenv import load_dotenv
from pathlib import Path
from sklearn.preprocessing import LabelEncoder

def db_connect():
	try:
		env_path = Path(__file__).resolve().parent.parent / '.env'
		load_dotenv(env_path)

		db = mysql.connector.connect(
			host=os.getenv("DB_HOST"),
			user=os.getenv("DB_USER"),
			password=os.getenv("DB_PASSWORD"),
			database=os.getenv("DB_NAME")
		)
	
		return db

	except mysql.connector.Error as e:
		print("Database connection error:", e)
		return None


def save_object(obj, path):
	path = Path(path)
	path.parent.mkdir(parents=True, exist_ok=True)
	joblib.dump(obj, path)


def getDateStamp():
	date = datetime.datetime.now()
	date_string = date.strftime('%m/%d/%Y').replace("/", "-")
	return date_string


def get_historical_matches():
	db = db_connect()
	
	try:
		df_matches = pd.read_sql_query("SELECT * FROM MATCHES", db)
		df_team_stats = pd.read_sql_query("SELECT * FROM match_team_stats", db)

		return df_matches, df_team_stats
	
	except Exception as e:
		print("Error fetching historical matches:", e)
		return None, None


def get_hth_wins(cursor, team_a, team_b):
    query = """
    SELECT 
        IFNULL(SUM(CASE 
            WHEN team_a = %s AND outcome = 1 THEN 1
            WHEN team_b = %s AND outcome = 0 THEN 1
            ELSE 0 END), 0) AS wins_team_a,

        IFNULL(SUM(CASE 
            WHEN team_b = %s AND outcome = 1 THEN 1
            WHEN team_a = %s AND outcome = 0 THEN 1
            ELSE 0 END), 0) AS wins_team_b
    FROM matches
    WHERE 
        (team_a = %s AND team_b = %s)
        OR
        (team_a = %s AND team_b = %s)
    """
    cursor.execute(query, (team_a, team_a, team_b, team_b, team_a, team_b, team_b, team_a))
    result = cursor.fetchone()
    return result if result else (0, 0)


def process_matches(df_matches, df_team_stats):
	db = db_connect()
	
	cursor = db.cursor()

	print("Beginning to process matches...")

	# Team name encoding
	encoder_path = Path(__file__).resolve().parent / 'encoders/team_encoder.pkl'

	if os.path.exists(encoder_path):
		team_encoder = joblib.load(encoder_path)

	else:
		all_teams = pd.concat([df_matches['team_a'], df_matches['team_b'], df_team_stats['team_name']]).unique()
		team_encoder = LabelEncoder()
		team_encoder.fit(all_teams)
		save_object(team_encoder, encoder_path)

	team_stats_dict = {(row.match_id, row.team_name): row for row in df_team_stats.itertuples(index=False)}

	list_matches = [] # A 2-D Array storing individual matches

	for match_row in df_matches.itertuples(index=False):
		encoded_team_a = team_encoder.transform([match_row.team_a])[0]
		encoded_team_b = team_encoder.transform([match_row.team_b])[0]

		match_stats = [
            encoded_team_a, 
            encoded_team_b, 
        ] # A list storing features for ml models

		# Get hth wins
		hth_wins = get_hth_wins(cursor, match_row.team_a, match_row.team_b)
		team_a_hth_wins = hth_wins[0]
		team_b_hth_wins = hth_wins[1]

		# Process Team A stats
		team_a_key = (match_row.match_id, match_row.team_a)
		team_a_stats = team_stats_dict.get(team_a_key)
		match_stats.extend([
            team_a_stats.team_rating if team_a_stats else 1,
            team_a_stats.avg_kda if team_a_stats else 1.0,
            team_a_stats.avg_kast if team_a_stats else 70.0,
            team_a_stats.avg_adr if team_a_stats else 80.0,
			team_a_hth_wins
        ])
        
        # Process Team B stats
		team_b_key = (match_row.match_id, match_row.team_b)
		team_b_stats = team_stats_dict.get(team_b_key)
		match_stats.extend([
			team_b_stats.team_rating if team_b_stats else 1,
			team_b_stats.avg_kda if team_b_stats else 1.0,
			team_b_stats.avg_kast if team_b_stats else 70.0,
			team_b_stats.avg_adr if team_b_stats else 80.0,
			team_b_hth_wins
		])
		
		match_stats.append(int(match_row.outcome))
		list_matches.append(match_stats)
		# Match stats should be ideally in the format (teamA, teamB, aRating, aKDA, aKAST, aAdr, hthWins,
		# bRating, bKDA, bKAST, bAdr, htwWins, label) where label is 1 if teamA wins and 0 if teamA loses

	print("Match processing complete")

	return list_matches