import pandas as pd
from pathlib import Path

clean_dir = Path("../data/clean")

def verify_file(file_name, id_column):
    file_path = clean_dir / file_name
    if not file_path.exists():
        print(f"File not found: {file_name}")
        return

    print(f"--- Checking {file_name} ---")
    # Read ONLY the ID column to save memory, but read the WHOLE file
    df = pd.read_csv(file_path, usecols=[id_column], dtype=str)
    
    dup_count = df[id_column].duplicated().sum()
    if dup_count > 0:
        print(f"❌ FOUND {dup_count} DUPLICATE IDs!")
        # Show an example of a duplicate
        print(f"Example duplicate: {df[df[id_column].duplicated()][id_column].iloc[0]}")
    else:
        print(f"✅ No duplicate IDs found in {id_column}.")
# 2. Junction/Link Tables (Composite ID check)
# These don't have one single ID, they have PAIRS that must be unique.
def verify_links(file_name, col1, col2):
    file_path = clean_dir / file_name
    if not file_path.exists(): return
    
    print(f"--- Checking Link Table: {file_name} ---")
    df = pd.read_csv(file_path, usecols=[col1, col2], dtype=str)
    dup_count = df.duplicated().sum()
    
    if dup_count > 0:
        print(f"❌ FOUND {dup_count} DUPLICATE PAIRS!")
    else:
        print(f"✅ All links are unique.")
# Run the check on the problem tables
verify_file("clean_applications.csv", "application_id")
verify_file("clean_inventors.csv", "inventor_id")
verify_file("clean_locations.csv", "location_id")
verify_file("clean_patents.csv", "patent_id")
verify_file("clean_patent_abstracts.csv", "patent_id")
verify_file("clean_applications.csv", "application_id")
verify_file("clean_inventors.csv", "inventor_id")
verify_file("clean_companies.csv", "company_id")


verify_links("clean_patent_inventor.csv", "patent_id", "inventor_id")
verify_links("clean_patent_assignee.csv", "patent_id", "company_id")