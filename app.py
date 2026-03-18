import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# ページ設定
st.set_page_config(page_title="店舗KPIダッシュボード", layout="wide")
st.title("📊 店舗KPIダッシュボード")

# スプレッドシートのURL
SPREADSHEET_URL = "(https://docs.google.com/spreadsheets/d/1iwGSIWU8aEoW82hzZCI6YO8VufhAc3zR8KnS4OPPMQA/edit?usp=sharing)"

@st.cache_data(ttl=300)
def load_all_sheets():
    conn = st.connection("gsheets", type=GSheetsConnection)
    data = {
        "carte":    conn.read(spreadsheet=SPREADSHEET_URL, worksheet="ストアカルテ"),
        "master":   conn.read(spreadsheet=SPREADSHEET_URL, worksheet="店舗データ"),
        "kpi_2026_dtl": conn.read(spreadsheet=SPREADSHEET_URL, worksheet="202603kpi"),
        "kpi_2026":     conn.read(spreadsheet=SPREADSHEET_URL, worksheet="202603"),
        "kpi_2025":     conn.read(spreadsheet=SPREADSHEET_URL, worksheet="202503"),
    }
    return data

try:
    all_sheets = load_all_sheets()
    store_list = all_sheets["master"]["店舗名"].dropna().unique()
    selected_store = st.sidebar.selectbox("店舗選択", store_list)

    st.subheader(f"🏠 {selected_store} の状況")
    
    # 簡易表示（テスト用）
    st.write("ストアカルテデータ:")
    st.dataframe(all_sheets["carte"][all_sheets["carte"]["店舗名"] == selected_store])

except Exception as e:
    st.error(f"エラー: {e}")
