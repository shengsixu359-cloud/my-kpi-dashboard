# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# --- 1. ページ基本設定 ---
# ページ設定はコードの冒頭に配置
st.set_page_config(page_title="ストアカルテ2026年3月", layout="wide")

# セッション状態の初期化
if 'needs_refresh' not in st.session_state:
    st.session_state.needs_refresh = False

# --- 2. Googleスプレッドシート接続設定 ---
try:
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    gc = gspread.authorize(creds)

    # 【重要】ご自身で作成した新しいスプレッドシートのIDに書き換えてください
    SAVE_SHEET_ID = "1_8XbvigwRRIR-HxT5OEDlrKdpW8J9AjYYtjEk33LPIk"
    sh = gc.open_by_key(SAVE_SHEET_ID)
    ws = sh.worksheet("シート1") 
except Exception as e:
    st.error(f"スプレッドシート接続エラー: Secretsの設定またはスプレッドシートIDを確認してください。")
    st.stop()

# 元の数値データ読み込み用URL
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
    """保存用シートから全データを取得"""
    try:
        data = ws.get_all_records()
        return {row['週']: row for row in data}
    except:
        return {}

def save_to_sheet(week_label, zasu, tanka, cvr, kyaku, summary):
    """該当週のデータを更新または追加"""
    all_data = ws.get_all_values()
    target_row = -1
    for i, row in enumerate(all_data):
        if row and row[0] == week_label:
            target_row = i + 1
            break
    
    new_row = [week_label, zasu, tanka, cvr, kyaku, summary]
    
    if target_row != -1:
        # 既存の行を更新
        ws.update(range_name=f"A{target_row}:F{target_row}", values=[new_row])
    else:
        # 新しい行として末尾に追加
        ws.append_row(new_row)

# --- 4. データ準備 ---
df_raw = load_raw_data()
saved_dict = get_saved_data()

