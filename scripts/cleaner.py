from pathlib import Path

import pandas as pd
from tqdm import tqdm

RAW = Path("../data/raw")
CLEAN = Path("../data/clean")
CLEAN.mkdir(parents=True, exist_ok=True)

CHUNK = 100_000

# Expected headers for non-zip source files.
SOURCE_HEADERS = {
    "g_application.tsv": [
        "application_id",
        "patent_id",
        "patent_application_type",
        "filing_date",
        "series_code",
        "rule_47_flag",
    ],
    "g_assignee_disambiguated.tsv": [
        "patent_id",
        "assignee_sequence",
        "assignee_id",
        "disambig_assignee_individual_name_first",
        "disambig_assignee_individual_name_last",
        "disambig_assignee_organization",
        "assignee_type",
        "location_id",
    ],
    "g_examiner_not_disambiguated.tsv": [
        "patent_id",
        "raw_examiner_name_first",
        "raw_examiner_name_last",
        "examiner_role",
        "art_group",
    ],
    "g_inventor_disambiguated.tsv": [
        "patent_id",
        "inventor_sequence",
        "inventor_id",
        "disambig_inventor_name_first",
        "disambig_inventor_name_last",
        "gender_code",
        "location_id",
    ],
    "g_location_disambiguated.tsv": [
        "location_id",
        "disambig_city",
        "disambig_state",
        "disambig_country",
        "latitude",
        "longitude",
        "county",
        "state_fips",
        "county_fips",
    ],
    "g_patent.tsv": [
        "patent_id",
        "patent_type",
        "patent_date",
        "patent_title",
        "wipo_kind",
        "num_claims",
        "withdrawn",
        "filename",
    ],
    "g_patent_abstract.tsv": ["patent_id", "patent_abstract"],
}


def reset_output(file_name):
    out_path = CLEAN / file_name
    if out_path.exists():
        out_path.unlink()
    return out_path


def validate_source_header(file_name, expected_columns):
    file_path = RAW / file_name
    if not file_path.exists():
        raise FileNotFoundError(f"Missing source file: {file_path}")

    actual_columns = pd.read_csv(file_path, sep="\t", nrows=0, low_memory=False).columns.tolist()
    missing = [col for col in expected_columns if col not in actual_columns]
    if missing:
        raise ValueError(
            f"Header mismatch in {file_name}. Missing columns: {missing}. "
            f"Actual columns: {actual_columns}"
        )

    return file_path


def get_chunk_reader(file_name):
    expected_columns = SOURCE_HEADERS[file_name]
    file_path = validate_source_header(file_name, expected_columns)
    return pd.read_csv(
        file_path,
        sep="\t",
        usecols=expected_columns,
        chunksize=CHUNK,
        low_memory=False,
        on_bad_lines="skip",
    )


def clean_patents():
    print("[1/7] Cleaning patents...")
    out_path = reset_output("clean_patents.csv")
    total_rows = 0
    header_written = False
    seen_patent_ids = set()
    reader = get_chunk_reader("g_patent.tsv")
    for chunk in tqdm(reader, desc="patents"):
        chunk = chunk.rename(columns={"patent_title": "title", "patent_date": "filing_date"})
        chunk = chunk.dropna(subset=["patent_id"])
        chunk = chunk.drop_duplicates(subset=["patent_id"])
        chunk = chunk[~chunk["patent_id"].isin(seen_patent_ids)]
        seen_patent_ids.update(chunk["patent_id"].tolist())

        chunk["title"] = chunk["title"].fillna("").str.strip()
        chunk["filing_date"] = pd.to_datetime(chunk["filing_date"], errors="coerce")
        chunk["year"] = chunk["filing_date"].dt.year.astype("Int64")
        chunk["filing_date"] = chunk["filing_date"].dt.strftime("%Y-%m-%d")
        chunk["num_claims"] = pd.to_numeric(chunk["num_claims"], errors="coerce").astype("Int64")

        output = chunk[
            [
                "patent_id",
                "title",
                "patent_type",
                "wipo_kind",
                "num_claims",
                "withdrawn",
                "filename",
                "filing_date",
                "year",
            ]
        ]
        output.to_csv(out_path, mode="a", index=False, header=not header_written)
        header_written = True
        total_rows += len(output)

    print(f"  Patents: {total_rows:,} rows")


def clean_patent_abstracts():
    print("[2/7] Cleaning patent abstracts...")
    out_path = reset_output("clean_patent_abstracts.csv")
    total_rows = 0
    header_written = False
    seen_abstract_ids = set()

    reader = get_chunk_reader("g_patent_abstract.tsv")
    for chunk in tqdm(reader, desc="patent_abstracts"):
        chunk = chunk.rename(columns={"patent_abstract": "abstract"})
        chunk = chunk.dropna(subset=["patent_id"])
        chunk["abstract"] = chunk["abstract"].fillna("").str.strip()

        # Deduplicate
        chunk = chunk.drop_duplicates(subset=["patent_id"])
        chunk = chunk[~chunk["patent_id"].isin(seen_abstract_ids)]
        seen_abstract_ids.update(chunk["patent_id"].tolist())

        output = chunk[["patent_id", "abstract"]]
        output.to_csv(out_path, mode="a", index=False, header=not header_written)
        header_written = True
        total_rows += len(output)

    print(f"  Patent abstracts: {total_rows:,} rows")


