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
            # すべてのセルを文字列として読み込む（型エラー防止）
            df = pd.read_csv(io.StringIO(response.text), header=None, dtype=str)
            return df, None
        return None, f"Error: {response.status_code}"
    except Exception as e:
        return None, str(e)

def force_num(val):
    """どんな値が来ても数値に変換を試みる"""
    if pd.isna(val): return 0.0
    try:
        s = str(val).replace(',','').replace('%','').replace('¥','').replace('円','').strip()
        if s == "" or s == "-" or s == "NaN": return 0.0
        return float(s)
    except:
        return 0.0

def find_pos(df, keyword):
    """シート内からキーワードを検索して(行, 列)を返す"""
    for r in range(len(df)):
        for c in range(len(df.columns)):
            if keyword in str(df.iloc[r, c]):
                return r + 1, c + 1
    return None, None

def color_text(text, is_reached):
    cls = "reach" if is_reached else "unmet"
    return f'<span class="{cls}">{text}</span>'

# --- サイドバー ---
st.sidebar.header("📅 期間選択")
y_val = st.sidebar.selectbox("年を選択", ["2026", "2025", "2024"])
m_val = st.sidebar.selectbox("月を選択", [f"{i:02d}" for i in range(1, 13)])
target_sheet = f"{y_val[2:]}{m_val}"

df, err = load_data_by_name(target_sheet)

