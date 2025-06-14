import pandas as pd
import json
import numpy as np
import torch
from pathlib import Path
import torch.nn as nn
import torch.optim as optim
from models.mlp import MLP
from torch.utils.data import DataLoader, TensorDataset
from sklearn.model_selection import KFold
from sklearn.metrics import accuracy_score, roc_auc_score, confusion_matrix
from ml_util import db_connect, save_object, getDateStamp, db_insert_feature_vector, insert_model_metrics, create_class_seperation_quality_plot, create_class_representation_bar_graph, create_cumm_accuracy_graph, create_rolling_accuracy_graph


def train_epoch(model, train_loader, criterion, optimizer, device):
  model.train()
  epoch_train_loss = 0
  for inputs, labels in train_loader:
      inputs, labels = inputs.to(device), labels.to(device).float().unsqueeze(1)
      optimizer.zero_grad()
      outputs = model(inputs)
      loss = criterion(outputs, labels)
      loss.backward()
      optimizer.step()
      epoch_train_loss += loss.item()
  return epoch_train_loss / len(train_loader)


def evaluate_model_on_fold(model, val_loader, criterion, device):
  model.eval()

  all_labels_fold = []
  all_probs_fold = []

  with torch.no_grad():
    epoch_val_loss = 0
    for inputs, labels_batch in val_loader:
      inputs = inputs.to(device)
      true_labels_batch = labels_batch.to(device).float().unsqueeze(1)

      outputs = model(inputs)
      probs = torch.sigmoid(outputs)

      loss = criterion(outputs, true_labels_batch)
      epoch_val_loss += loss.item()

      all_labels_fold.extend(true_labels_batch.cpu().numpy().flatten())
      all_probs_fold.extend(probs.cpu().numpy().flatten())

  calculated_loss = epoch_val_loss / len(val_loader) if len(val_loader) > 0 else float('nan')
  all_labels_np = np.array(all_labels_fold)
  all_probs_np = np.array(all_probs_fold)
  
  predictions_fold = (all_probs_np > 0.5).astype(int)

  calculated_accuracy = accuracy_score(all_labels_np, predictions_fold)
  calculated_roc_auc = roc_auc_score(all_labels_np, all_probs_np)
  cm = confusion_matrix(all_labels_np, predictions_fold)

  return calculated_accuracy, calculated_loss, calculated_roc_auc, cm


