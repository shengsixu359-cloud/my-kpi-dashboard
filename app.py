# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# --- 1. ページ基本設定 ---
st.set_page_config(page_title="ストアカルテ2026年3月", layout="wide")

# --- 2. Googleスプレッドシート接続設定 ---
try:
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    gc = gspread.authorize(creds)

    SAVE_SHEET_ID = "1_8XbvigwRRIR-HxT5OEDlrKdpW8J9AjYYtjEk33LPIk"
    sh = gc.open_by_key(SAVE_SHEET_ID)
    ws = sh.worksheet("シート1") 
except Exception as e:
    st.error(f"接続エラー: SecretsまたはスプレッドシートIDを確認してください。")
    st.stop()

# 数値データ読み込み
BASE_URL = "https://docs.google.com/spreadsheets/d/1KlZevjH2IbsV0kWQZxw1QjHy3EmsjG9vTKGtvVVTni8/export?format=csv&gid="
SHEET_GID = "1502960872"

@st.cache_data(ttl=5)
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

# --- 3. テキストデータの読み込み（キャッシュなし・直接取得） ---
def get_current_week_text(target_week):
    """スプレッドシートから特定の週のテキストを直接取得する"""
    try:
        rows = ws.get_all_values()
        # 初期値（空欄）
        res = {"zasu": "", "tanka": "", "cvr": "", "kyaku": "", "summary": ""}
        
        if len(rows) <= 1: return res
        
        for row in rows[1:]:
            if len(row) > 0 and row[0] == target_week:
                res["zasu"] = row[1] if len(row) > 1 else ""
                res["tanka"] = row[2] if len(row) > 2 else ""
                res["cvr"] = row[3] if len(row) > 3 else ""
                res["kyaku"] = row[4] if len(row) > 4 else ""
                res["summary"] = row[5] if len(row) > 5 else ""
                break
        return res
    except:
        return {"zasu": "", "tanka": "", "cvr": "", "kyaku": "", "summary": ""}

def save_to_sheet(week_label, zasu, tanka, cvr, kyaku, summary):
    all_data = ws.get_all_values()
    target_row = -1
    for i, row in enumerate(all_data):
        if row and row[0] == week_label:
            target_row = i + 1
            break
    new_row = [week_label, zasu, tanka, cvr, kyaku, summary]
    if target_row != -1:
        ws.update(range_name=f"A{target_row}:F{target_row}", values=[new_row])
    else:
        ws.append_row(new_row)

# --- 4. データ準備 ---
df_raw = load_raw_data()

