# -*- coding: utf-8 -*-

import streamlit as st

import pandas as pd



# --- データ取得・準備 ---

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



# データの読み込み

df_raw = load_raw_data()



# --- サイドバー・期間設定（page_titleのために先に定義） ---

if not df_raw.empty:

    st.sidebar.header("期間選択")

    week_map = {"W1 (3/1)": 57, "W2 (3/2-3/8)": 58, "W3 (3/9-3/15)": 59, "W4 (3/16-3/22)": 60, "W5 (3/23-3/29)": 61, "W6 (3/30-3/31)": 62}

    selected_label = st.sidebar.selectbox("表示週を選択", list(week_map.keys()))

    row_idx = week_map[selected_label]

    

    # PDFファイル名用：ラベルから「W1」などの文字だけを抽出

    file_period = selected_label.split()[0]

    dynamic_title = f"ストアカルテ2026年3月{file_period}"

else:

    dynamic_title = "ストアカルテ2026年3月"



# 1. ページ設定（ここでPDF保存時のデフォルトファイル名が決まります）

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

    h4 { margin-top: 20px; margin-bottom: 10px; padding-left: 0; border-left: none; }

</style>

''', unsafe_allow_html=True)



st.title("ストアカルテ2026年3月")



# --- 表示用ヘルパー関数群 ---

def color_text(text, is_reached):

    cls = "reach" if is_reached else "unmet"

    return f'<span class="{cls}">{text}</span>'



def fmt_num(val, is_reached, unit="", is_bold=False):

    if abs(val) >= 100:

        txt = f"{unit}{abs(val):,.0f}"

    else:

        txt = f"{unit}{abs(val):.2f}"

    if is_bold:

        txt = f"<b>{txt}</b>"

    return color_text(txt, is_reached)



def fmt_ratio(val, is_reached):

    txt = f"{val:.1f}%"

    return color_text(txt, is_reached)



# --- コンテンツ表示 ---

if not df_raw.empty:

    # --- 1. All Stores ---

    g2_act = sum([get_score(df_raw, i, 6) for i in range(12, 54)])

    g3_tgt, i3_bg, k3_ly = get_score(df_raw, 3, 7), get_score(df_raw, 3, 9), get_score(df_raw, 3, 11)

    g6_mtd_t, i6_mtd_b, k6_mtd_l = get_score(df_raw, 6, 7), get_score(df_raw, 6, 9), get_score(df_raw, 6, 11)



    st.markdown("<h4>All Stores ※FC excluded</h4>", unsafe_allow_html=True)

    all_html = f'''

    <table class="base-table">

        <tr><th>月次受注額</th><td colspan="5" style="font-size:1.2em;font-weight:bold;">{g2_act:,.0f}</td></tr>

        <tr><th>月次目標</th><td>{g3_tgt:,.0f}</td><th>月次予算</th><td>{i3_bg:,.0f}</td><th>前年受注額</th><td>{k3_ly:,.0f}</td></tr>

        <tr><th>目標比</th><td>{fmt_ratio(g2_act/g3_tgt*100 if g3_tgt else 0, g2_act>=g3_tgt)}</td><th>予算比</th><td>{fmt_ratio(g2_act/i3_bg*100 if i3_bg else 0, g2_act>=i3_bg)}</td><th>前年比</th><td>{fmt_ratio(g2_act/k3_ly*100 if k3_ly else 0, g2_act>=k3_ly)}</td></tr>

        <tr><th>差額</th><td>{fmt_num(g2_act-g3_tgt, g2_act>=g3_tgt)}</td><th>差額</th><td>{fmt_num(g2_act-i3_bg, g2_act>=i3_bg)}</td><th>差額</th><td>{fmt_num(g2_act-k3_ly, g2_act>=k3_ly)}</td></tr>

        <tr><th>MTD目標</th><td>{g6_mtd_t:,.0f}</td><th>MTD予算</th><td>{i6_mtd_b:,.0f}</td><th>MTD前年</th><td>{k6_mtd_l:,.0f}</td></tr>

        <tr><th>MTD目標 %</th><td>{fmt_ratio(g2_act/g6_mtd_t*100 if g6_mtd_t else 0, g2_act>=g6_mtd_t)}</td><th>MTD予算 %</th><td>{fmt_ratio(g2_act/i6_mtd_b*100 if i6_mtd_b else 0, g2_act>=i6_mtd_b)}</td><th>MTD前年 %</th><td>{fmt_ratio(g2_act/k6_mtd_l*100 if k6_mtd_l else 0,
