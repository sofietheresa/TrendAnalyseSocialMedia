import sqlite3
from pathlib import Path

DB_PATH = Path("data/social_media.db")

# Tabelle -> (Spalten zur Duplikaterkennung, Primärschlüssel)
TABLES = {
    "reddit_data": (["title", "text", "author", "created_utc"], "id"),
    "tiktok_data": (["description", "author_username", "created_time"], "id"),
    "youtube_data": (["title", "description", "channel_title", "published_at"], "video_id"),
}

def remove_duplicates():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for table, (cols, pk) in TABLES.items():
        # Baue SQL zur Auswahl von Duplikaten
        col_list = ", ".join(cols)
        dup_sql = f"""
            DELETE FROM {table}
            WHERE {pk} NOT IN (
                SELECT MIN({pk})
                FROM {table}
                GROUP BY {col_list}
            )
        """
        print(f"Bereinige Duplikate in '{table}' anhand von [{col_list}]...")
        cursor.execute(dup_sql)
        print(f"  → {cursor.rowcount} Duplikate gelöscht.")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    remove_duplicates()
