import pandas as pd
import streamlit as st


@st.cache_data
def load_data(path="data/clean/dataset.csv"):
    """Lê o dataset já tratado (exportado ao final de notebooks/tratamento-carros.ipynb)."""
    return pd.read_csv(path)
