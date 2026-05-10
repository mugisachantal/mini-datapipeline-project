import os
import sys
import psycopg2
from pathlib import Path

# Add scripts to path to import config
sys.path.insert(0, "scripts")
try:
    
    from cofig import get_conn

except ImportError:
    print("Error: config.py not found. Ensure it is in the 'scripts' folder.")
    sys.exit(1)

CLEAN = Path("../data/clean")

def copy_csv(conn, csv_path, table, columns):
    """
    Uses copy_expert to stream CSV data into PostgreSQL.
    This bypasses filesystem permission issues.
    """
    if not csv_path.exists():
        print(f"  × Skipping {table}: {csv_path.name} not found")
        return

    cols = ", ".join(columns)
    sql = f"COPY {table} ({cols}) FROM STDIN WITH (FORMAT csv, HEADER true, NULL '')"
    
    print(f"  COPY {table} ← {csv_path.name}")
    with open(csv_path, 'r', encoding='utf-8') as f:
        with conn.cursor() as cur:
            cur.copy_expert(sql, f)
    conn.commit()
    print(f"    ✓ Load complete")

# 1. Re-initialize Schema
print("Re-initializing schema...")
conn = get_conn()
with conn, conn.cursor() as cur:
    with open("../sql/schema.sql") as f:
        cur.execute(f.read())
print("  ✓ Schema ready\n")


def apply_post_load(conn, sql_file_path):
    """
    Executes the post-load SQL script to add PKs, FKs, and Indexes.
    """
    if not sql_file_path.exists():
        print(f"  × Error: {sql_file_path.name} not found!")
        return

    print(f"\nApplying post-load constraints and indexes from {sql_file_path.name}...")
    print("  (This may take a few minutes as it validates millions of rows...)")
    
    try:
        with open(sql_file_path, 'r') as f:
            sql = f.read()
        
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
        print("  ✓ Constraints and indexes applied successfully")
    except Exception as e:
        print(f"  × Failed to apply constraints: {e}")
        conn.rollback()

# 2. Load Tables in Dependency Order
# Parent tables first, then child/junction tables
# ... (Keep your existing imports and copy_csv function)

try:
    # Locations must be first (Inventors/Companies depend on it)
    copy_csv(conn, CLEAN / "clean_locations.csv", "locations", 
             ["location_id", "disambig_city", "disambig_state", "disambig_country", "latitude", "longitude", "county", "state_fips", "county_fips"])

    # Patents must be second (Everything else depends on it)
    copy_csv(conn, CLEAN / "clean_patents.csv", "patents", 
             ["patent_id", "title", "patent_type", "wipo_kind", "num_claims", "withdrawn", "filename", "filing_date", "year"])

    # Now load the rest
    copy_csv(conn, CLEAN / "clean_patent_abstracts.csv", "patent_abstracts", ["patent_id", "abstract"])
    
    copy_csv(conn, CLEAN / "clean_applications.csv", "applications", 
             ["application_id", "patent_id", "patent_application_type", "filing_date", "filing_year", "series_code", "rule_47_flag"])

    copy_csv(conn, CLEAN / "clean_inventors.csv", "inventors", ["inventor_id", "name", "gender_code", "location_id"])
    
    copy_csv(conn, CLEAN / "clean_companies.csv", "companies", ["company_id", "name", "assignee_type", "location_id"])

    copy_csv(conn, CLEAN / "clean_patent_inventor.csv", "patent_inventor", ["patent_id", "inventor_id"])
    
    copy_csv(conn, CLEAN / "clean_patent_assignee.csv", "patent_assignee", ["patent_id", "company_id"])
    
    copy_csv(conn, CLEAN / "clean_examiners.csv", "patent_examiner", ["patent_id", "examiner_name", "examiner_role", "art_group"])
    POST_LOAD_SQL = Path("../sql/post_load.sql") # Adjust path as needed
    apply_post_load(conn, POST_LOAD_SQL)
except Exception as e:
    print(f"\n[!] Load failed: {e}")
    conn.rollback()

# 3. Verification
print("\nVerifying Data Integrity...")
conn = get_conn()
with conn.cursor() as cur:
    tables = ["locations", "patents", "inventors", "companies", "patent_inventor", "patent_assignee"]
    for t in tables:
        cur.execute(f"SELECT COUNT(*) FROM {t}")
        count = cur.fetchone()[0]
        print(f"  {t:<20} | {count:>10,} rows")
conn.close()








