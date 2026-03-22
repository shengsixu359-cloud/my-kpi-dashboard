# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd

# 1. ページ設定
st.set_page_config(page_title="店舗KPI分析レポート", layout="wide")
st.title("📊 店舗KPI分析レポート")

# 2. データ取得設定
BASE_URL = "https://docs.google.com/spreadsheets/d/1iwGSIWU8aEoW82hzZCI6YO8VufhAc3zR8KnS4OPPMQA/export?format=csv&gid="
SHEETS = {
    "master": "1673023787",  # ② 店舗データ
    "kpi_26": "0",           # ④ 202603
    "kpi_25": "12345678"     # ⑤ 202503 (前年)
}

@st.cache_data(ttl=60)
def load_raw_df(gid):
    try:
        # ヘッダーなしで読み込み、行列番号(0始まり)で制御
        return pd.read_csv(f"{BASE_URL}{gid}", header=None)
    except:
        return pd.DataFrame()

def get_val(df, row_idx, col_idx):
    """行列インデックスから数値を安全に取得"""
    try:
        if df.empty: return 0
        val = df.iloc[row_idx, col_idx]
        clean_val = str(val).replace(',', '').replace('¥', '').replace('円', '').strip()
        return pd.to_numeric(clean_val, errors='coerce')
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
    master_body = raw_master.iloc[1:].copy()
    handler_list = sorted(master_body[4].dropna().unique())
    selected_handler = st.sidebar.selectbox("エリア担当者を選択", handler_list)

    # 2. 店舗選択 (C列 = index 2)
    stores_filtered = master_body[master_body[4] == selected_handler]
    store_list = stores_filtered[2].unique()
    selected_store = st.sidebar.selectbox("店舗を選択", store_list)

    # 3. 表示週を選択 (月曜始まり定義)
    # G列=6, H列=7... と実績が並んでいる想定
    week_options = {
        "全期間": None,
        "W1 (3/1)": 6,          # G列
        "W2 (3/2 - 3/8)": 7,    # H列
        "W3 (3/9 - 3/15)": 8,   # I列
        "W4 (3/16 - 3/22)": 9,  # J列
        "W5 (3/23 - 3/29)": 10, # K列
        "W6 (3/30 - 3/31)": 11  # L列
    }
    selected_week_label = st.sidebar.selectbox("表示週を選択", list(week_options.keys()))
    target_col_idx = week_options[selected_week_label]

    # --- 店舗の行を検索 ---
    # C列(index 2)から選択された店舗名の行を探す
    store_row_idx = None
    for idx, row in raw_26.iterrows():
        if str(row[2]).strip() == str(selected_store).strip():
            store_row_idx = idx
            break

    # --- メイン表示エリア ---
    st.subheader(f"📍 {selected_store} 分析レポート")

    if store_row_idx is not None:
        # 目標値 (F列 = index 5)
        val_target = get_val(raw_26, store_row_idx, 5)
        
        # 実績値 (G列以降)
        if target_col_idx is None:
            # 全期間：G列(6)からL列(11)までを合計
            val_actual = sum([get_val(raw_26, store_row_idx, c) for c in range(6, 12)])
            val_ly = sum([get_val(raw_25, store_row_idx, c) for c in range(6, 12)])
        else:
            # 特定の週
            val_actual = get_val(raw_26, store_row_idx, target_col_idx)
            val_ly = get_val(raw_25, store_row_idx, target_col_idx)

        # --- サマリー表示 ---
        st.markdown("### 🏆 受注実績サマリー")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("受注金額(実績)", f"{val_actual:,.0f}円")
        c2.metric("目標", f"{val_target:,.0f}円" if target_col_idx is None else "-")
        c3.metric("目標比", f"{(val_actual/val_target*100):.1f}%" if val_target and target_col_idx is None else "-")
        c4.metric("目標差額", f"{(val_actual - val_target):,.0f}円" if val_target and target_col_idx is None else "-")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("前年実績", f"{val_ly:,.0f}円")
        c2.metric("前年比", f"{(val_actual/val_ly*100):.1f}%" if val_ly else "-")
        c3.metric("前年差額", f"{(val_actual - val_ly):,.0f}円")

        st.divider()
        st.info(f"※{selected_week_label} のデータを表示中。目標は月間合計値です。")
    else:
        st.warning(f"店舗『{selected_store}』のデータが「202603」シート内に見つかりません。")

except Exception as e:
    st.error(f"システムエラーが発生しました: {e}")
