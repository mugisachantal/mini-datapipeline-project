import os  
import pandas as pd
from sqlalchemy import create_engine, text
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import sys

sys.path.insert(0, "scripts")
from cofig import CONN_STRING # Ensure this is in your config.py

OUT = "reports"
os.makedirs(OUT, exist_ok=True)

print("1. Fetching a random sample of 100,000 patent abstracts...")
engine = create_engine(CONN_STRING)
query = """
    SELECT p.year, p.patent_id, pa.abstract 
    FROM patent_abstracts pa
    JOIN patents p ON pa.patent_id = p.patent_id
    WHERE pa.abstract IS NOT NULL
    ORDER BY RANDOM() 
    LIMIT 100000;
"""
with engine.connect() as conn:
    df = pd.read_sql_query(text(query), conn)

print("2. Vectorizing text (TF-IDF)... this may take a minute.")
# Stop words remove common words like 'the', 'is', 'method', 'apparatus'
vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
X = vectorizer.fit_transform(df['abstract'])

print("3. Running K-Means Clustering (K=5)...")
# Let's assume 5 major technology groups for now
num_clusters = 5
kmeans = KMeans(n_clusters=num_clusters, random_state=42, n_init=10)
df['cluster'] = kmeans.fit_predict(X)

print("4. Identifying Cluster Labels based on Top Terms...")
order_centroids = kmeans.cluster_centers_.argsort()[:, ::-1]
terms = vectorizer.get_feature_names_out()

cluster_summary = []
for i in range(num_clusters):
    top_terms = [terms[ind] for ind in order_centroids[i, :7]]
    term_string = ", ".join(top_terms)
    print(f"Cluster {i}: {term_string}")
    
    # We assign a temporary label, you can adjust these manually later based on the terms
    cluster_summary.append({
        "cluster_id": i,
        "top_terms": term_string,
        "patent_count": len(df[df['cluster'] == i])
    })

# Save cluster definitions
summary_df = pd.DataFrame(cluster_summary)
summary_df.to_csv(f"{OUT}/cluster_summary.csv", index=False)

# Save the trend of these clusters over time
cluster_trends = df.groupby(['year', 'cluster']).size().reset_index(name='count')
cluster_trends.to_csv(f"{OUT}/cluster_trends.csv", index=False)

print(f"✓ Clustering complete! Results saved to {OUT}/")