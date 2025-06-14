import joblib
import pandas as pd
import os
import mysql.connector
import numpy as np
from sklearn.linear_model import LogisticRegression
from datetime import datetime, timedelta
from pathlib import Path
from ml_util import plot_graphs, get_hth_wins, db_connect, db_insert_feature_vector, get_past_stats, create_rolling_feature_metrics, create_matches_insertion_graph, create_correlation_matrix

def predict_match(model, model_name):
	stage = "Live"
	model_id = 1
	db = db_connect()
	cursor = db.cursor()

	scaler_path = Path(__file__).resolve().parent / "lr_model_data/standard_lr_scaler.pkl"
	scaler = joblib.load(scaler_path)

	today = datetime.now().date()
	past = today - timedelta(days=2)
    
	try:
		df_matches = pd.read_sql_query(f"SELECT * FROM upcoming_matches WHERE DATE(date) >= %s AND DATE(date) <= %s", db, params=(past, today))

	except Exception as e:
			print("Error fetching upcoming matches:", e)

	for match_row in df_matches.itertuples(index=False):
		query = f"SELECT ranking FROM team_stats_by_date WHERE team_name=%s ORDER BY ABS(DATEDIFF(date, CURDATE())) LIMIT 1"
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

		team_a_stats = get_past_stats(cursor, match_row.team_a, match_date)
		team_b_stats = get_past_stats(cursor, match_row.team_b, match_date)

		if team_a_stats is None or team_b_stats is None:
			continue

		try :
			rating_diff = team_a_stats[0] - team_b_stats[0]
			KDA_diff = team_a_stats[1] - team_b_stats[1]
			KAST_diff = team_a_stats[2] - team_b_stats[2]
			ADR_diff = team_a_stats[3] - team_b_stats[3]

		except:
			continue

		match_stat.extend([rating_diff, KDA_diff, KAST_diff, ADR_diff])

		if match_stat is None:
			continue
		
		match_stat_array = np.array(match_stat).reshape(1, -1)
		match_stat_scaled = scaler.transform(match_stat_array)
		proba = model.predict_proba(match_stat_scaled)[0]
		prediction = int(proba[1] >= 0.5)
		confidence = proba[prediction]
		match_id = match_row.match_id

		query = """
			INSERT INTO match_predictions (prediction, confidence, model_id, match_id)
			VALUES (%s, %s, %s, %s)
		"""
		
		try:
			cursor.execute(query, (
				int(prediction),
				float(confidence),
				model_id,
				match_id
			))
				
		except mysql.connector.Error as e:
			db.rollback()
			print("Error inserting info:", e)
		
		db.commit()

		try:
			db_insert_feature_vector(
				cursor, 
				int(match_row.match_id), 
				"live", 
				match_stat_scaled.tolist()[0],
				model_id
			)
			db.commit()
				
		except mysql.connector.Error as e:
			db.rollback()

		plot_graphs(db.cursor(), model_id, model_name, stage)

		db.close


def main():
	BASE_DIR = os.path.dirname(os.path.abspath(__file__))
	MODEL_PATH = os.path.join(BASE_DIR, "../ml_model/lr_model_data/lr_final_classifier_06-06-2025.pkl")

	model = None
	model_name = "logistic_regression"
	model_id = 1

	try:
		model = joblib.load(MODEL_PATH)
	except OSError as e:
		print("Error opening model:", e)

	predict_match(model, model_name)
	create_rolling_feature_metrics(model_name, model_id, "Live")
	create_matches_insertion_graph()
	create_correlation_matrix(model_name, model_id)
	

if __name__ == "__main__":
  main()