def nn_cross_validate(X, y, X_match_id):
  db = db_connect()
  cursor = db.cursor()

  X_data_tensor = torch.as_tensor(X, dtype=torch.float32)
  y_data_tensor = torch.as_tensor(y, dtype=torch.float32)

  num_folds = 5
  kf = KFold(n_splits=num_folds, shuffle=True, random_state=42)
  device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

  hyperparameters = {
    "hidden_units": [[64], [64, 128], [128], [256, 128], [256], [512, 256, 128]],
    "optimizer": ["Adam", "SGD"],
    "dropout": [0.0, 0.2, 0.4],
    "learning_rate": [0.0005, 0.001, 0.005, 0.01, 0.1],
    "batch_size": [64, 128, 256],
    "epochs": 20
  }

  all_configurations_results = []
  config_idx = 0
  total_configurations = len(hyperparameters["dropout"]) * len(hyperparameters["learning_rate"]) * len(hyperparameters["batch_size"]) * len(hyperparameters["hidden_units"]) * len(hyperparameters["optimizer"])

  print(f"\nStarting Hyperparameter Tuning with {num_folds}-Fold Cross-Validation.")

  for current_dropout_rate in hyperparameters["dropout"]:
      for current_lr in hyperparameters["learning_rate"]:
          for current_batch_size in hyperparameters["batch_size"]:
            for current_hidden_units in hyperparameters["hidden_units"]:
              for current_optimizer in hyperparameters["optimizer"]:
                config_idx += 1
                print(f"Configuration {config_idx}/{total_configurations}")
                print(f"Parameters: Dropout={current_dropout_rate}, LR={current_lr}, BatchSize={current_batch_size}, HiddenUnits={current_hidden_units}, Optimizer={current_optimizer}")

                fold_val_accuracies = []
                fold_loss = []
                fold_roc_auc = []
                fold_confusion_matrix = []

                for fold, (train_index, val_index) in enumerate(kf.split(X_data_tensor, y_data_tensor)):
                  X_train_fold, X_val_fold = X_data_tensor[train_index], X_data_tensor[val_index]
                  y_train_fold, y_val_fold = y_data_tensor[train_index], y_data_tensor[val_index]

                  train_dataset_fold = TensorDataset(X_train_fold, y_train_fold)
                  val_dataset_fold = TensorDataset(X_val_fold, y_val_fold)
                  
                  effective_train_batch_size = max(1, min(current_batch_size, len(train_dataset_fold)))
                  effective_val_batch_size = max(1, min(current_batch_size, len(val_dataset_fold)))

                  train_loader_fold = DataLoader(train_dataset_fold, batch_size=effective_train_batch_size, shuffle=True)
                  val_loader_fold = DataLoader(val_dataset_fold, batch_size=effective_val_batch_size, shuffle=False)

                  model = MLP(X_data_tensor.shape[1], current_hidden_units, 1, current_dropout_rate).to(device)
                  criterion = nn.BCEWithLogitsLoss()
                  optimizer = (optim.Adam if current_optimizer == 'Adam' else optim.SGD)(
                      model.parameters(), lr=current_lr
                  )

                  for epoch in range(hyperparameters['epochs']):
                    loss = train_epoch(model, train_loader_fold, criterion, optimizer, device)

                  val_accuracy, val_loss, val_roc_auc, cm = evaluate_model_on_fold(model, val_loader_fold, criterion, device)
                  fold_val_accuracies.append(val_accuracy)
                  fold_loss.append(val_loss)
                  fold_roc_auc.append(val_roc_auc)
                  fold_confusion_matrix.append(cm)

                avg_val_accuracy = np.nanmean(fold_val_accuracies)
                avg_val_loss = np.nanmean(fold_loss)
                avg_roc_auc = np.nanmean(fold_roc_auc)
                avg_cm = np.nanmean(np.array(fold_confusion_matrix), axis=0)

                all_configurations_results.append({
                  'params': {'dropout_rate': current_dropout_rate, 'learning_rate': current_lr, 'batch_size': current_batch_size, 'hidden_units': current_hidden_units, 'optimizer': current_optimizer},
                  'avg_val_accuracy': avg_val_accuracy,
                  'loss': avg_val_loss,
                  'ROC AUC': avg_roc_auc,
                  'confusion_matrix': avg_cm.tolist()
                })
  
  valid_results = [res for res in all_configurations_results if not np.isnan(res['avg_val_accuracy'])]

  print("\nSorting configurations by descending Accuracy, then descending F1-Score...")
  best_results_sorted = sorted(valid_results, key=lambda x: (-x['avg_val_accuracy']))

  best_config_overall = best_results_sorted[0]
  print(best_config_overall['avg_val_accuracy'])
  
  best_dropout = best_config_overall['params']['dropout_rate']
  best_lr = best_config_overall['params']['learning_rate']
  best_batch_size = best_config_overall['params']['batch_size']
  best_hidden_units = best_config_overall['params']['hidden_units']
  best_optimizer = best_config_overall['params']['optimizer']

  y_true_all = []
  y_prob_all = []

  for fold, (train_index, val_index) in enumerate(kf.split(X_data_tensor, y_data_tensor)):
    X_train_fold, X_val_fold = X_data_tensor[train_index], X_data_tensor[val_index]
    y_train_fold, y_val_fold = y_data_tensor[train_index], y_data_tensor[val_index]

    train_dataset_fold = TensorDataset(X_train_fold, y_train_fold)
    val_dataset_fold = TensorDataset(X_val_fold, y_val_fold)

    train_loader_fold = DataLoader(train_dataset_fold, batch_size=min(best_batch_size, len(train_dataset_fold)), shuffle=True)
    val_loader_fold = DataLoader(val_dataset_fold, batch_size=min(best_batch_size, len(val_dataset_fold)), shuffle=False)

    model = MLP(X_data_tensor.shape[1], best_hidden_units, 1, best_dropout).to(device)
    criterion = nn.BCEWithLogitsLoss()
    optimizer = (optim.Adam if best_optimizer == 'Adam' else optim.SGD)(
      model.parameters(), lr=best_lr
    )

    for epoch in range(hyperparameters['epochs']):
      train_epoch(model, train_loader_fold, criterion, optimizer, device)

    model.eval()
    with torch.no_grad():
      for inputs, labels in val_loader_fold:
        inputs = inputs.to(device)
        labels = labels.to(device).float().unsqueeze(1)
        outputs = model(inputs)
        probs = torch.sigmoid(outputs)

        y_true_all.extend(labels.cpu().numpy().flatten())
        y_prob_all.extend(probs.cpu().numpy().flatten())

  
  y_true_all_np = np.array(y_true_all)
  y_prob_all_np = np.array(y_prob_all)
  y_pred_all = (y_prob_all_np > 0.5).astype(int)

  try:
    create_class_seperation_quality_plot(y_true_all_np, y_prob_all_np, "neural_network", "Training")
    create_class_representation_bar_graph(y_pred_all, "neural_network", "Training")
    create_cumm_accuracy_graph(y_pred_all, y_true_all_np, "neural_network", "Training")
    create_rolling_accuracy_graph(y_pred_all, y_true_all_np, "neural_network", "Training")
  except Exception as e:
    print("Error", e)

  print("Hyperparameter Tuning Complete")
  print("Best Hyperparameter Configuration Found:")
  for param_name, param_value in best_config_overall['params'].items():
    print(f"{param_name}: {param_value}")

  try:
    insert_model_metrics(cursor, "neural_network", best_config_overall)
    db.commit()
  except Exception as e:
    print("Error inserting model metrics:", e)
    db.rollback()

  try:
    for current_id, feature_vector in zip(X_match_id, X):
      db_insert_feature_vector(cursor, current_id, "training", feature_vector, 2)

  except Exception as e:
    print("Error inserting training feature vector:", e)
    db.rollback()

  finally:
    db.commit()
    db.close()

  best_config_overall = None
  return best_config_overall, all_configurations_results


