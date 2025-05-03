import subprocess
import os
from datetime import datetime
from pathlib import Path
import pandas as pd
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import uuid
import logging

# 🔧 sicherstellen, dass logs-Verzeichnis vorhanden ist
Path("/app/logs").mkdir(parents=True, exist_ok=True)

# Liste der zu startenden Scraper (relativ zu scheduler/)
SCRAPER_SCRIPTS = [
    "jobs/reddit_scraper.py",
    "jobs/tiktok_scraper.py",
    "jobs/youtube_scraper.py"
]

def process_tiktok_data(csv_path):
    model = SentenceTransformer("all-MiniLM-L6-v2")
    client = QdrantClient(host="qdrant", port=6333)

    # Initialisiere Collection, falls noch nicht vorhanden
    COLLECTION_NAME = "tiktok"
    client.recreate_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=384, distance=Distance.COSINE)
    )

    # Lade die CSV-Daten
    df = pd.read_csv(csv_path)
    df["description_clean"] = (
        df["description"]
        .fillna("")
        .str.lower()
        .str.replace(r"[^\w\s]", "", regex=True)
    )

    # Embeddings erzeugen
    embeddings = model.encode(df["description_clean"].tolist(), show_progress_bar=True)

    # Punkte einfügen (mit Metadaten)
    points = []
    for idx, row in df.iterrows():
        vector = embeddings[idx]
        payload = {
            "id": row.get("id"),
            "author": row.get("author_username"),
            "likes": row.get("likes"),
            "desc": row.get("description"),
            "created": str(row.get("created_time"))
        }
        points.append(PointStruct(id=str(uuid.uuid4()), vector=vector.tolist(), payload=payload))

    client.upsert(collection_name=COLLECTION_NAME, points=points)

    logging.info(f"✅ {len(points)} Einträge in Qdrant geschrieben.")

def run_script(script):
    name = script.split("/")[-1].replace("_scraper.py", "")
    log_file = Path("/app/logs") / f"{name}.log"

    print(f"📄 Log-Datei: {log_file}")
    print(f"▶️  Starte {script} ...")

    start = datetime.now()

    # Logfile einmalig öffnen und stdout/stderr hineinschreiben
    try:
        with open(log_file, "a", encoding="utf-8") as log:
            subprocess.run(
                ["python", script],
                cwd="scheduler",
                env=os.environ.copy(),
                stdout=log,
                stderr=log,
                text=True,
                check=True
            )
        duration = (datetime.now() - start).seconds
        print(f"✅  {script} erfolgreich in {duration} Sekunden.")

    except subprocess.CalledProcessError:
        print(f"❌ Fehler beim Ausführen von {script} (siehe {log_file})")

def run_all():
    for script in SCRAPER_SCRIPTS:
        run_script(script)

if __name__ == "__main__":
    run_all()
