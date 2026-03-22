# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd

# 1. ページ設定
st.set_page_config(page_title="ストアカルテ2026年3月", layout="wide")

# スタイルの定義
st.markdown('''
<style>
    html,body,[class*="css"]{font-family:"Meiryo",sans-serif;}
    .reach { color: #1f77b4; font-weight: bold; } /* 達成: ブルー */
    .unmet { color: #d62728; } /* 未達: レッド */
    .eval-mark { font-weight: bold; font-size: 1.2em; }
    .base-table { width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 0.85em; }
    .base-table th { background-color: #4db6ac; color: white; padding: 6px; border: 1px solid #ddd; text-align: center; }
    .base-table td { border: 1px solid #ddd; padding: 6px; text-align: center; }
    .kpi-table th { background-color: #444!important; color: white!important; padding: 10px; border: 1px solid #ddd; }
    h4 { margin-top: 20px; margin-bottom: 10px; border-left: 5px solid #4db6ac; padding-left: 10px; }
</style>
''', unsafe_allow_html=True)

st.title("ストアカルテ2026年3月")

# 2. データ取得
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

# --- 表示用ヘルパー関数群 ---

def color_text(text, is_reached):
    """テキストに色クラスを付けて返す"""
    cls = "reach" if is_reached else "unmet"
    return f'<span class="{cls}">{text}</span>'

def fmt_num(val, is_reached, unit=""):
    """数値をカンマ区切りにし、色を付ける（▲+は付けない）"""
    if val >= 100 or val <= -100:
        txt = f"{unit}{abs(val):,.0f}"
    else:
        txt = f"{unit}{abs(val):.2f}"
    return color_text(txt, is_reached)

def fmt_ratio(val, is_reached):
    """比率を%にし、色を付ける"""
    return color_text(f"{val:.1f}%", is_reached)

df_raw = load_raw_data()

if not df_raw.empty:
    st.sidebar.header("期間選択")
    week_map = {"W1 (3/1)": 57, "W2 (3/2-3/8)": 58, "W3 (3/9-3/15)": 59, "W4 (3/16-3/22)": 60, "W5 (3/23-3/29)": 61, "W6 (3/30-3/31)": 62}
    selected_label = st.sidebar.selectbox("表示週を選択", list(week_map.keys()))
    row_idx = week_map[selected_label]

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
        <tr><th>MTD目標 %</th><td>{fmt_ratio(g2_act/g6_mtd_t*100 if g6_mtd_t else 0, g2_act>=g6_mtd_t)}</td><th>MTD予算 %</th><td>{fmt_ratio(g2_act/i6_mtd_b*100 if i6_mtd_b else 0, g2_act>=i6_mtd_b)}</td><th>MTD前年 %</th><td>{fmt_ratio(g2_act/k6_mtd_l*100 if k6_mtd_l else 0, g2_act>=k6_mtd_l)}</td></tr>
        <tr><th>MTD目標 差額</th><td>{fmt_num(g2_act-g6_mtd_t, g2_act>=g6_mtd_t)}</td><th>MTD予算 差額</th><td>{fmt_num(g2_act-i6_mtd_b, g2_act>=i6_mtd_b)}</td><th>MTD前年 差額</th><td>{fmt_num(g2_act-k6_mtd_l, g2_act>=k6_mtd_l)}</td></tr>
    </table>
    '''
    st.markdown(all_html, unsafe_allow_html=True)

    # --- 2. WEEKサマリー ---
    w_rows = ""
    for w_name, r_idx in week_map.items():
        wa, wt, wb, wl = get_score(df_raw, r_idx, 6), get_score(df_raw, r_idx, 7), get_score(df_raw, r_idx, 10), get_score(df_raw, r_idx, 13)
        w_rows += f'<tr><td>{w_name.split()[0]}</td><td>{wa:,.0f}</td><td>{wt:,.0f}</td><td>{fmt_num(wa-wt, wa>=wt)}</td><td>{fmt_ratio(wa/wt*100 if wt else 0, wa>=wt)}</td><td>{wb:,.0f}</td><td>{fmt_num(wa-wb, wa>=wb)}</td><td>{fmt_ratio(wa/wb*100 if wb else 0, wa>=wb)}</td><td>{wl:,.0f}</td><td>{fmt_ratio(wa/wl*100 if wl else 0, wa>=wl)}</td></tr>'
    
    st.markdown("<h4>WEEKサマリー</h4>", unsafe_allow_html=True)
    st.markdown(f'<table class="base-table"><tr><th>WEEK</th><th>受注額</th><th>目標</th><th>差額</th><th>達成率</th><th>予算</th><th>差額</th><th>達成率</th><th>前年実績</th><th>前年比</th></tr>{w_rows}</table>', unsafe_allow_html=True)

    # --- 3. 受注実績詳細 ---
    da, dt, dr = get_score(df_raw, row_idx, 6), get_score(df_raw, row_idx, 7), get_score(df_raw, row_idx, 9)
    dl, dlr = get_score(df_raw, row_idx, 13), get_score(df_raw, row_idx, 14)
    st.markdown(f"<h4>受注実績 {selected_label}</h4>", unsafe_allow_html=True)
    st.markdown(f'<table class="base-table kpi-table"><tr><th style="width:25%;">受注実績</th><th style="width:25%;">目標</th><th style="width:25%;">目標比</th><th style="width:25%;">差額</th></tr><tr><td rowspan="3" style="font-size:1.5em;font-weight:bold;">¥{da:,.0f}</td><td>¥{dt:,.0f}</td><td>{fmt_ratio(dr, dr>=100)}</td><td>{fmt_num(da-dt, da>=dt)}</td></tr><tr><th>LY</th><th>LY比</th><th>差額</th></tr><tr><td>¥{dl:,.0f}</td><td>{fmt_ratio(dlr, dlr>=100)}</td><td>{fmt_num(da-dl, da>=dl)}</td></tr></table>', unsafe_allow_html=True)

    # --- 4. KPI別 ---
    k_map = {"座数":(44,48,52), "客単価":(47,51,55), "CVR":(45,49,53), "客数":(46,50,54)}
    k_rows = ""
    for k, (ac, tc, lc) in k_map.items():
        av, tv, lv = get_score(df_raw, row_idx, ac), get_score(df_raw, row_idx, tc), get_score(df_raw, row_idx, lc)
        reached = av >= tv
        tr = av/tv*100 if tv else 0
        lr = av/lv*100 if lv else 0
        u = "¥" if k=="客単価" else ""
        m = "◯" if tr>=100 else "△" if tr>=90 else "✕"
        k_rows += f'<tr><td><span class="eval-mark">{m}</span></td><td>{k}</td><td>{tv:,.0f if tv>100 else tv:.2f}</td><td>{fmt_num(av, reached, u)}</td><td>{fmt_ratio(tr, tr>=100)}</td><td>{fmt_ratio(lr, lr>=100)}</td></tr>'
    st.markdown("<h4>KPI別</h4>", unsafe_allow_html=True)
    st.markdown(f'<table class="base-table kpi-table"><tr><th style="width:80px;">評</th><th>KPI</th><th>目標</th><th>実績</th><th>目標比</th><th>LY比</th></tr>{k_rows}</table>', unsafe_allow_html=True)

else:
    st.warning("データを読み込めませんでした。")
