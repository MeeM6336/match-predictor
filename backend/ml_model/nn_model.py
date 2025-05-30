import pandas as pd
import numpy as np
import mysql.connector
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader, TensorDataset
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report, roc_auc_score, log_loss


def nn_train_model():
  print("Hello")