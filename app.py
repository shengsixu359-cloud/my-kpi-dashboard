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
def load_data(gid):
    try:
        df = pd.read_csv(f"{BASE_URL}{gid}")
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except:
        return pd.DataFrame()

# 数値列を安全に合計する関数
def safe_sum(df, col_names):
    for col in col_names:
        if col in df.columns:
            return pd.to_numeric(df[col], errors='coerce').sum()
    return 0

try:
    # データの読み込み
    df_master = load_data(SHEETS["master"])
    df_26 = load_data(SHEETS["kpi_26"])
    df_25 = load_data(SHEETS["kpi_25"])
    df_dtl = load_data(SHEETS["kpi_d"])

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
    month_col = "月" if "月" in df_26.columns else "month"
    months = sorted(df_26[month_col].dropna().unique())
    selected_month = st.sidebar.selectbox("表示月を選択", months)
    
    week_col = "週" if "週" in df_26.columns else "week"
    weeks = ["全週"] + sorted(df_26[df_26[month_col] == selected_month][week_col].dropna().unique().tolist())
    selected_week = st.sidebar.selectbox("表示週を選択", weeks)

    # --- フィルタリング ---
    def filter_df(df):
        if df.empty: return df
        # 各シートで店舗名列を特定してフィルタ
        s_col = "店舗名" if "店舗名" in df.columns else df.columns[0]
        mask = (df[s_col] == selected_store) & (df[month_col] == selected_month)
        if selected_week != "全週":
            mask &= (df[week_col] == selected_week)
        return df[mask]

    f_26 = filter_df(df_26)
    f_25 = filter_df(df_25)

    # --- TOP: 全体受注実績サマリー ---
    st.markdown(f"### 🏆 {selected_store} 受注実績サマリー ({selected_month} / {selected_week})")
    
    # 列名の候補（スプレッドシートの表記ゆれに対応）
    sales_cols = ["受注実績", "実績", "売上", "売上実績"]
    target_cols = ["目標", "受注目標"]

    val_26 = safe_sum(f_26, sales_cols)
    val_target = safe_sum(f_26, target_cols)
    val_25 = safe_sum(f_25, sales_cols)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("受注実績", f"{val_26:,.0f}")
    c2.metric("目標", f"{val_target:,.0f}")
    c3.metric("目標比", f"{(val_26/val_target*100):.1f}%" if val_target else "0%")
    c4.metric("目標差額", f"{(val_26 - val_target):,.0f}")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("前年受注実績", f"{val_25:,.0f}")
    c2.metric("前年比", f"{(val_26/val_25*100):.1f}%" if val_25 else "0%")
    c3.metric("前年差額", f"{(val_26 - val_25):,.0f}")
    st.divider()

    # --- KPI分析テーブル ---
    st.markdown("### 📈 指標別KPI分析")
    
    kpi_items = ["座数", "客単価", "CVR", "客数"]
    kpi_results = []

    for item in kpi_items:
        # 詳細シート(df_dtl)から該当KPIを抽出
        d_store_col = "店舗名" if "店舗名" in df_dtl.columns else df_dtl.columns[0]
        kpi_col = "KPI" if "KPI" in df_dtl.columns else (df_dtl.columns[1] if len(df_dtl.columns)>1 else "")
        
        row_dtl = df_dtl[(df_dtl[d_store_col] == selected_store) & 
                        (df_dtl[month_col] == selected_month) & 
                        (df_dtl[kpi_col] == item)]
        
        if selected_week != "全週":
            row_dtl = row_dtl[row_dtl[week_col] == selected_week]

        act = safe_sum(row_dtl, ["実績", "数値"])
        tgt = safe_sum(row_dtl, ["目標"])
        ly = safe_sum(row_dtl, ["前年実績", "前年"])

        kpi_results.append({
            "KPI指標": item,
            "目標": f"{tgt:,.0f}" if tgt > 100 else f"{tgt:.2f}",
            "実績": f"{act:,.0f}" if act > 100 else f"{act:.2f}",
            "目標比": f"{(act/tgt*100):.1f}%" if tgt else "-",
            "前年比": f"{(act/ly*100):.1f}%" if ly else "-"
        })

    st.table(pd.DataFrame(kpi_results))

except Exception as e:
    st.error(f"表示エラー: {e}")
