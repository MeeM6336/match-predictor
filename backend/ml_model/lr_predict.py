import joblib
import pandas as pd
import os
import mysql.connector
import numpy as np
from sklearn.linear_model import LogisticRegression
from pathlib import Path
from ml_util import get_hth_wins, db_connect, db_insert_feature_vector, get_past_stats, create_class_seperation_quality_plot, create_class_representation_bar_graph, create_cumm_accuracy_graph, create_rolling_accuracy_graph, create_rolling_feature_metrics, create_matches_insertion_graph, create_correlation_matrix

def predict_match(model, model_name, stage):
	model_id = 1
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

		team_a_stats = get_past_stats(cursor, match_row.team_a, match_date)
		team_b_stats = get_past_stats(cursor, match_row.team_b, match_date)

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
				model_id,
				"live", 
				match_stat
			)
			db.commit()
				
		except mysql.connector.Error as e:
			db.rollback()
			print(f"Error inserting feature vector for matchID {match_row.match_id}:", e)
			
	# Graph creations
	query = """
		SELECT
			outcome,
			confidence, 
			actual_outcome
		FROM upcoming_Matches 
		WHERE 
			outcome IS NOT NULL AND
			confidence IS NOT NULL
	"""

	cursor.execute(query)
	match_outcomes = cursor.fetchall()

	all_outcome = []
	all_actual_outcomes = []
	all_confidences = []

	for outcome, confidence, actual_outcome in match_outcomes:
		all_actual_outcomes.append(actual_outcome)
		all_outcome.append(outcome)

		if outcome == 0:
			all_confidences.append(confidence - 0.5)
		
		else:
			all_confidences.append(confidence)

	create_class_seperation_quality_plot(all_actual_outcomes, all_confidences, model_name, stage)
	create_class_representation_bar_graph(all_outcome, model_name, stage)
	create_cumm_accuracy_graph(all_outcome, all_actual_outcomes, model_name, stage)
	create_rolling_accuracy_graph(all_outcome, all_actual_outcomes, model_name, stage)

	db.close()


def main():
	BASE_DIR = os.path.dirname(os.path.abspath(__file__))
	MODEL_PATH = os.path.join(BASE_DIR, "../ml_model/lr_model_data/lr_final_classifier_05-27-2025.pkl")

	model = None
	model_name = "logistic_regression"
	model_id = 1
	stage = "Live"

	try:
		model = joblib.load(MODEL_PATH)
	except OSError as e:
		print("Error opening model:", e)

	predict_match(model, model_name, stage)
	create_rolling_feature_metrics(model_name, model_id, stage)
	create_matches_insertion_graph()
	create_correlation_matrix(model_name, model_id)
	

if __name__ == "__main__":
  main()