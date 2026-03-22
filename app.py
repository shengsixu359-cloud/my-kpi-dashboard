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
            df = pd.read_csv(io.StringIO(response.text), header=None)
            return df, None
        else:
            return None, f"アクセス失敗: {response.status_code}"
    except Exception as e:
        return None, str(e)

def get_val(df, row_idx, col_idx):
    try:
        if row_idx is None or row_idx <= 0: return 0
        val = df.iloc[row_idx-1, col_idx-1]
        if pd.isna(val): return 0
        s = str(val).replace(',','').replace('%','').replace('¥','').replace('円','').replace(' ','').strip()
        return pd.to_numeric(s, errors='coerce') or 0
    except:
        return 0

def find_row(df, keyword):
    try:
        # A列(index 0)を最優先で探す
        for i, val in enumerate(df[0]):
            if keyword in str(val):
                return i + 1
        # A列になければ全セルを探す
        for i, row in df.iterrows():
            if any(keyword in str(cell) for cell in row):
                return i + 1
        return None
    except:
        return None

# --- サイドバー ---
st.sidebar.header("📅 期間選択")
y_val = st.sidebar.selectbox("年を選択", ["2026", "2025", "2024"])
m_val = st.sidebar.selectbox("月を選択", [f"{i:02d}" for i in range(1, 13)])
target_sheet = f"{y_val[2:]}{m_val}"

df_raw, err = load_data_by_name(target_sheet)

