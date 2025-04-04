import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.model_selection import cross_val_score
from sklearn.datasets import load_breast_cancer

def logisticRegressionClassifier(matches):
    matches = np.array(matches)
    
    X = matches[:, :-1]
    y = matches[:, -1]

    model = LogisticRegression(penalty='l2', max_iter=2000)
    scores = cross_val_score(model, X, y, cv=5)
    print(f"Average accuracy: {scores.mean():.2f} (±{scores.std():.2f})")