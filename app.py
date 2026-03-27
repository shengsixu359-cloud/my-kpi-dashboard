# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# --- 1. ページ基本設定 ---
st.set_page_config(page_title="ストアカルテ", layout="wide")

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

# --- 3. 引用元データ設定 ---
BASE_URL = "https://docs.google.com/spreadsheets/d/1KlZevjH2IbsV0kWQZxw1QjHy3EmsjG9vTKGtvVVTni8/export?format=csv&gid="
MONTH_CONFIG = {
    "2026": {
        "3月": {"gid": "1502960872"},
        "4月": {"gid": "166364340"}
    }
}

@st.cache_data(ttl=5)
def load_raw_data(gid):
    try:
        return pd.read_csv(f"{BASE_URL}{gid}", header=None)
    except:
        return pd.DataFrame()

def get_score(df, row, col):
    try:
        val = df.iloc[row-1, col-1]
        if pd.isna(val): return 0
        return pd.to_numeric(str(val).replace(',','').replace('%','').replace('¥','').replace('円','').strip(), errors='coerce')
    except: return 0

# --- 4. テキスト読み書き (直接アクセス・強制変換版) ---
def fetch_text_no_cache(search_key):
    """キャッシュを通さず、スプレッドシートから直接最新データを1行取得する"""
    try:
        # 毎回最新の全データを取得
        all_data = ws.get_all_values()
        # デフォルト値
        res = {"zasu": "", "tanka": "", "cvr": "", "kyaku": "", "summary": ""}
        
        search_key_clean = str(search_key).strip()
        
        for row in all_data:
            if row and str(row[0]).strip() == search_key_clean:
                # 取得した値をすべて文字列(str)に強制変換し、Noneを空文字に置換
                res["zasu"] = str(row[1]) if len(row) > 1 and row[1] is not None else ""
                res["tanka"] = str(row[2]) if len(row) > 2 and row[2] is not None else ""
                res["cvr"] = str(row[3]) if len(row) > 3 else ""
                res["kyaku"] = str(row[4]) if len(row) > 4 else ""
                res["summary"] = str(row[5]) if len(row) > 5 else ""
                break
        return res
    except:
        return {"zasu": "", "tanka": "", "cvr": "", "kyaku": "", "summary": ""}

def save_to_sheet_stable(search_key, data_list):
    all_values = ws.get_all_values()
    target_row_idx = -1
    search_key_clean = str(search_key).strip()
    
    for i, row in enumerate(all_values):
        if row and str(row[0]).strip() == search_key_clean:
            target_row_idx = i + 1
            break
    
    # 書き込む内容をすべて文字列にする
    final_row = [search_key_clean] + [str(d) for d in data_list]
    if target_row_idx != -1:
        ws.update(range_name=f"A{target_row_idx}:F{target_row_idx}", values=[final_row])
    else:
        ws.append_row(final_row)

# --- 5. UI設定とデータ同期 ---
st.sidebar.header("📅 期間選択")
sel_year = st.sidebar.selectbox("西暦", list(MONTH_CONFIG.keys()))
sel_month = st.sidebar.selectbox("月", list(MONTH_CONFIG[sel_year].keys()))

week_row_map = {"W1": 57, "W2": 58, "W3": 59, "W4": 60, "W5": 61, "W6": 62}
sel_week = st.sidebar.selectbox("週", list(week_row_map.keys()))

# 検索用の絶対キー
current_key = f"{sel_year}-{sel_month}-{sel_week}"

# ★ ここで直接読み込みを実行 (リブートされても最新を取得)
current_txt = fetch_text_no_cache(current_key)

with st.sidebar.form("input_form"):
    st.info(f"📍 読込キー: {current_key}")
    r_zasu = st.text_area("座数の理由", value=current_txt["zasu"])
    r_tanka = st.text_area("客単価の理由", value=current_txt["tanka"])
    r_cvr = st.text_area("CVRの理由", value=current_txt["cvr"])
    r_kyaku = st.text_area("客数の理由", value=current_txt["kyaku"])
    sum_text = st.text_area("■総評 / 今週のアクション", value=current_txt["summary"], height=150)
    
    if st.form_submit_button("全ユーザーに共有保存"):
        save_to_sheet_stable(current_key, [r_zasu, r_tanka, r_cvr, r_kyaku, sum_text])
        st.cache_data.clear() # 数値データのキャッシュをリセット
        st.rerun()

# --- 6. メイン表示 (数値・レイアウト) ---
current_gid = MONTH_CONFIG[sel_year][sel_month]["gid"]
df_raw = load_raw_data(current_gid)

