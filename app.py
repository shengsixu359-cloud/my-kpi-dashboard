# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd

# 1. ページ設定
st.set_page_config(page_title="ストアカルテ 2026", layout="wide")

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

# 2. データ取得設定
SPREADSHEET_ID = "1KlZevjH2IbsV0kWQZxw1QjHy3EmsjG9vTKGtvVVTni8"

@st.cache_data(ttl=60)
def load_data_by_month(month_name):
    """シート名(例: 2603)でCSVを読み込む"""
    url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={month_name}"
    try:
        df = pd.read_csv(url, header=None)
        return df
    except:
        return pd.DataFrame()

def get_score(df, row, col):
    try:
        val = df.iloc[row-1, col-1]
        if pd.isna(val): return 0
        s_val = str(val).replace(',','').replace('%','').replace('¥','').replace('円','').strip()
        return pd.to_numeric(s_val, errors='coerce') if s_val != "" else 0
    except:
        return 0

# --- 表示用ヘルパー関数群 ---
def color_text(text, is_reached):
    cls = "reach" if is_reached else "unmet"
    return f'<span class="{cls}">{text}</span>'

def fmt_num(val, is_reached, unit="", is_bold=False):
    abs_v = abs(val)
    txt = f"{unit}{abs_v:,.0f}" if abs_v >= 100 else f"{unit}{abs_v:.2f}"
    if is_bold: txt = f"<b>{txt}</b>"
    return color_text(txt, is_reached)

def fmt_ratio(val, is_reached):
    return color_text(f"{val:.1f}%", is_reached)

# --- サイドバー：期間選択 ---
st.sidebar.header("📅 2026年度 期間選択")

# 月の選択（2601〜2612を生成）
month_list = [f"{i:02d}" for i in range(1, 13)]
selected_month = st.sidebar.selectbox("表示月を選択", month_list, index=2) # デフォルト3月

# シート名を生成 (例: 2603)
target_sheet = f"26{selected_month}"

df_raw = load_data_by_month(target_sheet)