if not df_raw.empty:
    # サイドバー：期間選択
    st.sidebar.header("📅 期間選択")
    week_map = {
        "W1 (3/1)": 57, "W2 (3/2-3/8)": 58, "W3 (3/9-3/15)": 59, 
        "W4 (3/16-3/22)": 60, "W5 (3/23-3/29)": 61, "W6 (3/30-3/31)": 62
    }
    selected_label = st.sidebar.selectbox("表示週を選択", list(week_map.keys()))
    row_idx = week_map[selected_label]
    
    # 保存済みデータの取得
    current_data = saved_dict.get(selected_label, {
        "週": selected_label, "座数理由": "", "客単価理由": "", "CVR理由": "", "客数理由": "", "総評": ""
    })
    
    st.sidebar.markdown("---")
    st.sidebar.subheader(f"📝 {selected_label} 共有・保存")
    
    # 理由・総評入力フォーム
    with st.sidebar.form("input_form"):
        r_zasu = st.text_area("座数の理由", value=current_data.get("座数理由",""))
        r_tanka = st.text_area("客単価の理由", value=current_data.get("客単価理由",""))
        r_cvr = st.text_area("CVRの理由", value=current_data.get("CVR理由",""))
        r_kyaku = st.text_area("客数の理由", value=current_data.get("客数理由",""))
        sum_text = st.text_area("■総評 / 今週のアクション", value=current_data.get("総評",""), height=150)
        
        if st.form_submit_button("全ユーザーに共有保存"):
            save_to_sheet(selected_label, r_zasu, r_tanka, r_cvr, r_kyaku, sum_text)
            st.success("共有スプレッドシートに保存しました！")
            st.cache_data.clear() # 最新データを読み込むためキャッシュクリア
            st.rerun()

    # --- 5. デザイン設定 (指定カラーパレット) ---
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

    # --- 6. 表示用ヘルパー関数 ---
    def fmt_num_h(val, is_reached, unit=""):
        txt = f"{unit}{abs(val):,.0f}" if abs(val) >= 100 else f"{unit}{abs(val):.2f}"
        cls = "reach" if is_reached else "unmet"
        return f'<span class="{cls}">{txt}</span>'

    def fmt_ratio_h(val, is_reached):
        cls = "reach" if is_reached else "unmet"
        return f'<span class="{cls}">{val:.1f}%</span>'

    # --- 7. 各セクションの表示 ---
    
    # All Stores
    g2_act = sum([get_score(df_raw, i, 6) for i in range(12, 54)])
    g3_tgt, i3_bg, k3_ly = get_score(df_raw, 3, 7), get_score(df_raw, 3, 9), get_score(df_raw, 3, 11)
    
    st.markdown("<h4>All Stores ※FC excluded</h4>", unsafe_allow_html=True)
    st.markdown(f'''
    <table class="base-table">
        <tr><th style="background-color:#606970;">月次受注額</th><td colspan="5" style="font-size:1.2em;font-weight:bold;">{g2_act:,.0f}</td></tr>
        <tr><th>月次目標</th><td>{g3_tgt:,.0f}</td><th>月次予算</th><td>{i3_bg:,.0f}</td><th>前年受注額</th><td>{k3_ly:,.0f}</td></tr>
        <tr><th>目標比</th><td>{fmt_ratio_h(g2_act/g3_tgt*100 if g3_tgt else 0, g2_act>=g3_tgt)}</td><th>予算比</th><td>{fmt_ratio_h(g2_act/i3_bg*100 if i3_bg else 0, g2_act>=i3_bg)}</td><th>前年比</th><td>{fmt_ratio_h(g2_act/k3_ly*100 if k3_ly else 0, g2_act>=k3_ly)}</td></tr>
        <tr><th>差額</th><td>{fmt_num_h(g2_act-g3_tgt, g2_act>=g3_tgt)}</td><th>差額</th><td>{fmt_num_h(g2_act-i3_bg, g2_act>=i3_bg)}</td><th>差額</th><td>{fmt_num_h(g2_act-k3_ly, g2_act>=k3_ly)}</td></tr>
    </table>
    ''', unsafe_allow_html=True)

    # KPI別
    k_map = {
        "座数": (44, 48, 52, "座数理由"),
        "客単価": (47, 51, 55, "客単価理由"),
        "CVR": (45, 49, 53, "CVR理由"),
        "客数": (46, 50, 54, "客数理由")
    }
    k_rows_html = ""
    for k, (ac, tc, lc, r_key) in k_map.items():
        av, tv, lv = get_score(df_raw, row_idx, ac), get_score(df_raw, row_idx, tc), get_score(df_raw, row_idx, lc)
        tr, lr = (av/tv*100 if tv else 0), (av/lv*100 if lv else 0)
        u = "¥" if k == "客単価" else ""
        m = "◯" if tr >= 100 else "△" if tr >= 90 else "✕"
        
        # 目標値の整形をループ内で事前に行う（エラー回避）
        if tv >= 100:
            val_tgt_display = f"{u}{tv:,.0f}"
        else:
            val_tgt_display = f"{u}{tv:.2f}"
            
        reason = str(current_data.get(r_key, "")).replace("\n", "<br>")
        
        k_rows_html += f'''
        <tr>
            <td><span class="eval-mark">{m}</span></td>
            <td>{k}</td>
            <td>{val_tgt_display}</td>
            <td>{fmt_num_h(av, av >= tv, u)}</td>
            <td>{fmt_ratio_h(tr, tr >= 100)}</td>
            <td>{fmt_ratio_h(lr, lr >= 100)}</td>
            <td class="comment-cell">{reason}</td>
        </tr>
        '''
    
    st.markdown(f'''
    <h4>KPI別</h4>
    <table class="base-table kpi-table">
        <tr>
            <th style="width:40px;">評</th><th style="width:80px;">KPI</th>
            <th style="width:100px;">目標</th><th style="width:100px;">実績</th>
            <th style="width:80px;">目標比</th><th style="width:80px;">LY比</th>
            <th>理由</th>
        </tr>
        {k_rows_html}
    </table>
    ''', unsafe_allow_html=True)

    # 総評
    st.markdown("<h4>■総評 / 今週のアクション</h4>", unsafe_allow_html=True)
    st.markdown(f'<div class="summary-box">{current_data.get("総評", "")}</div>', unsafe_allow_html=True)

else:
    st.warning("データを読み込めませんでした。")
