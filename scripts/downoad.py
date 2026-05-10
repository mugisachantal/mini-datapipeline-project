import os, requests
from tqdm import tqdm
import zipfile
import glob

RAW = "data/raw"

# These are the S3 URLs — check patentsview.org if any are outdated
# Updated USPTO Open Data Portal links (April 2026)
FILES = {
    "g_application.tsv.zip": 
        "https://data.uspto.gov/bulkdata/datasets/pvgpatdis/g_application.tsv.zip",
    "g_patent.tsv.zip": 
        "https://data.uspto.gov/bulkdata/datasets/pvgpatdis/g_patent.tsv.zip",
    "g_patent_abstract.tsv.zip": 
        "https://data.uspto.gov/bulkdata/datasets/pvgpatdis/g_patent_abstract.tsv.zip",
    "g_inventor_disambiguated.tsv.zip": 
        "https://data.uspto.gov/bulkdata/datasets/pvgpatdis/g_inventor_disambiguated.tsv.zip",
    "g_location_disambiguated.tsv.zip": 
        "https://data.uspto.gov/bulkdata/datasets/pvgpatdis/g_location_disambiguated.tsv.zip",
    "g_assignee_disambiguated.tsv.zip": 
        "https://data.uspto.gov/bulkdata/datasets/pvgpatdis/g_assignee_disambiguated.tsv.zip",
}
def download(url, dest):
    if os.path.exists(dest):
        print(f"  skip (exists): {dest}"); return
    r = requests.get(url, stream=True,allow_redirects=True)
    total = int(r.headers.get('content-length', 0))
    with open(dest, "wb") as fh, tqdm(total=total, unit="B", unit_scale=True, desc=os.path.basename(dest)) as bar:
        for chunk in r.iter_content(65536):
            fh.write(chunk); bar.update(len(chunk))

for fname, url in FILES.items():
    download(url, f"{RAW}/{fname}")


print("\nUnzipping...")
for zip_path in glob.glob(f"{RAW}/*.zip"):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(RAW)
        print(f"  Extracted: {os.path.basename(zip_path)}")