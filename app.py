# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from datetime import datetime

# 1. ページ設定
st.set_page_config(page_title="店舗KPI分析レポート", layout="wide")
st.title("📊 店舗KPI分析レポート")

# 2. データ取得設定
BASE_URL = "https://docs.google.com/spreadsheets/d/1iwGSIWU8aEoW82hzZCI6YO8VufhAc3zR8KnS4OPPMQA/export?format=csv&gid="
SHEETS = {
    "master": "1673023787",  # ② 店舗データ
    "kpi_26": "0",           # ④ 202603
    "kpi_25": "12345678"     # ⑤ 202503
}

@st.cache_data(ttl=60)
def load_raw_df(gid):
    try:
        # header=Noneで読み込み、セル位置(0始まりの行列)で制御しやすくする
        return pd.read_csv(f"{BASE_URL}{gid}", header=None)
    except:
        return pd.DataFrame()

def get_val(df, row_idx, col_idx):
    """行列インデックスから数値を安全に取得"""
    try:
        val = df.iloc[row_idx, col_idx]
        return pd.to_numeric(str(val).replace(',', '').replace('¥', '').replace('円', '').strip(), errors='coerce')
    except:
        return 0

try:
    # データの読み込み
    raw_master = load_raw_df(SHEETS["master"])
    raw_26 = load_raw_df(SHEETS["kpi_26"])
    raw_25 = load_raw_df(SHEETS["kpi_25"])

    if raw_master.empty:
        st.error("データの読み込みに失敗しました。共有設定を確認してください。")
        st.stop()

    # --- サイドバー：条件設定 ---
    st.sidebar.header("🔍 表示条件")

    # 1. エリア担当者 (E列 = index 4)
    # 2行目(index 1)以降を取得
    master_data = raw_master.iloc[1:].copy()
    handler_list = sorted(master_data[4].dropna().unique())
    selected_handler = st.sidebar.selectbox("エリア担当者を選択", handler_list)

    # 2. 店舗選択 (C列 = index 2)
    # 選択した担当者に紐づく店舗のみ表示
    stores_df = master_data[master_data[4] == selected_handler]
    store_list = stores_df[2].unique()
    selected_store = st.sidebar.selectbox("店舗を選択", store_list)

    # 3. 表示週を選択 (月曜始まり定義)
    # W1: 3/1のみ, W2: 3/2-3/8, W3: 3/9-3/15...
    # スプレッドシートの列構成（G列=index 6 から週実績が並んでいる想定）
    week_options = {