if not df_raw.empty:
    # サイドバー
    st.sidebar.header("📅 期間選択")
    week_map = {"W1 (3/1)": 57, "W2 (3/2-3/8)": 58, "W3 (3/9-3/15)": 59, "W4 (3/16-3/22)": 60, "W5 (3/23-3/29)": 61, "W6 (3/30-3/31)": 62}
    selected_label = st.sidebar.selectbox("表示週を選択", list(week_map.keys()))
    row_idx = week_map[selected_label]
    
    # 【重要】選択した週のテキストを「今」スプレッドシートから取ってくる
    current_txt = get_current_week_text(selected_label)
    
    with st.sidebar.form("input_form"):
        r_zasu = st.text_area("座数の理由", value=current_txt["zasu"])
        r_tanka = st.text_area("客単価の理由", value=current_txt["tanka"])
        r_cvr = st.text_area("CVR의 理由", value=current_txt["cvr"])
        r_kyaku = st.text_area("客数の理由", value=current_txt["kyaku"])
        sum_text = st.text_area("■総評 / 今週のアクション", value=current_txt["summary"], height=150)
        if st.form_submit_button("全ユーザーに共有保存"):
            save_to_sheet(selected_label, r_zasu, r_tanka, r_cvr, r_kyaku, sum_text)
            st.cache_data.clear()
            st.rerun()

    # --- 5. スタイル設定 ---
    st.markdown(f'''
    <style>
        html, body, [class*="css"] {{ font-family: "Meiryo", sans-serif; color: #3b484e; }}
        .reach {{ color: #58b5ca; font-weight: bold; }}
        .unmet {{ color: #f3a359; font-weight: bold; }}
        .eval-mark {{ font-weight: bold; font-size: 1.2em; }}
        .base-table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 0.85em; background-color: white; }}
        .base-table th {{ background-color: rgba(88, 181, 202, 0.9); color: white; padding: 8px; border: 1px solid #eeece1; text-align: center; }}
        .base-table td {{ border: 1px solid #eeece1; padding: 8px; text-align: center; }}
        .kpi-table th {{ background-color: #3F484F !important; color: #eeece1 !important; }}
        .comment-cell {{ text-align: left !important; background-color: #fdfcf7 !important; white-space: pre-wrap; vertical-align: middle; font-size: 0.9em; }}
        .summary-box {{ background-color: #e1f2f7; border: 1px solid #58b5ca; padding: 15px; border-radius: 4px; white-space: pre-wrap; color: #3b484e; line-height: 1.6; }}
        h4 {{ color: #3b484e; border-bottom: 2px solid #fcde9c; padding-bottom: 5px; margin-top: 25px; }}
    </style>
    ''', unsafe_allow_html=True)

    st.title("📊 ストアカルテ2026年3月")

    def fmt_v(val, cond, unit=""):
        cls = "reach" if cond else "unmet"
        t = f"{unit}{abs(val):,.0f}" if abs(val) >= 100 else f"{unit}{abs(val):.2f}"
        return f'<span class="{cls}">{t}</span>'

    def fmt_p(val, cond):
        cls = "reach" if cond else "unmet"
        return f'<span class="{cls}">{val:.1f}%</span>'

    # --- 6. All Stores ---
    act = sum([get_score(df_raw, i, 6) for i in range(12, 54)])
    tgt, bgt, ly = get_score(df_raw, 3, 7), get_score(df_raw, 3, 9), get_score(df_raw, 3, 11)
    mt, mb, ml = get_score(df_raw, 6, 7), get_score(df_raw, 6, 9), get_score(df_raw, 6, 11)

    st.markdown("<h4>All Stores ※FC excluded</h4>", unsafe_allow_html=True)
    st.markdown(f'''
    <table class="base-table">
        <tr><th style="background-color:#606970;">月次受注額</th><td colspan="5" style="font-size:1.2em;font-weight:bold;">{act:,.0f}</td></tr>
        <tr><th>月次目標</th><td>{tgt:,.0f}</td><th>月次予算</th><td>{bgt:,.0f}</td><th>前年受注</th><td>{ly:,.0f}</td></tr>
        <tr><th>目標比</th><td>{fmt_p(act/tgt*100 if tgt else 0, act>=tgt)}</td><th>予算比</th><td>{fmt_p(act/bgt*100 if bgt else 0, act>=bgt)}</td><th>前年比</th><td>{fmt_p(act/ly*100 if ly else 0, act>=ly)}</td></tr>
        <tr><th>目標差</th><td>{fmt_v(act-tgt, act>=tgt)}</td><th>予算差</th><td>{fmt_v(act-bgt, act>=bgt)}</td><th>前年差</th><td>{fmt_v(act-ly, act>=ly)}</td></tr>
        <tr><th>MTD目標</th><td>{mt:,.0f}</td><th>MTD予算</th><td>{mb:,.0f}</td><th>MTD前年</th><td>{ml:,.0f}</td></tr>
        <tr><th>MTD目標%</th><td>{fmt_p(act/mt*100 if mt else 0, act>=mt)}</td><th>MTD予算%</th><td>{fmt_p(act/mb*100 if mb else 0, act>=mb)}</td><th>MTD前年%</th><td>{fmt_p(act/ml*100 if ml else 0, act>=ml)}</td></tr>
        <tr><th>MTD目標差</th><td>{fmt_v(act-mt, act>=mt)}</td><th>MTD予算差</th><td>{fmt_v(act-mb, act>=mb)}</td><th>MTD前年差</th><td>{fmt_v(act-ml, act>=ml)}</td></tr>
    </table>
    ''', unsafe_allow_html=True)

    # --- 7. Weeklyサマリー ---
    st.markdown("<h4>WEEKサマリー</h4>", unsafe_allow_html=True)
    w_rows = ""
    for w_n, r_i in week_map.items():
        wa, wt, wb, wl = get_score(df_raw, r_i, 6), get_score(df_raw, r_i, 7), get_score(df_raw, r_i, 10), get_score(df_raw, r_i, 13)
        w_rows += f'<tr><td>{w_n.split()[0]}</td><td>{wa:,.0f}</td><td>{wt:,.0f}</td><td>{fmt_v(wa-wt, wa>=wt)}</td><td>{fmt_p(wa/wt*100 if wt else 0, wa>=wt)}</td><td>{wb:,.0f}</td><td>{fmt_v(wa-wb, wa>=wb)}</td><td>{fmt_p(wa/wb*100 if wb else 0, wa>=wb)}</td><td>{wl:,.0f}</td><td>{fmt_p(wa/wl*100 if wl else 0, wa>=wl)}</td></tr>'
    st.markdown(f'<table class="base-table"><tr><th>WEEK</th><th>受注額</th><th>目標</th><th>差額</th><th>達成率</th><th>予算</th><th>差額</th><th>達成率</th><th>前年実績</th><th>前年比</th></tr>{w_rows}</table>', unsafe_allow_html=True)

    # --- 8. KPI別 ---
    st.markdown("<h4>KPI別</h4>", unsafe_allow_html=True)
    k_map = {"座数": (44, 48, 52, "zasu"), "客単価": (47, 51, 55, "tanka"), "CVR": (45, 49, 53, "cvr"), "客数": (46, 50, 54, "kyaku")}
    k_rows = ""
    for k, (ac, tc, lc, r_k) in k_map.items():
        av, tv, lv = get_score(df_raw, row_idx, ac), get_score(df_raw, row_idx, tc), get_score(df_raw, row_idx, lc)
        u = "¥" if k == "客単価" else ""
        m = "◯" if (av/tv if tv else 0) >= 1 else "△" if (av/tv if tv else 0) >= 0.9 else "✕"
        t_s = f"{u}{tv:,.0f}" if tv >= 100 else f"{u}{tv:.2f}"
        
        # 理由をHTML用に整形
        reason_html = str(current_txt[r_k]).replace("\n", "<br>")
        k_rows += f'<tr><td><span class="eval-mark">{m}</span></td><td>{k}</td><td>{t_s}</td><td>{fmt_v(av, av>=tv, u)}</td><td>{fmt_p(av/tv*100 if tv else 0, av>=tv)}</td><td>{fmt_p(av/lv*100 if lv else 0, av>=lv)}</td><td class="comment-cell">{reason_html}</td></tr>'

    st.markdown(f'<table class="base-table kpi-table"><tr><th>評</th><th>KPI</th><th>目標</th><th>実績</th><th>目標比</th><th>LY比</th><th>理由</th></tr>{k_rows}</table>', unsafe_allow_html=True)

    # --- 9. 総評 ---
    st.markdown("<h4>■総評 / 今週のアクション</h4>", unsafe_allow_html=True)
    st.markdown(f'<div class="summary-box">{str(current_txt["summary"])}</div>', unsafe_allow_html=True)

else:
    st.warning("データを読み込めませんでした。")
