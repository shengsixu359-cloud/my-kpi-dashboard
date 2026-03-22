# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd

# 1. ページ設定
st.set_page_config(page_title="週次KPIダッシュボード", layout="wide")
st.title("📊 週次KPIダッシュボード (2026年3月)")

# 2. データ取得設定 (新しいURLとGID)
# 末尾を /export?format=csv&gid= に書き換えてCSVとして読み込みます
BASE_URL = "https://docs.google.com/spreadsheets/d/1KlZevjH2IbsV0kWQZxw1QjHy3EmsjG9vTKGtvVVTni8/export?format=csv&gid="
SHEET_GID = "1502960872" # 「2603」タブのGID

@st.cache_data(ttl=60) # 1分間キャッシュ
def load_raw_data():
    try:
        # ヘッダーなし(header=None)で読み込み、セル位置(行列番号)で指定可能にする
        url = f"{BASE_URL}{SHEET_GID}"
        df = pd.read_csv(url, header=None)
        return df
    except Exception as e:
        st.error(f"データの読み込みに失敗しました: {e}")
        return pd.DataFrame()

def get_score(df, row_idx, col_idx):
    """Excelの行列番号(A1=1,1)から、pandasのインデックス(0,0)に変換して数値を取得"""
    try:
        if df.empty: return 0
        # pandasは0始まりのため、行と列から1を引く
        val = df.iloc[row_idx-1, col_idx-1]
        # 文字列を数値に変換（カンマや%を除去）
        clean_val = str(val).replace(',', '').replace('%', '').replace('¥', '').strip()
        return pd.to_numeric(clean_val, errors='coerce')
    except:
        return 0

# 列名(A, B, C...)を数字(1, 2, 3...)に変換する補助関数
def col_to_num(col_str):
    num = 0
    for c in col_str.upper():
        num = num * 26 + (ord(c) - ord('A') + 1)
    return num

# --- メイン処理 ---
df_raw = load_raw_data()

if not df_raw.empty:
    # --- サイドバー：週選択 ---
    st.sidebar.header("📅 期間選択")
    # A57～A62にあるW1～W6を選択肢にする
    week_map = {
        "W1 (3/1)": 57,
        "W2 (3/2-3/8)": 58,
        "W3 (3/9-3/15)": 59,
        "W4 (3/16-3/22)": 60,
        "W5 (3/23-3/29)": 61,
        "W6 (3/30-3/31)": 62
    }
    selected_week_label = st.sidebar.selectbox("表示週を選択", list(week_map.keys()))
    row_idx = week_map[selected_week_label] # 選択された週の行番号(Excel形式)

    st.subheader(f"🗃️ {selected_week_label} 受注・KPIレポート")

    # --- ① 受注実績サマリー (ご指定のセル位置から抽出) ---
    st.markdown("#### 🏆 受注実績")
    
    # 本年実績
    act_sales = get_score(df_raw, row_idx, col_to_num("F")) # F列:受注実績
    tgt_sales = get_score(df_raw, row_idx, col_to_num("G")) # G列:受注目標
    diff_sales = get_score(df_raw, row_idx, col_to_num("H")) # H列:差額
    ratio_sales = get_score(df_raw, row_idx, col_to_num("I")) # I列:受注目標比(%)

    # 前年比較
    ly_sales = get_score(df_raw, row_idx, col_to_num("M")) # M列:前年実績
    ly_ratio = get_score(df_raw, row_idx, col_to_num("N")) # N列:前年比(%)
    # ご指示通り「F列 - M列」で計算
    ly_diff = act_sales - ly_sales

    # メトリック表示 (本年)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("受注実績", f"{act_sales:,.0f}円")
    c2.metric("受注目標", f"{tgt_sales:,.0f}円")
    c3.metric("目標比", f"{ratio_sales:.1f}%", delta=f"{diff_sales:,.0f}円")
    c4.empty()

    # メトリック表示 (前年比較)
    c5, c6, c7, c8 = st.columns(4)
    c5.metric("前年実績", f"{ly_sales:,.0f}円")
    c6.metric("前年比", f"{ly_ratio:.1f}%", delta=f"{ly_diff:,.0f}円")
    c7.empty()
    c8.empty()

    st.divider()

    # --- ② KPI別実績 (ご指定のセル位置から抽出) ---
    st.markdown("#### 📈 指標別KPI分析")
    
    kpi_data = []
    # 各KPIの列定義 (本年, 目標, 前年)
    kpi_cols = {
        "座数":   {"act": "AR", "tgt": "AV", "ly": "AZ"},
        "客単価": {"act": "AU", "tgt": "AY", "ly": "BC"},
        "CVR":    {"act": "AS", "tgt": "AW", "ly": "BA"},
        "客数":   {"act": "AT", "tgt": "AX", "ly": "BB"},
    }

    for item, cols in kpi_cols.items():
        act_val = get_score(df_raw, row_idx, col_to_num(cols["act"]))
        tgt_val = get_score(df_raw, row_idx, col_to_num(cols["tgt"]))
        ly_val = get_score(df_raw, row_idx, col_to_num(cols["ly"]))

        # 比率計算
        tgt_ratio = (act_val / tgt_val * 100) if tgt_val else 0
        ly_ratio = (act_val / ly_val * 100) if ly_val else 0

        # テーブル表示用に整形
        kpi_data.append({
            "KPI指標": item,
            "本年実績": f"{act_val:,.0f}" if act_val > 100 else f"{act_val:.2f}",
            "本年目標": f"{tgt_val:,.0f}" if tgt_val > 100 else f"{tgt_val:.2f}",
            "目標比": f"{tgt_ratio:.1f}%",
            "前年実績": f"{ly_val:,.0f}" if ly_val > 100 else f"{ly_val:.2f}",
            "前年比": f"{ly_ratio:.1f}%"
        })

    # テーブルとして表示
    st.table(pd.DataFrame(kpi_data))

    st.info(f"※{selected_week_label} のデータをスプレッドシートの {row_idx} 行目から抽出しています。")

else:
    st.warning("スプレッドシートからデータを読み込めませんでした。URLと共有設定を確認してください。")
