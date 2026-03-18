# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd

# 1. ページ設定
st.set_page_config(page_title="店舗KPIダッシュボード", layout="wide")
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
        # 列名の前後の空白を削除
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except:
        return pd.DataFrame()

# 列名を安全に取得する関数（指定した名前がなければ1番目の列を返す）
def get_safe_col(df, target_name):
    if df.empty: return None
    if target_name in df.columns:
        return target_name
    return df.columns[0] # 見つからなければ最初の列を「店舗名」等として扱う

try:
    # データの読み込み
    df_master = load_data(SHEETS["master"])
    df_26 = load_data(SHEETS["kpi_26"])
    df_25 = load_data(SHEETS["kpi_25"])
    df_dtl = load_data(SHEETS["kpi_d"])

    # 各シートの「店舗名」に相当する列名を自動特定
    m_store_col = get_safe_col(df_master, "店舗名")
    k26_store_col = get_safe_col(df_26, "店舗名")
    k25_store_col = get_safe_col(df_25, "店舗名")
    dtl_store_col = get_safe_col(df_dtl, "店舗名")

    # --- サイドバー：条件選択 ---
    st.sidebar.header("🔍 表示条件")
    selected_store = st.sidebar.selectbox("店舗を選択", df_master[m_store_col].unique())
    
    m_col = get_safe_col(df_26, "月")
    months = sorted(df_26[m_col].unique())
    selected_month = st.sidebar.selectbox("表示月を選択", months)
    
    w_col = get_safe_col(df_26, "週")
    weeks = sorted(df_26[df_26[m_col] == selected_month][w_col].unique())
    selected_weeks = st.sidebar.multiselect(f"{selected_month}月の表示週", options=weeks)

    # --- フィルタリング ---
    def filter_df(df, s_col):
        if df.empty: return df
        mask = (df[s_col] == selected_store) & (df[get_safe_col(df, "月")] == selected_month)
        if selected_weeks and get_safe_col(df, "週"):
            mask &= (df[get_safe_col(df, "週")].isin(selected_weeks))
        return df[mask]

    f_26 = filter_df(df_26, k26_store_col)
    f_25 = filter_df(df_25, k25_store_col)

    # --- TOP: 受注実績サマリー ---
    st.markdown("### 🏆 全体受注実績サマリー")
    
    s_col = "受注実績"
    t_col = "目標"
    
    # 指標の計算
    sales_26 = f_26[s_col].sum() if s_col in f_26.columns else 0
    target_26 = f_26[t_col].sum() if t_col in f_26.columns else 0
    sales_25 = f_25[s_col].sum() if s_col in f_25.columns else 0

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

    # 詳細シート(df_dtl)からデータを抽出
    for item in kpi_items:
        # 「KPI項目」または「KPI」という列を探す
        k_col = "KPI項目" if "KPI項目" in df_dtl.columns else (df_dtl.columns[1] if len(df_dtl.columns)>1 else None)
        
        row_dtl = df_dtl[(df_dtl[dtl_store_col] == selected_store) & 
                        (df_dtl[get_safe_col(df_dtl, "月")] == selected_month) & 
                        (df_dtl[k_col] == item)]
        
        actual = row_dtl["実績"].sum() if "実績" in row_dtl.columns else 0
        target = row_dtl["目標"].sum() if "目標" in row_dtl.columns else 0
        # 前年実績は2025年シートまたは詳細シートの特定列から取得（構造に合わせて調整）
        ly_actual = row_dtl["前年実績"].sum() if "前年実績" in row_dtl.columns else 0

        kpi_data.append({
            "KPI指標": item,
            "目標": f"{target:,.0f}" if target > 100 else target,
            "実績": f"{actual:,.0f}" if actual > 100 else actual,
            "目標比": f"{(actual/target*100):.1f}%" if target else "-",
            "前年比": f"{(actual/ly_actual*100):.1f}%" if ly_actual else "-"
        })

    st.table(pd.DataFrame(kpi_data))

except Exception as e:
    st.error(f"エラーが発生しました: {e}")
    st.info("スプレッドシートの1行目の名前が正しいか、またはデータが入っているか確認してください。")
