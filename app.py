import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# ページ設定
st.set_page_config(page_title="Store KPI Dashboard", layout="wide")
st.title("📊 店舗KPIダッシュボード")

# スプレッドシートのURL（末尾の #gid... などを除いたシンプルな形式）
# ※必ず半角のダブルクォーテーション " で囲んでください
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1iwGSIWU8aEoW82hzZCI6YO8VufhAc3zR8KnS4OPPMQA/edit"

@st.cache_data(ttl=300)
def load_all_sheets():
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # 日本語のシート名を安全に読み込む設定
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
    
    # サイドバーで店舗を選択
    # 「店舗名」という列名もスプレッドシートと完全一致させてください
    store_list = all_sheets["master"]["店舗名"].dropna().unique()
    selected_store = st.sidebar.selectbox("店舗を選択", store_list)

    st.subheader(f"🏠 {selected_store} の状況")
    
    # データの表示
    st.write("### ストアカルテ")
    st.dataframe(all_sheets["carte"][all_sheets["carte"]["店舗名"] == selected_store], hide_index=True)

except Exception as e:
    st.error(f"データの読み込み中にエラーが発生しました。")
    st.info(f"詳細な原因: {e}")
