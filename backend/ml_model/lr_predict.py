import joblib
import pandas as pd
import os
import mysql.connector
import numpy as np
from sklearn.linear_model import LogisticRegression
from pathlib import Path
from ml_util import get_hth_wins, db_connect, db_insert_feature_vector, get_past_stats

def predict_match(model):
	db = db_connect()
	cursor = db.cursor()

	scaler_path = Path(__file__).resolve().parent / "lr_model_data/standard_lr_scaler.pkl"
	scaler = joblib.load(scaler_path)
    
	try:
		df_matches = pd.read_sql_query("SELECT * FROM upcoming_matches WHERE outcome IS NULL", db)

	except Exception as e:
			print("Error fetching upcoming matches:", e)

	for match_row in df_matches.itertuples(index=False):
		query = f"SELECT ranking FROM teams WHERE team_name=%s"
		cursor.execute(query, (match_row.team_a,))
		a_ranking = cursor.fetchone()

		cursor.execute(query, (match_row.team_b,))
		b_ranking = cursor.fetchone()
		ranking_diff = 0
		if ((a_ranking and b_ranking) is not None):
			ranking_diff = a_ranking[0] - b_ranking[0]

		# Get hth wins
		hth_wins = get_hth_wins(cursor, match_row.team_a, match_row.team_b)
		hth_diff = 0
		if (hth_wins is not None):
			hth_diff = hth_wins[0] - hth_wins[1]

		match_date = match_row.date

		match_stat = [
			match_row.tournament_type,
			match_row.best_of,
			int(ranking_diff),
			int(hth_diff)
		]

		# Get avg of stats
		for team in [match_row.team_a, match_row.team_b]:
			team_stats = get_past_stats(cursor, team, match_date)

			if team_stats is None or any(x is None for x in team_stats):
				match_stat = None
				break

			match_stat.extend([
				float(team_stats[0]), # team_rating
				float(team_stats[1]), # team_kda
				float(team_stats[2]), # team_kast
				float(team_stats[3]), # team_adr
			])

		if match_stat is None:
			continue
		
		match_stat_array = np.array(match_stat).reshape(1, -1)
		match_stat_scaled = scaler.transform(match_stat_array)
		proba = model.predict_proba(match_stat_scaled)[0]
		prediction = int(proba[1] >= 0.5)
		confidence = proba[prediction]

		query = f"""
		UPDATE upcoming_matches 
			SET outcome = %s, 
			confidence = %s 
		WHERE 
			team_a = %s AND
			team_b = %s AND
			date = %s AND
			tournament_name = %s
		"""
		
		try:
			cursor.execute(query, (
				int(prediction),
				float(confidence),
				match_row.team_a,
				match_row.team_b,
				match_row.date,
				match_row.tournament_name
			))
			db.commit()
				
		except mysql.connector.Error as e:
			db.rollback()
			print("Error inserting info:", e)

		try:
			db_insert_feature_vector(
				cursor, 
				int(match_row.match_id), 
				"live", 
				match_stat
			)
			db.commit()
				
		except mysql.connector.Error as e:
			db.rollback()
			print(f"Error inserting feature vector for matchID {match_row.match_id}:", e)
			
	db.close()

def main():
	BASE_DIR = os.path.dirname(os.path.abspath(__file__))
	MODEL_PATH = os.path.join(BASE_DIR, "../ml_model/lr_model_data/lr_final_classifier_05-16-2025.pkl")

	model = None

	try:
		model = joblib.load(MODEL_PATH)
	except OSError as e:
		print("Error opening model:", e)

	predict_match(model)

if __name__ == "__main__":
  main()