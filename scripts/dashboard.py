import streamlit as st
import pandas as pd
import json
import plotly.express as px
import os
# --- Page Config ---
st.set_page_config(page_title="Patent Intelligence Dashboard", layout="wide")
st.title("🌐 Global Patent Intelligence Dashboard")

# --- Load Data ---
@st.cache_data
def load_data():
    # 1. Get the absolute path of the directory where dashboard.py is located
    # On Streamlit Cloud, this will be: /mount/src/mini-datapipeline-project/scripts/
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 2. Point to the 'reports' folder that is inside 'scripts'
    reports_dir = os.path.join(current_dir, "reports")
    
    report_path = os.path.join(reports_dir, "patent_report.json")
    cluster_summary_path = os.path.join(reports_dir, "cluster_summary.csv")
    cluster_trends_path = os.path.join(reports_dir, "cluster_trends.csv")

    # 3. Diagnostic check (helps if it fails again)
    if not os.path.exists(report_path):
        raise FileNotFoundError(f"Missing file at {report_path}. "
                                f"Current directory contents: {os.listdir(current_dir)}")

    # 4. Open and load
    with open(report_path, "r") as f:
        report = json.load(f)
    
    df_trends = pd.DataFrame(report["year_trends"])
    
    try:
        df_clusters = pd.read_csv(cluster_summary_path)
        df_cluster_trends = pd.read_csv(cluster_trends_path)
    except Exception:
        df_clusters, df_cluster_trends = None, None

    return report, df_trends, df_clusters, df_cluster_trends

report, df_trends, df_clusters, df_cluster_trends = load_data()

# --- Top Level Metrics ---
col1, col2, col3 = st.columns(3)
col1.metric("Total Patents Analyzed", f"{report['total_patents']:,}")
col2.metric("Unique Countries", len(report["top_countries"]))
col3.metric("Top Company", report["top_companies"][0]["name"] if report["top_companies"] else "N/A")

st.markdown("---")

# --- Global Trends & Demographics ---
st.header("📈 Historical Patent Trends")
if not df_trends.empty:
    fig_trends = px.line(df_trends, x="year", y="patents_filed", title="Patents Filed per Year")
    st.plotly_chart(fig_trends, use_container_width=True)

col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Top 10 Companies")
    st.dataframe(pd.DataFrame(report["top_companies"]), use_container_width=True)

with col_b:
    st.subheader("Top 10 Countries by Share")
    df_countries = pd.DataFrame(report["top_countries"])
    fig_pie = px.pie(df_countries, values='patents', names='country', hole=0.4)
    st.plotly_chart(fig_pie, use_container_width=True)

st.markdown("---")

# --- AI & Clustering Insights ---
st.header("🧠 Machine Learning Technology Categories (K-Means)")

if df_clusters is not None:
    st.markdown("Based on an unsupervised NLP analysis of patent abstracts, here are the dominant technology clusters:")
    st.dataframe(df_clusters, use_container_width=True)
    
    st.subheader("Technology Cluster Growth Over Time")
    fig_cluster_trend = px.line(
        df_cluster_trends, 
        x="year", 
        y="count", 
        color="cluster", 
        title="Sampled Patent Growth by Identified Tech Cluster"
    )
    st.plotly_chart(fig_cluster_trend, use_container_width=True)
else:
    st.warning("Cluster data not found. Run `python scripts/cluster_abstracts.py` to generate NLP insights.")