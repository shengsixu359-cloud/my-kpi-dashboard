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

    # 保存用スプレッドシートID
    SAVE_SHEET_ID = "1_8XbvigwRRIR-HxT5OEDlrKdpW8J9AjYYtjEk33LPIk"
    sh = gc.open_by_key(SAVE_SHEET_ID)
    ws = sh.worksheet("シート1") 
except Exception as e:
    st.error(f"スプレッドシート接続エラー: SecretsまたはIDを確認してください。")
    st.stop()

# 数値データ読み込み用URL
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

def get_saved_data():
    try:
        data = ws.get_all_records()
        return {row['週']: row for row in data}
    except:
        return {}

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

# --- 3. データ準備 ---
df_raw = load_raw_data()
saved_dict = get_saved_data()

if not df_raw.empty:
    # サイドバー
    st.sidebar.header("📅 期間選択")
    week_map = {"W1 (3/1)": 57, "W2 (3/2-3/8)": 58, "W3 (3/9-3/15)": 59, "W4 (3/16-3/22)": 60, "W5 (3/23-3/29)": 61, "W6 (3/30-3/31)": 62}
    selected_label = st.sidebar.selectbox("表示週を選択", list(week_map.keys()))
    row_idx = week_map[selected_label]
    
    current_data = saved_dict.get(selected_label, {"座数理由": "", "客単価理由":"", "CVR理由":"", "客数理由":"", "総評":""})
    
    with st.sidebar.form("input_form"):
        r_zasu = st.text_area("座数の理由", value=current_data.get("座数理由",""))
        r_tanka = st.text_area("客単価の理由", value=current_data.get("客単価理由",""))
        r_cvr = st.text_area("CVRの理由", value=current_data.get("CVR理由",""))
        r_kyaku = st.text_area("客数の理由", value=current_data.get("客数理由",""))
        sum_text = st.text_area("■総評 / 今週のアクション", value=current_data.get("総評",""), height=150)
        if st.form_submit_button("全ユーザーに共有保存"):
            save_to_sheet(selected_label, r_zasu, r_tanka, r_cvr, r_kyaku, sum_text)
            st.cache_data.clear()
            st.rerun()

    # --- 4. スタイル設定 ---
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
        .comment-cell {{ text-align: left !important; background-color: #fdfcf7 !important; white-space: pre-wrap; vertical-align: middle; color: #3b484e; }}
        .summary-box {{ background-color: #e1f2f7; border: 1px solid #58b5ca; padding: 15px; border-radius: 4px; white-space: pre-wrap; color: #3b484e; }}
        h4 {{ color: #3b484e; border-bottom: 2px solid #fcde9c; padding-bottom: 5px; }}
    </style>
    ''', unsafe_allow_html=True)

    st.title("📊 ストアカルテ2026年3月")

    def fmt_val(v, cond, unit=""):
        cls = "reach" if cond else "unmet"
        txt = f"{unit}{v:,.0f}" if abs(v) >= 100 else f"{unit}{v:.2f}"
        return f'<span class="{cls}">{txt}</span>'

    def fmt_pct(v, cond):
        cls = "reach" if cond else "unmet"
        return f'<span class="{cls}">{v:.1f}%</span>'

    # --- 5. All Stores ---
    act = sum([get_score(df_raw, i, 6) for i in range(12, 54)])
    tgt, bgt, ly = get_score(df_raw, 3, 7), get_score(df_raw, 3, 9), get_score(df_raw, 3, 11)
    mt, mb, ml = get_score(df_raw, 6, 7), get_score(df_raw, 6, 9), get_score(df_raw, 6, 11)

    st.markdown("<h4>All Stores ※FC excluded</h4>", unsafe_allow_html=True)
    st.markdown(f'''
    <table class="base-table">
        <tr><th style="background-color:#606970;">月次受注額</th><td colspan="5" style="font-size:1.2em;font-weight:bold;">{act:,.0f}</td></tr>
        <tr><th>月次目標</th><td>{tgt:,.0f}</td><th>月次予算</th><td>{bgt:,.0f}</td><th>前年受注</th><td>{ly:,.0f}</td></tr>
        <tr><th>目標比</th><td>{fmt_pct(act/tgt*100, act>=tgt)}</td><th>予算比</th><td>{fmt_pct(act/bgt*100, act>=bgt)}</td><th>前年比</th><td>{fmt_pct(act/ly*100, act>=ly)}</td></tr>
        <tr><th>目標差</th><td>{fmt_val(act-tgt, act>=tgt)}</td><th>予算差</th><td>{fmt_val(act-bgt, act>=bgt)}</td><th>前年差</th><td>{fmt_val(act-ly, act>=ly)}</td></tr>
        <tr><th>MTD目標</th><td>{mt:,.0f}</td><th>MTD予算</th><td>{mb:,.0f}</td><th>MTD前年</th><td>{ml:,.0f}</td></tr>
        <tr><th>MTD目標%</th><td>{fmt_pct(act/mt*100, act>=mt)}</td><th>MTD予算%</th><td>{fmt_pct(act/mb*100, act>=mb)}</td><th>MTD前年%</th><td>{fmt_pct(act/ml*100, act>=ml)}</td></tr>
    </table>
    ''', unsafe_allow_html=True)

    # --- 6. KPI別 ---
    st.markdown("<h4>KPI別</h4>", unsafe_allow_html=True)
    k_map = {
        "座数": (44, 48, 52, "座数理由"),
        "客単価": (47, 51, 55, "客単価理由"),
        "CVR": (45, 49, 53, "CVR理由"),
        "客数": (46, 50, 54, "客数理由")
    }
    
    rows = ""
    for k, (ac, tc, lc, r_key) in k_map.items():
        av, tv, lv = get_score(df_raw, row_idx, ac), get_score(df_raw, row_idx, tc), get_score(df_raw, row_idx, lc)
        u = "¥" if k == "客単価" else ""
        m = "◯" if (av/tv if tv else 0) >= 1 else "△" if (av/tv if tv else 0) >= 0.9 else "✕"
        t_str = f"{u}{tv:,.0f}" if tv >= 100 else f"{u}{tv:.2f}"
        reason = str(current_data.get(r_key, "")).replace("\n", "<br>")
        
        rows += f'<tr><td><span class="eval-mark">{m}</span></td><td>{k}</td><td>{t_str}</td><td>{fmt_val(av, av>=tv, u)}</td><td>{fmt_pct(av/tv*100 if tv else 0, av>=tv)}</td><td>{fmt_pct(av/lv*100 if lv else 0, av>=lv)}</td><td class="comment-cell">{reason}</td></tr>'

    st.markdown(f'''
    <table class="base-table kpi-table">
        <tr><th>評</th><th>KPI</th><th>目標</th><th>実績</th><th>目標比</th><th>LY比</th><th>理由</th></tr>
        {rows}
    </table>
    ''', unsafe_allow_html=True)

    # --- 7. 総評 ---
    st.markdown("<h4>■総評 / 今週のアクション</h4>", unsafe_allow_html=True)
    st.markdown(f'<div class="summary-box">{current_data.get("総評", "")}</div>', unsafe_allow_html=True)

else:
    st.warning("データを読み込めませんでした。")
