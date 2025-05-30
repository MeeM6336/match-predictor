import mysql.connector
import pandas as pd
import os
import datetime
import joblib
import math
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch
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


def get_team_ranking(cursor, team_name, date):
	query = """
	SELECT ranking 
		FROM team_stats_by_date
		WHERE team_name = %s
	"""

	cursor.execute(query, (team_name,))
	result = cursor.fetchone()

	return result[0] if result else None


def get_team_stats_by_date(cursor, team_name, date):
	query = """
	SELECT 
		ranking, 
		round_wr, 
		opening_kill_rate, 
		multikill_rate, 
		5v4_wr, 
		4v5_wr, 
		trade_rate, 
		utility_adr, 
		flash_assists, 
		pistol_wr, 
		round2_conv, 
		round2_break
	FROM team_stats_by_date
		WHERE team_name = %s
	ORDER BY ABS(TIMESTAMPDIFF(SECOND, date, %s))
    LIMIT 1
	"""
	cursor.execute(query, (team_name, date))
	result = cursor.fetchone()

	return result


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
			LIMIT 10
		) AS last_10_matches;
	"""

	cursor.execute(query, (team_name, match_date, team_name, match_date))
	past_stats = cursor.fetchone()
	
	return past_stats
	

def db_insert_feature_vector(cursor, match_id, source, match, model_id):
	if source == "training":
		query = """
		INSERT INTO feature_vectors (
				match_id, model_id, best_of, tournament_type, ranking_diff, hth_wins_diff,
				rating_diff, KDA_diff, KAST_diff, ADR_diff
		) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
		"""
	elif source == "live":
		query = """
		INSERT INTO live_feature_vectors (
				match_id, model_id, best_of, tournament_type, ranking_diff, hth_wins_diff,
				rating_diff, KDA_diff, KAST_diff, ADR_diff
		) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
		"""
	
	cursor.execute(query, (match_id, model_id,*match))


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

	# Match stats should be ideally in the format (tournament_type, best_of, ranking_diff, hth_diff, rating_diff, KDA_diff, KAST_diff, ADR_diff, label, match_id) 
	# where label is 1 if teamA wins and 0 if teamA loses
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

		team_a_stats = get_past_stats(cursor, a_team, match_date)
		team_b_stats = get_past_stats(cursor, b_team, match_date)

		if (a_ranking == None or b_ranking == None or team_a_stats[0] == None or team_b_stats[0] == None):
			continue

		ranking_diff = a_ranking - b_ranking
		ranking_diff = math.copysign(math.log(abs(ranking_diff) + 1), ranking_diff)

		aHthWins = hth_record[(a_team, b_team)]
		bHthWins = hth_record[(b_team, a_team)]

		hth_diff = aHthWins - bHthWins
		
		rating_diff = team_a_stats[0] - team_b_stats[0]
		KDA_diff = team_a_stats[1] - team_b_stats[1]
		KAST_diff = team_a_stats[2] - team_b_stats[2]
		ADR_diff = team_a_stats[3] - team_b_stats[3]


		# Append aggregate stats
		x = [
			tournament_type, best_of, ranking_diff, hth_diff,
			rating_diff, KDA_diff, KAST_diff, ADR_diff,
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


def process_matches_nn():
	print("Beginning to process matches...")
	db = db_connect()
	cursor = db.cursor(dictionary=True)

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
	rows = cursor.fetchall()
	df = pd.DataFrame(rows)

	# Initialize feature columns
	new_columns = [
    'ranking_diff', 'rating_diff', 'KDA_diff', 'KAST_diff', 'ADR_diff',
    'round_wr_diff', 'opening_kill_rate_diff', 'multikill_rate_diff',
    '5v4_wr_diff', '4v5_wr_diff', 'trade_rate_diff', 'utility_adr_diff',
    'flash_assists_diff', 'pistol_wr_diff', 'round2_conv_diff',
    'round2_break_diff', 'hth_wins_diff'
	]

	for col in new_columns:
		df[col] = None

	hth_record = defaultdict(int)

	for idx, row in df.iterrows():
		a_team = row['team_a']
		b_team = row['team_b']
		match_date = row['date']

		team_a_stats = get_team_stats_by_date(cursor, a_team, match_date)
		team_b_stats = get_team_stats_by_date(cursor, b_team, match_date)

		team_a_player_stats = get_past_stats(cursor, a_team, match_date)
		team_b_player_stats = get_past_stats(cursor, b_team, match_date)

		aHthWins = hth_record[(a_team, b_team)]
		bHthWins = hth_record[(b_team, a_team)]

		try:
			ranking_diff = team_a_stats['ranking'] - team_b_stats['ranking']
			ranking_diff = math.copysign(math.log(abs(ranking_diff) + 1), ranking_diff)
			round_wr_diff = team_a_stats['round_wr'] - team_b_stats['round_wr']
			opening_kill_rate_diff = team_a_stats['opening_kill_rate'] - team_b_stats['opening_kill_rate']
			multikill_rate_diff = team_a_stats['multikill_rate'] - team_b_stats['multikill_rate']
			_5v4_wr_diff = team_a_stats['5v4_wr'] - team_b_stats['5v4_wr']
			_4v5_wr_diff = team_a_stats['4v5_wr'] - team_b_stats['4v5_wr']
			trade_rate_diff = team_a_stats['trade_rate'] - team_b_stats['trade_rate']
			utility_adr_diff = team_a_stats['utility_adr'] - team_b_stats['utility_adr']
			flash_assists_diff = team_a_stats['flash_assists'] - team_b_stats['flash_assists']
			pistol_wr_diff = team_a_stats['pistol_wr'] - team_b_stats['pistol_wr']
			round2_conv_diff = team_a_stats['round2_conv'] - team_b_stats['round2_conv']
			round2_break_diff = team_a_stats['round2_break'] - team_b_stats['round2_break']
			rating_diff = team_a_player_stats['team_rating'] - team_b_player_stats['team_rating']
			KDA_diff = team_a_player_stats['avg_kda'] - team_b_player_stats['avg_kda']
			KAST_diff = team_a_player_stats['avg_kast'] - team_b_player_stats['avg_kast']
			ADR_diff = team_a_player_stats['avg_adr'] - team_b_player_stats['avg_adr']
			hth_diff = aHthWins - bHthWins

			df.at[idx, 'ranking_diff'] = ranking_diff
			df.at[idx, 'rating_diff'] = rating_diff
			df.at[idx, 'KDA_diff'] = KDA_diff
			df.at[idx, 'KAST_diff'] = KAST_diff
			df.at[idx, 'ADR_diff'] = ADR_diff
			df.at[idx, 'round_wr_diff'] = round_wr_diff
			df.at[idx, 'opening_kill_rate_diff'] = opening_kill_rate_diff
			df.at[idx, 'multikill_rate_diff'] = multikill_rate_diff
			df.at[idx, '5v4_wr_diff'] = _5v4_wr_diff
			df.at[idx, '4v5_wr_diff'] = _4v5_wr_diff
			df.at[idx, 'trade_rate_diff'] = trade_rate_diff
			df.at[idx, 'utility_adr_diff'] = utility_adr_diff
			df.at[idx, 'flash_assists_diff'] = flash_assists_diff
			df.at[idx, 'pistol_wr_diff'] = pistol_wr_diff
			df.at[idx, 'round2_conv_diff'] = round2_conv_diff
			df.at[idx, 'round2_break_diff'] = round2_break_diff
			df.at[idx, 'hth_wins_diff'] = hth_diff

			if row['outcome'] == 1:
					hth_record[(a_team, b_team)] += 1
			elif row['outcome'] == 0:
					hth_record[(b_team, a_team)] += 1

		except TypeError as e:
			continue

	db.close()
	cursor.close()

	df = df.dropna()

	return df
	
	
def create_class_seperation_quality_plot(y_true, y_prob, model_name, stage):
	plt.figure(figsize=(8, 4.5))
	length = len(y_prob)
	xmin = length * (-1)
	xmax = length * 2

	for i in range(length):
			color = 'blue' if y_true[i] == 1 else 'red'
			plt.scatter(i, y_prob[i], color=color, alpha=0.6, s=15)

	plt.axhline(0.5, linestyle='--', color='gray', label='Decision Threshold (0.5)')
	plt.xlim(xmin, xmax)
	plt.xticks([])
	plt.ylabel("Probability")
	plt.legend()
	plt.grid(True)

	legend_elements = [
				Patch(facecolor='blue', label='Win'),
				Patch(facecolor='red', label='Lose')
	]

	plt.legend(handles=legend_elements, loc='lower right')
	plt.tight_layout()

	path = Path(__file__).resolve().parent.parent.parent / f"frontend/public/images/{model_name}_{stage}_class_seperation_quality_plot.png"
	path.parent.mkdir(parents=True, exist_ok=True)

	plt.savefig(path)
	plt.close()


def create_class_representation_bar_graph(y_pred, model_name, stage):
	plt.figure(figsize=(8, 4.5))
	zero = 0 
	one = 0
	for i in range(len(y_pred)):
		if y_pred[i] == 1:
				one += 1
		else:
				zero += 1
	
	plt.bar(["Win", "Lose"], [one, zero], color=["blue", "blue"])

	plt.xlabel("Class")
	plt.ylabel("Class Frequency")
	plt.tight_layout()

	path = Path(__file__).resolve().parent.parent.parent / f"frontend/public/images/{model_name}_{stage}_class_representation_bar_graph.png"
	path.parent.mkdir(parents=True, exist_ok=True)

	plt.savefig(path)
	plt.close()


def create_cumm_accuracy_graph(y_pred, y_true, model_name, stage):
	y_true_np = np.array(y_true)
	y_pred_np = np.array(y_pred)
	num_matches = len(y_true)
	match_indices = np.arange(1, num_matches + 1)
	is_correct = (y_true_np == y_pred_np).astype(int)
	cumulative_correct = np.cumsum(is_correct)
	cumulative_accuracy = cumulative_correct / match_indices

	plt.figure(figsize=(8, 4.5))
	plt.plot(match_indices, cumulative_accuracy, 'b-', linewidth=2, label='Cumulative Accuracy')
	plt.xlabel('Match Number')
	plt.ylabel('Accuracy')
	plt.ylim(0, 1)
	plt.grid(True, linestyle='--', alpha=0.7)
	plt.axhline(y=np.mean(is_correct), color='r', linestyle='--', label=f'Overall Accuracy: {np.mean(is_correct):.2f}')
	plt.legend()
	plt.tight_layout()

	path = Path(__file__).resolve().parent.parent.parent / f"frontend/public/images/{model_name}_{stage}_cumm_accuracy_graph.png"
	path.parent.mkdir(parents=True, exist_ok=True)

	plt.savefig(path)
	plt.close()


def create_rolling_accuracy_graph(y_pred, y_true, model_name, stage):
	window_size = 10
	y_true_np = np.array(y_true)
	y_pred_np = np.array(y_pred)
	num_matches = len(y_true)
	match_indices = np.arange(1, num_matches + 1)
	is_correct = (y_true_np == y_pred_np).astype(int)

	rolling_accuracy = pd.Series(is_correct).rolling(window=window_size).mean()

	plt.figure(figsize=(8, 4.5))
	plt.plot(match_indices[window_size-1:], rolling_accuracy[window_size-1:], 'b-', linewidth=2, label=f'Rolling Accuracy (Window={window_size})')
	plt.xlabel('Match Number')
	plt.ylabel('Accuracy')
	plt.ylim(0, 1)
	plt.grid(True, linestyle='--', alpha=0.7)
	plt.axhline(y=np.mean(is_correct), color='r', linestyle='--', label=f'Overall Accuracy: {np.mean(is_correct):.2f}')
	plt.legend()
	plt.tight_layout()

	path = Path(__file__).resolve().parent.parent.parent / f"frontend/public/images/{model_name}_{stage}_rolling_accuracy_graph.png"
	path.parent.mkdir(parents=True, exist_ok=True)

	plt.savefig(path)
	plt.close()


def create_rolling_feature_metrics(model_name, model_id, stage):
	db = db_connect()
	cursor = db.cursor(dictionary=True)
	try:
		query = """
			SELECT 
				live_feature_vectors.tournament_type, 
				live_feature_vectors.best_of, 
				live_feature_vectors.ranking_diff, 
				live_feature_vectors.hth_wins_diff, 
				live_feature_vectors.rating_diff, 
				live_feature_vectors.KDA_diff, 
				live_feature_vectors.KAST_diff, 
				live_feature_vectors.ADR_diff,
				upcoming_matches.date
			FROM live_feature_vectors JOIN upcoming_matches ON live_feature_vectors.match_id=upcoming_matches.match_id WHERE model_id=%s
			ORDER BY 
				upcoming_matches.date DESC
		"""

		cursor.execute(query, (model_id,))
		features = cursor.fetchall()
	except Exception as e:
		print("Error fetching feature vectors:", e)
		return None

	df = pd.DataFrame(features)
	df['date'] = pd.to_datetime(df['date'])
	df = df.set_index('date')
	df = df.sort_index()
	
	rolling_window = '15D'
	numerical_features = ['tournament_type', 'best_of', 'ranking_diff', 'hth_wins_diff', 'rating_diff', 'KDA_diff', 'KAST_diff', 'ADR_diff']

	for feature in numerical_features:
		plt.figure(figsize=(12, 6))

		df_feature_rolling_mean = df[feature].rolling(window=rolling_window, min_periods=1).mean()
		df_feature_rolling_median = df[feature].rolling(window=rolling_window, min_periods=1).median()
		df_feature_rolling_std = df[feature].rolling(window=rolling_window, min_periods=1).std()

		plt.plot(df.index, df[feature], alpha=0.3, label=f'{feature} Raw', marker='.', linestyle='None')

		plt.plot(df.index, df_feature_rolling_mean, label=f'{feature} Rolling Mean ({rolling_window})', color='blue', linewidth=1.5)
		plt.plot(df.index, df_feature_rolling_median, label=f'{feature} Rolling Median ({rolling_window})', color='green', linestyle='--', linewidth=1.5)
		plt.plot(df.index, df_feature_rolling_std, label=f'{feature} Rolling Std Dev ({rolling_window})', color='red', linestyle=':', linewidth=1.5)

		plt.ylabel(feature)
		plt.xlabel('Date')
		plt.grid(True, linestyle='--', alpha=0.7)
		plt.xticks(rotation=45)
		plt.legend(loc='best', fontsize='small')
		plt.gcf().autofmt_xdate()
		
		plt.tight_layout()

		path = Path(__file__).resolve().parent.parent.parent / f"frontend/public/images/{model_name}_{stage}_rolling_stats_{feature}.png"
		path.parent.mkdir(parents=True, exist_ok=True)

		plt.savefig(path)
		
		plt.close()

	db.close()

def create_matches_insertion_graph():
	db = db_connect()
	cursor = db.cursor()
	try:
		query = """
			SELECT 
				date
			FROM upcoming_matches 
			WHERE
				OUTCOME IS NOT NULL
		"""

		cursor.execute(query)
		dates = cursor.fetchall()

	except Exception as e:
		print("Error fetching feature vectors:", e)
		return None
	
	date_counts = {}

	for (dt,) in dates:
		only_date = dt.date()
		date_counts[only_date] = date_counts.get(only_date, 0) + 1

	sorted_counts = dict(sorted(date_counts.items()))
	dates = list(sorted_counts.keys())
	counts = list(list(sorted_counts.values()))

	plt.figure(figsize=(8, 4.5))
	plt.plot(dates, counts, marker='o', color='blue', linewidth=1.5)
	plt.xlabel('Date')
	plt.ylabel('Count')
	plt.grid(True)
	plt.xticks(rotation=45)
	plt.tight_layout()

	path = Path(__file__).resolve().parent.parent.parent / f"frontend/public/images/Live_match_insertions.png"
	path.parent.mkdir(parents=True, exist_ok=True)

	plt.savefig(path)
	
	plt.close()
	db.close()
	

def create_correlation_matrix(model_name, model_id): # Need to refactor for different models
	db = db_connect()
	cursor = db.cursor(dictionary=True)
	try:
		query = """
			SELECT 
				tournament_type, 
				best_of, 
				ranking_diff, 
				hth_wins_diff, 
				rating_diff, 
				KDA_diff, 
				KAST_diff, 
				ADR_diff
			FROM feature_vectors WHERE model_id = %s
		"""

		cursor.execute(query, (model_id,))
		features = cursor.fetchall()
	except Exception as e:
		print("Error fetching feature vectors:", e)
		return None

	df = pd.DataFrame(features)
	spearman_corr_matrix = df.corr(method='spearman')

	path = Path(__file__).resolve().parent.parent.parent / f"frontend/public/data/{model_name}_Live_spearman_corr_matrix.json"
	path.parent.mkdir(parents=True, exist_ok=True)

	spearman_corr_matrix.to_json(path, orient='index', indent=4)