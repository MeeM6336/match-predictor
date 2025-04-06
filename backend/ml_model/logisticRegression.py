import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.model_selection import cross_validate
from sklearn.datasets import load_breast_cancer

def logisticRegressionClassifier(matches):
    matches = np.array(matches)
    
    X = matches[:, :-1]
    y = matches[:, -1]

    model = LogisticRegression(penalty='l1', solver='liblinear', max_iter=1000)

    scoring = ['accuracy', 'f1']
    scores = cross_validate(model, X, y, cv=5, scoring=scoring, return_train_score=False, n_jobs=-1)

    avg_accuracy = np.mean(scores['test_accuracy'])
    std_accuracy = np.std(scores['test_accuracy'])
    avg_f1 = np.mean(scores['test_f1'])
    std_f1 = np.std(scores['test_f1'])

    print(f"Average accuracy: {avg_accuracy:.2f} (±{std_accuracy:.2f})")
    print(f"Average F1 score: {avg_f1:.2f} (±{std_f1:.2f})")

    model.fit(X, y)

    return model