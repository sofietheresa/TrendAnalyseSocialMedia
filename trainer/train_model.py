import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
import joblib
import mlflow

def train():
    df = pd.read_csv("data/processed/tiktok_clean.csv")
    X = df["description_clean"]
    y = (df["likes"] > 50).astype(int)  # Beispiel: binäres Label

    from sklearn.feature_extraction.text import CountVectorizer
    X_vec = CountVectorizer().fit_transform(X)
    X_train, X_test, y_train, y_test = train_test_split(X_vec, y, test_size=0.2)

    clf = LogisticRegression()
    clf.fit(X_train, y_train)

    acc = clf.score(X_test, y_test)

    mlflow.log_metric("accuracy", acc)
    joblib.dump(clf, "models/tiktok_model.pkl")

if __name__ == "__main__":
    mlflow.set_experiment("TikTok Sentiment")
    with mlflow.start_run():
        train()
