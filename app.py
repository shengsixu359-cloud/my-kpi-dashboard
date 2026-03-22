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
    # CSVを読み込む（dtype=strで全て文字列として読み込み、後で変換する）
    url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    try:
        df = pd.read_csv(url, header=None, dtype=str)
        return df, None
    except Exception as e:
        return None, str(e)

def get_score(df, row, col):
    try:
        if row is None or col is None: return 0
        val = df.iloc[row-1, col-1]
        if pd.isna(val): return 0
        # 文字列から数値への変換を強化（不要な文字をすべて消す）
        s_val = str(val).replace(',','').replace('%','').replace('¥','').replace('円','').strip()
        # 空文字やハイフンの場合は0を返す
        if s_val in ["", "-", "NaN"]: return 0
        return pd.to_numeric(s_val, errors='coerce') or 0
    except:
        return 0

# --- 表示用ヘルパー関数群 ---

def color_text(text, is_reached):
    cls = "reach" if is_reached else "unmet"
    return f'<span class="{cls}">{text}</span>'

def fmt_num(val, is_reached, unit="", is_bold=False):
    abs_v = abs(val)
    if abs_v >= 100:
        txt = f"{unit}{abs_v:,.0f}"
    else:
        txt = f"{unit}{abs_v:.2f}"
    if is_bold: txt = f"<b>{txt}</b>"
    return color_text(txt, is_reached)

def fmt_ratio(val, is_reached):
    return color_text(f"{val:.1f}%", is_reached)

# --- サイドバー ---
st.sidebar.header("📅 期間選択")
y_val = st.sidebar.selectbox("年を選択", ["2026", "2025", "2024"])
m_val = st.sidebar.selectbox("月を選択", [f"{i:02d}" for i in range(12, 0, -1)])
target_sheet = f"{y_val[2:]}{m_val}" 

df_raw, error_detail = load_data_safe(target_sheet)

if df_raw is None:
    st.error(f"シート「{target_sheet}」が読み込めませんでした。")
else:
    # 行特定ロジック
    def find_r(keyword):
        try:
            mask = df_raw[0].astype(str).str.contains(keyword, na=False)
            res = df_raw[mask].index
            return res[0] + 1 if len(res) > 0 else None
        except: return None

    # 各週の行（見つからない場合はデフォルト行）
    rows_map = {w: find_r(w) or d for w, d in zip(["W1","W2","W3","W4","W5","W6"], [57,58,59,60,61,62])}
    sel_w = st.sidebar.selectbox("表示週", list(rows_map.keys()))
    row_idx = rows_map[sel_w]

    st.title(f"ストアカルテ {y_val}年{m_val}月")

    # --- 1. All Stores ---
    # F列(6列目) 12行から53行の合計
    actual_sum = sum([get_score(df_raw, i, 6) for i in range(12, 54)])
    g3_t = get_score(df_raw, 3, 7)
    i3_b = get_score(df_raw, 3, 9)
    k3_l = get_score(df_raw, 3, 11)
    g6_t, i6_b, k6_l = get_score(df_raw, 6, 7), get_score(df_raw, 6, 9), get_score(df_raw, 6, 11)

    all_html = f'''
    <h4>All Stores</h4>
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
    w_rows_html = ""
    for w, r in rows_map.items():
        wa = get_score(df_raw, r, 6)
        wt, wb, wl = get_score(df_raw, r, 7), get_score(df_raw, r, 10), get_score(df_raw, r, 13)
        if wa > 0 or wt > 0:
            w_rows_html += f'<tr><td>{w}</td><td>{wa:,.0f}</td><td>{wt:,.0f}</td><td>{fmt_num(wa-wt, wa>=wt)}</td><td>{fmt_ratio(wa/wt*100 if wt else 0, wa>=wt)}</td><td>{wb:,.0f}</td><td>{fmt_num(wa-wb, wa>=wb)}</td><td>{fmt_ratio(wa/wb*100 if wb else 0, wa>=wb)}</td><td>{wl:,.0f}</td><td>{fmt_ratio(wa/wl*100 if wl else 0, wa>=wl)}</td></tr>'
    
    st.markdown(f'<h4>WEEKサマリー</h4><table class="base-table"><tr><th>WEEK</th><th>受注額</th><th>目標</th><th>差額</th><th>達成率</th><th>予算</th><th>差額</th><th>達成率</th><th>前年実績</th><th>前年比</th></tr>{w_rows_html}</table>', unsafe_allow_html=True)

    # --- 3. 受注実績詳細 ---
    # 受注実績(F:6), 目標(G:7), 目標比(I:9), LY(M:13), LY比(N:14)
    da = get_score(df_raw, row_idx, 6)
    dt = get_score(df_raw, row_idx, 7)
    dr = get_score(df_raw, row_idx, 9)
    dl = get_score(df_raw, row_idx, 13)
    dlr = get_score(df_raw, row_idx, 14)
    
    st.markdown(f'<h4>受注実績 {sel_w}</h4><table class="base-table kpi-table"><tr><th>受注実績</th><th>目標</th><th>目標比</th><th>差額</th></tr><tr><td rowspan="3" style="font-size:1.5em;font-weight:bold;">¥{da:,.0f}</td><td>¥{dt:,.0f}</td><td>{fmt_ratio(dr, dr>=100)}</td><td>{fmt_num(da-dt, da>=dt)}</td></tr><tr><th>LY</th><th>LY比</th><th>差額</th></tr><tr><td>¥{dl:,.0f}</td><td>{fmt_ratio(dlr, dlr>=100)}</td><td>{fmt_num(da-dl, da>=dl)}</td></tr></table>', unsafe_allow_html=True)

    # --- 4. KPI別 ---
    # 座数(AR:44), 客単価(AU:47), CVR(AS:45), 客数(AT:46)
    # それぞれの実績に対応する目標列(AR+4=AV:48, AU+4=AY:51, AS+4=AW:49, AT+4=AX:50)
    k_map = {
        "座数":   {"act": 44, "tgt": 48, "ly": 52},
        "客単価": {"act": 47, "tgt": 51, "ly": 55},
        "CVR":    {"act": 45, "tgt": 49, "ly": 53},
        "客数":   {"act": 46, "tgt": 50, "ly": 54},
    }
    k_rows = ""
    for k, cols in k_map.items():
        av = get_score(df_raw, row_idx, cols["act"])
        tv = get_score(df_raw, row_idx, cols["tgt"])
        lv = get_score(df_raw, row_idx, cols["ly"])
        
        tr = (av/tv*100) if tv else 0
        lr = (av/lv*100) if lv else 0
        u = "¥" if k=="客単価" else ""
        m = "◯" if tr>=100 else "△" if tr>=90 else "✕"
        
        # 目標・実績の整形（CVRは小数点対応）
        f_tgt = f"{u}{tv:,.0f}" if tv >= 100 else f"{u}{tv:.2f}"
        f_act = fmt_num(av, av>=tv, u)
        
        k_rows += f'<tr><td><b>{m}</b></td><td>{k}</td><td>{f_tgt}</td><td>{f_act}</td><td>{fmt_ratio(tr, tr>=100)}</td><td>{fmt_ratio(lr, lr>=100)}</td></tr>'
    
    st.markdown(f'<h4>KPI別</h4><table class="base-table kpi-table"><tr><th>評</th><th>KPI</th><th>目標</th><th>実績</th><th>目標比</th><th>LY比</th></tr>{k_rows}</table>', unsafe_allow_html=True)
