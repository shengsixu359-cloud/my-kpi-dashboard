# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd

# --- 1. ページ基本設定 ---
st.set_page_config(layout="wide")

# セッション状態の初期化
if 'kpi_comments' not in st.session_state:
    st.session_state.kpi_comments = {}
if 'weekly_summary' not in st.session_state:
    # 総評保存用辞書
    st.session_state.weekly_summary = {}

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

# --- サイドバー・期間設定 ---
if not df_raw.empty:
    st.sidebar.header("期間選択")
    week_map = {"W1 (3/1)": 57, "W2 (3/2-3/8)": 58, "W3 (3/9-3/15)": 59, "W4 (3/16-3/22)": 60, "W5 (3/23-3/29)": 61, "W6 (3/30-3/31)": 62}
    selected_label = st.sidebar.selectbox("表示週を選択", list(week_map.keys()))
    row_idx = week_map[selected_label]
    
    # --- サイドバー・入力フォーム ---
    st.sidebar.markdown("---")
    st.sidebar.subheader(f"{selected_label} 理由/総評入力")
    
    # 1. 各KPIの理由入力
    current_comments = st.session_state.kpi_comments.get(selected_label, {"座数": "", "客単価": "", "CVR": "", "客数": ""})
    updated_comments = {}
    for kpi in ["座数", "客単価", "CVR", "客数"]:
        updated_comments[kpi] = st.sidebar.text_area(f"{kpi}の理由", value=current_comments.get(kpi, ""), key=f"re_{selected_label}_{kpi}", height=80)
    st.session_state.kpi_comments[selected_label] = updated_comments
    
    # 2. 総評入力
    current_summary = st.session_state.weekly_summary.get(selected_label, "")
    st.session_state.weekly_summary[selected_label] = st.sidebar.text_area("■総評 / 今週のアクション", value=current_summary, key=f"sum_{selected_label}", height=150)

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
    .comment-cell { text-align: left !important; font-size: 0.9em; color: #333; min-width: 250px; white-space: pre-wrap; vertical-align: middle; }
    .summary-box { background-color: #f9f9f9; border: 1px solid #ddd; padding: 15px; border-radius: 5px; white-space: pre-wrap; font-size: 0.95em; line-height: 1.6; }
    h4 { margin-top: 20px; margin-bottom: 10px; border-left: none; }
</style>
''', unsafe_allow_html=True)

st.title("ストアカルテ2026年3月")

# --- 表示用ヘルパー関数 ---
def fmt_num_html(val, is_reached, unit=""):
    txt = f"{unit}{abs(val):,.0f}" if abs(val) >= 100 else f"{unit}{abs(val):.2f}"
    cls = "reach" if is_reached else "unmet"
    return f'<span class="{cls}">{txt}</span>'

def fmt_ratio_html(val, is_reached):
    cls = "reach" if is_reached else "unmet"
    return f'<span class="{cls}">{val:.1f}%</span>'

# --- コンテンツ表示 ---
if not df_raw.empty:
    # 1. All Stores
    g2_act = sum([get_score(df_raw, i, 6) for i in range(12, 54)])
    g3_tgt, i3_bg, k3_ly = get_score(df_raw, 3, 7), get_score(df_raw, 3, 9), get_score(df_raw, 3, 11)
    
    st.markdown(f'''
    <h4>All Stores ※FC excluded</h4>
    <table class="base-table">
        <tr><th>月次受注額</th><td colspan="5" style="font-size:1.2em;font-weight:bold;">{g2_act:,.0f}</td></tr>
        <tr><th>月次目標</th><td>{g3_tgt:,.0f}</td><th>月次予算</th><td>{i3_bg:,.0f}</td><th>前年受注額</th><td>{k3_ly:,.0f}</td></tr>
        <tr><th>目標比</th><td>{fmt_ratio_html(g2_act/g3_tgt*100 if g3_tgt else 0, g2_act>=g3_tgt)}</td><th>予算比</th><td>{fmt_ratio_html(g2_act/i3_bg*100 if i3_bg else 0, g2_act>=i3_bg)}</td><th>前年比</th><td>{fmt_ratio_html(g2_act/k3_ly*100 if k3_ly else 0, g2_act>=k3_ly)}</td></tr>
        <tr><th>差額</th><td>{fmt_num_html(g2_act-g3_tgt, g2_act>=g3_tgt)}</td><th>差額</th><td>{fmt_num_html(g2_act-i3_bg, g2_act>=i3_bg)}</td><th>差額</th><td>{fmt_num_html(g2_act-k3_ly, g2_act>=k3_ly)}</td></tr>
    </table>
    ''', unsafe_allow_html=True)

    # 2. WEEKサマリー
    w_rows = ""
    for w_name, r_idx in week_map.items():
        wa, wt, wb, wl = get_score(df_raw, r_idx, 6), get_score(df_raw, r_idx, 7), get_score(df_raw, r_idx, 10), get_score(df_raw, r_idx, 13)
        w_rows += f'<tr><td>{w_name.split()[0]}</td><td>{wa:,.0f}</td><td>{wt:,.0f}</td><td>{fmt_num_html(wa-wt, wa>=wt)}</td><td>{fmt_ratio_html(wa/wt*100 if wt else 0, wa>=wt)}</td><td>{wb:,.0f}</td><td>{fmt_num_html(wa-wb, wa>=wb)}</td><td>{fmt_ratio_html(wa/wb*100 if wb else 0, wa>=wb)}</td><td>{wl:,.0f}</td><td>{fmt_ratio_html(wa/wl*100 if wl else 0, wa>=wl)}</td></tr>'
    st.markdown(f'<h4>WEEKサマリー</h4><table class="base-table"><tr><th>WEEK</th><th>受注額</th><th>目標</th><th>差額</th><th>達成率</th><th>予算</th><th>差額</th><th>達成率</th><th>前年実績</th><th>前年比</th></tr>{w_rows}</table>', unsafe_allow_html=True)

    # 3. 受注実績詳細 (選択週)
    da, dt, dr = get_score(df_raw, row_idx, 6), get_score(df_raw, row_idx, 7), get_score(df_raw, row_idx, 9)
    dl, dlr = get_score(df_raw, row_idx, 13), get_score(df_raw, row_idx, 14)
    st.markdown(f"<h4>受注実績 {selected_label}</h4>", unsafe_allow_html=True)
    st.markdown(f'''
    <table class="base-table kpi-table">
        <tr><th style="width:25%;">受注実績</th><th style="width:25%;">目標</th><th style="width:25%;">目標比</th><th style="width:25%;">差額</th></tr>
        <tr><td rowspan="3" style="font-size:1.5em;font-weight:bold;">¥{da:,.0f}</td><td>¥{dt:,.0f}</td><td>{fmt_ratio_html(dr, dr>=100)}</td><td>{fmt_num_html(da-dt, da>=dt)}</td></tr>
        <tr><th>LY</th><th>LY比</th><th>差額</th></tr>
        <tr><td>¥{dl:,.0f}</td><td>{fmt_ratio_html(dlr, dlr>=100)}</td><td>{fmt_num_html(da-dl, da>=dl)}</td></tr>
    </table>
    ''', unsafe_allow_html=True)

    # 4. KPI別
    k_map = {"座数":(44,48,52), "客単価":(47,51,55), "CVR":(45,49,53), "客数":(46,50,54)}
    k_rows_html = ""
    week_reasons = st.session_state.kpi_comments.get(selected_label, {})

    for k, (ac, tc, lc) in k_map.items():
        av, tv, lv = get_score(df_raw, row_idx, ac), get_score(df_raw, row_idx, tc), get_score(df_raw, row_idx, lc)
        tr, lr = (av/tv*100 if tv else 0), (av/lv*100 if lv else 0)
        u = "¥" if k=="客単価" else ""
        m = "◯" if tr>=100 else "△" if tr>=90 else "✕"
        
        val_tgt = f"{u}{tv:,.0f}" if tv >= 100 else f"{u}{tv:.2f}"
        val_act = fmt_num_html(av, av>=tv, u)
        
        reason = week_reasons.get(k, "").replace("\n", "<br>")
        k_rows_html += f'<tr><td><span class="eval-mark">{m}</span></td><td>{k}</td><td>{val_tgt}</td><td>{val_act}</td><td>{fmt_ratio_html(tr, tr>=100)}</td><td>{fmt_ratio_html(lr, lr>=100)}</td><td class="comment-cell">{reason}</td></tr>'
    
    st.markdown(f'''
    <h4>KPI別</h4>
    <table class="base-table kpi-table">
        <tr><th style="width:40px;">評</th><th style="width:80px;">KPI</th><th style="width:100px;">目標</th><th style="width:100px;">実績</th><th style="width:80px;">目標比</th><th style="width:80px;">LY比</th><th>理由</th></tr>
        {k_rows_html}
    </table>
    ''', unsafe_allow_html=True)

    # 5. 総評 / 今週のアクション
    st.markdown("<h4>■総評 / 今週のアクション</h4>", unsafe_allow_html=True)
    summary_text = st.session_state.weekly_summary.get(selected_label, "")
    if summary_text:
        st.markdown(f'<div class="summary-box">{summary_text}</div>', unsafe_allow_html=True)
    else:
        st.info("サイドバーから総評を入力してください。")

else:
    st.warning("データを読み込めませんでした。")
