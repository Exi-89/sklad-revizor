import streamlit as st
import pypdf
import re
import pandas as pd
import os
import streamlit.components.v1 as components

# Nastavení stránky
st.set_page_config(page_title="SKLAD ZZN 2026", layout="wide")

# --- DESIGN ---
st.markdown("""
    <style>
    .main { background-color: #0b0e14; }
    .logo-container { display: flex; justify-content: center; padding: 25px 0px; }
    .logo-img { width: 520px; transition: transform 0.4s ease; cursor: pointer; }
    .logo-img:hover { transform: scale(1.1); filter: brightness(1.2); }
    
    /* Záložky s barvami */
    button[data-baseweb="tab"] { font-weight: bold !important; font-size: 18px !important; }
    #tabs-b3-tab-0 { color: #ff4b4b !important; }
    #tabs-b3-tab-1 { color: #0072FF !important; }
    #tabs-b3-tab-2 { color: #adbac7 !important; }

    /* Vlastní řádek v regálu */
    .row-item {
        display: flex; align-items: center; border-radius: 8px;
        margin-bottom: 6px; background: #1c2128; border: 1px solid #30363d;
        padding: 5px 10px; cursor: pointer;
    }
    .color-strip { width: 10px; height: 30px; border-radius: 4px; margin-right: 15px; }
    .cat-blue { background-color: #0072FF; }
    .cat-yellow { background-color: #FFD700; }
    .cat-green { background-color: #28a745; }
    .cat-red { background-color: #f85149; }
    .cat-orange { background-color: #ff9f43; }
    .cat-default { background-color: #444c56; }
    
    /* Aktivní (vybraný) řádek */
    .selected-row { border: 2px solid #58a6ff !important; background: #262c36 !important; }
    </style>
    """, unsafe_allow_html=True)

# LOGO
repo_url = "https://raw.githubusercontent.com/Exi-89/sklad-revizor/main/logo_zzn.png"
st.markdown(f'<div class="logo-container"><a href="https://www.zznhp.cz" target="_blank"><img src="{repo_url}" class="logo-img"></a></div>', unsafe_allow_html=True)

# --- DATABÁZE ---
DB_FILE = "sklad_databaze.csv"

if 'vybrane' not in st.session_state: st.session_state.vybrane = set()
if 'db' not in st.session_state:
    if os.path.exists(DB_FILE):
        try: st.session_state.db = pd.read_csv(DB_FILE)['polozka'].tolist()
        except: st.session_state.db = ["50011210 Hrábě švédské", "35020060 Hadice 1 m"]
    else: st.session_state.db = ["50011210 Hrábě švédské", "35020060 Hadice 1 m"]

def uloz_do_db(nove):
    st.session_state.db = sorted(list(set(st.session_state.db + nove)))
    pd.DataFrame({'polozka': st.session_state.db}).to_csv(DB_FILE, index=False)

# --- SKENER DIALOG ---
@st.dialog("📸 SKENOVÁNÍ")
def skenovat():
    components.html("""
        <script src="https://unpkg.com/html5-qrcode"></script>
        <div id="reader" style="width:100%; border-radius:10px; overflow:hidden;"></div>
        <script>
            const html5QrCode = new Html5Qrcode("reader");
            html5QrCode.start({ facingMode: "environment" }, { fps: 20, qrbox: 250 }, (txt) => {
                window.parent.postMessage({type: 'barcode_scanned', value: txt}, '*');
                html5QrCode.stop();
            });
        </script>
    """, height=350)

# --- PANEL OVLÁDÁNÍ ---
col_a, col_b = st.columns([0.3, 0.7])
with col_a:
    if st.button("📸 SPUSTIT SKENER", use_container_width=True): skenovat()
with col_b:
    search = st.selectbox("🔍 NAŠEPTÁVAČ:", [""] + st.session_state.db, index=0).lower()

# --- IMPORTY ---
t1, t2, t3 = st.tabs(["📄 PDF Převodka", "🌐 Import", "📝 Ruční"])
with t1:
    up = st.file_uploader("PDF", type="pdf")
    if st.button("Uložit PDF"):
        if up:
            z_pdf = [r.strip() for p in pypdf.PdfReader(up).pages for r in p.extract_text().split('\n') if len(r) > 5]
            uloz_do_db(z_pdf); st.rerun()
with t2:
    web = st.text_area("Text k importu...")
    if st.button("Importovat"):
        if web: uloz_do_db([r.strip() for r in web.split('\n') if len(r) > 3]); st.rerun()
with t3:
    c1, c2 = st.columns(2)
    k, n = c1.text_input("Kód"), c2.text_input("Název")
    if st.button("Přidat"):
        if k and n: uloz_do_db([f"{k} {n}"]); st.rerun()

st.divider()

# --- LOGIKA KATEGORIÍ ---
def get_color(text):
    text = text.lower()
    if any(x in text for x in ["hadice", "voda"]): return "cat-blue"
    if any(x in text for x in ["hrábě", "lopat"]): return "cat-yellow"
    if any(x in text for x in ["hnojiv", "postřik"]): return "cat-green"
    if any(x in text for x in ["pletivo", "drát"]): return "cat-red"
    if any(x in text for x in ["nářadí", "kladiv"]): return "cat-orange"
    return "cat-default"

l, r = st.columns(2)

with l:
    st.subheader("📦 REGÁLY")
    filtr = [p for p in st.session_state.db if search in p.lower()]
    
    for p in filtr:
        color = get_color(p)
        is_sel = p in st.session_state.vybrane
        
        # Místo checkboxu použijeme tlačítko přes celý řádek
        row_col, del_col = st.columns([0.85, 0.15])
        
        with row_col:
            # Tlačítko se tváří jako řádek
            label = f"{'✅' if is_sel else '⬜'} {p}"
            if st.button(label, key=f"row_{p}", use_container_width=True):
                if is_sel: st.session_state.vybrane.remove(p)
                else: st.session_state.vybrane.add(p)
                st.rerun()
        
        with del_col:
            if st.button("🗑️", key=f"db_del_{p}"):
                st.session_state.db.remove(p)
                if p in st.session_state.vybrane: st.session_state.vybrane.remove(p)
                pd.DataFrame({'polozka': sorted(st.session_state.db)}).to_csv(DB_FILE, index=False)
                st.rerun()

with r:
    st.subheader("📝 SEZNAM K OBJEDNÁNÍ")
    # Zde je to nejdůležitější: Mazání funguje přímo na setu
    for p in sorted(list(st.session_state.vybrane)):
        col_txt, col_btn = st.columns([0.85, 0.15])
        col_txt.write(f"• {p}")
        if col_btn.button("❌", key=f"kill_{p}"):
            st.session_state.vybrane.remove(p)
            st.rerun()

    if st.session_state.vybrane:
        st.divider()
        copy_text = "\\n".join(sorted(list(st.session_state.vybrane)))
        components.html(f"""
            <button id="cBtn" style="width:100%; background:#1f6feb; color:white; padding:15px; border:none; border-radius:10px; font-weight:bold; cursor:pointer;">📋 KOPÍROVAT SEZNAM</button>
            <script>
            document.getElementById('cBtn').onclick = () => {{
                navigator.clipboard.writeText(`{copy_text}`).then(() => alert('Zkopírováno!'));
            }};
            </script>
        """, height=70)
        
        if st.button("🗑️ VYMAZAT VŠE", use_container_width=True):
            st.session_state.vybrane.clear()
            st.rerun()
