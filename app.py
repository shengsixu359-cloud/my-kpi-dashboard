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
    "kpi_25": "12345678"     # 202503シート
}

@st.cache_data(ttl=60)
def load_raw_df(gid):
    try:
        # 読み込み（1行目をヘッダーとして扱う）
        df = pd.read_csv(f"{BASE_URL}{gid}")
        df.columns = [str(c).strip() for c in df.columns]
        return df
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

    if df_master.empty:
        st.error("マスターデータが読み込めませんでした。スプレッドシートの共有設定を確認してください。")
        st.stop()

    # --- サイドバー：表示条件（連動プルダウン） ---
    st.sidebar.header("🔍 表示条件")
    
    # 1. エリア担当者を選択 (E列 = index 4)
    handler_col = df_master.columns[4]
    handlers = sorted(df_master[handler_col].dropna().unique())
    selected_handler = st.sidebar.selectbox("エリア担当者を選択", handlers)
    
    # 2. 担当店舗を選択 (C列 = index 2)
    store_col = df_master.columns[2]
    available_stores = df_master[df_master[handler_col] == selected_handler][store_col].unique()
    selected_store = st.sidebar.selectbox("店舗を選択", available_stores)

    # 3. 期間選択
    selected_month = st.sidebar.selectbox("表示月を選択", ["2026/03"])
    selected_week = st.sidebar.selectbox("表示週を選択", ["全週", "1W", "2W", "3W", "4W", "5W"])

    # --- TOP: 全体受注実績サマリー ---
    st.markdown(f"### 🏆 {selected_store} 受注実績サマリー ({selected_month})")
    
    # E3, F3から取得
    val_sales = get_cell_value_raw(SHEETS["kpi_26"], 3, 5)  # E3
    val_target = get_cell_value_raw(SHEETS["kpi_26"], 3, 6) # F3
    val_25 = get_cell_value_raw(SHEETS["kpi_25"], 3, 5)     # 前年E3
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("受注実績", f"{val_sales:,.0f}円")
    c2.metric("目標", f"{val_target:,.0f}円")
    c3.metric("目標比", f"{(val_sales/val_target*100):.1f}%" if val_target else "0%")
    c4.metric("目標差額", f"{(val_sales - val_target):,.0f}円")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("前年実績", f"{val_25:,.0f}円")
    c2.metric("前年比", f"{(val_sales/val_25*100):.1f}%" if val_25 else "0%")
    c3.metric("前年差額", f"{(val_sales - val_25):,.0f}円")
    
    st.divider()

    # --- KPI分析テーブル ---
    st.markdown("### 📈 指標別KPI分析")
    
    kpi_map = {
        "座数": {"act": (5, 5), "tgt": (5, 6), "ly": (5, 7)},
        "客単価": {"act": (6, 5), "tgt": (6, 6), "ly": (6, 7)},
        "CVR": {"act": (7, 5), "tgt": (7, 6), "ly": (7, 7)},
        "客数": {"act": (8, 5), "tgt": (8, 6), "ly": (8, 7)},
    }
    
    kpi_results = []
    for item, pos in kpi_map.items():
        act = get_cell_value_raw(SHEETS["kpi_26"], pos["act"][0], pos["act"][1])
        tgt = get_cell_value_raw(SHEETS["kpi_26"], pos["tgt"][0], pos["tgt"][1])
        ly = get_cell_value_raw(SHEETS["kpi_25"], pos["ly"][0], pos["ly"][1])

        kpi_results.append({
            "KPI指標": item,
            "目標": f"{tgt:,.0f}" if tgt > 100 else f"{tgt:.2f}",
            "実績": f"{act:,.0f}" if act > 100 else f"{act:.2f}",
            "目標比": f"{(act/tgt*100):.1f}%" if tgt else "-",
            "前年比": f"{(act/ly*100):.1f}%" if ly else "-"
        })

    st.table(pd.DataFrame(kpi_results))

except Exception as e:
    st.error(f"システムエラーが発生しました: {e}")
