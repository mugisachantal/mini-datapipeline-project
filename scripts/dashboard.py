import streamlit as st
import pandas as pd
import json
import plotly.express as px
import os

# --- Page Config ---
st.set_page_config(page_title="Invention investigation basing on patents", layout="wide")
st.title("Investigation Visual Dashboard")

# --- Load Data ---
@st.cache_data
def load_data():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    reports_dir = os.path.join(current_dir, "reports")
    
    report_path = os.path.join(reports_dir, "patent_report.json")
    cluster_summary_path = os.path.join(reports_dir, "cluster_summary.csv")
    cluster_trends_path = os.path.join(reports_dir, "cluster_trends.csv")
    cluster_2d_path = os.path.join(reports_dir, "cluster_2d.csv")   # optional: precomputed PCA/t-SNE

    if not os.path.exists(report_path):
        raise FileNotFoundError(f"Missing file at {report_path}. "
                                f"Current directory contents: {os.listdir(current_dir)}")

    with open(report_path, "r") as f:
        report = json.load(f)
    
    df_trends = pd.DataFrame(report["year_trends"])
    
    try:
        df_clusters = pd.read_csv(cluster_summary_path)
        df_cluster_trends = pd.read_csv(cluster_trends_path)
    except Exception:
        df_clusters, df_cluster_trends = None, None

    # Load 2D embedding if exists
    df_2d = None
    if os.path.exists(cluster_2d_path):
        df_2d = pd.read_csv(cluster_2d_path)

    return report, df_trends, df_clusters, df_cluster_trends, df_2d

report, df_trends, df_clusters, df_cluster_trends, df_2d = load_data()

# --- Top Level Metrics ---
col1, col2, col3 = st.columns(3)
col1.metric("Total Patents Analyzed", f"{report['total_patents']:,}")
col2.metric("Unique Countries", len(report["top_countries"]))
col3.metric("Top Company", report["top_companies"][0]["name"] if report["top_companies"] else "N/A")

st.markdown("---")

# --- Global Trends & Demographics ---
# --- Global Trends & Demographics ---
st.header(" Historical Patent Trends")
if not df_trends.empty:
    fig_trends = px.line(df_trends, x="year", y="patents_filed", title="Patents Filed per Year")
    st.plotly_chart(fig_trends, use_container_width=True)

col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Top 10 Companies")
    df_companies = pd.DataFrame(report["top_companies"])
    # Bar graph for companies
    fig_companies_bar = px.bar(df_companies, x='name', y='patents', 
                               title="Patent Count by Company",
                               labels={'name':'Company', 'patents':'Number of Patents'})
    st.plotly_chart(fig_companies_bar, use_container_width=True)
    # Keep the table for detailed view
    st.dataframe(df_companies, use_container_width=True)

with col_b:
    st.subheader("Top 10 Countries by Share")
    df_countries = pd.DataFrame(report["top_countries"])
    # Restored pie chart
    fig_pie = px.pie(df_countries, values='patents', names='country', hole=0.4,
                     title="Patent Share by Country")
    st.plotly_chart(fig_pie, use_container_width=True)

st.markdown("---")

# --- AI & Clustering Insights ---
st.header(" Machine Learning Technology Categorization (K-Means)")

if df_clusters is not None and df_cluster_trends is not None:
    # Human-readable labels
    cluster_labels = {
        0: "Chemistry & Materials",
        1: "Semiconductor Devices", 
        2: "Data Processing & Communications",
        3: "Electrical Circuits & Power",
        4: "Mechanical Structures"
    }
    
    # Transform cluster summary table
    df_clusters['cluster_label'] = df_clusters['cluster_id'].map(cluster_labels)
    df_clusters_display = df_clusters[['cluster_label', 'top_terms', 'patent_count']]
    df_clusters_display.columns = ['Technology Cluster', 'Top Terms', 'Patent Count']
    
    # Transform trend data
    df_cluster_trends['cluster_label'] = df_cluster_trends['cluster'].map(cluster_labels)
    
    # Display table
    st.markdown("Dominant technology clusters based on an unsupervised NLP analysis of patent abstracts:")
    st.dataframe(df_clusters_display, use_container_width=True)
    
    # ---- Bar graph for top categories by patent count ----
    st.subheader("Patent Count per Technology Category")
    fig_cat_bar = px.bar(df_clusters_display, x='Technology Cluster', y='Patent Count',
                         title="Number of Patents in Each AI‑Detected Cluster",
                         color='Technology Cluster')
    st.plotly_chart(fig_cat_bar, use_container_width=True)
    
    # ---- Cluster trend over time (line chart) ----
    st.subheader("Tech category innovation and invention Trend Over Time")
    fig_cluster_trend = px.line(
        df_cluster_trends, 
        x="year", 
        y="count", 
        color="cluster_label", 
        title="Sampled Patent Growth by Identified Tech Cluster"
    )
    st.plotly_chart(fig_cluster_trend, use_container_width=True)
    
    # ---- K-Means clustering visualization (2D projection) ----
    st.subheader("🔍 Visualising the Clustering Process")
    if df_2d is not None and {'x', 'y', 'cluster'}.issubset(df_2d.columns):
        # Map cluster numbers to labels
        df_2d['cluster_label'] = df_2d['cluster'].map(cluster_labels)
        fig_scatter = px.scatter(df_2d, x='x', y='y', color='cluster_label',
                                 title="Patent Abstracts Projected into 2D (PCA / t-SNE)",
                                 hover_data=['patent_id'] if 'patent_id' in df_2d.columns else None)
        st.plotly_chart(fig_scatter, use_container_width=True)
        st.caption("Each point represents one patent abstract. Colours correspond to the K‑Means cluster labels.")
    else:
        st.info("💡 To see a 2D visualisation of the clusters, generate a file `reports/cluster_2d.csv` with columns `x, y, cluster, patent_id` using PCA or t‑SNE on the TF‑IDF matrix.")
else:
    st.warning("Cluster data not found. Run `python scripts/cluster_abstracts.py` to generate NLP insights.")