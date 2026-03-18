# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# 1. ページ設定
st.set_page_config(page_title="KPI Dashboard", layout="wide")
st.title("Store KPI Dashboard")

# 2. スプレッドシートURL（末尾の余計な文字をすべてカットしました）
URL = "https://docs.google.com/spreadsheets/d/1iwGSIWU8aEoW82hzZCI6YO8VufhAc3zR8KnS4OPPMQA/edit"

# 3. データ読み込み（エラー回避用の設定を追加）
@st.cache_data(ttl=300)
def load_data():
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # 日本語シート名を一度変数に入れてから読み込みます
    s1 = "ストアカルテ"
    s2 = "店舗データ"
    s3 = "202603kpi"
    s4 = "202603"
    s5 = "202503"
    
    data = {
        "carte":  conn.read(spreadsheet=URL, worksheet=s1),
        "master": conn.read(spreadsheet=URL, worksheet=s2),
        "kpi_d":  conn.read(spreadsheet=URL, worksheet=s3),
        "kpi_26": conn.read(spreadsheet=URL, worksheet=s4),
        "kpi_25": conn.read(spreadsheet=URL, worksheet=s5),
    }
    return data

# 4. メイン表示
try:
    all_data = load_data()
    
    # サイドバーの「店舗名」という文字も変数化してエラーを防止
    col_name = "店舗名"
    stores = all_data["master"][col_name].dropna().unique()
    selected = st.sidebar.selectbox("Select Store", stores)

    st.header(f"Store: {selected}")
    
    # データの表示
    st.subheader("Store Carte")
    df_c = all_data["carte"]
    st.dataframe(df_c[df_c[col_name] == selected], hide_index=True)

except Exception as e:
    st.error("Error occurred while loading data.")
    st.info(f"Technical Details: {e}")
