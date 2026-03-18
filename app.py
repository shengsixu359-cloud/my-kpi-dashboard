# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd

# 1. ページ設定
st.set_page_config(page_title="店舗KPIダッシュボード", layout="wide")
st.title("📊 店舗KPI分析レポート (月・週フィルタ付)")

# 2. データ取得用URL設定 (gidは実際のスプレッドシートに合わせてください)
BASE_URL = "https://docs.google.com/spreadsheets/d/1iwGSIWU8aEoW82hzZCI6YO8VufhAc3zR8KnS4OPPMQA/export?format=csv&gid="

# 各シートのgidを正確に設定してください
SHEETS = {
    "carte":  "869736914",   # ① ストアカルテ
    "master": "1673023787",  # ② 店舗データ
    "kpi_d":  "244052959",   # ③ 202603kpi (詳細)
    "kpi_26": "0",           # ④ 202603 (メイン)
    "kpi_25": "12345678"     # ⑤ 202503 (前年)
}

@st.cache_data(ttl=60)
def load_data(gid):
    # 日本語エラー回避のため、URL経由でCSVとして読み込み
    try:
        df = pd.read_csv(f"{BASE_URL}{gid}")
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

    # --- サイドバー設定 ---
    st.sidebar.header("🔍 表示条件")
    
    # 店舗選択
    store_col = "店舗名"
    stores = df_master[store_col].dropna().unique()
    selected_store = st.sidebar.selectbox("店舗を選択", stores)

    # 期間選択 (月)
    month_col = "月"
    week_col = "週" # スプレッドシートに「週」という列がある想定
    
    if month_col in df_26.columns:
        months = sorted(df_26[month_col].unique())
        selected_month = st.sidebar.selectbox("表示月を選択", months)
        
        # 選択された月のデータから「週」のリストを作成
        available_weeks = sorted(df_26[df_26[month_col] == selected_month][week_col].unique())
        
        # 週フィルターの追加 (「全週」または特定の週を選択)
        selected_week = st.sidebar.multiselect(
            f"{selected_month}月の表示週を選択 (未選択で全表示)", 
            options=available_weeks,
            default=[]
        )
    else:
        st.sidebar.warning("データに '月' 列が見つかりません")
        selected_month = None
        selected_week = []

    # --- フィルタリング処理 ---
    def filter_data(df):
        if df.empty: return df
        mask = (df[store_col] == selected_store)
        if selected_month:
            mask &= (df[month_col] == selected_month)
        if selected_week:
            mask &= (df[week_col].isin(selected_week))
        return df[mask]

    f_26 = filter_data(df_26)
    f_25 = filter_data(df_25)
    f_dtl = filter_data(df_dtl)

    # --- 表示エリア ---
    
    # 1. ストアカルテ
    st.subheader(f"📍 {selected_store} の概況")
    st.dataframe(df_carte[df_carte[store_col] == selected_store], hide_index=True)

    st.divider()

    # 2. KPIサマリー
    period_label = f"{selected_month} {', '.join(selected_week) if selected_week else '全週'}"
    st.subheader(f"💰 KPIサマリー ({period_label})")
    
    c1, c2, c3 = st.columns(3)
    target_col = "売上"
    
    if target_col in f_26.columns:
        val_26 = f_26[target_col].sum()
        val_25 = f_25[target_col].sum()
        
        diff = val_26 - val_25
        growth = (val_26 / val_25 * 100) if val_25 != 0 else 0
        
        c1.metric("当期実績", f"{val_26:,.0f}円")
        c2.metric("前年同期比", f"{growth:.1f}%", delta=f"{diff:,.0f}円")
        
        if "目標" in f_26.columns:
            target_val = f_26["目標"].sum()
            achieve = (val_26 / target_val * 100) if target_val != 0 else 0
            c3.metric("目標達成率", f"{achieve:.1f}%")

    st.divider()

    # 3. 詳細KPIレポート
    st.subheader(f"📈 詳細KPI推移 (202603kpi)")
    if not f_dtl.empty:
        st.dataframe(f_dtl, use_container_width=True, hide_index=True)
        
        # 数値項目のグラフ化
        num_cols = f_dtl.select_dtypes(include=['number']).columns.tolist()
        if num_cols:
            chart_item = st.selectbox("グラフ表示する指標", num_cols)
            st.bar_chart(f_dtl.set_index(week_col if week_col in f_dtl.columns else month_col)[chart_item])
    else:
        st.info("選択された期間のデータはありません。")

except Exception as e:
    st.error("エラーが発生しました。スプレッドシートの列名やGIDを確認してください。")
    st.info(f"詳細: {e}")
