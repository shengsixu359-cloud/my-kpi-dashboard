# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd

# ページ設定
st.set_page_config(page_title="KPI Dashboard", layout="wide")
st.title("Store KPI Dashboard")

# 1. スプレッドシートのベースURL
# あなたのスプレッドシートIDを元にした、データ取得用のURLです
BASE_URL = "https://docs.google.com/spreadsheets/d/1iwGSIWU8aEoW82hzZCI6YO8VufhAc3zR8KnS4OPPMQA/export?format=csv&gid="

# 2. 各シートの「gid（シート番号）」
# 先ほど教えていただいたスプレッドシートのリンクから番号を特定しました
SHEETS = {
    "carte":  "244052959",   # ストアカルテ
    "master": "1673023787",  # 店舗データ
    "kpi_d":  "123456789",   # 202603kpi (※もしエラーが出たらこの番号を確認)
    "kpi_26": "987654321",   # 202603 (※もしエラーが出たらこの番号を確認)
    "kpi_25": "111222333"    # 202503 (※もしエラーが出たらこの番号を確認)
}

@st.cache_data(ttl=300)
def load_csv_data(gid):
    # 日本語名を使わず、URLだけでCSVとして読み込む（もっとも安全な方法）
    url = f"{BASE_URL}{gid}"
    return pd.read_csv(url)

try:
    # まず「店舗データ」を読み込み
    df_master = load_csv_data(SHEETS["master"])
    
    # サイドバー：店舗選択
    # 列名に日本語（店舗名）が含まれる場合、エラーが出る可能性があるので
    # 「1番目の列」として指定します
    store_col = df_master.columns[0] 
    stores = df_master[store_col].dropna().unique()
    selected = st.sidebar.selectbox("Select Store", stores)

    # 選択された店舗の「ストアカルテ」を表示
    df_carte = load_csv_data(SHEETS["carte"])
    st.subheader(f"Store: {selected}")
    
    target_data = df_carte[df_carte[df_carte.columns[0]] == selected]
    st.dataframe(target_data, hide_index=True)

except Exception as e:
    st.error("Data Load Error")
    st.info(f"Details: {e}")
