import pandas as pd
import json

def load_tiktok_data():
    # Einlesen der CSV-Datei
    df = pd.read_csv('data/raw/tiktok_data.csv')
    
    # Behalte nur die ersten 10 relevanten Spalten
    relevant_columns = [
        'id', 'description', 'author_username', 'author_id',
        'likes', 'shares', 'comments', 'plays', 'video_url', 'created_time'
    ]
    df = df[relevant_columns]
    
    # Spalten umbenennen für bessere Lesbarkeit
    df = df.rename(columns={
        'author_username': 'username',
        'author_id': 'user_id',
        'created_time': 'timestamp'
    })
    
    # Numerische Spalten als int konvertieren
    numeric_cols = ['likes', 'shares', 'comments', 'plays']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Entferne Zeilen, wo alle wichtigen Metriken NaN sind
    df = df.dropna(subset=['likes', 'shares', 'comments', 'plays'], how='all')
    
    return df

if __name__ == "__main__":
    # Test des Dateinladens
    df = load_tiktok_data()
    print("Dataframe Info:")
    print(df.info())
    print("\nErste 5 Zeilen:")
    print(df.head()) 