def clean_applications():
    print("[3/7] Cleaning applications...")
    out_path = reset_output("clean_applications.csv")
    total_rows = 0
    header_written = False
    seen_application_ids = set()

    reader = get_chunk_reader("g_application.tsv")
    for chunk in tqdm(reader, desc="applications"):
        # CRITICAL: Force ID to string immediately to prevent type mismatch (int vs str)
        chunk["application_id"] = chunk["application_id"].astype(str).str.strip()
        
        chunk = chunk.dropna(subset=["application_id", "patent_id"])
        
        # 2. DROP DUPLICATES within this chunk
        chunk = chunk.drop_duplicates(subset=["application_id"])
        
        # 3. DROP DUPLICATES that appeared in previous chunks
        chunk = chunk[~chunk["application_id"].isin(seen_application_ids)]
        
        # Update our tracker
        seen_application_ids.update(chunk["application_id"].tolist())

        # Date cleaning logic
        chunk["filing_date"] = pd.to_datetime(chunk["filing_date"], errors="coerce")
        chunk["filing_year"] = chunk["filing_date"].dt.year.astype("Int64")
        chunk["filing_date"] = chunk["filing_date"].dt.strftime("%Y-%m-%d")

        output = chunk[[
            "application_id", "patent_id", "patent_application_type", 
            "filing_date", "filing_year", "series_code", "rule_47_flag"
        ]]
        
        output.to_csv(out_path, mode="a", index=False, header=not header_written)
        header_written = True
        total_rows += len(output)

    # --- THE INSURANCE POLICY (Post-Clean Check) ---
    print("  Verifying final file for duplicates...")
    # We only load the ID column to save memory
    final_check = pd.read_csv(out_path, usecols=["application_id"], dtype=str)
    dup_count = final_check["application_id"].duplicated().sum()

    while dup_count > 0:
        
            print(f"  ⚠️ Found {dup_count} sneaky duplicates. Commencing manual purge...")
            # Load the whole file, drop duplicates, and overwrite
            full_df = pd.read_csv(out_path, dtype=str)
            full_df = full_df.drop_duplicates(subset=["application_id"], keep="first")
            full_df.to_csv(out_path, index=False)
            total_rows = len(full_df)
            print(f"  ✅ Cleanup successful. Final count: {total_rows:,} rows.")
       

    print(f"  Applications: {total_rows:,} rows")


def clean_examiners():
    print("[4/7] Cleaning examiners...")
    out_path = reset_output("clean_examiners.csv")
    total_rows = 0
    header_written = False
    
    reader = get_chunk_reader("g_examiner_not_disambiguated.tsv")
    for chunk in tqdm(reader, desc="examiners"):
        chunk = chunk.dropna(subset=["patent_id"])
        chunk["examiner_name"] = (
            chunk["raw_examiner_name_first"].fillna("").str.strip()
            + " "
            + chunk["raw_examiner_name_last"].fillna("").str.strip()
        ).str.strip()

        output = chunk[["patent_id", "examiner_name", "examiner_role", "art_group"]]
        output.to_csv(out_path, mode="a", index=False, header=not header_written)
        header_written = True
        total_rows += len(output)

    print(f"  Examiners: {total_rows:,} rows")


def clean_locations():
    print("[5/7] Cleaning locations...")
    out_path = reset_output("clean_locations.csv")
    total_rows = 0
    header_written = False
    seen_location_ids = set()
    reader = get_chunk_reader("g_location_disambiguated.tsv")
    for chunk in tqdm(reader, desc="locations"):
        chunk = chunk.dropna(subset=["location_id"])
        # Deduplicate
        
        chunk = chunk.drop_duplicates(subset=["location_id"])
        chunk = chunk[~chunk["location_id"].isin(seen_location_ids)]
        seen_location_ids.update(chunk["location_id"].tolist())
        
        chunk["latitude"] = pd.to_numeric(chunk["latitude"], errors="coerce")
        chunk["longitude"] = pd.to_numeric(chunk["longitude"], errors="coerce")

        output = chunk[
            [
                "location_id",
                "disambig_city",
                "disambig_state",
                "disambig_country",
                "latitude",
                "longitude",
                "county",
                "state_fips",
                "county_fips",
            ]
        ]
        output.to_csv(out_path, mode="a", index=False, header=not header_written)
        header_written = True
        total_rows += len(output)

    print(f"  Locations: {total_rows:,} rows")