if df_raw is not None:
    # 行番号を自動特定
    w_rows = {w: find_row(df_raw, w) or d for w, d in zip(["W1","W2","W3","W4","W5","W6"], [57,58,59,60,61,62])}
    sel_w = st.sidebar.selectbox("表示週", list(w_rows.keys()))
    row_idx = w_rows[sel_w]

    st.title(f"ストアカルテ {y_val}年{m_val}月")

    # --- 1. All Stores ---
    actual_sum = sum([get_val(df_raw, i, 6) for i in range(12, 54)])
    g3_t = get_val(df_raw, 3, 7)
    i3_b = get_val(df_raw, 3, 9)
    k3_l = get_val(df_raw, 3, 11)

    all_html = f'''
    <table class="base-table">
        <tr><th>月次受注額</th><td colspan="5" style="font-size:1.2em;font-weight:bold;">{actual_sum:,.0f}</td></tr>
        <tr><th>月次目標</th><td>{g3_t:,.0f}</td><th>月次予算</th><td>{i3_b:,.0f}</td><th>前年受注額</th><td>{k3_l:,.0f}</td></tr>
        <tr><th>目標比</th><td><span class="{"reach" if actual_sum>=g3_t else "unmet"}">{actual_sum/g3_t*100 if g3_t else 0:.1f}%</span></td>
            <th>予算比</th><td><span class="{"reach" if actual_sum>=i3_b else "unmet"}">{actual_sum/i3_b*100 if i3_b else 0:.1f}%</span></td>
            <th>前年比</th><td><span class="{"reach" if actual_sum>=k3_l else "unmet"}">{actual_sum/k3_l*100 if k3_l else 0:.1f}%</span></td></tr>
        <tr><th>差額</th><td><span class="{"reach" if actual_sum>=g3_t else "unmet"}">{abs(actual_sum-g3_t):,.0f}</span></td>
            <th>差額</th><td><span class="{"reach" if actual_sum>=i3_b else "unmet"}">{abs(actual_sum-i3_b):,.0f}</span></td>
            <th>差額</th><td><span class="{"reach" if actual_sum>=k3_l else "unmet"}">{abs(actual_sum-k3_l):,.0f}</span></td></tr>
    </table>
    '''
    st.markdown("<h4>All Stores</h4>", unsafe_allow_html=True)
    st.markdown(all_html, unsafe_allow_html=True)

    # --- 2. WEEKサマリー ---
    w_rows_html = ""
    for w, r in w_rows.items():
        wa = get_val(df_raw, r, 6)
        wt, wb, wl = get_val(df_raw, r, 7), get_val(df_raw, r, 10), get_val(df_raw, r, 13)
        if wa != 0 or wt != 0:
            w_rows_html += f'<tr><td>{w}</td><td>{wa:,.0f}</td><td>{wt:,.0f}</td><td><span class="{"reach" if wa>=wt else "unmet"}">{abs(wa-wt):,.0f}</span></td><td><span class="{"reach" if wa>=wt else "unmet"}">{wa/wt*100 if wt else 0:.1f}%</span></td><td>{wb:,.0f}</td><td><span class="{"reach" if wa>=wb else "unmet"}">{abs(wa-wb):,.0f}</span></td><td><span class="{"reach" if wa>=wb else "unmet"}">{wa/wb*100 if wb else 0:.1f}%</span></td><td>{wl:,.0f}</td><td><span class="{"reach" if wa>=wl else "unmet"}">{wa/wl*100 if wl else 0:.1f}%</span></td></tr>'
    st.markdown(f'<h4>WEEKサマリー</h4><table class="base-table"><tr><th>WEEK</th><th>受注額</th><th>目標</th><th>差額</th><th>達成率</th><th>予算</th><th>差額</th><th>達成率</th><th>前年実績</th><th>前年比</th></tr>{w_rows_html}</table>', unsafe_allow_html=True)

    # --- 3. 受注実績詳細 ---
    da, dt, dr = get_val(df_raw, row_idx, 6), get_val(df_raw, row_idx, 7), get_val(df_raw, row_idx, 9)
    dl, dlr = get_val(df_raw, row_idx, 13), get_val(df_raw, row_idx, 14)
    st.markdown(f'<h4>受注実績 {sel_w}</h4><table class="base-table kpi-table"><tr><th>受注実績</th><th>目標</th><th>目標比</th><th>差額</th></tr><tr><td rowspan="3" style="font-size:1.5em;font-weight:bold;">¥{da:,.0f}</td><td>¥{dt:,.0f}</td><td><span class="{"reach" if dr>=100 else "unmet"}">{dr:.1f}%</span></td><td><span class="{"reach" if da>=dt else "unmet"}">{abs(da-dt):,.0f}</span></td></tr><tr><th>LY</th><th>LY比</th><th>差額</th></tr><tr><td>¥{dl:,.0f}</td><td><span class="{"reach" if dlr>=100 else "unmet"}">{dlr:.1f}%</span></td><td><span class="{"reach" if da>=dl else "unmet"}">{abs(da-dl):,.0f}</span></td></tr></table>', unsafe_allow_html=True)

    # --- 4. KPI別 ---
    k_map = {"座数":(44,48,52), "客単価":(47,51,55), "CVR":(45,49,53), "客数":(46,50,54)}
    k_rows_html = ""
    for k, (ac, tc, lc) in k_map.items():
        av, tv, lv = get_val(df_raw, row_idx, ac), get_val(df_raw, row_idx, tc), get_val(df_raw, row_idx, lc)
        tr, lr = (av/tv*100 if tv else 0), (av/lv*100 if lv else 0)
        u = "¥" if k=="客単価" else ""
        fmt_t = f"{u}{tv:,.0f}" if tv >= 100 else f"{u}{tv:.2f}"
        fmt_a = f"{u}{av:,.0f}" if av >= 100 else f"{u}{av:.2f}"
        k_rows_html += f'<tr><td><b>{"◯" if tr>=100 else "△" if tr>=90 else "✕"}</b></td><td>{k}</td><td>{fmt_t}</td><td><span class="{"reach" if av>=tv else "unmet"}">{fmt_a}</span></td><td><span class="{"reach" if tr>=100 else "unmet"}">{tr:.1f}%</span></td><td><span class="{"reach" if lr>=100 else "unmet"}">{lr:.1f}%</span></td></tr>'
    st.markdown(f'<h4>KPI別</h4><table class="base-table kpi-table"><tr><th>評</th><th>KPI</th><th>目標</th><th>実績</th><th>目標比</th><th>LY比</th></tr>{k_rows_html}</table>', unsafe_allow_html=True)

else:
    st.error(f"シート「{target_sheet}」を読み込めませんでした。")
    st.info("タブ名が「2503」のような数字4桁であることを確認してください。")