if df is not None:
    # 行番号を自動特定（全月対応）
    def get_w_row(kw):
        r, _ = find_pos(df, kw)
        return r

    w_rows = {w: get_w_row(w) for w in ["W1","W2","W3","W4","W5","W6"]}
    # 見つかった週だけのリストを作る（エラー防止）
    available_weeks = {k: v for k, v in w_rows.items() if v is not None}
    
    if not available_weeks:
        st.warning(f"シート「{target_sheet}」内に週（W1等）のデータが見当たりません。")
        st.stop()

    sel_w = st.sidebar.selectbox("表示週を選択", list(available_weeks.keys()))
    row_idx = available_weeks[sel_w]

    st.title(f"ストアカルテ {y_val}年{m_val}月")

    # --- 1. All Stores ---
    # F列(6列目)相当。もしズレていたらここを自動化も可能
    f_col = 6
    g_col, i_col, m_col, n_col = 7, 9, 13, 14
    
    actual_sum = sum([force_num(df.iloc[i, f_col-1]) for i in range(11, 53)])
    g3_t = force_num(df.iloc[2, g_col-1])
    i3_b = force_num(df.iloc[2, i_col-1])
    k3_l = force_num(df.iloc[2, m_col-1])

    all_html = f'''
    <table class="base-table">
        <tr><th>月次受注額</th><td colspan="5" style="font-size:1.2em;font-weight:bold;">{actual_sum:,.0f}</td></tr>
        <tr><th>月次目標</th><td>{g3_t:,.0f}</td><th>月次予算</th><td>{i3_b:,.0f}</td><th>前年受注額</th><td>{k3_l:,.0f}</td></tr>
        <tr><th>目標比</th><td>{color_text(f"{actual_sum/g3_t*100 if g3_t else 0:.1f}%", actual_sum>=g3_t)}</td>
            <th>予算比</th><td>{color_text(f"{actual_sum/i3_b*100 if i3_b else 0:.1f}%", actual_sum>=i3_b)}</td>
            <th>前年比</th><td>{color_text(f"{actual_sum/k3_l*100 if k3_l else 0:.1f}%", actual_sum>=k3_l)}</td></tr>
        <tr><th>差額</th><td>{color_text(f"{abs(actual_sum-g3_t):,.0f}", actual_sum>=g3_t)}</td>
            <th>差額</th><td>{color_text(f"{abs(actual_sum-i3_b):,.0f}", actual_sum>=i3_b)}</td>
            <th>差額</th><td>{color_text(f"{abs(actual_sum-k3_l):,.0f}", actual_sum>=k3_l)}</td></tr>
    </table>
    '''
    st.markdown("<h4>All Stores</h4>", unsafe_allow_html=True)
    st.markdown(all_html, unsafe_allow_html=True)

    # --- 2. WEEKサマリー ---
    w_html = ""
    for w, r in available_weeks.items():
        wa = force_num(df.iloc[r-1, f_col-1])
        wt = force_num(df.iloc[r-1, g_col-1])
        wb = force_num(df.iloc[r-1, i_col+1]) # 予算J列
        wl = force_num(df.iloc[r-1, m_col-1]) # 前年M列
        if wa != 0 or wt != 0:
            w_html += f'<tr><td>{w}</td><td>{wa:,.0f}</td><td>{wt:,.0f}</td><td>{color_text(f"{abs(wa-wt):,.0f}", wa>=wt)}</td><td>{color_text(f"{wa/wt*100 if wt else 0:.1f}%", wa>=wt)}</td><td>{wb:,.0f}</td><td>{color_text(f"{abs(wa-wb):,.0f}", wa>=wb)}</td><td>{color_text(f"{wa/wb*100 if wb else 0:.1f}%", wa>=wb)}</td><td>{wl:,.0f}</td><td>{color_text(f"{wa/wl*100 if wl else 0:.1f}%", wa>=wl)}</td></tr>'
    st.markdown(f'<h4>WEEKサマリー</h4><table class="base-table"><tr><th>WEEK</th><th>受注額</th><th>目標</th><th>差額</th><th>達成率</th><th>予算</th><th>差額</th><th>達成率</th><th>前年実績</th><th>前年比</th></tr>{w_html}</table>', unsafe_allow_html=True)

    # --- 3. 受注実績詳細 ---
    da, dt, dr = force_num(df.iloc[row_idx-1, f_col-1]), force_num(df.iloc[row_idx-1, g_col-1]), force_num(df.iloc[row_idx-1, i_col-1])
    dl, dlr = force_num(df.iloc[row_idx-1, m_col-1]), force_num(df.iloc[row_idx-1, n_col-1])
    st.markdown(f'<h4>受注実績 {sel_w}</h4><table class="base-table kpi-table"><tr><th>受注実績</th><th>目標</th><th>目標比</th><th>差額</th></tr><tr><td rowspan="3" style="font-size:1.5em;font-weight:bold;">¥{da:,.0f}</td><td>¥{dt:,.0f}</td><td>{color_text(f"{dr:.1f}%", dr>=100)}</td><td>{color_text(f"{abs(da-dt):,.0f}", da>=dt)}</td></tr><tr><th>LY</th><th>LY比</th><th>差額</th></tr><tr><td>¥{dl:,.0f}</td><td>{color_text(f"{dlr:.1f}%", dlr>=100)}</td><td>{color_text(f"{abs(da-dl):,.0f}", da>=dl)}</td></tr></table>', unsafe_allow_html=True)

    # --- 4. KPI別 ---
    k_map = {"座数":(44,48,52), "客単価":(47,51,55), "CVR":(45,49,53), "客数":(46,50,54)}
    k_html = ""
    for k, (ac, tc, lc) in k_map.items():
        av, tv, lv = force_num(df.iloc[row_idx-1, ac-1]), force_num(df.iloc[row_idx-1, tc-1]), force_num(df.iloc[row_idx-1, lc-1])
        tr, lr = (av/tv*100 if tv else 0), (av/lv*100 if lv else 0)
        u = "¥" if k=="客単価" else ""
        fmt_t = f"{u}{tv:,.0f}" if tv >= 100 else f"{u}{tv:.2f}"
        fmt_a = f"{u}{av:,.0f}" if av >= 100 else f"{u}{av:.2f}"
        k_html += f'<tr><td><b>{"◯" if tr>=100 else "△" if tr>=90 else "✕"}</b></td><td>{k}</td><td>{fmt_t}</td><td>{color_text(fmt_a, av>=tv)}</td><td>{color_text(f"{tr:.1f}%", tr>=100)}</td><td>{color_text(f"{lr:.1f}%", lr>=100)}</td></tr>'
    st.markdown(f'<h4>KPI別</h4><table class="base-table kpi-table"><tr><th>評</th><th>KPI</th><th>目標</th><th>実績</th><th>目標比</th><th>LY比</th></tr>{k_html}</table>', unsafe_allow_html=True)

else:
    st.error("データの読み込みに失敗しました。共有設定やシート名を確認してください。")
