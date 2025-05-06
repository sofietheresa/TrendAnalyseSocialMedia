from pathlib import Path
import pandas as pd
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from transformers import pipeline

# === Datei laden ===

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data/processed"
DATA_PATH = DATA_DIR / "cleaned_social_media_data.csv"


df = pd.read_csv(DATA_PATH)

# === Textquelle vorbereiten ===
df["text"] = df["title"].fillna("") + " " + df["description/text"].fillna("")
texts = df["text"].tolist()

# === Modell vorbereiten ===
model_name = "cardiffnlp/twitter-roberta-base-sentiment"  # gut für kurze Social-Media-Texte
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)

# === Sentiment-Pipeline definieren ===
sentiment_pipeline = pipeline("sentiment-analysis", model=model, tokenizer=tokenizer)

# === Sentiment berechnen ===
sentiments = []
batch_size = 32

for i in range(0, len(texts), batch_size):
    batch = texts[i:i + batch_size]
    try:
        results = sentiment_pipeline(batch, truncation=True)
        sentiments.extend(results)
    except Exception as e:
        print(f"Fehler bei Batch {i}: {e}")
        sentiments.extend([{"label": "ERROR", "score": 0.0}] * len(batch))

# === Ergebnisse integrieren ===
df["sentiment_label"] = [s["label"] for s in sentiments]
df["sentiment_score"] = [s["score"] for s in sentiments]

# === Ergebnis speichern ===
OUTPUT_PATH = DATA_DIR / "sentiment_annotated_data.csv"
df.to_csv(OUTPUT_PATH, index=False)

print(f"Datei gespeichert unter: {OUTPUT_PATH}")
