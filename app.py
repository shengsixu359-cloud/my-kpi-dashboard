# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd

# 1. ページ設定
st.set_page_config(page_title="ストアカルテ2026年3月", layout="wide")

# スタイルの定義
style_html = """
<style>
    html, body, [class*="css"] {
        font-family: "Meiryo", "MS PGothic", sans-serif;
    }
    .reach { color: #1f77b4; font-weight: bold; }
    .unmet { color: #d62728; }
    .kpi-table { width: 100%; border-collapse: collapse; border: 1px solid #ddd; margin-bottom: 20px; }
    .kpi-table th { background-color: #444; color: white; padding: 10px; text-align: center; border: 1px solid #ddd; }
    .kpi-table td { border: 1px solid #ddd; padding: 8px; text-align: center; }
</style>
"""
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
        clean_val = str(val).replace(',', '').replace('%', '').replace('¥', '').replace('円', '').strip()
        return pd.to_numeric(clean_val, errors='coerce')
    except:
        return 0

def col_to_num(col_str):
    num = 0
    for c in col_str.upper():
        num = num * 26 + (ord(c) - ord('A') + 1)
    return num

def get_eval_mark(ratio):
    if ratio >= 100: return "◯"
    elif ratio >= 90: return "△"
    else: return "✕"

def format_ratio_text(ratio):
    # HTMLタグを含めた文字列を返す
    if ratio >= 100:
        return f'<span class="reach">{ratio:.1f}%</span>'
    else:
        return f'<span class="unmet">{ratio:.1f}%</span>'

def num_fmt(val, unit=""):
    if pd.isna(val) or val == 0: return "-"
    return f"{unit}{val:,.0f}" if val >= 100 else f"{unit}{val:.2f}"

df_raw = load_raw_data()

if not df_raw.empty:
    st.sidebar.header("期間選択")
    week_map = {
        "W1 (3/1)": 57, "W2 (3/2-3/8)": 58, "W3 (3/9-3/15)": 59,
        "W4 (3/16-3/22)": 60, "W5 (3/23-3/29)": 61, "W6 (3/30-3/31)": 62
    }
    selected_week_label = st.sidebar.selectbox("表示週を選択", list(week_map.keys()))
    row_idx = week_map[selected_week_label]

    # --- 受注実績テーブル生成 ---
    act_s = get_score(df_raw, row_idx, col_to_num("F"))
    tgt_s = get_score(df_raw, row_idx, col_to_num("G"))
    ratio_s = get_score(df_raw, row_idx, col_to_num("I"))
    diff_s = get_score(df_raw, row_idx, col_to_num("H"))
    ly_s = get_score(df_raw, row_idx, col_to_num("M"))
    ly_r = get_score(df_raw, row_idx, col_to_num("N"))
    ly_diff = act_s - ly_s

    sales_html = f"""
    <h4>受注実績</h4>
    <table class="kpi-table">
        <tr>
            <th style="width: 25%;">受注実績</th>
            <th style="width: 25%;">目標</th>
            <th style="width: 25%;">目標比</th>
            <th style="width: 25%;">差額</th>
        </tr>
        <tr>
            <td rowspan="3" style="font-size: 1.5em; font-weight: bold;">¥{act_s:,.0f}</td>
            <td>¥{tgt_s:,.0f}</td>
            <td>{format_ratio_text(ratio_s)}</td>
            <td>¥{diff_s:,.0f}</td>
        </tr>
        <tr>
            <th>LY</th>
            <th>LY比</th>
            <th>差額</th>
        </tr>
        <tr>
            <td>¥{ly_s:,.0f}</td>
            <td>{format_ratio_text(ly_r)}</td>
            <td>¥{ly_diff:,.0f}</td>
        </tr>
    </table>
    """
    st.markdown(sales_html, unsafe_allow_html=True)

    # --- KPI別テーブル生成 ---
    kpi_cols = {
        "座数":   {"act": "AR", "tgt": "AV", "ly": "AZ"},
        "客単価": {"act": "AU", "tgt": "AY", "ly": "BC"},
        "CVR":    {"act": "AS", "tgt": "AW", "ly": "BA"},
        "客数":   {"act": "AT", "tgt": "AX", "ly": "BB"},
    }

    rows_html = ""
    for item, cols in kpi_cols.items():
        a = get_score(df_raw, row_idx, col_to_num(cols["act"]))
        t = get_score(df_raw, row_idx, col_to_num(cols["tgt"]))
        ly = get_score(df_raw, row_idx, col_to_num(cols["ly"]))
        tr = (a / t * 100) if t else 0
        lr = (a / ly * 100) if ly else 0
        unit = "¥" if item == "客単価" else ""
        
        rows_html += f"""
        <tr>
            <td>{get_eval_mark(tr)}</td>
            <td>{item}</td>
            <td>{num_fmt(t, unit)}</td>
            <td>{num_fmt(a, unit)}</td>
            <td>{format_ratio_text(tr)}</td>
            <td>{format_ratio_text(lr)}</td>
        </tr>
        """

    full_kpi_html = f"""
    <h4>KPI別</h4>
    <table class="kpi-table">
        <tr>
            <th style="width: 80px;">評</th>
            <th>KPI</th>
            <th>目標</th>
            <th>実績</th>
            <th>目標比</th>
            <th>LY比</th>
        </tr>
        {rows_html}
    </table>
    """
    st.markdown(full_kpi_html, unsafe_allow_html=True)

else:
    st.warning("データを読み込めませんでした。")
