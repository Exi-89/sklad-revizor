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
    
    button[data-baseweb="tab"] { font-weight: bold !important; font-size: 18px !important; }
    #tabs-b3-tab-0 { color: #ff4b4b !important; }
    #tabs-b3-tab-1 { color: #adbac7 !important; }

    div.stButton > button {
        text-align: left !important;
        justify-content: flex-start !important;
        background-color: #1c2128 !important;
        border: 1px solid #30363d !important;
        color: #adbac7 !important;
        padding: 10px !important;
        display: block !important;
        width: 100% !important;
    }
    div.stButton > button:hover { border-color: #58a6ff !important; }
    </style>
    """, unsafe_allow_html=True)

# LOGO
repo_url = "https://raw.githubusercontent.com/Exi-89/sklad-revizor/main/logo_zzn.png"
st.markdown(f'<div class="logo-container"><a href="https://www.zznhp.cz" target="_blank"><img src="{repo_url}" class="logo-img"></a></div>', unsafe_allow_html=True)

# --- DATABÁZE ---
DB_FILE = "sklad_databaze.csv"

if 'vybrane' not in st.session_state: st.session_state.vybrane = set()
if 'scanned_code' not in st.session_state: st.session_state.scanned_code = ""
if 'db' not in st.session_state:
    if os.path.exists(DB_FILE):
        try: st.session_state.db = pd.read_csv(DB_FILE)['polozka'].tolist()
        except: st.session_state.db = []
    else: st.session_state.db = ["50011210 Hrábě švédské", "35020060 Hadice 1 m"]

def uloz_do_db(seznam_polozek):
    st.session_state.db = sorted(list(set(st.session_state.db + seznam_polozek)))
    pd.DataFrame({'polozka': st.session_state.db}).to_csv(DB_FILE, index=False)

# --- SKENER DIALOG (Optimalizováno pro EAN-13) ---
@st.dialog("📸 SKENOVÁNÍ EAN-13")
def skenovat():
    # JavaScript pro komunikaci mezi kamerou a Streamlitem
    components.html("""
        <script src="https://unpkg.com/html5-qrcode"></script>
        <div id="reader" style="width:100%; border-radius:10px; overflow:hidden;"></div>
        <script>
            function onScanSuccess(decodedText, decodedResult) {
                window.parent.postMessage({
                    type: 'streamlit:set_widget_value',
                    value: decodedText,
                    id: 'barcode_input'
                }, '*');
                // Pošleme signál pro zavření nebo refresh
                window.parent.postMessage({type: 'barcode_scanned', value: decodedText}, '*');
            }
            const html5QrCode = new Html5Qrcode("reader");
            const config = { fps: 20, qrbox: {width: 250, height: 150} };
            html5QrCode.start({ facingMode: "environment" }, config, onScanSuccess);
        </script>
    """, height=350)

# --- HLAVNÍ OVLÁDÁNÍ ---
col_a, col_b = st.columns([0.3, 0.7])
with col_a:
    if st.button("📸 SKENOVAT EAN", use_container_width=True):
        skenovat()

with col_b:
    # Pokud je něco naskenováno, použije se to jako výchozí filtr
    search = st.selectbox(
        "🔍 NAŠEPTÁVAČ / VÝSLEDEK SKENU:", 
        [""] + st.session_state.db, 
        index=0,
        help="Zde se objeví i naskenovaný kód"
    ).lower()

# --- VSTUPY DAT ---
t1, t2 = st.tabs(["📄 PDF Převodka", "📝 Ruční přidání"])
with t1:
    up = st.file_uploader("Nahraj PDF", type="pdf")
    if st.button("Uložit z PDF"):
        if up:
            lines = []
            reader = pypdf.PdfReader(up)
            for page in reader.pages:
                for radek in page.extract_text().split('\n'):
                    match = re.search(r'(\d{8,13})\s+(.*)', radek)
                    if match:
                        kod, nazev = match.groups()
                        nazev = re.split(r'(\d+[\s,.]+\d+|Kč|ks|bal|m\d)', nazev)[0].strip()
                        lines.append(f"{kod} {nazev}")
            if lines: uloz_do_db(lines); st.rerun()

with t2:
    c1, c2 = st.columns(2)
    k = c1.text_input("EAN / Kód")
    n = c2.text_input("Název")
    if st.button("Přidat do regálů"):
        if k and n: uloz_do_db([f"{k} {n}"]); st.rerun()

st.divider()

# --- VÝPIS REGÁLŮ A SEZNAMU ---
l, r = st.columns(2)

with l:
    st.subheader("📦 REGÁLY")
    filtr = [p for p in st.session_state.db if search in p.lower()]
    for p in filtr:
        is_sel = p in st.session_state.vybrane
        c_row, c_del = st.columns([0.88, 0.12])
        with c_row:
            ikona = "✅" if is_sel else "⬜"
            if st.button(f"{ikona} {p}", key=f"r_{p}", use_container_width=True):
                if is_sel: st.session_state.vybrane.remove(p)
                else: st.session_state.vybrane.add(p)
                st.rerun()
        with c_del:
            if st.button("🗑️", key=f"d_{p}"):
                st.session_state.db.remove(p)
                st.session_state.vybrane.discard(p)
                pd.DataFrame({'polozka': sorted(st.session_state.db)}).to_csv(DB_FILE, index=False)
                st.rerun()

with r:
    st.subheader("📝 SEZNAM K OBJEDNÁNÍ")
    akt_seznam = sorted(list(st.session_state.vybrane))
    for p in akt_seznam:
        ct, cb = st.columns([0.88, 0.12])
        ct.write(f"**• {p}**")
        if cb.button("❌", key=f"x_{p}"):
            st.session_state.vybrane.remove(p)
            st.rerun()

    if st.session_state.vybrane:
        st.divider()
        txt = "\\n".join(akt_seznam)
        components.html(f"""
            <button id="cp" style="width:100%; background:#1f6feb; color:white; padding:15px; border:none; border-radius:10px; font-weight:bold; cursor:pointer; font-size:16px;">📋 KOPÍROVAT SEZNAM</button>
            <script>
            document.getElementById('cp').onclick = () => {{
                navigator.clipboard.writeText(`{txt}`).then(() => alert('Zkopírováno!'));
            }};
            </script>
        """, height=70)
        
        if st.button("🗑️ VYMAZAT VŠE", use_container_width=True):
            st.session_state.vybrane.clear()
            st.rerun()