def clean_inventors_and_links():
    print("[6/7] Cleaning inventors and patent-inventor links...")
    inv_path = reset_output("clean_inventors.csv")
    links_path = reset_output("clean_patent_inventor.csv")

    inv_header_written = False
    links_header_written = False
    seen_inv_ids = set()

    reader = get_chunk_reader("g_inventor_disambiguated.tsv")
    for chunk in tqdm(reader, desc="inventors"):
        # Force IDs to string to prevent int/str mismatch
        chunk["inventor_id"] = chunk["inventor_id"].astype(str).str.strip()
        chunk["patent_id"] = chunk["patent_id"].astype(str).str.strip()

        # Name Logic
        chunk["name"] = (
            chunk["disambig_inventor_name_first"].fillna("").str.strip()
            + " "
            + chunk["disambig_inventor_name_last"].fillna("").str.strip()
        ).str.strip()
         
        # --- PROCESS INVENTORS ---
        inventors = chunk[["inventor_id", "name", "gender_code", "location_id"]].copy()
        inventors = inventors.dropna(subset=["inventor_id"])
        
        # Deduplicate inside this chunk first
        inventors = inventors.drop_duplicates(subset=["inventor_id"])
        # Filter against what we've already written
        inventors = inventors[~inventors["inventor_id"].isin(seen_inv_ids)]
        
        seen_inv_ids.update(inventors["inventor_id"].tolist())
        inventors.to_csv(inv_path, mode="a", index=False, header=not inv_header_written)
        inv_header_written = True

        # --- PROCESS LINKS (Junction Table) ---
        links = chunk[["patent_id", "inventor_id"]].dropna().drop_duplicates()
        links.to_csv(links_path, mode="a", index=False, header=not links_header_written)
        links_header_written = True

    # --- THE INSURANCE POLICY (Manual Purge) ---
    print("  Commencing post-clean purge for Inventors & Links...")
    
    # 1. Purge Inventors
    inv_df = pd.read_csv(inv_path, dtype=str)
    inv_df = inv_df.drop_duplicates(subset=["inventor_id"])
    inv_df.to_csv(inv_path, index=False)
    
    # 2. Purge Links (Check for duplicate PAIRS)
    link_df = pd.read_csv(links_path, dtype=str)
    link_df = link_df.drop_duplicates(subset=["patent_id", "inventor_id"])
    link_df.to_csv(links_path, index=False)

    print(f"  ✓ Cleanup complete. Final Inventors: {len(inv_df):,}")
    print(f"  ✓ Cleanup complete. Final Links: {len(link_df):,}")

def clean_companies_and_links():
    print("[7/7] Cleaning companies and patent-assignee links...")
    comp_path = reset_output("clean_companies.csv")
    links_path = reset_output("clean_patent_assignee.csv")

    comp_header_written = False
    links_header_written = False
    seen_comp_ids = set()

    reader = get_chunk_reader("g_assignee_disambiguated.tsv")
    for chunk in tqdm(reader, desc="assignees"):
        # Standardize IDs
        chunk["assignee_id"] = chunk["assignee_id"].astype(str).str.strip()
        chunk["patent_id"] = chunk["patent_id"].astype(str).str.strip()

        # Name Logic
        org = chunk["disambig_assignee_organization"].fillna("").str.strip()
        indiv = (chunk["disambig_assignee_individual_name_first"].fillna("") + " " + 
                 chunk["disambig_assignee_individual_name_last"].fillna("")).str.strip()
        chunk["name"] = org.where(org != "", indiv).replace("", "Unknown")

        # --- PROCESS COMPANIES ---
        companies = chunk[["assignee_id", "name", "assignee_type", "location_id"]].copy()
        companies = companies.rename(columns={"assignee_id": "company_id"})
        companies = companies.dropna(subset=["company_id"])
        
        # 1. Deduplicate within chunk
        companies = companies.drop_duplicates(subset=["company_id"])
        # 2. Filter against global set
        companies = companies[~companies["company_id"].isin(seen_comp_ids)]
        
        seen_comp_ids.update(companies["company_id"].tolist())
        companies.to_csv(comp_path, mode="a", index=False, header=not comp_header_written)
        comp_header_written = True

        # --- PROCESS LINKS ---
        links = chunk[["patent_id", "assignee_id"]].dropna().drop_duplicates()
        links = links.rename(columns={"assignee_id": "company_id"})
        links.to_csv(links_path, mode="a", index=False, header=not links_header_written)
        links_header_written = True

    # --- THE INSURANCE POLICY ---
    print("  Commencing post-clean purge for Companies & Links...")
    
    # 1. Purge Companies
    comp_df = pd.read_csv(comp_path, dtype=str)
    comp_df = comp_df.drop_duplicates(subset=["company_id"])
    comp_df.to_csv(comp_path, index=False)
    
    # 2. Purge Links (Check for duplicate PAIRS)
    link_df = pd.read_csv(links_path, dtype=str)
    link_df = link_df.drop_duplicates(subset=["patent_id", "company_id"])
    link_df.to_csv(links_path, index=False)

    print(f"  ✓ Cleanup complete. Final Companies: {len(comp_df):,}")
    print(f"  ✓ Cleanup complete. Final Links: {len(link_df):,}")

if __name__ == "__main__":
    print("Using only .tsv files from data/raw (zip files are ignored).")
   # clean_patents()
    #clean_patent_abstracts()
    #clean_applications()
    #clean_examiners()
    #clean_locations()
    clean_inventors_and_links()
    clean_companies_and_links()
    print("\nAll clean CSVs written to data/clean/")