def nn_train_final_model(X, y, best_params):
  num_epochs_final_train=40
  X_tensor = torch.as_tensor(X, dtype=torch.float32)
  y_tensor = torch.as_tensor(y, dtype=torch.float32)
  device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

  output_dim = 1
  hidden_units = best_params['params']['hidden_units']
  dropout_rate = best_params['params']['dropout_rate']
  lr = best_params['params']['learning_rate']
  batch_size = best_params['params']['batch_size']
  optimizer = best_params['params']['optimizer']

  final_model = MLP(X_tensor.shape[1], hidden_units, output_dim, dropout_rate).to(device)
  criterion = nn.BCEWithLogitsLoss()
  optimizer = (optim.Adam if optimizer == 'Adam' else optim.SGD)(final_model.parameters(), lr=lr)

  full_dataset = TensorDataset(X_tensor, y_tensor)
  effective_batch_size = max(1, min(batch_size, len(full_dataset)))
  full_loader = DataLoader(full_dataset, batch_size=effective_batch_size, shuffle=True)

  for epoch in range(num_epochs_final_train):
      epoch_loss = train_epoch(final_model, full_loader, criterion, optimizer, device)

  print("Final model training complete.")
  final_model_path = Path(__file__).resolve().parent / f"nn_model_data/nn_final_classifier_{getDateStamp()}.pkl"

  save_object(final_model, final_model_path)