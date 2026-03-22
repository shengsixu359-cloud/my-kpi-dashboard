# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd

# 1. ページ設定
st.set_page_config(page_title="ストアカルテ・ダッシュボード", layout="wide")

# スタイル
st.markdown('''
<style>
    html,body,[class*="css"]{font-family:"Meiryo",sans-serif;}
    .reach { color: #1f77b4; font-weight: bold; }
    .unmet { color: #d62728; }
    .base-table { width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 0.85em; }
    .base-table th { background-color: #4db6ac; color: white; padding: 6px; border: 1px solid #ddd; text-align: center; }
    .base-table td { border: 1px solid #ddd; padding: 6px; text-align: center; }
    .kpi-table th { background-color: #444!important; color: white!important; padding: 10px; border: 1px solid #ddd; }
    h4 { margin-top: 20px; margin-bottom: 10px; padding-left: 0; border-left: none; }
</style>
''', unsafe_allow_html=True)

# 2. 基本設定
SPREADSHEET_ID = "1KlZevjH2IbsV0kWQZxw1QjHy3EmsjG9vTKGtvVVTni8"

@st.cache_data(ttl=30)
def load_data_safe(sheet_name):
    url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    try:
        df = pd.read_csv(url, header=None)
        if df.empty:
            return None, "シートは読み込めましたが、中身が空です。"
        return df, None
    except Exception as e:
        return None, f"読み込みエラー: {e}"

def get_score(df, row, col):
    try:
        val = df.iloc[row-1, col-1]
        if pd.isna(val): return 0
        s_val = str(val).replace(',','').replace('%','').replace('¥','').replace('円','').strip()
        return pd.to_numeric(s_val, errors='coerce') if s_val != "" else 0
    except:
        return 0

def color_text(text, is_reached):
    return f'<span class="{"reach" if is_reached else "unmet"}">{text}</span>'

def fmt_num(val, is_reached, unit=""):
    txt = f"{unit}{abs(val):,.0f}" if abs(val) >= 100 else f"{unit}{abs(val):.2f}"
    return color_text(txt, is_reached)

# --- サイドバー ---
st.sidebar.header("📅 期間選択")
y_val = st.sidebar.selectbox("年を選択", ["2026", "2025", "2024"])
m_val = st.sidebar.selectbox("月を選択", [f"{i:02d}" for i in range(12, 0, -1)])
target_sheet = f"{y_val[2:]}{m_val}"

df_raw, error_msg = load_data_safe(target_sheet)

if error_msg:
    st.error(f"シート「{target_sheet}」の読み込みに失敗しました。")
    st.info("確認事項: 1. スプレッドシートを「リンクを知っている全員」に公開。 2. タブ名を「2603」等の4桁数字にする。")
