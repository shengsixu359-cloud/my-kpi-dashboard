# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# ページ設定
st.set_page_config(page_title="Store KPI Dashboard", layout="wide")

# タイトル
st.title("📊 店舗KPIダッシュボード")

# スプレッドシートURL（ID部分のみを抽出した最も安全な形式）
# ※URLの末尾が /edit で終わっていることを確認してください
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1iwGSIWU8aEoW82hzZCI6YO8VufhAc3zR8KnS4OPPMQA/edit"

@st.cache_data(ttl=300)
def load_data():
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # worksheets引数を使わず、1枚ずつ丁寧に読み込む方式に変更します
    # これにより400エラーの原因となる「シート指定の不備」を回避しやすくなります
    try:
        df_carte  = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="ストアカルテ")
        df_master = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="店舗データ")
        df_kpi_d  = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="202603kpi")
        df_kpi_26 = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="202603")
        df_kpi_25 = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="202503")
        
        return {
            "carte": df_carte,
            "master": df_master,
            "kpi_d": df_kpi_d,
            "kpi_26": df_kpi_26,
            "kpi_25": df_kpi_25
        }
    except Exception as e:
        st.error(f"シートの読み込みに失敗しました。名前が一致しているか確認してください: {e}")
        return None

# メイン処理
data = load_data()

if data:
    try:
        # サイドバーで店舗名を選択
        # ※「店舗データ」シートに「店舗名」という列名があることが前提です
        store_list = data["master"]["店舗名"].dropna().unique()
        selected_store = st.sidebar.selectbox("店舗を選択してください", store_list)

        # データの表示（ストアカルテ）
        st.subheader(f"🏠 {selected_store} の概況")
        carte_df = data["carte"]
        selected_carte = carte_df[carte_df["店舗名"] == selected_store]
        st.dataframe(selected_carte, hide_index=True)

        # 2026年実績
        st.subheader("📈 2026年度実績")
        kpi26_df = data["kpi_26"]
        st.dataframe(kpi26_df[kpi26_df["店舗名"] == selected_store], hide_index=True)

    except KeyError as e:
        st.error(f"スプレッドシートの列名が一致しません。'店舗名' という列があるか確認してください。")
    except Exception as e:
        st.error(f"予期せぬエラーが発生しました: {e}")
