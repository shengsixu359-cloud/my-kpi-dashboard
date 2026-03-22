# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd

# 1. ページ設定
st.set_page_config(page_title="ストアカルテ 2026", layout="wide")

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
# ※2026年3月(2603)のGIDを固定値として設定します
SPREADSHEET_ID = "1KlZevjH2IbsV0kWQZxw1QjHy3EmsjG9vTKGtvVVTni8"
GID_2603 = "1502960872"

@st.cache_data(ttl=30)
def load_data_by_gid(gid):
    url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={gid}"
    try:
        return pd.read_csv(url, header=None)
    except:
        return pd.DataFrame()

def get_val(df, r, c):
    """行列指定で数値を取得（1開始）"""
    try:
        val = df.iloc[r-1, c-1]
        if pd.isna(val): return 0
        s = str(val).replace(',','').replace('%','').replace('¥','').replace('円','').strip()
        return pd.to_numeric(s, errors='coerce') or 0
    except:
        return 0

def color_text(text, is_reached):
    return f'<span class="{"reach" if is_reached else "unmet"}">{text}</span>'

# --- メイン処理 ---
st.title("ストアカルテ 2026年03月")

# データの読み込み（まずは2603固定で確実に表示させます）
df = load_data_by_gid(GID_2603)

if not df.empty:
    # 期間選択（サイドバー）
    st.sidebar.header("📅 期間選択")
    def find_r(kw):
        mask = df[0].astype(str).str.contains(kw, na=False)
        res = df[mask].index
        return res[0] + 1 if len(res) > 0 else None

    rows = {w: find_r(w) or d for w, d in zip(["W1","W2","W3","W4","W5","W6"], [57,58,59,60,61,62])}
    sel_w = st.sidebar.selectbox("表示週を選択", list(rows.keys()))
    row_idx = rows[sel_w]

    # --- 1. All Stores (ご提示のロジックを反映) ---
    # 月次受注額=sum(F12:F53)
    g2_act = sum([get_val(df, i, 6) for i in range(12, 54)])
    # 月次目標=sum(G12:G53)
    g3_tgt = sum([get_val(df, i, 7) for i in range(12, 54)])
    
    # 月次予算(I3) / 前年受注額(K3) はセルから直接取得
    i3_bg = get_val(df, 3, 9) 
    k3_ly = get_val(df, 3, 11)

    # MTD系 (G6, I6, K6)
    g6_mtd_t = get_val(df, 6, 7)
    i6_mtd_b = get_val(df, 6, 9)
    k6_mtd_l = get_val(df, 6, 11)

    all_html = f'''
    <table class="base-table">
        <tr><th>月次受注額</th><td colspan="5" style="font-size:1.2em;font-weight:bold;">{g2_act:,.0f}</td></tr>
        <tr><th>月次目標</th><td>{g3_tgt:,.0f}</td><th>月次予算</th><td>{i3_bg:,.0f}</td><th>前年受注額</th><td>{k3_ly:,.0f}</td></tr>
        <tr><th>目標比</th><td>{color_text(f"{g2_act/g3_tgt*100 if g3_tgt else 0:.1f}%", g2_act>=g3_tgt)}</td>
            <th>予算比</th><td>{color_text(f"{g2_act/i3_bg*100 if i3_bg else 0:.1f}%", g2_act>=i3_bg)}</td>
            <th>前年比</th><td>{color_text(f"{g2_act/k3_ly*100 if k3_ly else 0:.1f}%", g2_act>=k3_ly)}</td></tr>
        <tr><th>差額</th><td>{color_text(f"{abs(g2_act-g3_tgt):,.0f}", g2_act>=g3_tgt)}</td>
            <th>差額</th><td>{color_text(f"{abs(g2_act-i3_bg):,.0f}", g2_act>=i3_bg)}</td>
            <th>差額</th><td>{color_text(f"{abs(g2_act-k3_ly):,.0f}", g2_act>=k3_ly)}</td></tr>
        <tr><th>MTD目標</th><td>{g6_mtd_t:,.0f}</td><th>MTD予算</th><td>{i6_mtd_b:,.0f}</td><th>MTD前年</th><td>{k6_mtd_l:,.0f}</td></tr>
        <tr><th>MTD目標 %</th><td>{color_text(f"{g2_act/g6_mtd_t*100 if g6_mtd_t else 0:.1f}%", g2_act>=g6_mtd_t)}</td>
            <th>MTD予算 %</th><td>{color_text(f"{g2_act/i6_mtd_b*100 if i6_mtd_b else 0:.1f}%", g2_act>=i6_mtd_b)}</td>
            <th>MTD前年 %</th><td>{color_text(f"{g2_act/k6_mtd_l*100 if k6_mtd_l else 0:.1f}%", g2_act>=k6_mtd_l)}</td></tr>
        <tr><th>MTD目標 差額</th><td>{color_text(f"{abs(g2_act-g6_mtd_t):,.0f}", g2_act>=g6_mtd_t)}</td>
            <th>MTD予算 差額</th><td>{color_text(f"{abs(g2_act-i6_mtd_b):,.0f}", g2_act>=i6_mtd_b)}</td>
            <th>MTD前年 差額</th><td>{color_text(f"{abs(g2_act-k6_mtd_l):,.0f}", g2_act>=k6_mtd_l)}</td></tr>
    </table>
    '''
    st.markdown("<h4>All Stores ※FC excluded</h4>", unsafe_allow_html=True)
    st.markdown(all_html, unsafe_allow_html=True)

    # --- 2. WEEKサマリー ---
    w_rows = ""
    for w, r in rows.items():
        wa = get_val(df, r, 6)
        wt, wb, wl = get_val(df, r, 7), get_val(df, r, 10), get_val(df, r, 13)
        if wa > 0 or wt > 0:
            w_rows += f'<tr><td>{w}</td><td>{wa:,.0f}</td><td>{wt:,.0f}</td><td>{color_text(f"{abs(wa-wt):,.0f}", wa>=wt)}</td><td>{color_text(f"{wa/wt*100 if wt else 0:.1f}%", wa>=wt)}</td><td>{wb:,.0f}</td><td>{color_text(f"{abs(wa-wb):,.0f}", wa>=wb)}</td><td>{color_text(f"{wa/wb*100 if wb else 0:.1f}%", wa>=wb)}</td><td>{wl:,.0f}</td><td>{color_text(f"{wa/wl*100 if wl else 0:.1f}%", wa>=wl)}</td></tr>'
    st.markdown(f'<h4>WEEKサマリー</h4><table class="base-table"><tr><th>WEEK</th><th>受注額</th><th>目標</th><th>差額</th><th>達成率</th><th>予算</th><th>差額</th><th>達成率</th><th>前年実績</th><th>前年比</th></tr>{w_rows}</table>', unsafe_allow_html=True)

    # --- 3. 受注実績詳細 ---
    da, dt, dr = get_val(df, row_idx, 6), get_val(df, row_idx, 7), get_val(df, row_idx, 9)
    dl, dlr = get_val(df, row_idx, 13), get_val(df, row_idx, 14)
    st.markdown(f'<h4>受注実績 {sel_w}</h4><table class="base-table kpi-table"><tr><th>受注実績</th><th>目標</th><th>目標比</th><th>差額</th></tr><tr><td rowspan="3" style="font-size:1.5em;font-weight:bold;">¥{da:,.0f}</td><td>¥{dt:,.0f}</td><td>{color_text(f"{dr:.1f}%", dr>=100)}</td><td>{color_text(f"{abs(da-dt):,.0f}", da>=dt)}</td></tr><tr><th>LY</th><th>LY比</th><th>差額</th></tr><tr><td>¥{dl:,.0f}</td><td>{color_text(f"{dlr:.1f}%", dlr>=100)}</td><td>{color_text(f"{abs(da-dl):,.0f}", da>=dl)}</td></tr></table>', unsafe_allow_html=True)

    # --- 4. KPI別 ---
    k_map = {"座数":(44,48,52), "客単価":(47,51,55), "CVR":(45,49,53), "客数":(46,50,54)}
    k_html = ""
    for k, (ac, tc, lc) in k_map.items():
        av, tv, lv = get_val(df, row_idx, ac), get_val(df, row_idx, tc), get_val(df, row_idx, lc)
        tr = av/tv*100 if tv else 0
        lr = av/lv*100 if lv else 0
        u = "¥" if k=="客単価" else ""
        fmt_t = f"{u}{tv:,.0f}" if tv >= 100 else f"{u}{tv:.2f}"
        fmt_a = f"{u}{av:,.0f}" if av >= 100 else f"{u}{av:.2f}"
        k_html += f'<tr><td><b>{"◯" if tr>=100 else "△" if tr>=90 else "✕"}</b></td><td>{k}</td><td>{fmt_t}</td><td>{color_text(fmt_a, av>=tv)}</td><td>{color_text(f"{tr:.1f}%", tr>=100)}</td><td>{color_text(f"{lr:.1f}%", lr>=100)}</td></tr>'
    st.markdown(f'<h4>KPI別</h4><table class="base-table kpi-table"><tr><th>評</th><th>KPI</th><th>目標</th><th>実績</th><th>目標比</th><th>LY比</th></tr>{k_html}</table>', unsafe_allow_html=True)

else:
    st.error("データの読み込みに失敗しました。スプレッドシートが「リンクを知っている全員」に公開されているか確認してください。")
