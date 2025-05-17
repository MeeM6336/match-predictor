import mysql.connector
import pandas as pd
import os
import datetime
import joblib
from dotenv import load_dotenv
from pathlib import Path
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


# Used in live match prediction to get all hth lineups
def get_hth_wins(cursor, team_a, team_b):
    query = """
    SELECT
        team,
        COUNT(*) AS wins
    FROM (
        SELECT
            CASE
                WHEN outcome = 1 THEN team_a
                ELSE team_b
            END AS team
        FROM matches
        WHERE
            (team_a = %s AND team_b = %s) OR
            (team_a = %s AND team_b = %s)
    ) AS hth
    GROUP BY team;
    """
    cursor.execute(query, (team_a, team_b, team_b, team_a))
    results = cursor.fetchall()

    # Initialize wins dict
    wins = {team_a: 0, team_b: 0}

    for row in results:
        team, count = row
        wins[team] = count

    return (wins[team_a], wins[team_b])


def get_team_ranking(cursor, team_name):
	query = """
	SELECT ranking 
		FROM teams
		WHERE team_name = %s
	"""

	cursor.execute(query, (team_name,))
	result = cursor.fetchone()

	return result[0] if result else None


def get_past_stats(cursor, team_name, match_date):
	query = """
		SELECT 
			AVG(team_rating) AS team_rating,
			AVG(avg_kda) AS avg_kda,
			AVG(avg_kast) AS avg_kast,
			AVG(avg_adr) AS avg_adr
		FROM (
			SELECT * FROM (
				SELECT 
					match_id, 
					team_a_rating AS team_rating, 
					team_a_kda AS avg_kda, 
					team_a_kast AS avg_kast, 
					team_a_adr AS avg_adr,
					date
				FROM matches
				WHERE team_a = %s AND match_id < %s

				UNION ALL

				SELECT 
					match_id, 
					team_b_rating AS team_rating, 
					team_b_kda AS avg_kda, 
					team_b_kast AS avg_kast, 
					team_b_adr AS avg_adr,
					date
				FROM matches
				WHERE team_b = %s AND match_id < %s
			) AS team_matches
			ORDER BY date DESC
			LIMIT 15
		) AS last_10_matches;
	"""

	cursor.execute(query, (team_name, match_date, team_name, match_date))
	past_stats = cursor.fetchone()
	
	return past_stats
	

def db_insert_feature_vector(cursor, match_id, source, match):
	if source == "training":
		query = """
		INSERT INTO feature_vectors (
				match_id, best_of, tournament_type, ranking_diff, hth_wins_diff,
				aRating, aKDA, aKAST, aADR,
				bRating, bKDA, bKAST, bADR
		) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
		"""
	elif source == "live":
		query = """
		INSERT INTO live_feature_vectors (
				match_id, best_of, tournament_type, ranking_diff, hth_wins_diff,
				aRating, aKDA, aKAST, aADR,
				bRating, bKDA, bKAST, bADR
		) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
		"""
	
	cursor.execute(query, (match_id,*match))


def process_matches():
	print("Beginning to process matches...")
	db = db_connect()
	cursor = db.cursor()

	query = """
	SELECT 
		match_id, 
		date, 
		tournament_type, 
		best_of, 
		team_a,
		team_b,
		outcome 
	FROM matches
	ORDER BY date asc
	"""

	cursor.execute(query)
	matches = cursor.fetchall()

	list_features = []
	hth_record = defaultdict(int)

	# Match stats should be ideally in the format (tournament_type, best_of, ranking_diff, hth_diff, aRating, aKDA, aKAST, aAdr,
	# bRating, bKDA, bKAST, bAdr, label, match_id) where label is 1 if teamA wins and 0 if teamA loses
	for match in matches:
		match_id = match[0]
		match_date = match[1]
		tournament_type = match[2]
		best_of = match[3]
		a_team = match[4]
		b_team = match[5]
		match_outcome = match[6]

		a_ranking = get_team_ranking(cursor, a_team)
		b_ranking = get_team_ranking(cursor, b_team)

		if (a_ranking == None or b_ranking == None):
			continue

		ranking_diff = a_ranking - b_ranking

		aHthWins = hth_record[(a_team, b_team)]
		bHthWins = hth_record[(b_team, a_team)]

		hth_diff = aHthWins - bHthWins

		team_stats = []
		for team in [a_team, b_team]:
			team_stats.append(get_past_stats(cursor, team, match_date))

		# Append aggregate stats
		x = [
			tournament_type, best_of, ranking_diff, hth_diff,
			team_stats[0][0], team_stats[0][1], team_stats[0][2], team_stats[0][3],
			team_stats[1][0], team_stats[1][1], team_stats[1][2], team_stats[1][3],
			match_outcome, match_id
		]

		# Checks for any null values
		if any(val is None for val in x):
			continue

		if match_outcome == 1:
			hth_record[(a_team, b_team)] += 1
		else:
			hth_record[(b_team, a_team)] += 1

		list_features.append(x)

	cursor.close()
	db.close()

	return list_features