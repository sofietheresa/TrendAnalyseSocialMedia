import streamlit as st
import sqlite3
import pandas as pd
from pathlib import Path
from zenml.client import Client
import plotly.express as px

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logs"
DB_PATH = BASE_DIR / "data" / "social_media.db"

def load_data(table: str) -> pd.DataFrame:
    if not DB_PATH.exists():
        return pd.DataFrame()
    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
    return df

# --- Seitenaufbau ---
st.set_page_config(page_title="Social Media Dashboard", layout="wide")
st.sidebar.title("📁 Navigation")
page = st.sidebar.radio("Seite wählen:", [
    "📊 Dashboard",
    "🗣️ Reddit",
    "🎵 TikTok",
    "📺 YouTube",
    "📋 Logs",
    "📦 Orchestration"
])

# --- Dashboard ---
if page == "📊 Dashboard":
    st.title("📊 Übersicht")
    try:
        reddit = load_data("reddit_data")[["created_utc", "scraped_at"]].copy()
        reddit["source"] = "Reddit"

        tiktok = load_data("tiktok_data")[["created_time", "scraped_at"]].copy()
        tiktok = tiktok.rename(columns={"created_time": "created_utc"})
        tiktok["source"] = "TikTok"

        youtube = load_data("youtube_data")[["published_at"]].copy()
        youtube["scraped_at"] = youtube["published_at"]
        youtube["created_utc"] = pd.to_datetime(youtube["scraped_at"]).astype(int) // 10**9
        youtube["source"] = "YouTube"

        df = pd.concat([reddit, tiktok, youtube], ignore_index=True)
        df["created_utc"] = pd.to_datetime(df["created_utc"], unit="s", errors="coerce")
        df["date"] = df["created_utc"].dt.date
        # Nur April und Mai anzeigen
        df = df[(df["created_utc"].dt.month.isin([4, 5])) & (df["created_utc"].dt.year == 2025)]
        counts = df.groupby(["date", "source"]).size().unstack(fill_value=0)

        st.line_chart(counts)

    except Exception as e:
        st.error(f"Fehler beim Laden der Daten: {e}")

# --- Reddit ---
elif page == "🗣️ Reddit":
    st.title("🗣️ Reddit Daten")
    st.dataframe(load_data("reddit_data"))

# --- TikTok ---
elif page == "🎵 TikTok":
    st.title("🎵 TikTok Daten")
    st.dataframe(load_data("tiktok_data"))

# --- YouTube ---
elif page == "📺 YouTube":
    st.title("📺 YouTube Daten")
    st.dataframe(load_data("youtube_data"))

# --- Logs ---
elif page == "📋 Logs":
    st.title("📋 Logs")
    for log_file in ["reddit.log", "tiktok.log", "youtube.log"]:
        path = LOG_DIR / log_file
        if path.exists():
            st.subheader(f"📄 {log_file}")
            with open(path) as f:
                # Logs anzeigen (automatisch gescrollt)
                logs = path.read_text()
                st.text_area("📄 " + log_file, logs, height=300, key=log_file)
                st.markdown(f"<script>var textarea = window.document.querySelector('textarea#{log_file}'); textarea.scrollTop = textarea.scrollHeight;</script>", unsafe_allow_html=True)

        else:
            st.warning(f"{log_file} nicht gefunden.")

# --- Orchestration ---
elif page == "📦 Orchestration":
    st.title("📦 ZenML Orchestration Dashboard")

    client = Client()
    try:
        pipelines = client.list_pipelines()

        for pipeline in pipelines:
            st.subheader(f"🧪 Pipeline: `{pipeline.name}`")

            # Letzten Run finden
            runs = client.list_pipeline_runs(pipeline_name=pipeline.name, size=1).items
            if runs:
                last_run = runs[0]
                st.write(f"Letzter Status: `{last_run.status}`")
                st.write(f"Letzter Run: {last_run.created.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                st.info("Noch kein Lauf vorhanden.")

            if st.button(f"🚀 Starte `{pipeline.name}`", key=f"run_{pipeline.name}"):
                client.run_pipeline(pipeline.name)
                st.success(f"✅ Pipeline `{pipeline.name}` gestartet.")

        # Stack-Infos anzeigen
        st.subheader("🧱 Aktiver Stack")
        stack = client.active_stack
        st.markdown(f"**Stack Name:** `{stack.name}`")
        st.markdown("**Orchestrator:** `{}`".format(stack.orchestrator.flavor))
        st.markdown("**Artifact Store:** `{}`".format(stack.artifact_store.uri))
        st.markdown("**Experiment Tracker:** `{}`".format(stack.experiment_tracker.name if stack.experiment_tracker else "–"))

    except Exception as e:
        st.error(f"❌ Fehler beim Abrufen von ZenML-Pipelines: {e}")

