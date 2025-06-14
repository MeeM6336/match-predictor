import joblib
import json
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import confusion_matrix, log_loss, roc_auc_score
from ml_util import insert_model_metrics, getDateStamp, save_object, db_insert_feature_vector, db_connect, create_class_seperation_quality_plot, create_class_representation_bar_graph, create_cumm_accuracy_graph, create_rolling_accuracy_graph

def lr_train_model(match_feature_lists):
	model_id = 1
	db = db_connect()
	cursor = db.cursor()

	print("Beginning model training...")
	matches = np.array(match_feature_lists, dtype=object)
	
	X = matches[:, :-2].astype(float)
	y = matches[:, -2].astype(int)

	scaler = StandardScaler()
	X_scaled = scaler.fit_transform(X)

	X_trainval, X_test, y_trainval, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=7)
	
	test_data_path = Path(__file__).resolve().parent / f"lr_model_data/test_data_{getDateStamp()}.npz"
	np.savez(test_data_path, X_test=X_test, y_test=y_test)

	scaler_path = Path(__file__).resolve().parent / "lr_model_data/standard_lr_scaler.pkl"
	save_object(scaler, scaler_path)

	# Grid search
	param_grid = {
		'penalty': ['l1', 'l2'], 
		'C': [0.1, 1, 10, 20, 50],
		'max_iter': [500, 1000, 1500, 2500]
	}

	model = LogisticRegression(solver='liblinear')
	grid_search = GridSearchCV(model, param_grid, cv=5, scoring='f1', n_jobs=-1)
	grid_search.fit(X_trainval, y_trainval)

	lr_classifier_path = Path(__file__).resolve().parent / f"lr_model_data/lr_classifier_{getDateStamp()}.pkl"
	print(grid_search.best_estimator_)

	save_object(grid_search.best_estimator_, lr_classifier_path)

	try:
		for match, features in zip(match_feature_lists, X_scaled):
			db_insert_feature_vector(cursor, match[-1], "training", features, model_id)
			db.commit()
	except Exception as e:
		print("Error inserting training feature vector:", e)
		db.rollback()
	finally:
		db.commit()
		db.close()

	print("Finished model training")
	

def evaluate_model(model, test_data, model_name):
	print("Starting model evalutation")

	db = db_connect()
	cursor = db.cursor()

	model = joblib.load(model)
	data = np.load(test_data)
	stage = "Training"
	
	X_test, y_test = data['X_test'], data['y_test']

	y_pred = model.predict(X_test)
	y_prob = model.predict_proba(X_test)[:, 1]

	cm = confusion_matrix(y_test, y_pred).tolist()
	loss = log_loss(y_test, y_prob)
	roc_auc = roc_auc_score(y_test, y_prob)

	results = {
		"loss": loss,
		"ROC AUC": roc_auc,
		"confusion_matrix": cm,
	}

	try:
		insert_model_metrics(cursor, "logistic_regression", results)
		db.commit()
	except Exception as e:
		print("Error inserting model metrics:", e)
		db.rollback()
	
	create_class_seperation_quality_plot(y_test, y_prob, model_name, stage)
	create_class_representation_bar_graph(y_pred, model_name, stage)
	create_cumm_accuracy_graph(y_pred, y_test, model_name, stage)
	create_rolling_accuracy_graph(y_pred, y_test, model_name, stage)

	print("Finished model evaluation")


def lr_train_final_model(model, matches):
    model = joblib.load(model)
    scaler = joblib.load("lr_model_data/standard_lr_scaler.pkl")
    matches = np.array(matches, dtype=object)

    features = [
    'tournament_type', 'best_of', 'ranking_diff', 'hth_wins_diff',
    'rating_diff', 'KDA_diff', 'KAST_diff', 'ADR_diff'
    ]
    
    X = matches[:, :-2].astype(float)
    y = matches[:, -2].astype(int)

    X_scaled = scaler.transform(X)

    model.fit(X_scaled, y)

    coefficients = model.coef_[0]
    feature_weights = pd.DataFrame({
    'Feature': features,
    'Weight': coefficients
    })

    print("Weights")
    print(feature_weights)

    final_model_path = Path(__file__).resolve().parent / f"lr_model_data/lr_final_classifier_{getDateStamp()}.pkl"
    save_object(model, final_model_path)