import sys
from pathlib import Path

# Dynamisch das Wurzelverzeichnis zum Modulpfad hinzufügen
project_root = Path(__file__).resolve().parents[2]  # Gehe 2 Ebenen nach oben (bis zu Projektwurzel)
sys.path.append(str(project_root / "src"))

import pandas as pd
from pathlib import Path
import logging
from scripts.deduplication import compute_row_hash, skip_already_processed
from scripts.sentiment_analysis import analyze_sentiment
from scripts.topic_modeling import generate_topics
from scripts.utils import preprocess_text, extract_text_features, normalize_metrics
from scripts.utils import detect_language

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PLATFORMS = ["tiktok", "youtube", "reddit"]
TEXT_COLUMNS = {
    "tiktok": ["description"],
    "youtube": ["title", "description"],
    "reddit": ["title", "text"]
}
NUMERIC_COLUMNS = {
    "tiktok": ["likes", "shares", "comments", "plays"],
    "youtube": ["view_count", "like_count", "comment_count"],
    "reddit": ["score", "comments"]
}

def apply_processing(df, text_cols):
    df = df.copy()
    for col in text_cols:
        df[col] = df[col].fillna("").astype(str).str.strip()
        df[f"{col}_language"] = df[col].apply(detect_language)
        df = df[df[f"{col}_language"].isin(["en", "de"])]  # Nur gewollte Sprachen behalten
        df[f"{col}_clean"] = df[col].apply(lambda x: preprocess_text(x, remove_stopwords=True))
        features = df[f"{col}_clean"].apply(extract_text_features)
        feature_df = pd.DataFrame(features.tolist())
        feature_df.columns = [f"{col}_{c}" for c in feature_df.columns]
        df = pd.concat([df, feature_df], axis=1)

        # Sentiment
        df[[f"{col}_sentiment", f"{col}_sentiment_score"]] = df[f"{col}_clean"].apply(
            lambda x: pd.Series(analyze_sentiment(x))
        )
    return df

def main():
    base_dir = Path(__file__).resolve().parents[2] 
    raw_dir = base_dir / "data/raw"
    processed_dir = base_dir / "data/processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    for platform in PLATFORMS:
        input_path = raw_dir / f"{platform}_data.csv"
        output_path = processed_dir / f"{platform}_processed.csv"

        logger.info(f"Processing {platform} data...")
        df = pd.read_csv(input_path)

        # Deduplication
        df['hash'] = df.apply(compute_row_hash, axis=1)
        df = skip_already_processed(df, output_path)
        if df.empty:
            logger.info(f"No new {platform} data to process.")
            continue

        df = apply_processing(df, TEXT_COLUMNS.get(platform, []))

        # Normalize selected metrics
        df = normalize_metrics(df, [col for col in df.columns if 'engagement' in col or 'sentiment_score' in col])

        # Topic Modeling (optional)
        try:
            topic_col = TEXT_COLUMNS[platform][0]
            df['topic'] = generate_topics(df[f"{topic_col}_clean"].tolist())
        except Exception as e:
            logger.warning(f"Topic modeling failed: {e}")

        # Append to existing processed file
        if output_path.exists():
            existing_df = pd.read_csv(output_path)
            df = pd.concat([existing_df, df], ignore_index=True)

        df.to_csv(output_path, index=False)
        logger.info(f"Saved processed {platform} data to {output_path}")

if __name__ == "__main__":
    main()
