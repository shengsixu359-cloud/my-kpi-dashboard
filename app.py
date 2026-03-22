# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd

# 1. ページ設定
st.set_page_config(page_title="店舗KPI分析レポート", layout="wide")
st.title("📊 店舗KPI分析レポート")

# 2. データ取得設定
BASE_URL = "https://docs.google.com/spreadsheets/d/1iwGSIWU8aEoW82hzZCI6YO8VufhAc3zR8KnS4OPPMQA/export?format=csv&gid="
SHEETS = {
    "master": "1673023787",  # 店舗データシート
    "kpi_26": "0",           # 202603シート
    "kpi_25": "12345678"     # 202503シート（仮）
}

@st.cache_data(ttl=60)
def load_raw_df(gid):
    try:
        # 読み込み（1行目をヘッダーとして扱う）
        return pd.read_csv(f"{BASE_URL}{gid}")
    except:
        return pd.DataFrame()

def get_cell_value_raw(gid, row, col):
    """特定のセルの値を直接取得するための補助関数"""
    df = load_raw_df(gid)
    try:
        # header=0で読み込んでいるため、行番号を調整
        val = df.iloc[row-2, col-1] 
        clean_val = str(val).replace(',', '').replace('¥', '').replace('円', '').strip()
        return pd.to_numeric(clean_val, errors='coerce')
    except:
        return 0

try:
    # データの読み込み
    df_master = load_raw_df(SHEETS["master"])
    # 列名の空白削除
    df_master.columns = [str(c).strip() for c in df_master.columns]

    # --- サイドバー：表示条件（連動プルダウン） ---
    st.sidebar.header("🔍 表示条件")
    
    # 1. エリア担当者を選択 (E列)
    # E列が「エリア担当者」であることを指定
    area_handler_col = df_master.columns[4] # 0始まりで4番目＝E列
    handlers = sorted(df_master[area_handler_col].dropna().unique())
    selected_handler = st.sidebar.selectbox("エリア担当者を選択", handlers)
    
    # 2. 担当店舗を選択 (C列)
    # 選択された担当者に紐づくC列（店舗名）を抽出
    store_name_col = df_master.columns[2] # 0始まりで2番目＝C列
    available_stores = df_master[df_master[area_handler_col] == selected_handler][store_name_col].unique()
    selected_store = st.sidebar.selectbox("店舗を選択", available_stores)

    # 3. 期間選択
    selected_month = st.sidebar.selectbox("表示月を選択", ["2026/03"])
    selected_week = st.sidebar.selectbox("表示週を選択", ["全週", "1W", "2W", "3W", "4W", "5W"])

    # --- TOP: 全体受注実績サマリー ---
    st.markdown(f"### 🏆 {selected_store} 受注実績サマリー ({selected_month})")
    
    # E3, F3から取得
    val_sales = get_cell_value_raw(SHEETS["kpi_26"], 3, 5)  # E3
    val_target = get_cell_value_raw(SHEETS["kpi_26"], 3, 6)
