import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "patent_analysis_db")
DB_USER = os.getenv("DB_USER", "mugisa")
DB_PASS = os.getenv("DB_PASS", "mugisa")

CONN_STRING = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
def get_conn():
    try:
        return psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
            dbname=os.getenv("DB_NAME", "patent_analysis_db"),
            user=os.getenv("DB_USER", "mugisa"),
            password=os.getenv("DB_PASS", "mugisa"),
        )



    except Exception as e:
        print(f"❌ Error: Unable to connect to the database.\n{e}")
        return None
# --- TESTING THE CONNECTION ---
connection = get_conn()

if connection:
    print("✅ Connection successfully created!")
    
    # Optional: Test a simple query to be 100% sure
    cur = connection.cursor()
    cur.execute("SELECT version();")
    record = cur.fetchone()
    print(f"Connected to: {record}")
    
    # Clean up
    cur.close()
    connection.close()
else:
    print("Failed to establish connection.")