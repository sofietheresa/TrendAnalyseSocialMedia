import os
import psycopg2
from urllib.parse import urlparse

def list_tables():
    url = os.getenv("DATABASE_URL")
    if not url:
        raise ValueError("DATABASE_URL environment variable not set")
    
    try:
        conn = psycopg2.connect(url)  # Connect directly to the railway database
        cur = conn.cursor()
        
        # Get all tables
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        
        print("\nTables in railway database:")
        print("-" * 40)
        for table in cur.fetchall():
            print(table[0])
            
            # Get row count for each table
            cur.execute(f"SELECT COUNT(*) FROM {table[0]}")
            count = cur.fetchone()[0]
            print(f"Number of rows: {count}\n")
            
            # Get table structure
            cur.execute(f"""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = '{table[0]}'
                ORDER BY ordinal_position
            """)
            print("Table structure:")
            for col in cur.fetchall():
                print(f"- {col[0]}: {col[1]}")
            print("-" * 40 + "\n")
            
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    list_tables() 