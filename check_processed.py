import pandas as pd
import os

def compare_texts(df, text_cols):
    """Compare original and processed text columns"""
    for col in text_cols:
        orig_col = col
        proc_col = f"{col}_processed" if f"{col}_processed" in df.columns else None
        
        if proc_col:
            print(f"\n=== Comparing {orig_col} ===")
            sample = df[df[orig_col].notna()].head(2)
            for idx, row in sample.iterrows():
                print(f"\nOriginal: {row[orig_col]}")
                print(f"Processed: {row[proc_col]}")

# Load the processed files
processed_dir = "data/processed"

# TikTok
print("\n=== TIKTOK ===")
df_tiktok = pd.read_csv(os.path.join(processed_dir, "tiktok_processed.csv"))
compare_texts(df_tiktok, ["description"])

# YouTube
print("\n=== YOUTUBE ===")
df_youtube = pd.read_csv(os.path.join(processed_dir, "youtube_processed.csv"))
compare_texts(df_youtube, ["title", "description"])

# Reddit
print("\n=== REDDIT ===")
df_reddit = pd.read_csv(os.path.join(processed_dir, "reddit_processed.csv"))
compare_texts(df_reddit, ["title", "text"]) 