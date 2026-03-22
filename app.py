# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd

# 1. ページ設定
st.set_page_config(page_title="ストアカルテ2026年3月", layout="wide")

# メイリオフォントの適用と色のスタイル定義
st.markdown("""
    <style>
    html, body, [class*="css"] {
        font-family: "Meiryo", "MS PGothic", sans-serif;
    }
    .reach { color: #1f77b4; font-weight: bold; } /* 達成: ブルー + 太字 */
    .unmet { color: #d62728; } /* 未達: 赤字 */
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

# 数値の書式設定（達成なら太字にするHTMLを返す）
def format_ratio_html(ratio, is_table=False):
    if ratio >= 100:
        color = "#1f77b4" # ブルー
        return f'<span style="color:{color}; font-weight:bold;">{ratio:.1f}%</span>'
    else:
        color = "#d62728" # 赤
        return f'<span style="color:{color};">{ratio:.1f}%</span>'

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

    st.subheader(f"{selected_week_label} 受注・KPIレポート")

    # --- 受注実績サマリー ---
    st.markdown("#### 受注実績")
    
    act_s = get_score(df_raw, row_idx, col_to_num("F"))
    tgt_s = get_score(df_raw, row_idx, col_to_num("G"))
    diff_s = get_score(df_raw, row_idx, col_to_num("H"))
    ratio_s = get_score(df_raw, row_idx, col_to_num("I"))
    ly_s = get_score(df_raw, row_idx, col_to_num("M"))
    ly_r = get_score(df_raw, row_idx, col_to_num("N"))
    ly_diff = act_s - ly_s

    # メトリックの表示
    c1, c2, c3, c4 = st.columns(4)
    c1.write(f"受注実績: **¥{act_s:,.0f}**")
    c2.write(f"受注目標: **¥{tgt_s:,.0f}**")
    c3.markdown(f"目標比: {format_ratio_html(ratio_s)} (差額 ¥{diff_s:,.0f})", unsafe_allow_html=True)
    
    c1, c2, c3, c4 = st.columns(4)
    c1.write(f"前年実績: **¥{ly_s:,.0f}**")
    c2.markdown(f"前年比: {format_ratio_html(ly_r)} (差額 ¥{ly_diff:,.0f})", unsafe_allow_html=True)

    st.divider()

    # --- KPI別 ---
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

        # 通貨記号の付与（客単価のみ¥を付けるなど調整可能）
        unit = "¥" if item == "客単価" else ""

        kpi_rows.append({
            "KPI指標": item,
            "本年実績": f"{unit}{a:,.0f}" if a > 100 else f"{a:.2f}",
            "本年目標": f"{unit}{t:,.0f}" if t > 100 else f"{t:.2f}",
            "目標比": format_ratio_html(tr),
            "前年実績": f"{unit}{ly:,.0f}" if ly > 100 else f"{ly:.2f}",
            "前年比": format_ratio_html(lr)
        })

    # HTMLテーブルとして出力（Pandasの標準テーブルでは色指定が難しいため）
    kpi_df = pd.DataFrame(kpi_rows)
    st.write(kpi_df.to_html(escape=False, index=False), unsafe_allow_html=True)

else:
    st.warning("データを読み込めませんでした。")