if not df_raw.empty:
    # 行特定ロジック
    def find_r(keyword):
        try:
            mask = df_raw[0].astype(str).str.contains(keyword, na=False)
            res = df_raw[mask].index
            return res[0] + 1 if len(res) > 0 else None
        except: return None

    # 各週の行（見つからない場合はデフォルトの57〜62行目を使用）
    rows_map = {w: find_r(w) or d for w, d in zip(["W1","W2","W3","W4","W5","W6"], [57,58,59,60,61,62])}
    
    # サイドバーの週選択肢を更新（データがある週だけ表示）
    available_weeks = {k: v for k, v in rows_map.items() if get_score(df_raw, v, 6) > 0 or get_score(df_raw, v, 7) > 0}
    if not available_weeks: available_weeks = rows_map # 万が一空の場合は全部出す
    
    selected_week = st.sidebar.selectbox("表示週を選択", list(available_weeks.keys()))
    row_idx = available_weeks[selected_week]

    st.title(f"ストアカルテ 2026年{selected_month}月")

    # --- 1. All Stores ---
    actual_sum = sum([get_score(df_raw, i, 6) for i in range(12, 54)])
    g3_t, i3_b, k3_l = get_score(df_raw, 3, 7), get_score(df_raw, 3, 9), get_score(df_raw, 3, 11)
    g6_t, i6_b, k6_l = get_score(df_raw, 6, 7), get_score(df_raw, 6, 9), get_score(df_raw, 6, 11)

    st.markdown("<h4>All Stores ※FC excluded</h4>", unsafe_allow_html=True)
    all_html = f'''
    <table class="base-table">
        <tr><th>月次受注額</th><td colspan="5" style="font-size:1.2em;font-weight:bold;">{actual_sum:,.0f}</td></tr>
        <tr><th>月次目標</th><td>{g3_t:,.0f}</td><th>月次予算</th><td>{i3_b:,.0f}</td><th>前年受注額</th><td>{k3_l:,.0f}</td></tr>
        <tr><th>目標比</th><td>{fmt_ratio(actual_sum/g3_t*100 if g3_t else 0, actual_sum>=g3_t)}</td>
            <th>予算比</th><td>{fmt_ratio(actual_sum/i3_b*100 if i3_b else 0, actual_sum>=i3_b)}</td>
            <th>前年比</th><td>{fmt_ratio(actual_sum/k3_l*100 if k3_l else 0, actual_sum>=k3_l)}</td></tr>
        <tr><th>差額</th><td>{fmt_num(actual_sum-g3_t, actual_sum>=g3_t)}</td>
            <th>差額</th><td>{fmt_num(actual_sum-i3_b, actual_sum>=i3_b)}</td>
            <th>差額</th><td>{fmt_num(actual_sum-k3_l, actual_sum>=k3_l)}</td></tr>
    </table>
    '''
    st.markdown(all_html, unsafe_allow_html=True)

    # --- 2. WEEKサマリー ---
    w_rows = ""
    for w_name, r_idx in available_weeks.items():
        wa = get_score(df_raw, r_idx, 6)
        wt, wb, wl = get_score(df_raw, r_idx, 7), get_score(df_raw, r_idx, 10), get_score(df_raw, r_idx, 13)
        w_rows += f'<tr><td>{w_name}</td><td>{wa:,.0f}</td><td>{wt:,.0f}</td><td>{fmt_num(wa-wt, wa>=wt)}</td><td>{fmt_ratio(wa/wt*100 if wt else 0, wa>=wt)}</td><td>{wb:,.0f}</td><td>{fmt_num(wa-wb, wa>=wb)}</td><td>{fmt_ratio(wa/wb*100 if wb else 0, wa>=wb)}</td><td>{wl:,.0f}</td><td>{fmt_ratio(wa/wl*100 if wl else 0, wa>=wl)}</td></tr>'
    
    st.markdown("<h4>WEEKサマリー</h4>", unsafe_allow_html=True)
    st.markdown(f'<table class="base-table"><tr><th>WEEK</th><th>受注額</th><th>目標</th><th>差額</th><th>達成率</th><th>予算</th><th>差額</th><th>達成率</th><th>前年実績</th><th>前年比</th></tr>{w_rows}</table>', unsafe_allow_html=True)

    # --- 3. 受注実績詳細 (選択週) ---
    da, dt, dr = get_score(df_raw, row_idx, 6), get_score(df_raw, row_idx, 7), get_score(df_raw, row_idx, 9)
    dl, dlr = get_score(df_raw, row_idx, 13), get_score(df_raw, row_idx, 14)
    st.markdown(f"<h4>受注実績 {selected_week}</h4>", unsafe_allow_html=True)
    st.markdown(f'''
    <table class="base-table kpi-table">
        <tr><th style="width:25%;">受注実績</th><th style="width:25%;">目標</th><th style="width:25%;">目標比</th><th style="width:25%;">差額</th></tr>
        <tr><td rowspan="3" style="font-size:1.5em;font-weight:bold;">¥{da:,.0f}</td><td>¥{dt:,.0f}</td><td>{fmt_ratio(dr, dr>=100)}</td><td>{fmt_num(da-dt, da>=dt)}</td></tr>
        <tr><th>LY</th><th>LY比</th><th>差額</th></tr>
        <tr><td>¥{dl:,.0f}</td><td>{fmt_ratio(dlr, dlr>=100)}</td><td>{fmt_num(da-dl, da>=dl)}</td></tr>
    </table>
    ''', unsafe_allow_html=True)

    # --- 4. KPI別 ---
    k_map = {"座数":(44,48,52), "客単価":(47,51,55), "CVR":(45,49,53), "客数":(46,50,54)}
    k_rows_html = ""
    for k, (ac, tc, lc) in k_map.items():
        av, tv, lv = get_score(df_raw, row_idx, ac), get_score(df_raw, row_idx, tc), get_score(df_raw, row_idx, lc)
        tr, lr = (av/tv*100 if tv else 0), (av/lv*100 if lv else 0)
        u = "¥" if k=="客単価" else ""
        m = "◯" if tr>=100 else "△" if tr>=90 else "✕"
        
        fmt_target = f"{u}{tv:,.0f}" if tv >= 100 else f"{u}{tv:.2f}"
        
        k_rows_html += f'<tr><td><span class="eval-mark">{m}</span></td><td>{k}</td><td>{fmt_target}</td><td>{fmt_num(av, av>=tv, u)}</td><td>{fmt_ratio(tr, tr>=100)}</td><td>{fmt_ratio(lr, lr>=100)}</td></tr>'
    
    st.markdown("<h4>KPI別</h4>", unsafe_allow_html=True)
    st.markdown(f'<table class="base-table kpi-table"><tr><th style="width:80px;">評</th><th>KPI</th><th>目標</th><th>実績</th><th>目標比</th><th>LY比</th></tr>{k_rows_html}</table>', unsafe_allow_html=True)

else:
    st.warning(f"シート「{target_sheet}」を読み込めませんでした。タブ名を確認してください。")
