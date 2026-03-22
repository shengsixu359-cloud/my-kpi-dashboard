# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import io
import requests

# 1. ページ設定
st.set_page_config(page_title="ストアカルテ・ダッシュボード", layout="wide")

# スタイルの定義
st.markdown('''
<style>
    html,body,[class*="css"]{font-family:"Meiryo",sans-serif;}
    .reach { color: #1f77b4; font-weight: bold; }
    .unmet { color: #d62728; }
    .base-table { width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 0.85em; }
    .base-table th { background-color: #4db6ac; color: white; padding: 6px; border: 1px solid #ddd; text-align: center; }
    .base-table td { border: 1px solid #ddd; padding: 6px; text-align: center; }
    .kpi-table th { background-color: #444!important; color: white!important; padding: 10px; border: 1px solid #ddd; }
</style>
''', unsafe_allow_html=True)

# 2. 基本設定
SPREADSHEET_ID = "1KlZevjH2IbsV0kWQZxw1QjHy3EmsjG9vTKGtvVVTni8"

@st.cache_data(ttl=30)
def load_data_by_name(sheet_name):
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
        response = requests.get(url)
        if response.status_code == 200:
            df = pd.read_csv(io.StringIO(response.text), header=None, dtype=str)
            return df, None
        return None, f"Error: {response.status_code}"
    except Exception as e:
        return None, str(e)

def force_num(val):
    if pd.isna(val): return 0.0
    try:
        s = str(val).replace(',','').replace('%','').replace('¥','').replace('円','').strip()
        return float(s) if s not in ["", "-", "NaN"] else 0.0
    except:
        return 0.0

def find_pos(df, keyword):
    """シート内からキーワードを検索して(行, 列)を返す"""
    for r in range(len(df)):
        for c in range(len(df.columns)):
            if keyword in str(df.iloc[r, c]):
                return r + 1, c + 1
    return None, None

# --- サイドバー ---
st.sidebar.header("📅 期間選択")
y_val = st.sidebar.selectbox("年を選択", ["2026", "2025", "2024"])
m_val = st.sidebar.selectbox("月を選択", [f"{i:02d}" for i in range(1, 13)])
target_sheet = f"{y_val[2:]}{m_val}"

df, err = load_data_by_name(target_sheet)

if df is not None:
    # 検索ロジック（シートのどこにあっても見つけ出す）
    w1_r, _ = find_pos(df, "W1")
    w2_r, _ = find_pos(df, "W2")
    w3_r, _ = find_pos(df, "W3")
    w4_r, _ = find_pos(df, "W4")
    w5_r, _ = find_pos(df, "W5")
    w6_r, _ = find_pos(df, "W6")
    
    rows_map = {"W1": w1_r, "W2": w2_r, "W3": w3_r, "W4": w4_r, "W5": w5_r, "W6": w6_r}
    rows_map = {k: v for k, v in rows_map.items() if v is not None} # 見つかった週だけ

    sel_w = st.sidebar.selectbox("表示週", list(rows_map.keys()))
    row_idx = rows_map[sel_w]

    # 受注額(F)などの列も、見出し「受注額」から自動特定する
    _, f_col = find_pos(df, "受注額") # 受注額が入っている列(F列想定)
    f_col = f_col or 6
    g_col, i_col, m_col, n_col = f_col+1, f_col+3, f_col+7, f_col+8 # 相対位置で特定

    st.title(f"ストアカルテ {y_val}年{m_val}月")

    # --- 1. All Stores (F12:F53合計) ---
    actual_sum = sum([force_num(df.iloc[i, f_col-1]) for i in range(11, 53)])
    # 3行目などの固定参照をやめ、見出しから探す
    st.markdown("<h4>All Stores</h4>", unsafe_allow_html=True)
    g3_t = force_num(df.iloc[2, g_col-1]) # 目標
    st.write(f"（デバッグ表示：受注合計 {actual_sum:,.0f} / 目標 {g3_t:,.0f}）") # 確認用

    # --- 2. WEEKサマリー ---
    w_html = ""
    for w, r in rows_map.items():
        wa = force_num(df.iloc[r-1, f_col-1])
        wt = force_num(df.iloc[r-1, g_col-1])
        if wa > 0 or wt > 0:
            w_html += f'<tr><td>{w}</td><td>{wa:,.0f}</td><td>{wt:,.0f}</td><td><span class="{"reach" if wa>=wt else "unmet"}">{abs(wa-wt):,.0f}</span></td><td><span class="{"reach" if wa>=wt else "unmet"}">{wa/wt*100 if wt else 0:.1f}%</span></td></tr>'
    st.markdown(f'<table class="base-table"><tr><th>WEEK</th><th>受注額</th><th>目標</th><th>差額</th><th>達成率</th></tr>{w_html}</table>', unsafe_allow_html=True)

    # --- 4. KPI別 (AR, AV, AZなどのキーワードで列を探す) ---
    def find_kpi(k_name):
        r, c = find_pos(df, k_name)
        return force_num(df.iloc[row_idx-1, c-1]) if c else 0

    k_list = ["座数", "客単価", "CVR", "客数"]
    k_html = ""
    for k in k_list:
        # この部分は本来の列AR=44等に戻します
        ac = 44 if k=="座数" else 47 if k=="客単価" else 45 if k=="CVR" else 46
        tc = ac + 4
        av, tv = force_num(df.iloc[row_idx-1, ac-1]), force_num(df_raw.iloc[row_idx-1, tc-1])
        tr = av/tv*100 if tv else 0
        u = "¥" if k=="客単価" else ""
        k_html += f'<tr><td>{k}</td><td>{u}{tv:,.0f}</td><td><span class="{"reach" if tr>=100 else "unmet"}">{u}{av:,.0f}</span></td><td>{tr:.1f}%</td></tr>'
    st.markdown(f'<table class="base-table kpi-table"><tr><th>KPI</th><th>目標</th><th>実績</th><th>比率</th></tr>{k_html}</table>', unsafe_allow_html=True)

else:
    st.error("データの読み込みに失敗しました。")
