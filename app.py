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
    st.error(f"スプレッドシート接続エラー: Secretsの設定またはスプレッドシートIDを確認してください。")
    st.stop()

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

# --- 3. 保存・読込ロジック ---
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

# --- 4. データ準備 ---
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

    # --- 5. デザイン (CSS) ---
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
        .comment-cell {{ text-align: left !important; background-color: #fdfcf7 !important; white-space: pre-wrap; vertical-align: middle; font-size: 0.9em; color: #3b484e; }}
        .summary-box {{ background-color: #e1f2f7; border: 1px solid #58b5ca; padding: 15px; border-radius: 4px; white-space: pre-wrap; color: #3b484e; line-height: 1.6; }}
        h4 {{ color: #3b484e; border-bottom: 2px solid #fcde9c; padding-bottom: 5px; margin-top: 25px; }}
    </style>
    ''', unsafe_allow_html=True)

    st.title("📊 ストアカルテ2026年3月")

    def fmt_num_h(val, is_reached, unit=""):
        txt = f"{unit}{abs(val):,.0f}" if abs(val) >= 100 else f"{unit}{abs(val):.2f}"
        return f'<span class="{"reach" if is_reached else "unmet"}">{txt}</span>'

    def fmt_ratio_h(val, is_reached):
        return f'<span class="{"reach" if is_reached else "unmet"}">{val:.1f}%</span>'

    # --- 6. All Stores ---
    act = sum([get_score(df_raw, i, 6) for i in range(12, 54)])
    tgt, bgt, ly = get_score(df_raw, 3, 7), get_score(df_raw, 3, 9), get_score(df_raw, 3, 11)
    mt, mb, ml = get_score(df_raw, 6, 7), get_score(df_raw, 6, 9), get_score(df_raw, 6, 11)

    st.markdown("<h4>All Stores ※FC excluded</h4>", unsafe_allow_html=True)
    st.markdown(f'''
    <table class="base-table">
        <tr><th style="background-color:#606970;">月次受注額</th><td colspan="5" style="font-size:1.2em;font-weight:bold;">{act:,.0f}</td></tr>
        <tr><th>月次目標</th><td>{tgt:,.0f}</td><th>月次予算</th><td>{bgt:,.0f}</td><th>前年受注額</th><td>{ly:,.0f}</td></tr>
        <tr><th>目標比</th><td>{fmt_ratio_h(act/tgt*100 if tgt else 0, act>=tgt)}</td><th>予算比</th><td>{fmt_ratio_h(act/bgt*100 if bgt else 0, act>=bgt)}</td><th>前年比</th><td>{fmt_ratio_h(act/ly*100 if ly else 0, act>=ly)}</td></tr>
        <tr><th>差額</th><td>{fmt_num_h(act-tgt, act>=tgt)}</td><th>差額</th><td>{fmt_num_h(act-bgt, act>=bgt)}</td><th>差額</th><td>{fmt_num_h(act-ly, act>=ly)}</td></tr>
        <tr><th>MTD目標</th><td>{mt:,.0f}</td><th>MTD予算</th><td>{mb:,.0f}</td><th>MTD前年</th><td>{ml:,.0f}</td></tr>
        <tr><th>MTD目標%</th><td>{fmt_ratio_h(act/mt*100 if mt else 0, act>=mt)}</td><th>MTD予算%</th><td>{fmt_ratio_h(act/mb*100 if mb else 0, act>=mb)}</td><th>MTD前年%</th><td>{fmt_ratio_h(act/ml*100 if ml else 0, act>=ml)}</td></tr>
        <tr><th>MTD目標差額</th><td>{fmt_num_h(act-mt, act>=mt)}</td><th>MTD予算差額</th><td>{fmt_num_h(act-mb, act>=mb)}</td><th>MTD前年差額</th><td>{fmt_num_h(act-ml, act>=ml)}</td></tr>
    </table>
    ''', unsafe_allow_html=True)

    # --- 7. Weeklyサマリー (復活箇所) ---
    st.markdown("<h4>WEEKサマリー</h4>", unsafe_allow_html=True)
    w_rows = ""
    for w_name, r_idx in week_map.items():
        wa, wt, wb, wl = get_score(df_raw, r_idx, 6), get_score(df_raw, r_idx, 7), get_score(df_raw, r_idx, 10), get_score(df_raw, r_idx, 13)
        w_rows += f'''
        <tr>
            <td>{w_name.split()[0]}</td>
            <td>{wa:,.0f}</td>
            <td>{wt:,.0f}</td>
            <td>{fmt_num_h(wa-wt, wa>=wt)}</td>
            <td>{fmt_ratio_h(wa/wt*100 if wt else 0, wa>=wt)}</td>
            <td>{wb:,.0f}</td>
            <td>{fmt_num_h(wa-wb, wa>=wb)}</td>
            <td>{fmt_ratio_h(wa/wb*100 if wb else 0, wa>=wb)}</td>
            <td>{wl:,.0f}</td>
            <td>{fmt_ratio_h(wa/wl*100 if wl else 0, wa>=wl)}</td>
        </tr>'''
    st.markdown(f'''
    <table class="base-table">
        <tr><th>WEEK</th><th>受注額</th><th>目標</th><th>差額</th><th>達成率</th><th>予算</th><th>差額</th><th>達成率</th><th>前年実績</th><th>前年比</th></tr>
        {w_rows}
    </table>
    ''', unsafe_allow_html=True)

    # --- 8. KPI別 ---
    st.markdown("<h4>KPI別</h4>", unsafe_allow_html=True)
    k_map = {"座数": (44, 48, 52, "座数理由"), "客単価": (47, 51, 55, "客単価理由"), "CVR": (45, 49, 53, "CVR理由"), "客数": (46, 50, 54, "客数理由")}
    k_rows = ""
    for k, (ac, tc, lc, r_key) in k_map.items():
        av, tv, lv = get_score(df_raw, row_idx, ac), get_score(df_raw, row_idx, tc), get_score(df_raw, row_idx, lc)
        u = "¥" if k == "客単価" else ""
        tr = av/tv if tv else 0
        m = "◯" if tr >= 1 else "△" if tr >= 0.9 else "✕"
        t_str = f"{u}{tv:,.0f}" if tv >= 100 else f"{u}{tv:.2f}"
        reason = str(current_data.get(r_key, "")).replace("\n", "<br>")
        
        k_rows += f'''
        <tr>
            <td><span class="eval-mark">{m}</span></td>
            <td>{k}</td>
            <td>{t_str}</td>
            <td>{fmt_num_h(av, av>=tv, u)}</td>
            <td>{fmt_ratio_h(av/tv*100 if tv else 0, av>=tv)}</td>
            <td>{fmt_ratio_h(av/lv*100 if lv else 0, av>=lv)}</td>
            <td class="comment-cell">{reason}</td>
        </tr>'''

    st.markdown(f'''
    <table class="base-table kpi-table">
        <tr><th>評</th><th>KPI</th><th>目標</th><th>実績</th><th>目標比</th><th>LY比</th><th>理由</th></tr>
        {k_rows}
    </table>
    ''', unsafe_allow_html=True)

    # --- 9. 総評 ---
    st.markdown("<h4>■総評 / 今週のアクション</h4>", unsafe_allow_html=True)
    st.markdown(f'<div class="summary-box">{current_data.get("総評", "")}</div>', unsafe_allow_html=True)

else:
    st.warning("データを読み込めませんでした。")
