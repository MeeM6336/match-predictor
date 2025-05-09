import mysql.connector
import pandas as pd
import os
import datetime
import joblib
from dotenv import load_dotenv
from pathlib import Path
from sklearn.preprocessing import LabelEncoder
from collections import defaultdict

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


def get_team_ranking(cursor, team_name):
	query = """
	SELECT ranking 
		FROM teams
		WHERE team_name = %s
	"""

	cursor.execute(query, (team_name,))
	result = cursor.fetchone()

	return result[0] if result else 9999 # Returns 9999 if ranking not found


def get_historical_matches():
	db = db_connect()
	
	try:
		df_matches = pd.read_sql_query("SELECT * FROM matches", db)

		return df_matches
	
	except Exception as e:
		print("Error fetching historical matches:", e)
		return None


def process_matches(df_matches):
	print("Beginning to process matches...")
	db = db_connect()
	cursor = db.cursor()

	df_matches = df_matches.sort_values(by='date').reset_index(drop=True)

	# Team name encoding
	encoder_path = Path(__file__).resolve().parent / 'encoders/team_encoder.pkl'

	if os.path.exists(encoder_path):
		team_encoder = joblib.load(encoder_path)

	else:
		all_teams = pd.concat([df_matches['team_a'], df_matches['team_b']]).unique()
		team_encoder = LabelEncoder()
		team_encoder.fit(all_teams)
		save_object(team_encoder, encoder_path)

	list_matches = []
	hth_record = defaultdict(int)

	# Match stats should be ideally in the format (tournament_type, best_of, teamA, aRanking, aRating, aKDA, aKAST, aAdr, hthWins,
	# teamB, bRanking, bRating, bKDA, bKAST, bAdr, hthWins, label) where label is 1 if teamA wins and 0 if teamA loses
	for _, row in df_matches.iterrows():
		encoded_team_a = team_encoder.transform([row.team_a])[0]
		encoded_team_b = team_encoder.transform([row.team_b])[0]
		tournament_type = row['tournament_type']
		best_of = row['best_of']

		a_ranking = get_team_ranking(cursor, row.team_a)
		b_ranking = get_team_ranking(cursor, row.team_b)

		aRating = row['team_a_rating']
		aKDA = row['team_a_kda']
		aKAST = row['team_a_adr']
		aAdr = row['team_a_kast']

		bRating = row['team_b_rating']
		bKDA = row['team_b_kda']
		bKAST = row['team_b_adr']
		bAdr = row['team_b_kast']

		aHthWins = hth_record[(row.team_a, row.team_b)]
		bHthWins = hth_record[(row.team_b, row.team_a)]

		label = row['outcome']

		match = [
						tournament_type, best_of,
            encoded_team_a, a_ranking,
            aRating, aKDA, aKAST, aAdr, aHthWins,
            encoded_team_b, b_ranking,
						bRating, bKDA, bKAST, bAdr, bHthWins,
            label
    ]
		list_matches.append(match)

		if label == 1:
			hth_record[(row.team_a, row.team_b)] += 1
		else:
				hth_record[(row.team_b, row.team_a)] += 1

	print("Match processing complete and length of matches is", len(df_matches))

	return list_matches