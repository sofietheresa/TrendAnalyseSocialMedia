import streamlit as st
import pandas as pd
import os

st.title("📊 Social Media Trends")

data_path = "data/processed/topic_summary.csv"

if os.path.exists(data_path):
    df = pd.read_csv(data_path)
    st.dataframe(df)
else:
    st.warning("Keine verarbeiteten Daten gefunden.")
