# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd

# 1. ページ設定
st.set_page_config(page_title="店舗KPI分析レポート", layout="wide")
st.title("📊 店舗KPI分析レポート")

# 2. データ取得設定
BASE_URL = "https://docs.google.com/spreadsheets/d/1iwGSIWU8aEoW82hzZCI6YO8VufhAc3zR8KnS4OPPMQA/export?format=csv&gid="
SHEETS = {
    "carte":  "869736914",   # ① ストアカルテ
    "master": "1673023787",  # ② 店舗データ
    "kpi_d":  "244052959",   # ③ 202603kpi
    "kpi_26": "0",           # ④ 202603
    "kpi_25": "12345678"     # ⑤ 202503
}

@st.cache_data(ttl=60)
def load_raw_df(gid):
    try:
        # header=Noneで読み込むことで、セル位置(行列番号)で指定可能にする
        return pd.read_csv(f"{BASE_URL}{gid}", header=None)
    except:
        return pd.DataFrame()

def get_cell_value(df, row, col):
    """特定のセルの値を数値として取得 (Excel形式のA1→0,0に対応)"""
    try:
        val = df.iloc[row-1, col-1]
        return pd.to_numeric(str(val).replace(',', '').replace('¥', ''), errors='coerce')
    except:
        return 0

try:
    # データの読み込み
    raw_master = load_raw_df(SHEETS["master"])
    raw_26 = load_raw_df(SHEETS["kpi_26"])
    raw_25 = load_raw_df(SHEETS["kpi_25"])
    
    # マスターデータ（店舗リスト用）を整形
    df_master = raw_master.copy()
    df_master.columns = [str(c).strip() for c in df_master.iloc[0]]
    df_master = df_master[1:]

    # --- サイドバー：表示条件 ---
    st.sidebar.header("🔍 表示条件")
    
    # 1. エリア選択
    area_col = "エリア" if "エリア" in df_master.columns else df_master.columns[1]
    areas = ["すべて"] + list(df_master[area_col].dropna().unique())
    selected_area = st.sidebar.selectbox("エリアを選択", areas)
    
    # 2. 店舗選択（エリアに連動）
    store_col = "店舗名" if "店舗名" in df_master.columns else df_master.columns[0]
    if selected_area == "すべて":
        available_stores = df_master[store_col].unique()
    else:
        available_stores = df_master[df_master[area_col] == selected_area][store_col].unique()
    selected_store = st.sidebar.selectbox("店舗を選択", available_stores)

    # 3. 期間選択（プルダウン）
    # ※シート④(202603)から月と週のリストを取得（場所は仮定）
    selected_month = st.sidebar.selectbox("表示月を選択", ["2026/03"]) # 固定またはリスト取得
    selected_week = st.sidebar.selectbox("表示週を選択", ["全週", "1W", "2W", "3W", "4W", "5W"])

    # --- TOP: 全体受注実績サマリー ---
    st.markdown(f"### 🏆 全体受注実績サマリー ({selected_month})")
    
    # ご指摘のセル位置から取得 (E3=行3,列5 / F3=行3,列6)
    val_sales = get_cell_value(raw_26, 3, 5)  # E3: 受注金額
    val_target = get_cell_value(raw_26, 3, 6) # F3: 目標
    val_25 = get_cell_value(raw_25, 3, 5)     # 前年同時期のE3
    
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
    
    # KPI項目と、それぞれの値がスプレッドシートのどのセルにあるか（仮定）
    # ※もし位置がわかる場合は、(行, 列)を修正してください
    kpi_map = {
        "座数": {"act": (5, 5), "tgt": (5, 6), "ly": (5, 7)},
        "客単価": {"act": (6, 5), "tgt": (6, 6), "ly": (6, 7)},
        "CVR": {"act": (7, 5), "tgt": (7, 6), "ly": (7, 7)},
        "客数": {"act": (8, 5), "tgt": (8, 6), "ly": (8, 7)},
    }
    
    kpi_results = []
    for item, pos in kpi_map.items():
        act = get_cell_value(raw_26, pos["act"][0], pos["act"][1])
        tgt = get_cell_value(raw_26, pos["tgt"][0], pos["tgt"][1])
        ly = get_cell_value(raw_25, pos["ly"][0], pos["ly"][1])

        kpi_results.append({
            "KPI指標": item,
            "目標": f"{tgt:,.0f}" if tgt > 100 else f"{tgt:.2f}",
            "実績": f"{act:,.0f}" if act > 100 else f"{act:.2f}",
            "目標比": f"{(act/tgt*100):.1f}%" if tgt else "-",
            "前年比": f"{(act/ly*100):.1f}%" if ly else "-"
        })

    st.table(pd.DataFrame(kpi_results))

except Exception as e:
    st.error(f"データの抽出中にエラーが発生しました
