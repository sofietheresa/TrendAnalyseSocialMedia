from pathlib import Path
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer

# Pfad zur Datei (kann für Container oder lokal angepasst werden)
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data/processed"
data_path = DATA_DIR / "cleaned_social_media_data.csv"


# === Daten einlesen ===
df = pd.read_csv(data_path)

# === Kombiniere Titel und Beschreibung/Text ===
df["text_for_embedding"] = df["title"].fillna("") + " " + df["description/text"].fillna("")

# === Embedding-Modell laden ===
model = SentenceTransformer("paraphrase-MiniLM-L6-v2")

# === Embeddings berechnen ===
embeddings = model.encode(df["text_for_embedding"].tolist(), show_progress_bar=True)

# === Ergebnisse als DataFrame speichern ===
embedding_df = pd.DataFrame(embeddings)
embedding_df["source"] = df["source"]
embedding_df["created_date"] = df["created date"]
embedding_df["text"] = df["text_for_embedding"]

# Optional: Speichern für spätere Analyse
embedding_df.to_csv(DATA_DIR /"text_embeddings.csv", index=False)
