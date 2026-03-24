# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd

# --- 1. ページ設定 ---
# セッション状態の初期化（週ごとのコメント保持用）
if 'kpi_comments' not in st.session_state:
    st.session_state.kpi_comments = {}

# データ取得
BASE_URL = "https://docs.google.com/spreadsheets/d/1KlZevjH2IbsV0kWQZxw1QjHy3EmsjG9vTKGtvVVTni8/export?format=csv&gid="
SHEET_GID = "1502960872"

@st.cache_data(ttl=60)
def load_raw_data():
    try:
        return pd.read_csv(f"{BASE_URL}{SHEET_GID}", header=None)
    except:
        return pd.DataFrame()

def get_score(df, row, col):
    try:
        val = df.iloc[row-1, col-1]
        if pd.isna(val): return 0
        return pd.to_numeric(str(val).replace(',','').replace('%','').replace('¥','').replace('円','').strip(), errors='coerce')
    except: return 0

df_raw = load_raw_data()

# サイドバー設定
if not df_raw.empty:
    st.sidebar.header("期間選択")
    week_map = {"W1 (3/1)": 57, "W2 (3/2-3/8)": 58, "W3 (3/9-3/15)": 59, "W4 (3/16-3/22)": 60, "W5 (3/23-3/29)": 61, "W6 (3/30-3/31)": 62}
    selected_label = st.sidebar.selectbox("表示週を選択", list(week_map.keys()))
    row_idx = week_map[selected_label]
    
    # 理由入力フォーム
    st.sidebar.markdown("---")
    st.sidebar.subheader(f"{selected_label} 理由入力")
    current_comments = st.session_state.kpi_comments.get(selected_label, {"座数": "", "客単価": "", "CVR": "", "客数": ""})
    
    updated_comments = {}
    for kpi in ["座数", "客単価", "CVR", "客数"]:
        # text_areaで入力を受け付ける
        updated_comments[kpi] = st.sidebar.text_area(f"{kpi}の理由", value=current_comments.get(kpi, ""), key=f"in_{selected_label}_{kpi}", height=80)
    st.session_state.kpi_comments[selected_label] = updated_comments

    dynamic_title = f"ストアカルテ2026年3月{selected_label.split()[0]}"
else:
    dynamic_title = "ストアカルテ2026年3月"

st.set_page_config(page_title=dynamic_title, layout="wide")

# スタイルの定義
st.markdown('''
<style>
    html,body,[class*="css"]{font-family:"Meiryo",sans-serif;}
    .reach { color: #1f77b4; font-weight: bold; }
    .unmet { color: #d62728; }
    .eval-mark { font-weight: bold; font-size: 1.2em; }
    .base-table { width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 0.85em; }
    .base-table th { background-color: #4db6ac; color: white; padding: 6px; border: 1px solid #ddd; text-align: center; }
    .base-table td { border: 1px solid #ddd; padding: 6px; text-align: center; }
    .kpi-table th { background-color: #444!important; color: white!important; padding: 10px; border: 1px solid #ddd; }
    .comment-cell { text-align: left !important; font-size: 0.9em; color: #333; min-width: 250px; vertical-align: middle; white-space: pre-wrap; }
    h4 { margin-top: 20px; margin-bottom: 10px; border-left: none; }
</style>
''', unsafe_allow_html=True)

st.title("ストアカルテ2026年3月")

# --- 表示用関数 ---
def fmt_num_span(val, is_reached, unit=""):
    txt = f"{unit}{abs(val):,.0f}" if abs(val) >= 100 else f"{unit}{abs(val):.2f}"
    cls = "reach" if is_reached else "unmet"
    return f'<span class="{cls}">{txt}</span>'

def fmt_ratio_span(val, is_reached):
    cls = "reach" if is_reached else "unmet"
    return f'<span class="{cls}">{val:.1f}%</span>'

# --- コンテンツ ---
if not df_raw.empty:
    # 1. All Stores
    g2_act = sum([get_score(df_raw, i, 6) for i in range(12, 54)])
    g3_tgt, i3_bg, k3_ly = get_score(df_raw, 3, 7), get_score(df_raw, 3, 9), get_score(df_raw, 3, 11)
    
    all_stores_html = f'''
    <h4>All Stores ※FC excluded</h4>
    <table class="base-table">
        <tr><th>月次受注額</th><td colspan="5" style="font-size:1.2em;font-weight:bold;">{g2_act:,.0f}</td></tr>
        <tr><th>
