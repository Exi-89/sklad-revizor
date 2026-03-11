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
    #tabs-b3-tab-1 { color: #0072FF !important; }
    #tabs-b3-tab-2 { color: #adbac7 !important; }

    .row-container {
        display: flex; align-items: center; border-radius: 8px;
        margin-bottom: 6px; background: #1c2128; border: 1px solid #30363d; overflow: hidden;
    }
    .color-strip { width: 14px; align-self: stretch; }
    .cat-blue { background-color: #0072FF; }
    .cat-yellow { background-color: #FFD700; }
    .cat-green { background-color: #28a745; }
    .cat-red { background-color: #f85149; }
    .cat-orange { background-color: #ff9f43; }
    .cat-default { background-color: #444c56; }
    </style>
    """, unsafe_allow_html=True)

# LOGO
repo_url = "https://raw.githubusercontent.com/Exi-89/sklad-revizor/main/logo_zzn.png"
st.markdown(f'<div class="logo-container"><a href="https://www.zznhp.cz" target="_blank"><img src="{repo_url}" class="logo-img"></a></div>', unsafe_allow_html=True)

# --- LOGIKA DAT ---
DB_FILE = "sklad_databaze.csv"

# Inicializace stavů
if 'vybrane_polozky' not in st.session_state: st.session_state.vybrane_polozky = set()
if 'db' not in st.session_state:
    if os.path.exists(DB_FILE):
        try: st.session_state.db = pd.read_csv(DB_FILE)['polozka'].tolist()
        except: st.session_state.db = []
    else: st.session_state.db = ["50011210 Hrábě švédské", "35020060 Hadice 1 m"]

def uloz_data(nove):
    st.session_state.db = sorted(list(set(st.session_state.db + nove)))
    pd.DataFrame({'polozka': st.session_state.db}).to_csv(DB_FILE, index=False)

# --- ZÁLOŽKY ---
t1, t2, t3 = st.tabs(["📄 PDF Převodka", "🌐 Import", "📝 Ruční"])
with t1:
    up = st.file_uploader("Nahraj PDF", type="pdf")
    if st.button("Uložit z PDF"):
        if up:
            reader = pypdf.PdfReader(up)
            z_pdf = [r.strip() for p in reader.pages for r in p.extract_text().split('\n') if len(r) > 5]
            uloz_data(z_pdf); st.rerun()
with t2:
    web = st.text_area("Vložit text...")
    if st.button("Importovat"):
        if web: uloz_data([r.strip() for r in web.split('\n') if len(r) > 3]); st.rerun()
with t3:
    c1, c2 = st.columns(2)
    k, n = c1.text_input("Kód"), c2.text_input("Název")
    if st.button("Přidat zboží"):
        if k and n: uloz_data([f"{k} {n}"]); st.rerun()

st.divider()

# --- HLAVNÍ ČÁST (REGÁLY A SEZNAM) ---
search_query = st.text_input("🔍 Rychlé hledání v regálech:", "").lower()

def urcit_barvu(text):
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
    vyfiltrovano = [p for p in st.session_state.db if search_query in p.lower()]
    
    for i, p in enumerate(vyfiltrovano):
        barva = urcit_barvu(p)
        c_line, c_del = st.columns([0.85, 0.15])
        with c_line:
            st.markdown(f'<div class="row-container"><div class="color-strip {barva}"></div>', unsafe_allow_html=True)
            # Klíčová oprava: checkbox přímo upravuje set v session_state
            if st.checkbox(p, key=f"check_{p}", value=(p in st.session_state.vybrane_polozky)):
                st.session_state.vybrane_polozky.add(p)
            else:
                st.session_state.vybrane_polozky.discard(p)
            st.markdown('</div>', unsafe_allow_html=True)
        with c_del:
            if st.button("🗑️", key=f"db_del_{p}"):
                st.session_state.db.remove(p)
                st.session_state.vybrane_polozky.discard(p) # Smazat i z výběru
                pd.DataFrame({'polozka': sorted(st.session_state.db)}).to_csv(DB_FILE, index=False)
                st.rerun()

with r:
    st.subheader("📝 SEZNAM K OBJEDNÁNÍ")
    
    akt_seznam = sorted(list(st.session_state.vybrane_polozky))
    
    for p in akt_seznam:
        col_t, col_b = st.columns([0.85, 0.15])
        col_t.write(f"• {p}")
        if col_b.button("❌", key=f"list_del_{p}"):
            st.session_state.vybrane_polozky.discard(p)
            # Tady smažeme i stav checkboxu v paměti Streamlitu
            if f"check_{p}" in st.session_state:
                del st.session_state[f"check_{p}"]
            st.rerun()

    if st.session_state.vybrane_polozky:
        st.divider()
        vysledek_js = "\\n".join(akt_seznam)
        st.components.v1.html(f"""
            <button id="cpBtn" style="width:100%; background:linear-gradient(90deg, #1f6feb, #58a6ff); color:white; padding:15px; border:none; border-radius:10px; font-size:18px; font-weight:bold; cursor:pointer;">📋 KOPÍROVAT SEZNAM</button>
            <script>
            document.getElementById('cpBtn').addEventListener('click', function() {{
                navigator.clipboard.writeText(`{vysledek_js}`).then(() => alert('Zkopírováno!'));
            }});
            </script>
        """, height=70)
        
        if st.button("🗑️ VYMAZAT VŠE"):
            # Totální čistka
            for p in list(st.session_state.vybrane_polozky):
                if f"check_{p}" in st.session_state:
                    del st.session_state[f"check_{p}"]
            st.session_state.vybrane_polozky.clear()
            st.rerun()
