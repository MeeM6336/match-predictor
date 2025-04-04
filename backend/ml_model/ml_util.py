import mysql.connector
import pandas as pd
import os
from dotenv import load_dotenv
from pathlib import Path
from sklearn.preprocessing import LabelEncoder


def get_historical_matches():
	try:
		env_path = Path(__file__).resolve().parent.parent / '.env'
		load_dotenv(env_path)

		db = mysql.connector.connect(
			host=os.getenv("DB_HOST"),
			user=os.getenv("DB_USER"),
			password=os.getenv("DB_PASSWORD"),
			database=os.getenv("DB_NAME")
		)

	except mysql.connector.Error as e:
		print("Database connection error:", e)
		return None, None, None
	
	try:
		df_matches = pd.read_sql_query("SELECT * FROM MATCHES", db)
		df_team_stats = pd.read_sql_query("SELECT * FROM team_stats", db)
		df_map_stats = pd.read_sql_query("SELECT * FROM map_stats", db)

		return df_matches, df_team_stats, df_map_stats
	
	except Exception as e:
		print("Error fetching DB:", e)
		return None, None, None



def process_matches(df_matches, df_team_stats, df_map_stats):
	print("Beginning to process matches...")

	# Map encoding to int
	all_maps = df_matches['map'].unique().tolist() + df_map_stats['map_name'].unique().tolist()
	map_encoder = LabelEncoder()
	map_encoder.fit(list(set(all_maps)))

	# Team name encoding
	all_teams = pd.concat([df_matches['team_a'], df_matches['team_b'], df_team_stats['team_name'], df_map_stats['team_name']]).unique()
	team_encoder = LabelEncoder()
	team_encoder.fit(all_teams)

	team_stats_dict = {(row.match_id, row.team_name): row for row in df_team_stats.itertuples(index=False)}
	map_stats_dict = {(row.team_name, row.map_name): row for row in df_map_stats.itertuples(index=False)}

	list_matches = [] # A 2-D Array storing individual matches

	for match_row in df_matches.itertuples(index=False):
		encoded_map = map_encoder.transform([match_row.map])[0]
		encoded_team_a = team_encoder.transform([match_row.team_a])[0]
		encoded_team_b = team_encoder.transform([match_row.team_b])[0]

		match_stats = [
            encoded_map,
            encoded_team_a, 
            encoded_team_b, 
        ] # A list storing features for ml models

		# Process Team A stats
		team_a_key = (match_row.match_id, match_row.team_a)
		team_a_stats = team_stats_dict.get(team_a_key)
		match_stats.extend([
            team_a_stats.team_rating if team_a_stats else 1,
            team_a_stats.first_kills if team_a_stats else 0.5,
            team_a_stats.clutches_won if team_a_stats else 0.1,
            team_a_stats.avg_kda if team_a_stats else 1.0,
            team_a_stats.avg_kast if team_a_stats else 70.0,
            team_a_stats.avg_adr if team_a_stats else 80.0
        ])
        
        # Process Team B stats
		team_b_key = (match_row.match_id, match_row.team_b)
		team_b_stats = team_stats_dict.get(team_b_key)
		match_stats.extend([
			team_b_stats.team_rating if team_b_stats else 1,
			team_b_stats.first_kills if team_b_stats else 0.5,
			team_b_stats.clutches_won if team_b_stats else 0.1,
			team_b_stats.avg_kda if team_b_stats else 1.0,
			team_b_stats.avg_kast if team_b_stats else 70.0,
			team_b_stats.avg_adr if team_b_stats else 80.0
		])
		
		# Process Team A map stats
		map_a_key = (match_row.team_a, match_row.map)
		map_a_stats = map_stats_dict.get(map_a_key)
		match_stats.extend([
            map_a_stats.wins if map_a_stats else 0,
            map_a_stats.losses if map_a_stats else 0
        ])
        
        # Process Team B map stats
		map_b_key = (match_row.team_b, match_row.map)
		map_b_stats = map_stats_dict.get(map_b_key)
		match_stats.extend([
            map_b_stats.wins if map_b_stats else 0,
            map_b_stats.losses if map_b_stats else 0
        ])
		
		match_stats.append(1 if match_row.rounds_team_a > match_row.rounds_team_b else 0)
		list_matches.append(match_stats)
		# Match stats should be ideally in the format (map, teamA, teamB, aRating, aFK, aCW, aKDA, aKAST, aAdr, 
		# bRating, bFK, bCW, bKDA, bKAST, bAdr, aMW, aML, bMW, bML, label) where label is 1 if teamA wins and 0 if teamA loses

	return list_matches