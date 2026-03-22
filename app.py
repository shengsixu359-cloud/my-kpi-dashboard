# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd

# 1. ページ設定
st.set_page_config(page_title="ストアカルテ2026年3月", layout="wide")

# メイリオフォントと条件付き書式、テーブルデザインの適用
st.markdown("""
    <style>
    html, body, [class*="css"] {
        font-family: "Meiryo", "MS PGothic", sans-serif;
    }
    .reach { color: #1f77b4; font-weight: bold; } /* 達成: ブルー + 太字 */
    .unmet { color: #d62728; } /* 未達: 赤字 */
    th { background-color: #444 !important; color: white !important; } /* 表の見出しを黒っぽく */
    </style>
    """, unsafe_allow_html=True)

st.title("ストアカルテ2026年3月")

# 2. データ取得設定
BASE_URL = "https://docs.google.com/spreadsheets/d/1KlZevjH2IbsV0kWQZxw1QjHy3EmsjG9vTKGtvVVTni8/export?format=csv&gid="
SHEET_GID = "1502960872"

@st.cache_data(ttl=60)
def load_raw_data():
    try:
        url = f"{BASE_URL}{SHEET_GID}"
        return pd.read_csv(url, header=None)
    except Exception as e:
        st.error(f"データの読み込みに失敗しました: {e}")
        return pd.DataFrame()

def get_score(df, row_idx, col_idx):
    try:
        if df.empty: return 0
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

# 評価記号の判定
def get_eval_mark(ratio):
    if ratio >= 100: return "◯"
    elif ratio >= 90: return "△"
    else: return "✕"

# 数値の書式設定（HTML）
def format_ratio_html(ratio):
    if ratio >= 100:
        return f'<span class="reach">{ratio:.1f}%</span>'
    else:
        return f'<span class="unmet">{ratio:.1f}%</span>'

# --- メイン処理 ---
df_raw = load_raw_data()

if not df_raw.empty:
    st.sidebar.header("期間選択")
    week_map = {
        "W1 (3/1)": 57, "W2 (3/2-3/8)": 58, "W3 (3/9-3/15)": 59,
        "W4 (3/16-3/22)": 60, "W5 (3/23-3/29)": 61, "W6 (3/30-3/31)": 62
    }
    selected_week_label = st.sidebar.selectbox("表示週を選択", list(week_map.keys()))
    row_idx = week_map[selected_week_label]

    # --- 受注実績セクション（表形式に変更） ---
    st.markdown("#### 受注実績")
    
    act_s = get_score(df_raw, row_idx, col_to_num("F")) # 受注実績
    tgt_s = get_score(df_raw, row_idx, col_to_num("G")) # 目標
    ratio_s = get_score(df_raw, row_idx, col_to_num("I")) # 目標比
    diff_s = get_score(df_raw, row_idx, col_to_num("H")) # 差額
    ly_s = get_score(df_raw, row_idx, col_to_num("M")) # LY(前年実績)
    ly_r = get_score(df_raw, row_idx, col_to_num("N")) # LY比
    ly_diff = act_s - ly_s # LY差額

    sales_table = f"""
    <table style="width:100%; border-collapse: collapse; text-align: center; border: 1px solid #ddd;">
        <tr style="background-color: #444; color: white;">
            <th style="padding: 10px;">受注実績</th>
            <th>目標</th>
            <th>目標比</th>
            <th>差額</th>
        </tr>
        <tr>
            <td rowspan="3" style="font-size: 1.2em; font-weight: bold; border: 1px solid #ddd;">¥{act_s:,.0f}</td>
            <td style="border: 1px solid #ddd;">¥{tgt_s:,.0f}</td>
            <td style="border: 1px solid #ddd;">{format_ratio_html(ratio_s)}</td>
            <td style="border: 1px solid #ddd;">¥{diff_s:,.0f}</td>
        </tr>
        <tr style="background-color: #444; color: white;">
            <th>LY</th>
            <th>LY比</th>
            <th>差額</th>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd;">¥{ly_s:,.0f}</td>
            <td style="border: 1px solid #ddd;">{format_ratio_html(ly_r)}</td>
            <td style="border: 1px solid #ddd;">¥{ly_diff:,.0f}</td>
        </tr>
    </table>
    """
    st.write(sales_table, unsafe_allow_html=True)
    st.write("") # スペース用

    # --- KPI別セクション ---
    st.markdown("#### KPI別")
    
    kpi_cols = {
        "座数":   {"act": "AR", "tgt": "AV", "ly": "AZ"},
        "客単価": {"act": "AU", "tgt": "AY", "ly": "BC"},
        "CVR":    {"act": "AS", "tgt": "AW", "ly": "BA"},
        "客数":   {"act": "AT", "tgt": "AX", "ly": "BB"},
    }

    kpi_rows = []
    for item, cols in kpi_cols.items():
        a = get_score(df_raw, row_idx, col_to_num(cols["act"]))
        t = get_score(df_raw, row_idx, col_to_num(cols["tgt"]))
        ly = get_score(df_raw, row_idx, col_to_num(cols["ly"]))

        tr = (a / t * 100) if t else 0
        lr = (a / ly * 100) if ly else 0
        
        unit = "¥" if item == "客単価" else ""
        eval_mark = get_eval_mark(tr) # 評価記号

        kpi_rows.append(f"""
        <tr>
            <td style="border: 1px solid #ddd; padding: 8px;">{eval_mark}</td>
            <td style="border: 1px solid #ddd; padding: 8px;">{item}</td>
            <td style="border: 1px solid #ddd; padding: 8px;">{unit}{t:,.0f if t > 100 else t:.2f}</td>
            <td style="border: 1px solid #ddd; padding: 8px;">{unit}{a:,.0f if a > 100 else a:.2f}</td>
            <td style="border: 1px solid #ddd; padding: 8px;">{format_ratio_html(tr)}</td>
            <td style="border: 1px solid #ddd; padding: 8px;">{format_ratio_html(lr)}</td>
        </tr>
        """)

    kpi_table_html = f"""
    <table style="width:100%; border-collapse: collapse; text-align: center; border: 1px solid #ddd;">
        <tr style="background-color: #444; color: white;">
            <th style="width: 50px;">評</th>
            <th>KPI</th>
            <th>目標</th>
            <th>実績</th>
            <th>目標比</th>
            <th>LY比</th>
        </tr>
        {"".join(kpi_rows)}
    </table>
    """
    st.write(kpi_table_html, unsafe_allow_html=True)

else:
    st.warning("データを読み込めませんでした。")
