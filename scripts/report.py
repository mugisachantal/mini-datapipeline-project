import sys, os, json
import psycopg2
import psycopg2.extras
import pandas as pd
sys.path.insert(0, "scripts")
from cofig import get_conn # Fixed typo from 'cofig'

OUT = "reports"
os.makedirs(OUT, exist_ok=True)
conn = get_conn()

# ─── Helper: run query → pandas DataFrame ─────────────────────────────────────
def query_df(sql, limit=None):
    if limit:
        sql = sql.rstrip(";") + f" LIMIT {limit}"
    # Use the optimized work_mem for these heavy joins
    with conn.cursor() as cur:
        cur.execute("SET work_mem = '256MB';")
    return pd.read_sql_query(sql, conn)

# ─── Load results ──────────────────────────────────────────────────────────────

# Joined with locations to get 'disambig_country'
top_inventors = query_df("""
    SELECT inv.name, loc.disambig_country AS country, COUNT(pi.patent_id) AS patents
    FROM inventors inv 
    JOIN patent_inventor pi ON inv.inventor_id = pi.inventor_id
    LEFT JOIN locations loc ON inv.location_id = loc.location_id
    GROUP BY inv.inventor_id, inv.name, loc.disambig_country
    ORDER BY patents DESC LIMIT 20
""")

top_companies = query_df("""
    SELECT c.name, COUNT(pa.patent_id) AS patents
    FROM companies c 
    JOIN patent_assignee pa ON c.company_id = pa.company_id
    GROUP BY c.company_id, c.name 
    ORDER BY patents DESC LIMIT 20
""")

# Joined with locations and filtered 'Unknown' from disambig_country
top_countries = query_df("""
    SELECT loc.disambig_country AS country,
           COUNT(pi.patent_id) AS patents,
           ROUND(COUNT(pi.patent_id)*100.0/SUM(COUNT(pi.patent_id)) OVER(), 2) AS share_pct
    FROM inventors inv 
    JOIN patent_inventor pi ON inv.inventor_id = pi.inventor_id
    JOIN locations loc ON inv.location_id = loc.location_id
    WHERE loc.disambig_country NOT IN ('Unknown', '', 'NULL')
    GROUP BY loc.disambig_country 
    ORDER BY patents DESC LIMIT 20
""")

year_trends = query_df("""
    SELECT year, COUNT(*) AS patents_filed
    FROM patents 
    WHERE year BETWEEN 1976 AND 2024
    GROUP BY year 
    ORDER BY year
""")

total_patents = pd.read_sql_query("SELECT COUNT(*) AS n FROM patents", conn).iloc[0]["n"]
conn.close()

# ─── Console Report & Exports (Logic remains the same, using updated columns) ──
W = 60
print("\n" + "═"*W)
print("       GLOBAL PATENT INTELLIGENCE REPORT")
print("═"*W)
print(f"\n  Total Patents in Database : {total_patents:>12,}")
print(f"  Unique Inventors Scoped   : {len(top_inventors):>12,}")

print("\n  ── TOP 10 INVENTORS ──────────────────────")
for i, r in top_inventors.head(10).iterrows():
    print(f"  {i+1:>2}. {str(r['name']):<28} {str(r['country'])[:5]:<5} {r['patents']:>7,}")

print("\n  ── TOP 10 COMPANIES ──────────────────────")
for i, r in top_companies.head(10).iterrows():
    print(f"  {i+1:>2}. {str(r['name']):<32}  {r['patents']:>7,}")

print("\n  ── TOP 10 COUNTRIES ──────────────────────")
for i, r in top_countries.head(10).iterrows():
    print(f"  {i+1:>2}. {str(r['country']):<8} {r['patents']:>9,}  ({r['share_pct']}%)")

print("\n  ── PATENT TRENDS (last 15 years) ─────────")
if not year_trends.empty:
    max_p = year_trends["patents_filed"].max()
    for _, r in year_trends.tail(15).iterrows():
        bar_len = int(r["patents_filed"] / max_p * 30) if max_p > 0 else 0
        print(f"  {int(r['year'])} │ {'█'*bar_len:<30} {r['patents_filed']:>8,}")

# Save CSVs
top_inventors.to_csv(f"{OUT}/top_inventors.csv",   index=False)
top_companies.to_csv(f"{OUT}/top_companies.csv",   index=False)
top_countries.to_csv(f"{OUT}/country_trends.csv",  index=False)
year_trends.to_csv(f"{OUT}/year_trends.csv",       index=False)

# Save JSON
report_data = {
    "total_patents": int(total_patents),
    "top_inventors": top_inventors.head(10).to_dict(orient="records"),
    "top_companies": top_companies.head(10).to_dict(orient="records"),
    "top_countries": top_countries.head(10).to_dict(orient="records"),
    "year_trends": year_trends.to_dict(orient="records"),
}
with open(f"{OUT}/patent_report.json", "w") as f:
    json.dump(report_data, f, indent=2, default=str)

print(f"\n✓ Reports generated successfully in /{OUT}")