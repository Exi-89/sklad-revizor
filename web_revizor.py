import streamlit as st
import pypdf
import re
import pandas as pd
import os
import streamlit.components.v1 as components

# Nastavení stránky
st.set_page_config(page_title="SKLAD ZZN 2026", layout="wide")

# --- STYLE - NOVÝ DECENTNÍ DESIGN ---
st.markdown("""
    <style>
    .main { background-color: #0b0e14; }
    .logo-link-container { display: flex; justify-content: center; padding: 10px 0px; }
    
    /* Kontejner položky v regálu */
    .row-container {
        display: flex;
        align-items: center;
        border-radius: 8px;
        margin-bottom: 6px;
        background: #1c2128;
        border: 1px solid #30363d;
        overflow: hidden;
    }
    .color-strip { width: 10px; align-self: stretch; }
    
    /* Barvy kategorií */
    .cat-blue { background-color: #0072FF; }
    .cat-yellow { background-color: #FFD700; }
    .cat-green { background-color: #28a745; }
    .cat-red { background-color: #f85149; }
    .cat-orange { background-color: #ff9f43; }
    .cat-default { background-color: #444c56; }

    /* Stylování tlačítek - ŠEDO-MODRÁ místo ČERVENÉ */
    div.stButton > button:first-child {
        background-color: #30363d !important;
        color: #adbac7 !important;
        border: 1px solid #444c56 !important;
        height: 3em;
        width: 100%;
        font-weight: 600 !important;
        border-radius: 8px !important;
        transition: 0.3s;
    }
    div.stButton > button:first-child:hover {
        border-color: #58a6ff !important;
        color: #58a6ff !important;
        background-color: #30363d !important;
    }
    </style>
    """, unsafe_allow_html=True)

# LOGO
if os.path.exists("logo_zzn.png"):
    repo_url = "https://raw.githubusercontent.com/Exi-89/sklad-revizor/main/logo_zzn.png"
    st.markdown(f'<div class="logo-link-container"><a href="https://www.zznhp.cz" target="_blank"><img src="{repo_url}" width="300"></a></div>', unsafe_allow_html=True)

# --- DATABÁZE A SEZNAM ---
DB_FILE = "sklad_databaze.csv"

if 'vybrane_polozky' not in st.session_state:
    st.session_state.vybrane_polozky = []

def nacti_data():
    if os.path.exists(DB_FILE):
        try: return pd.read_csv(DB_FILE)['polozka'].tolist()
        except: return []
    return ["50011210 Hrábě švédské drát.pevné", "35020060 Hadice 1 m"]

def uloz_data(nove_polozky):
    aktualni = nacti_data()
    finalni = list(set(aktualni + nove_polozky))
    pd.DataFrame({'polozka': sorted(finalni)}).to_csv(DB_FILE, index=False)
    st.session_state.db = sorted(finalni)

if 'db' not in st.session_state: st.session_state.db = nacti_data()
if 'reset_key' not in st.session_state: st.session_state.reset_key = 0

# --- SKENER DIALOG ---
@st.dialog("📸 SKENOVÁNÍ EAN-13")
def skenovat():
    st.write("Namiřte na čárový kód...")
    components.html("""
        <script src="https://unpkg.com/html5-qrcode"></script>
        <div id="reader" style="width:100%; border-radius:10px; overflow:hidden;"></div>
        <script>
            const html5QrCode = new Html5Qrcode("reader");
            html5QrCode.start({ facingMode: "environment" }, { fps: 20, qrbox: {width: 250, height: 150} }, (txt) => {
                window.parent.postMessage({type: 'barcode_scanned', value: txt}, '*');
                html5QrCode.stop();
            });
        </script>
    """, height=350)

# --- HLAVNÍ OVLÁDÁNÍ ---
col_scan, _ = st.columns([1, 1])
with col_scan:
    if st.button("📸 SPUSTIT SKENER"):
        skenovat()

# NASEPTAVAC VE VYHLEDAVANI
search_query = st.selectbox("🔍 Hledat v databázi (napiš název nebo kód):", [""] + st.session_state.db, index=0).lower()

# --- ZÁLOŽKY ---
t1, t2, t3 = st.tabs(["📄 PDF Převodka", "🌐 Import", "📝 Ruční"])

with t1:
    up = st.file_uploader("Nahraj PDF", type="pdf")
    if st.button("Uložit z PDF"):
        if up:
            reader = pypdf.PdfReader(up)
            z_pdf = [r.strip() for p in reader.pages for r in p.extract_text().split('\n') if len(r) > 5]
            uloz_data(z_pdf)
            st.rerun()

with t2:
    web = st.text_area("Vložit text z webu...")
    if st.button("Importovat text"):
        if web:
            uloz_data([r.strip() for r in web.split('\n') if len(r) > 3])
            st.rerun()

with t3:
    c1, c2 = st.columns(2)
    k = c1.text_input("Kód zboží")
    n = c2.text_input("Název zboží")
    if st.button("Přidat do regálů"):
        if k and n:
            uloz_data([f"{k} {n}"])
            st.rerun()

# --- REGÁLY A SEZNAM ---
st.divider()

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
        st.markdown(f'<div class="row-container"><div class="color-strip {barva}"></div>', unsafe_allow_html=True)
        # Pokud uživatel klikne, přidáme do seznamu (pokud tam už není)
        if st.checkbox(p, key=f"p_{st.session_state.reset_key}_{i}"):
            cista = re.sub(r',?\s*\d+,\d+\s*(ks|m).*', '', p).strip()
            if cista not in st.session_state.vybrane_polozky:
                st.session_state.vybrane_polozky.append(cista)
        st.markdown('</div>', unsafe_allow_html=True)

with r:
    st.subheader("📝 SEZNAM K OBJEDNÁNÍ")
    
    # Výpis položek s možností mazání
    smazat_index = -1
    for idx, pol in enumerate(st.session_state.vybrane_polozky):
        c_pol, c_del = st.columns([0.85, 0.15])
        c_pol.write(f"• {pol}")
        if c_del.button("❌", key=f"del_{idx}"):
            smazat_index = idx
    
    if smazat_index != -1:
        st.session_state.vybrane_polozky.pop(smazat_index)
        st.rerun()

    if st.session_state.vybrane_polozky:
        st.divider()
        vysledek_js = "\\n".join(st.session_state.vybrane_polozky)
        st.components.v1.html(f"""
            <button id="cpBtn" style="width:100%; background:linear-gradient(90deg, #1f6feb, #58a6ff); color:white; padding:15px; border:none; border-radius:10px; font-size:18px; font-weight:bold; cursor:pointer;">📋 KOPÍROVAT SEZNAM</button>
            <script>
            document.getElementById('cpBtn').addEventListener('click', function() {{
                navigator.clipboard.writeText(`{vysledek_js}`).then(() => alert('Zkopírováno!'));
            }});
            </script>
        """, height=70)
        
        if st.button("🗑️ SMAZAT CELÝ SEZNAM"):
            st.session_state.vybrane_polozky = []
            st.session_state.reset_key += 1
            st.rerun()
