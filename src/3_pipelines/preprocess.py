import pandas as pd
from pathlib import Path
import re

def clean_text(text):
    return re.sub(r"[^\w\s]", "", str(text).lower())

def preprocess_file(input_path, output_path):
    df = pd.read_csv(input_path)
    df["description_clean"] = df["description"].apply(clean_text)
    df.to_csv(output_path, index=False)

if __name__ == "__main__":
    raw = Path("data/raw/tiktok_data.csv")
    processed = Path("data/processed/tiktok_clean.csv")
    preprocess_file(raw, processed)
