# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd

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
    h4 { margin-top: 20px; margin-bottom: 10px; }
</style>
''', unsafe_allow_html=True)

# 2. 基本設定
SPREADSHEET_ID = "1KlZevjH2IbsV0kWQZxw1QjHy3EmsjG9vTKGtvVVTni8"

@st.cache_data(ttl=30)
def load_data_safe(sheet_name):
    url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    try:
        df = pd.read_csv(url, header=None)
        return df, None
    except Exception as e:
        return None, str(e)

def get_score(df, row, col):
    try:
        if row is None or row <= 0: return 0
        val = df.iloc[row-1, col-1]
        if pd.isna(val): return 0
        s_val = str(val).replace(',','').replace('%','').replace('¥','').replace('円','').strip()
        return pd.to_numeric(s_val, errors='coerce') if s_val != "" else 0
    except:
        return 0

# --- ヘルパー関数 ---

def color_text(text, is_reached):
    cls = "reach" if is_reached else "unmet"
    return f'<span class="{cls}">{text}</span>'

def fmt_num(val, is_reached, unit=""):
    abs_v = abs(val)
    # 100未満（CVRなど）は小数、それ以外は整数カンマ
    txt = f"{unit}{abs_v:,.0f}" if abs_v >= 100 else f"{unit}{abs_v:.2f}"
    return color_text(txt, is_reached)

def fmt_ratio(val, is_reached):
    return color_text(f"{val:.1f}%", is_reached)

# --- サイドバー ---
st.sidebar.header("📅 期間選択")
y_val = st.sidebar.selectbox("年を選択", ["2026", "2025", "2024"])
m_val = st.sidebar.selectbox("月を選択", [f"{i:02d}" for i in range(1, 13)]) # 1月から12月
target_sheet = f"{y_val[2:]}{m_val}"

df_raw, error_detail = load_data_safe(target_sheet)

if df_raw is None:
    st.error(f"シート「{target_sheet}」が見つかりません。")
    st.info(f"スプレッドシートのタブ名が「{target_sheet}」になっているか、共有設定が公開されているか確認してください。")
else:
    # --- 行番号を自動で特定する（検索ルールを強化） ---
    def find_r_advanced(keywords):
        """A列から複数のキーワードのいずれかを含む行を探す"""
        for kw in keywords:
            mask = df_raw[0].astype(str).str.contains(kw, na=False, case=False)
            res = df_raw[mask].index
            if len(res) > 0:
                return res[0] + 1
        return None

    # 各週の行を特定（月によってズレても大丈夫なように予備の行番号もセット）
    rows_map = {
        "W1": find_r_advanced(["W1", "3/1", "1週"]) or 57,
        "W2": find_r_advanced(["W2", "3/2", "2週"]) or 58,
        "W3": find_r_advanced(["W3", "3/9", "3週"]) or 59,
        "W4": find_r_advanced(["W4", "3/16", "4週"]) or 60,
        "W5": find_r_advanced(["W5", "3/23", "5週"]) or 61,
        "W6": find_r_advanced(["W6", "3/30", "6週"]) or 62,
    }

    sel_w = st.sidebar.selectbox("表示週", list(rows_map.keys()))
    row_idx = rows_map[sel_w]

    st.title(f"ストアカルテ {y_val}年{m_val}月")

    # --- 1. All Stores ---
    # F12:F53 (12行目から53行目) を合計
    actual_sum = sum([get_score(df_raw, i, 6) for i in range(12, 54)])
    g3_t = get_score(df_raw, 3, 7)
    i3_b = get_score(df_raw, 3, 9)
    k3_l = get_score(df_raw, 3, 11)
    g6_t, i6_b, k6_l = get_score(df_raw, 6, 7), get_score(df_raw, 6, 9), get_score(df_raw, 6, 11)

    all_html = f'''
    <h4>All Stores ※FC excluded</h4>
    <table class="base-table">
        <tr><th>月次受注額</th><td colspan="5" style="font-size:1.2em;font-weight:bold;">{actual_sum:,.0f}</td></tr>
        <tr><th>月次目標</th><td>{g3_t:,.0f}</td><th>月次予算</th><td>{i3_b:,.0f}</td><th>前年受注額</th><td>{k3_l:,.0f}</td></tr>
        <tr><th>目標比</th><td>{fmt_ratio(actual_sum/g3_t*100 if g3_t else 0, actual_sum>=g3_t)}</td>
            <th>予算比</th><td>{fmt_ratio(actual_sum/i3_b*100 if i3_b else 0, actual_sum>=i3_b)}</td>
            <th>前年比</th><td>{fmt_ratio(actual_sum/k3_l*100 if k3_l else 0, actual_sum>=k3_l)}</td></tr>
        <tr><th>差額</th><td>{fmt_num(actual_sum-g3_t, actual_sum>=g3_t)}</td>
            <th>差額</th><td>{fmt_num(actual_sum-i3_b, actual_sum>=i3_b)}</td>
            <th>差額</th><td>{fmt_num(actual_sum-k3_l, actual_sum>=k3_l)}</td></tr>
        <tr><th>MTD目標</th><td>{g6_t:,.0f}</td><th>MTD予算</th><td>{i6_b:,.0f}</td><th>MTD前年</th><td>{k6_l:,.0f}</td></tr>
        <tr><th>MTD目標 %</th><td>{fmt_ratio(actual_sum/g6_t*100 if g6_t else 0, actual_sum>=g6_t)}</td>
            <th>MTD予算 %</th><td>{fmt_ratio(actual_sum/i6_b*100 if i6_b else 0, actual_sum>=i6_b)}</td>
            <th>MTD前年 %</th><td>{fmt_ratio(actual_sum/k6_l*100 if k6_l else 0, actual_sum>=k6_l)}</td></tr>
        <tr><th>MTD目標 差額</th><td>{fmt_num(actual_sum-g6_t, actual_sum>=g6_t)}</td>
            <th>MTD予算 差額</th><td>{fmt_num(actual_sum-i6_b, actual_sum>=i6_b)}</td>
            <th>MTD前年 差額</th><td>{fmt_num(actual_sum-k6_l, actual_sum>=k6_l)}</td></tr>
    </table>
    '''
    st.markdown(all_html, unsafe_allow_html=True)

    # --- 2. WEEKサマリー ---
    w_rows = ""
    for w, r in rows_map.items():
        wa = get_score(df_raw, r, 6)
        wt, wb, wl = get_score(df_raw, r, 7), get_score(df_raw, r, 10), get_score(df_raw, r, 13)
        # 実績または目標がある週のみ表示
        if wa != 0 or wt != 0:
            w_rows += f'<tr><td>{w}</td><td>{wa:,.0f}</td><td>{wt:,.0f}</td><td>{fmt_num(wa-wt, wa>=wt)}</td><td>{fmt_ratio(wa/wt*100 if wt else 0, wa>=wt)}</td><td>{wb:,.0f}</td><td>{fmt_num(wa-wb, wa>=wb)}</td><td>{fmt_ratio(wa/wb*100 if wb else 0, wa>=wb)}</td><td>{wl:,.0f}</td><td>{fmt_ratio(wa/wl*100 if wl else 0, wa>=wl)}</td></tr>'
    
    st.markdown(f'<h4>WEEKサマリー</h4><table class="base-table"><tr><th>WEEK</th><th>受注額</th><th>目標</th><th>差額</th><th>達成率</th><th>予算</th><th>差額</th><th>達成率</th><th>前年実績</th><th>前年比</th></tr>{w_rows}</table>', unsafe_allow_html=True)

    # --- 3. 受注実績詳細 ---
    da, dt, dr = get_score(df_raw, row_idx, 6), get_score(df_raw, row_idx, 7), get_score(df_raw, row_idx, 9)
    dl, dlr = get_score(df_raw, row_idx, 13), get_score(df_raw, row_idx, 14)
    st.markdown(f'<h4>受注実績 {sel_w}</h4><table class="base-table kpi-table"><tr><th>受注実績</th><th>目標</th><th>目標比</th><th>差額</th></tr><tr><td rowspan="3" style="font-size:1.5em;font-weight:bold;">¥{da:,.0f}</td><td>¥{dt:,.0f}</td><td>{fmt_ratio(dr, dr>=100)}</td><td>{fmt_num(da-dt, da>=dt)}</td></tr><tr><th>LY</th><th>LY比</th><th>差額</th></tr><tr><td>¥{dl:,.0f}</td><td>{fmt_ratio(dlr, dlr>=100)}</td><td>{fmt_num(da-dl, da>=dl)}</td></tr></table>', unsafe_allow_html=True)

    # --- 4. KPI別 ---
    k_map = {"座数":(44,48,52), "客単価":(47,51,55), "CVR":(45,49,53), "客数":(46,50,54)}
    k_rows = ""
    for k, (ac, tc, lc) in k_map.items():
        av, tv, lv = get_score(df_raw, row_idx, ac), get_score(df_raw, row_idx, tc), get_score(df_raw, row_idx, lc)
        reached = av >= tv
        tr = av/tv*100 if tv else 0
        lr = av/lv*100 if lv else 0
        u = "¥" if k=="客単価" else ""
        
        target_txt = f"{u}{tv:,.0f}" if tv >= 100 else f"{u}{tv:.2f}"
        
        k_rows += f'<tr><td><b>{"◯" if tr>=100 else "△" if tr>=90 else "✕"}</b></td><td>{k}</td><td>{target_txt}</td><td>{fmt_num(av, reached, u)}</td><td>{fmt_ratio(tr, tr>=100)}</td><td>{fmt_ratio(lr, lr>=100)}</td></tr>'
    
    st.markdown(f'<h4>KPI別</h4><table class="base-table kpi-table"><tr><th>評</th><th>KPI</th><th>目標</th><th>実績</th><th>目標比</th><th>LY比</th></tr>{k_rows}</table>', unsafe_allow_html=True)
