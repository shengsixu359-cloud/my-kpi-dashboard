# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd

# 1. ページ設定
st.set_page_config(page_title="店舗KPIダッシュボード", layout="wide")
st.title("📊 店舗KPI分析レポート")

# 2. データ取得用URL設定
BASE_URL = "https://docs.google.com/spreadsheets/d/1iwGSIWU8aEoW82hzZCI6YO8VufhAc3zR8KnS4OPPMQA/export?format=csv&gid="

# 各シートのgid設定
SHEETS = {
    "carte":  "869736914",   # ① ストアカルテ
    "master": "1673023787",  # ② 店舗データ
    "kpi_d":  "244052959",   # ③ 202603kpi (詳細)
    "kpi_26": "0",           # ④ 202603 (メイン)
    "kpi_25": "12345678"     # ⑤ 202503 (前年)
}

@st.cache_data(ttl=60)
def load_data(gid):
    try:
        df = pd.read_csv(f"{BASE_URL}{gid}")
        # 列名の前後の空白を自動で削除する（エラー防止）
        df.columns = [c.strip() if isinstance(c, str) else c for c in df.columns]
        return df
    except:
        return pd.DataFrame()

try:
    # データの読み込み
    df_master = load_data(SHEETS["master"])
    df_carte = load_data(SHEETS["carte"])
    df_26 = load_data(SHEETS["kpi_26"])
    df_25 = load_data(SHEETS["kpi_25"])
    df_dtl = load_data(SHEETS["kpi_d"])

    # --- 列名の特定（エラー回避策） ---
    # 「店舗名」という列名が見つからない場合、各シートの「1列目」を店舗名とみなす
    def get_col(df, target):
        if target in df.columns: return target
        return df.columns[0] if not df.empty else None

    store_col = get_col(df_master, "店舗名")
    month_col = get_col(df_26, "月")
    week_col = get_col(df_26, "週")

    # --- サイドバー設定 ---
    st.sidebar.header("🔍 表示条件")
    
    if store_col:
        stores = df_master[store_col].dropna().unique()
        selected_store = st.sidebar.selectbox("店舗を選択", stores)
    else:
        st.error("データの読み込みに失敗しました。URLや共有設定を確認してください。")
        st.stop()

    # 期間選択
    if month_col and not df_26.empty:
        months = sorted(df_26[month_col].unique())
        selected_month = st.sidebar.selectbox("表示月を選択", months)
        
        # 週の選択
        if week_col:
            weeks = sorted(df_26[df_26[month_col] == selected_month][week_col].unique())
            selected_week = st.sidebar.multiselect(f"{selected_month}月の表示週", options=weeks)
        else:
            selected_week = []
    else:
        selected_month = None
        selected_week = []

    # --- フィルタリング処理 ---
    def filter_df(df, s_col):
        if df.empty or s_col not in df.columns: return df
        mask = (df[s_col] == selected_store)
        m_col = get_col(df, "月")
        w_col = get_col(df, "週")
        
        if m_col and selected_month:
            mask &= (df[m_col] == selected_month)
        if w_col and selected_week:
            mask &= (df[w_col].isin(selected_week))
        return df[mask]

    f_26 = filter_df(df_26, store_col)
    f_25 = filter_df(df_25, store_col)
    f_dtl = filter_df(df_dtl, store_col)

    # --- 表示エリア ---
    st.subheader(f"📍 {selected_store} の概況")
    st.dataframe(df_carte[df_carte[get_col(df_carte, "店舗名")] == selected_store], hide_index=True)

    st.divider()

    # KPIサマリー
    st.subheader(f"💰 KPIサマリー")
    c1, c2, c3 = st.columns(3)
    
    # 指標列の自動特定（「売上」が含まれる列を探す）
    def find_val_col(df):
        for c in df.columns:
            if "売上" in str(c): return c
        return None

    target_col = find_val_col(f_26)
    
    if target_col:
        val_26 = f_26[target_col].sum()
        val_25 = f_25[target_col].sum() if not f_25.empty else 0
        
        c1.metric("当期実績", f"{val_26:,.0f}")
        if val_25 > 0:
            growth = (val_26 / val_25 * 100)
            c2.metric("前年同期比", f"{growth:.1f}%", delta=f"{(val_26-val_25):,.0f}")
        
    st.divider()

    # 詳細KPI
    st.subheader("📈 詳細KPI推移")
    st.dataframe(f_dtl, hide_index=True)

except Exception as e:
    st.error(f"エラーが発生しました: {e}")
