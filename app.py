# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# UTF-8 encoding configuration
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

st.set_page_config(page_title="KPI Dashboard", layout="wide")
st.title("Store KPI Dashboard")

# URL (Simple format)
URL = "https://docs.google.com/spreadsheets/d/1iwGSIWU8aEoW82hzZCI6YO8VufhAc3zR8KnS4OPPMQA/edit"

@st.cache_data(ttl=300)
def load_data():
    conn = st.connection("gsheets", type=GSheetsConnection)
    # シート名を直接文字列で指定（変数を使わない）
    return {
        "carte":  conn.read(spreadsheet=URL, worksheet="ストアカルテ"),
        "master": conn.read(spreadsheet=URL, worksheet="店舗データ"),
        "kpi_d":  conn.read(spreadsheet=URL, worksheet="202603kpi"),
        "kpi_26": conn.read(spreadsheet=URL, worksheet="202603"),
        "kpi_25": conn.read(spreadsheet=URL, worksheet="202503"),
    }

try:
    all_data = load_data()
    # サイドバー：店舗名
    stores = all_data["master"]["店舗名"].dropna().unique()
    selected = st.sidebar.selectbox("Select Store", stores)

    st.header(f"Store: {selected}")
    
    # データの表示（フィルタリング）
    df_c = all_data["carte"]
    target_data = df_c[df_c["店舗名"] == selected]
    st.dataframe(target_data, hide_index=True)

except Exception as e:
    st.error("Data Load Error")
    st.info(f"Details: {e}")