if not df_raw.empty:
    st.title(f"📊 ストアカルテ {sel_year}年{sel_month}")
    
    # CSS設定 (カラーパレット適用)
    st.markdown('''
    <style>
        html, body, [class*="css"] { font-family: "Meiryo", sans-serif; color: #3b484e; }
        .reach { color: #58b5ca; font-weight: bold; }
        .unmet { color: #f3a359; font-weight: bold; }
        .base-table { width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 0.85em; background-color: white; }
        .base-table th { background-color: rgba(88, 181, 202, 0.9); color: white; padding: 8px; border: 1px solid #eeece1; text-align: center; }
        .base-table td { border: 1px solid #eeece1; padding: 8px; text-align: center; }
        .kpi-table th { background-color: #3F484F !important; color: #eeece1 !important; }
        .comment-cell { text-align: left !important; background-color: #fdfcf7 !important; white-space: pre-wrap; vertical-align: middle; color: #3b484e; min-width: 250px; }
        .summary-box { background-color: #e1f2f7; border: 1px solid #58b5ca; padding: 15px; border-radius: 4px; white-space: pre-wrap; color: #3b484e; min-height: 80px; }
        h4 { color: #3b484e; border-bottom: 2px solid #fcde9c; padding-bottom: 5px; margin-top: 25px; }
    </style>
    ''', unsafe_allow_html=True)

    def fmt_v(val, cond, unit=""):
        cls = "reach" if cond else "unmet"
        t = f"{unit}{abs(val):,.0f}" if abs(val) >= 100 else f"{unit}{abs(val):.2f}"
        return f'<span class="{cls}">{t}</span>'

    def fmt_p(val, cond):
        cls = "reach" if cond else "unmet"
        return f'<span class="{cls}">{val:.1f}%</span>'

    # All Stores
    act = sum([get_score(df_raw, i, 6) for i in range(12, 54)])
    tgt, bgt, ly = get_score(df_raw, 3, 7), get_score(df_raw, 3, 9), get_score(df_raw, 3, 11)
    mt, mb, ml = get_score(df_raw, 6, 7), get_score(df_raw, 6, 9), get_score(df_raw, 6, 11)

    st.markdown("<h4>All Stores ※FC excluded</h4>", unsafe_allow_html=True)
    st.markdown(f'''
    <table class="base-table">
        <tr><th style="background-color:#606970;">月次受注額</th><td colspan="5" style="font-size:1.2em;font-weight:bold;">{act:,.0f}</td></tr>
        <tr><th>月次目標</th><td>{tgt:,.0f}</td><th>月次予算</th><td>{bgt:,.0f}</td><th>前年受注</th><td>{ly:,.0f}</td></tr>
        <tr><th>目標比</th><td>{fmt_p(act/tgt*100 if tgt else 0, act>=tgt)}</td><th>予算比</th><td>{fmt_p(act/bgt*100 if bgt else 0, act>=bgt)}</td><th>前年比</th><td>{fmt_p(act/ly*100 if ly else 0, act>=ly)}</td></tr>
        <tr><th>MTD目標%</th><td>{fmt_p(act/mt*100 if mt else 0, act>=mt)}</td><th>MTD予算%</th><td>{fmt_p(act/mb*100 if mb else 0, act>=mb)}</td><th>MTD前年%</th><td>{fmt_p(act/ml*100 if ml else 0, act>=ml)}</td></tr>
    </table>
    ''', unsafe_allow_html=True)

    # Weeklyサマリー
    st.markdown("<h4>WEEKサマリー</h4>", unsafe_allow_html=True)
    w_rows = ""
    for w_n, r_i in week_row_map.items():
        wa, wt, wb, wl = get_score(df_raw, r_i, 6), get_score(df_raw, r_i, 7), get_score(df_raw, r_i, 10), get_score(df_raw, r_i, 13)
        w_rows += f'<tr><td>{w_n}</td><td>{wa:,.0f}</td><td>{wt:,.0f}</td><td>{fmt_v(wa-wt, wa>=wt)}</td><td>{fmt_p(wa/wt*100 if wt else 0, wa>=wt)}</td><td>{wb:,.0f}</td><td>{fmt_v(wa-wb, wa>=wb)}</td><td>{fmt_p(wa/wb*100 if wb else 0, wa>=wb)}</td><td>{wl:,.0f}</td><td>{fmt_p(wa/wl*100 if wl else 0, wa>=wl)}</td></tr>'
    st.markdown(f'<table class="base-table"><tr><th>WEEK</th><th>受注額</th><th>目標</th><th>差額</th><th>達成率</th><th>予算</th><th>差額</th><th>達成率</th><th>前年実績</th><th>前年比</th></tr>{w_rows}</table>', unsafe_allow_html=True)

    # KPI別
    row_idx = week_row_map[sel_week]
    st.markdown(f"<h4>KPI別 ({sel_week})</h4>", unsafe_allow_html=True)
    k_data = [("座数", 44, 48, 52, "zasu"), ("客単価", 47, 51, 55, "tanka"), ("CVR", 45, 49, 53, "cvr"), ("客数", 46, 50, 54, "kyaku")]
    k_rows = ""
    for k_n, ac, tc, lc, t_k in k_data:
        av, tv, lv = get_score(df_raw, row_idx, ac), get_score(df_raw, row_idx, tc), get_score(df_raw, row_idx, lc)
        u = "¥" if k_n == "客単価" else ""
        m = "◯" if (av/tv if tv else 0) >= 1 else "△" if (av/tv if tv else 0) >= 0.9 else "✕"
        t_s = f"{u}{tv:,.0f}" if tv >= 100 else f"{u}{tv:.2f}"
        
        # 理由テキストの埋め込み (str()で念押し)
        reason_html = str(current_txt[t_k]).replace("\n", "<br>")
        k_rows += f'<tr><td>{m}</td><td>{k_n}</td><td>{t_s}</td><td>{fmt_v(av, av>=tv, u)}</td><td>{fmt_p(av/tv*100 if tv else 0, av>=tv)}</td><td>{fmt_p(av/lv*100 if lv else 0, av>=lv)}</td><td class="comment-cell">{reason_html}</td></tr>'
    st.markdown(f'<table class="base-table kpi-table"><tr><th>評</th><th>KPI</th><th>目標</th><th>実績</th><th>目標比</th><th>LY比</th><th>理由</th></tr>{k_rows}</table>', unsafe_allow_html=True)

    # 総評
    st.markdown("<h4>■総評 / 今週のアクション</h4>", unsafe_allow_html=True)
    final_summary = str(current_txt["summary"]) if current_txt["summary"] else "(未入力)"
    st.markdown(f'<div class="summary-box">{final_summary}</div>', unsafe_allow_html=True)
else:
    st.warning("数値データを読み込めませんでした。")
