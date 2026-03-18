# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd

# 1. ページ設定
st.set_page_config(page_title="店舗KPI分析レポート", layout="wide")
st.title("📊 店舗KPI分析レポート")

# 2. データ取得用URL
BASE_URL = "https://docs.google.com/spreadsheets/d/1iwGSIWU8aEoW82hzZCI6YO8VufhAc3zR8KnS4OPPMQA/export?format=csv&gid="
SHEETS = {
    "carte":  "869736914",   # ストアカルテ
    "master": "1673023787",  # 店舗データ
    "kpi_d":  "244052959",   # 202603kpi
    "kpi_26": "0",           # 202603
    "kpi_25": "12345678"     # 202503
}

@st.cache_data(ttl=60)
def load_data(gid):
    try:
        df = pd.read_csv(f"{BASE_URL}{gid}")
        df.columns = [str(c).strip() for c in df.columns] # 列名クリーニング
        return df
    except:
        return pd.DataFrame()

try:
    # データの読み込み
    df_master = load_data(SHEETS["master"])
    df_26 = load_data(SHEETS["kpi_26"])
    df_25 = load_data(SHEETS["kpi_25"])
    df_dtl = load_data(SHEETS["kpi_d"])

    # --- サイドバー：店舗・期間選択 ---
    st.sidebar.header("🔍 表示条件")
    store_col = "店舗名"
    selected_store = st.sidebar.selectbox("店舗を選択", df_master[store_col].unique())
    
    month_col = "月"
    months = sorted(df_26[month_col].unique())
    selected_month = st.sidebar.selectbox("表示月を選択", months)
    
    week_col = "週"
    weeks = sorted(df_26[df_26[month_col] == selected_month][week_col].unique())
    selected_weeks = st.sidebar.multiselect(f"{selected_month}月の表示週", options=weeks)

    # --- フィルタリング ---
    def filter_df(df):
        if df.empty: return df
        mask = (df[store_col] == selected_store) & (df[month_col] == selected_month)
        if selected_weeks:
            mask &= (df[week_col].isin(selected_weeks))
        return df[mask]

    f_26 = filter_df(df_26)
    f_25 = filter_df(df_25)

    # --- TOP: 受注実績サマリー ---
    st.markdown("### 🏆 全体受注実績サマリー")
    
    # 指標の計算
    sales_26 = f_26["受注実績"].sum() if "受注実績" in f_26.columns else 0
    target_26 = f_26["目標"].sum() if "目標" in f_26.columns else 0
    sales_25 = f_25["受注実績"].sum() if "受注実績" in f_25.columns else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("受注実績", f"{sales_26:,.0f}")
    c2.metric("目標", f"{target_26:,.0f}")
    c3.metric("目標比", f"{(sales_26/target_26*100):.1f}%" if target_26 else "0%")
    c4.metric("目標差額", f"{(sales_26 - target_26):,.0f}")

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("前年受注実績", f"{sales_25:,.0f}")
    c6.metric("前年比", f"{(sales_26/sales_25*100):.1f}%" if sales_25 else "0%")
    c7.metric("前年差額", f"{(sales_26 - sales_25):,.0f}")
    c8.empty()

    st.divider()

    # --- KPI比較テーブル ---
    st.markdown("### 📈 指標別KPI分析")
    
    kpi_items = ["座数", "客単価", "CVR", "客数"]
    kpi_data = []

    for item in kpi_items:
        # スプレッドシート内で「KPI名」列に各指標が入っていることを想定（または列名）
        # ここでは、詳細シート(df_dtl)から各数値を抽出するロジック
        row_dtl = df_dtl[(df_dtl[store_col] == selected_store) & 
                        (df_dtl[month_col] == selected_month) & 
                        (df_dtl["KPI項目"] == item)] # 項目名は実データに合わせる
        
        # ※もしデータ構造が違う場合は、ここの抽出ロジックを微調整します
        actual = row_dtl["実績"].sum() if not row_dtl.empty else 0
        target = row_dtl["目標"].sum() if not row_dtl.empty else 0
        ly_actual = row_dtl["前年実績"].sum() if not row_dtl.empty else 0 # 2025年分

        kpi_data.append({
            "KPI指標": item,
            "目標": target,
            "実績": actual,
            "目標比": f"{(actual/target*100):.1f}%" if target else "-",
            "前年比": f"{(actual/ly_actual*100):.1f}%" if ly_actual else "-"
        })

    st.table(pd.DataFrame(kpi_data))

except Exception as e:
    st.error(f"レイアウト構成中にエラーが発生しました: {e}")