elif df_raw is not None:
    # 行特定ロジック
    def find_r(keyword):
        try:
            mask = df_raw[0].astype(str).str.contains(keyword, na=False)
            res = df_raw[mask].index
            return res[0] + 1 if len(res) > 0 else None
        except: return None

    # デフォルト行番号とのマッピング
    rows = {w: find_r(w) or d for w, d in zip(["W1","W2","W3","W4","W5","W6"], [57,58,59,60,61,62])}
    sel_w = st.sidebar.selectbox("表示週", list(rows.keys()))
    row_idx = rows[sel_w]

    st.title(f"ストアカルテ {y_val}年{m_val}月")

    # --- 1. All Stores ---
    actual_sum = sum([get_score(df_raw, i, 6) for i in range(12, 54)])
    g3_t = get_score(df_raw, 3, 7) # 目標
    i3_b = get_score(df_raw, 3, 9) # 予算
    k3_l = get_score(df_raw, 3, 11) # 前年
    g6_t = get_score(df_raw, 6, 7) # MTD目標
    i6_b = get_score(df_raw, 6, 9) # MTD予算
    k6_l = get_score(df_raw, 6, 11) # MTD前年

    st.markdown(f'''
    <h4>All Stores ※FC excluded</h4>
    <table class="base-table">
        <tr><th>月次受注額</th><td colspan="5" style="font-size:1.2em;font-weight:bold;">{actual_sum:,.0f}</td></tr>
        <tr><th>月次目標</th><td>{g3_t:,.0f}</td><th>月次予算</th><td>{i3_b:,.0f}</td><th>前年受注額</th><td>{k3_l:,.0f}</td></tr>
        <tr><th>目標比</th><td>{color_text(f"{actual_sum/g3_t*100:.1f}%" if g3_t else "0.0%", actual_sum>=g3_t)}</td>
            <th>予算比</th><td>{color_text(f"{actual_sum/i3_b*100:.1f}%" if i3_b else "0.0%", actual_sum>=i3_b)}</td>
            <th>前年比</th><td>{color_text(f"{actual_sum/k3_l*100:.1f}%" if k3_l else "0.0%", actual_sum>=k3_l)}</td></tr>
        <tr><th>差額</th><td>{fmt_num(actual_sum-g3_t, actual_sum>=g3_t)}</td>
            <th>差額</th><td>{fmt_num(actual_sum-i3_b, actual_sum>=i3_b)}</td>
            <th>差額</th><td>{fmt_num(actual_sum-k3_l, actual_sum>=k3_l)}</td></tr>
        <tr><th>MTD目標</th><td>{g6_t:,.0f}</td><th>MTD予算</th><td>{i6_b:,.0f}</td><th>MTD前年</th><td>{k6_l:,.0f}</td></tr>
        <tr><th>MTD目標 %</th><td>{color_text(f"{actual_sum/g6_t*100:.1f}%" if g6_t else "0.0%", actual_sum>=g6_t)}</td>
            <th>MTD予算 %</th><td>{color_text(f"{actual_sum/i6_b*100:.1f}%" if i6_b else "0.0%", actual_sum>=i6_b)}</td>
            <th>MTD前年 %</th><td>{color_text(f"{actual_sum/k6_l*100:.1f}%" if k6_l else "0.0%", actual_sum>=k6_l)}</td></tr>
        <tr><th>MTD目標 差額</th><td>{fmt_num(actual_sum-g6_t, actual_sum>=g6_t)}</td>
            <th>MTD予算 差額</th><td>{fmt_num(actual_sum-i6_b, actual_sum>=i6_b)}</td>
            <th>MTD前年 差額</th><td>{fmt_num(actual_sum-k6_l, actual_sum>=k6_l)}</td></tr>
    </table>
    ''', unsafe_allow_html=True)

    # --- 2. WEEKサマリー ---
    w_rows_html = ""
    for w, r in rows.items():
        wa = get_score(df_raw, r, 6)
        wt, wb, wl = get_score(df_raw, r, 7), get_score(df_raw, r, 10), get_score(df_raw, r, 13)
        if wa > 0 or wt > 0:
            w_rows_html += f'<tr><td>{w}</td><td>{wa:,.0f}</td><td>{wt:,.0f}</td><td>{fmt_num(wa-wt, wa>=wt)}</td><td>{color_text(f"{wa/wt*100:.1f}%" if wt else "0.0%", wa>=wt)}</td><td>{wb:,.0f}</td><td>{fmt_num(wa-wb, wa>=wb)}</td><td>{color_text(f"{wa/wb*100:.1f}%" if wb else "0.0%", wa>=wb)}</td><td>{wl:,.0f}</td><td>{color_text(f"{wa/wl*100:.1f}%" if wl else "0.0%", wa>=wl)}</td></tr>'
    
    st.markdown(f'<h4>WEEKサマリー</h4><table class="base-table"><tr><th>WEEK</th><th>受注額</th><th>目標</th><th>差額</th><th>達成率</th><th>予算</th><th>差額</th><th>達成率</th><th>前年実績</th><th>前年比</th></tr>{w_rows_html}</table>', unsafe_allow_html=True)

    # --- 3. 受注実績詳細 ---
    da, dt, dr = get_score(df_raw, row_idx, 6), get_score(df_raw, row_idx, 7), get_score(df_raw, row_idx, 9)
    dl, dlr = get_score(df_raw, row_idx, 13), get_score(df_raw, row_idx, 14)
    st.markdown(f'<h4>受注実績 {sel_w}</h4><table class="base-table kpi-table"><tr><th>受注実績</th><th>目標</th><th>目標比</th><th>差額</th></tr><tr><td rowspan="3" style="font-size:1.5em;font-weight:bold;">¥{da:,.0f}</td><td>¥{dt:,.0f}</td><td>{color_text(f"{dr:.1f}%", dr>=100)}</td><td>{fmt_num(da-dt, da>=dt)}</td></tr><tr><th>LY</th><th>LY比</th><th>差額</th></tr><tr><td>¥{dl:,.0f}</td><td>{color_text(f"{dlr:.1f}%", dlr>=100)}</td><td>{fmt_num(da-dl, da>=dl)}</td></tr></table>', unsafe_allow_html=True)

    # --- 4. KPI別 ---
    k_map = {"座数":(44,48,52), "客単価":(47,51,55), "CVR":(45,49,53), "客数":(46,50,54)}
    k_rows = ""
    for k, (ac, tc, lc) in k_map.items():
        av, tv, lv = get_score(df_raw, row_idx, ac), get_score(df_raw, row_idx, tc), get_score(df_raw, row_idx, lc)
        tr = av/tv*100 if tv else 0
        lr = av/lv*100 if lv else 0
        u = "¥" if k=="客単価" else ""
        m = "◯" if tr>=100 else "△" if tr>=90 else "✕"
        k_rows += f'<tr><td><b>{m}</b></td><td>{k}</td><td>{u}{tv:,.0f if tv>=100 else tv:.2f}</td><td>{fmt_num(av, av>=tv, u)}</td><td>{color_text(f"{tr:.1f}%", tr>=100)}</td><td>{color_text(f"{lr:.1f}%", lr>=100)}</td></tr>'
    st.markdown(f'<h4>KPI別</h4><table class="base-table kpi-table"><tr><th>評</th><th>KPI</th><th>目標</th><th>実績</th><th>目標比</th><th>LY比</th></tr>{k_rows}</table>', unsafe_allow_html=True)
