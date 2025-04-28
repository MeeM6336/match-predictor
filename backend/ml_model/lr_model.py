import joblib
import json
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from pathlib import Path
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import confusion_matrix, accuracy_score, f1_score, precision_score, recall_score, log_loss, roc_auc_score
from ml_util import getDateStamp, save_object

def lr_train_model(matches):
    print("Beginning model training...")
    matches = np.array(matches, dtype=object)
    
    X = matches[:, :-1].astype(float)
    y = matches[:, -1].astype(int)

    X_trainval, X_test, y_trainval, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model_path = Path(__file__).resolve().parent / f"lr_model_data/test_data_{getDateStamp()}.npz"

    np.savez(model_path, X_test=X_test, y_test=y_test)

    # Grid search
    param_grid = {'penalty': ['l1', 'l2'], 'C': [0.01, 0.1, 1, 10]}
    model = LogisticRegression(solver='liblinear', max_iter=1000)
    grid_search = GridSearchCV(model, param_grid, cv=5, scoring='f1', n_jobs=-1)
    grid_search.fit(X_trainval, y_trainval)

    lr_classifier_path = Path(__file__).resolve().parent / f"lr_model_data/lr_classifier_{getDateStamp()}.pkl"
    save_object(grid_search.best_estimator_, lr_classifier_path)


def evaluate_model(model, test_data):
    model = joblib.load(model)
    data = np.load(test_data)
    X_test, y_test = data['X_test'], data['y_test']

    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    cm = confusion_matrix(y_test, y_pred).tolist()
    loss = log_loss(y_test, y_prob)
    roc_auc = roc_auc_score(y_test, y_pred)

    results = {
        "accuracy": acc,
        "precision": prec,
        "recall": recall,
        "f1_score": f1,
        "confusion_matrix": cm,
        "log loss": loss,
        "ROC AUC": roc_auc
    }

    metrics_path = Path(__file__).resolve().parent / f"lr_model_data/lr_metrics_{getDateStamp()}.json"
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    with open(metrics_path, "w") as f:
        json.dump(results, f, indent=4)

def lr_train_final_model(model, matches):
    model = joblib.load(model)
    matches = np.array(matches, dtype=object)
    
    X = matches[:, :-1].astype(float)
    y = matches[:, -1].astype(int)

    model.fit(X, y)

    final_model_path = Path(__file__).resolve().parent / f"lr_model_data/lr_final_classifier_{getDateStamp()}.pkl"
    save_object(model, final_model_path)