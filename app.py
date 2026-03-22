# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd

# 1. ページ設定
st.set_page_config(page_title="ストアカルテ2026年3月", layout="wide")

# スタイルの定義
style_html = '''
<style>
    html, body, [class*="css"] { font-family: "Meiryo", "MS PGothic", sans-serif; }
    .reach { color: #1f77b4; font-weight: bold; }
    .unmet { color: #d62728; }
    .eval-mark { font-weight: bold; font-size: 1.2em; display: inline-block; width: 1.5em; text-align: center; }
    
    /* 各種テーブル共通設定 */
    .base-table { width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 0.85em; }
    .base-table th { background-color: #4db6ac; color: white; padding: 6px; border: 1px solid #ddd; text-align: center; }
    .base-table td { border: 1px solid #ddd; padding: 6px; text-align: center; }
    
    /* KPI・受注実績テーブル用（黒ヘッダー） */
    .kpi-table th { background-color: #444; color: white; padding: 10px; text-align: center; border: 1px solid #ddd; }
    .kpi-table td { border: 1px solid #ddd; padding: 8px; text-align: center; }
    
    h4 { margin-top: 20px; margin-bottom: 10px; border-left: 5px solid #4db6ac; padding-left: 10px; }
</style>
'''
st.markdown(style_html, unsafe_allow_html=True)
st.title("ストアカルテ2026年3月")

# 2. データ取得設定
BASE_URL = "https://docs.google.com/spreadsheets/d/1KlZevjH2IbsV0kWQZxw1QjHy3EmsjG9vTKGtvVVTni8/export?format=csv&gid="
SHEET_GID = "1502960872"

@st.cache_data(ttl=60)
def load_raw_data():
    try:
        url = f"{BASE_URL}{SHEET_GID}"
        return pd.read_csv(url, header=None)
    except:
        return pd.DataFrame()

def get_score(df, row_idx, col_idx):
    try:
        val = df.iloc[row_idx-1, col_idx-1]
        if pd.isna(val): return 0
        clean_val = str(val).replace(',', '').replace('%', '').replace('¥', '').replace('円', '').strip()
        return pd.to_numeric(clean_val, errors='coerce')
    except:
        return 0

def col_to_num(col_str):
    num = 0
    for c in col_str.upper():
        num = num * 26 + (ord(c) - ord('A') + 1)
    return num

def format_ratio_text(ratio):
    if pd.isna(ratio) or ratio == 0: return "0.0%"
    return f'<span class="{"reach" if ratio >= 100 else "unmet"}">{ratio:.1f}%</span>'

def diff_fmt(val):
    if pd.isna(val) or val == 0: return "0"
    return f'{"▲" if val < 0 else "+"}{abs(val):,.0f}'

df_raw = load_raw_data()

