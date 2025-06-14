import joblib
import pandas as pd
import math
import os
import numpy as np
import torch
from models.mlp import MLP
from datetime import datetime, timedelta
from pathlib import Path
from ml_util import plot_graphs, get_hth_wins, db_connect, db_insert_feature_vector, get_team_stats_by_date, get_past_stats, create_rolling_feature_metrics, create_correlation_matrix

def predict_match(model, model_name, model_id, device):
  stage = "Live"
  db = db_connect()
  cursor = db.cursor(dictionary=True)
  scaler_path = Path(__file__).resolve().parent / "nn_model_data/standard_nn_scaler.pkl"
  scaler = joblib.load(scaler_path)
  today = datetime.now().date()
  past = today - timedelta(days=2)

  query = """
	SELECT 
		match_id, 
		date, 
		tournament_type, 
		best_of, 
		team_a,
		team_b
	FROM upcoming_matches
    WHERE DATE(date) >= %s AND DATE(date) <= %s
	  ORDER BY date asc
	"""

  try:
    df = pd.read_sql_query(query, db, params=(past, today))

  except Exception as e:
    print("Error fetching upcoming matches:", e)
    return

  new_columns = [
    'ranking_diff', 'rating_diff', 'KDA_diff', 'KAST_diff', 'ADR_diff',
    'round_wr_diff', 'opening_kill_rate_diff', 'multikill_rate_diff',
    '5v4_wr_diff', '4v5_wr_diff', 'trade_rate_diff', 'utility_adr_diff',
    'flash_assists_diff', 'pistol_wr_diff', 'round2_conv_diff',
    'round2_break_diff', 'hth_wins_diff'
	]

  for col in new_columns:
    df[col] = None

  for idx, row in df.iterrows():
    try:
      team_a_stats = get_team_stats_by_date(cursor, row["team_a"], row["date"])
      team_b_stats = get_team_stats_by_date(cursor, row["team_b"], row["date"])
      team_a_player_stats = get_past_stats(cursor, row["team_a"], row["date"])
      team_b_player_stats = get_past_stats(cursor, row["team_b"], row["date"])

      if not all([team_a_stats, team_b_stats, team_a_player_stats, team_b_player_stats]):
        continue

      hth_wins = get_hth_wins(cursor, row["team_a"], row["team_b"])
      hth_diff = 0

      if (hth_wins is not None):
        hth_diff = hth_wins[0] - hth_wins[1]
      
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

    except:
      continue

  df = df.dropna()
  X = df.drop(["match_id", "date", "team_a", "team_b"], axis=1)
  X_scaled = scaler.transform(X)
  X_match_id = df["match_id"].tolist()
  input_tensor = torch.tensor(X_scaled, dtype=torch.float32).to(device)

  model.eval()

  with torch.no_grad():
    logits = model(input_tensor)
    probabilities_class_1 = torch.sigmoid(logits)
    predictions = (probabilities_class_1 > 0.5).long()
    probs_squeezed = probabilities_class_1.squeeze()
    preds_squeezed = predictions.squeeze()
    confidences = torch.where(preds_squeezed == 1, probs_squeezed, 1 - probs_squeezed)

  predictions_list = predictions.tolist()
  confidences_list = confidences.tolist()
  X_list = X_scaled.tolist()

  for i in range(len(df)):
    try:
      db_insert_feature_vector(
        cursor, 
        X_match_id[i], 
        "live", 
        X_list[i], 
        model_id
      )

      query = """
        INSERT INTO match_predictions (prediction, confidence, model_id, match_id)
        VALUES (%s, %s, %s, %s)
      """

      cursor.execute(query, (
        predictions_list[i][0],
        confidences_list[i],
        model_id,
        X_match_id[i]
      ))
      db.commit()
      
    except Exception as e:
      print("Error", e)
      continue

  plot_graphs(db.cursor(), model_id, model_name, stage)

  db.close()
    
      
def main():
  BASE_DIR = os.path.dirname(os.path.abspath(__file__))
  MODEL_PATH = os.path.join(BASE_DIR, "../ml_model/nn_model_data/nn_final_classifier_06-10-2025.pkl")
  device = torch.device("cpu")

  model = None
  model_name = "neural_network"
  model_id = 2

  try:
    model = joblib.load(MODEL_PATH)
    model.to(device)
  except OSError as e:
    print("Error opening model:", e)

  predict_match(model, model_name, model_id, device)
  create_rolling_feature_metrics(model_name, model_id, "Live")
  create_correlation_matrix(model_name, model_id)

if __name__ == "__main__":
  main()