if not df_raw.empty:
    st.sidebar.header("期間選択")
    week_map = {
        "W1 (3/1)": 57, "W2 (3/2-3/8)": 58, "W3 (3/9-3/15)": 59,
        "W4 (3/16-3/22)": 60, "W5 (3/23-3/29)": 61, "W6 (3/30-3/31)": 62
    }
    selected_week_label = st.sidebar.selectbox("表示週を選択", list(week_map.keys()))
    row_idx = week_map[selected_week_label]

    # --- 1. All Stores サマリー ---
    g2_actual = sum([get_score(df_raw, i, col_to_num("F")) for i in range(12, 54)])
    g3_target = get_score(df_raw, 3, col_to_num("G"))
    i3_budget = get_score(df_raw, 3, col_to_num("I"))
    k3_ly_val = get_score(df_raw, 3, col_to_num("K"))
    g6_mtd_target = get_score(df_raw, 6, col_to_num("G"))
    i6_mtd_budget = get_score(df_raw, 6, col_to_num("I"))
    k6_mtd_ly     = get_score(df_raw, 6, col_to_num("K"))

    all_stores_html = f'''
    <h4>All Stores ※FC excluded</h4>
    <table class="base-table">
        <tr><th style="width:15%;">月次受注額</th><td colspan="5" style="font-size:1.2em; font-weight:bold;">{g2_actual:,.0f}</td></tr>
        <tr><th>月次目標</th><td>{g3_target:,.0f}</td><th>月次予算</th><td>{i3_budget:,.0f}</td><th>前年受注額</th><td>{k3_ly_val:,.0f}</td></tr>
        <tr><th>目標比</th><td>{format_ratio_text(g2_actual/g3_target*100 if g3_target else 0)}</td><th>予算比</th><td>{format_ratio_text(g2_actual/i3_budget*100 if i3_budget else 0)}</td><th>前年比</th><td>{format_ratio_text(g2_actual/k3_ly_val*100 if k3_ly_val else 0)}</td></tr>
        <tr><th>差額</th><td>{diff_fmt(g2_actual - g3_target)}</td><th>差額</th><td>{diff_fmt(g2_actual - i3_budget)}</td><th>差額</th><td>{diff_fmt(g2_actual - k3_ly_val)}</td></tr>
        <tr><th>MTD目標</th><td>{g6_mtd_target:,.0f}</td><th>MTD予算</th><td>{i6_mtd_budget:,.0f}</td><th>MTD前年</th><td>{k6_mtd_ly:,.0f}</td></tr>
        <tr><th>MTD目標 %</th><td>{format_ratio_text(g2_actual/g6_mtd_target*100 if g6_mtd_target else 0)}</td><th>MTD予算 %</th><td>{format_ratio_text(g2_actual/i6_mtd_budget*100 if i6_mtd_budget else 0)}</td><th>MTD前年 %</th><td>{format_ratio_text(g2_actual/k6_mtd_ly*100 if k6_mtd_ly else 0)}</td></tr>
        <tr><th>MTD目標 差額</th><td>{diff_fmt(g2_actual - g6_mtd_target)}</td><th>MTD予算 差額</th><td>{diff_fmt(g2_actual - i6_mtd_budget)}</td><th>MTD前年 差額</th><td>{diff_fmt(g2_actual - k6_mtd_ly)}</td></tr>
    </table>
    '''
    st.markdown(all_stores_html, unsafe_allow_html=True)

    # --- 2. 週別受注額一覧 (WEEKサマリー) ---
    week_rows = ""
    for w_name, r_idx in week_map.items():
        w_act = get_score(df_raw, r_idx, col_to_num("F"))
        w_tgt = get_score(df_raw, r_idx, col_to_num("G"))
        w_bg  = get_score(df_raw, r_idx, col_to_num("J")) # 予算はJ列と仮定
        w_ly  = get_score(df_raw, r_idx, col_to_num("M"))
        week_rows += f'''
        <tr>
            <td>{w_name.split()[0]}</td>
            <td>{w_act:,.0f}</td><td>{w_tgt:,.0f}</td><td>{diff_fmt(w_act-w_tgt)}</td><td>{format_ratio_text(w_act/w_tgt*100 if w_tgt else 0)}</td>
            <td>{w_bg:,.0f}</td><td>{diff_fmt(w_act-w_bg)}</td><td>{format_ratio_text(w_act/w_bg*100 if w_bg else 0)}</td>
            <td>{w_ly:,.0f}</td><td>{format_ratio_text(w_act/w_ly*100 if w_ly else 0)}</td>
        </tr>'''
    
    # 合計(TTL)行
    ttl_html = f'<tr><td style="font-weight:bold; background-color:#f5f5f5;">TTL</td><td style="font-weight:bold;">{g2_actual:,.0f}</td><td colspan="6" style="background-color:#f5f5f5;"></td><td>{k3_ly_val:,.0f}</td><td>{format_ratio_text(g2_actual/k3_ly_val*100 if k3_ly_val else 0)}</td></tr>'

    week_table_html = f'''
    <h4>WEEKサマリー</h4>
    <table class="base-table">
        <tr>
            <th>WEEK</th><th>受注額</th><th>目標</th><th>差額</th><th>達成率</th><th>予算</th><th>差額</th><th>達成率</th><th>前年実績</th><th>前年比</th>
        </tr>
        {week_rows}
        {ttl_html}
    </table>
    '''
    st.markdown(week_table_html, unsafe_allow_html=True)

    # --- 3. 受注実績詳細 (選択週) ---
    act_s, tgt_s, ratio_s = get_score(df_raw, row_idx, col_to_num("F")), get_score(df_raw, row_idx, col_to_num("G")), get_score(df_raw, row_idx, col_to_num("I"))
    ly_s, ly_r = get_score(df_raw, row_idx, col_to_num("M")), get_score(df_raw, row_idx, col_to_num("N"))
    
    detail_html = f'''
    <h4>受注実績 {selected_week_label}</h4>
    <table class="base-table kpi-table">
        <tr><th style="width: 25%;">受注実績</th><th style="width: 25%;">目標</th><th style="width: 25%;">目標比</th><th style="width: 25%;">差額</th></tr>
        <tr><td rowspan="3" style="font-size: 1.5em; font-weight: bold;">¥{act_s:,.0f}</td><td>¥{tgt_s:,.0f}</td><td>{format_ratio_text(ratio_s)}</td><td>{diff_fmt(act_s - tgt_s)}</td></tr>
        <tr><th>LY</th><th>LY比</th><th>差額</th></tr>
        <tr><td>¥{ly_s:,.0f}</td><td>{format_ratio_text(ly_r)}</td><td>{diff_fmt(act_s - ly_s)}</td></tr>
    </table>
    '''
    st.markdown(detail_html, unsafe_allow_html=True)

    # --- 4. KPI別テーブル ---
    kpi_cols = {"座数": {"act": "AR", "tgt": "AV", "ly": "AZ"}, "客単価": {"act": "AU", "tgt": "AY", "ly": "BC"}, "CVR": {"act": "AS", "tgt": "AW", "ly": "BA"}, "客数": {"act": "AT", "tgt": "AX", "ly": "BB"}}
    rows_html = ""
    for item, cols in kpi_cols.items():
        a, t, ly = get_score(df_raw, row_idx, col_to_num(cols["act"])), get_score(df_raw, row_idx, col_to_num(cols["tgt"])), get_score(df_raw, row_idx, col_to_num(cols["ly"]))
        rows_html += f'<tr><td><span class="eval-mark">{"◯" if (a/t*100 if t else 0)>=100 else "△" if (a/t*100 if t else 0)>=90 else "✕"}</span></td><td>{item}</td><td>{f"¥{t:,.0f}" if item=="客単価" else f"{t:,.0f}" if t>100 else f"{t:.2f}"}</td><td>{f"¥{a:,.0f}" if item=="客単価" else f"{a:,.0f}" if a>100 else f"{a:.2f}"}</td><td>{format_ratio_text(a/t*100 if t else 0)}</td><td>{format_ratio_text(a/ly*100 if ly else 0)}</td></tr>'
    st.markdown(f'<h4>KPI別</h4><table class="base-table kpi-table"><tr><th style="width: 80px;">評</th><th>KPI</th><th>目標</th><th>実績</th><th>目標比</th><th>LY比</th></tr>{rows_html}</table>', unsafe_allow_html=True)

else:
    st.warning("データを読み込めませんでした。")
