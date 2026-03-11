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
    .logo-link-container { display: flex; justify-content: center; padding: 15px 0px; }
    
    /* Barevné kategorie */
    .stCheckbox { border-radius: 10px; padding: 10px; margin-bottom: 5px; background: #161b22; border: 1px solid #30363d; }
    
    /* Barvy podle textu */
    div[data-testid="stMarkdownContainer"]:contains("Hadice") { border-left: 10px solid #0072FF !important; }
    div[data-testid="stMarkdownContainer"]:contains("Hrábě") { border-left: 10px solid #FFD700 !important; }
    div[data-testid="stMarkdownContainer"]:contains("Postřik") { border-left: 10px solid #28a745 !important; }
    
    /* Velké skenovací tlačítko */
    div.stButton > button:first-child {
        background-color: #f85149;
        color: white;
        height: 3em;
        width: 100%;
        font-weight: bold;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# LOGO
if os.path.exists("logo_zzn.png"):
    repo_url = "https://raw.githubusercontent.com/Exi-89/sklad-revizor/main/logo_zzn.png"
    st.markdown(f'<div class="logo-link-container"><a href="https://www.zznhp.cz" target="_blank"><img src="{repo_url}" width="350"></a></div>', unsafe_allow_html=True)

# --- DATABÁZE ---
DB_FILE = "sklad_databaze.csv"

def nacti_data():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)['polozka'].tolist()
    return ["50011210 Hrábě švédské drát.pevné", "35020060 Hadice 1 m"]

def uloz_data(nove_polozky):
    aktualni = nacti_data()
    # Jednoduché očištění a sloučení
    finalni = list(set(aktualni + nove_polozky))
    pd.DataFrame({'polozka': sorted(finalni)}).to_csv(DB_FILE, index=False)
    st.session_state.db = sorted(finalni)

if 'db' not in st.session_state: st.session_state.db = nacti_data()
if 'reset_key' not in st.session_state: st.session_state.reset_key = 0
if 'search_val' not in st.session_state: st.session_state.search_val = ""

# --- SKENER DIALOG ---
@st.dialog("📸 SKENOVAT EAN-13")
def skenovat():
    st.write("Namiřte na čárový kód")
    components.html("""
        <script src="https://unpkg.com/html5-qrcode"></script>
        <div id="reader" style="width:100%;"></div>
        <script>
            const html5QrCode = new Html5Qrcode("reader");
            html5QrCode.start({ facingMode: "environment" }, { fps: 10, qrbox: 250 }, (txt) => {
                window.parent.postMessage({type: 'streamlit:setComponentValue', value: txt}, '*');
                html5QrCode.stop();
            });
        </script>
    """, height=300)

# --- HLAVNÍ PANELE ---
col_s, col_e = st.columns([1, 2])
with col_s:
    if st.button("📸 SPUSTIT SKENER"):
        skenovat()

search_query = st.text_input("🔍 Hledat v regálech (kód/název)...", value=st.session_state.search_val).lower()

# --- ZÁLOŽKY (OPRAVENO) ---
tab1, tab2, tab3 = st.tabs(["📄 PDF Převodka", "🌐 Import", "📝 Ruční"])

with tab1:
    soubor = st.file_uploader("Nahraj PDF", type="pdf")
    if soubor:
        reader = pypdf.PdfReader(soubor)
        texty = [r.strip() for p in reader.pages for r in p.extract_text().split('\n') if len(r) > 5]
        if st.button("Uložit data z PDF"):
            uloz_data(texty)
            st.success("Uloženo!")
            st.rerun()

with tab2:
    vlozeny_text = st.text_area("Vlož text z webu...")
    if st.button("Importovat z webu"):
        if vlozeny_text:
            radky = [r.strip() for r in vlozeny_text.split('\n') if len(r) > 3]
            uloz_data(radky)
            st.rerun()

with tab3:
    c1, c2 = st.columns(2)
    k = c1.text_input("Kód")
    n = c2.text_input("Název")
    if st.button("Přidat ručně"):
        if k and n:
            uloz_data([f"{k} {n}"])
            st.rerun()

# --- VÝPIS ---
st.divider()
l, r = st.columns(2)

with l:
    st.subheader("📦 REGÁLY")
    vyfiltrovano = [p for p in st.session_state.db if search_query in p.lower()]
    vybrane = []
    for i, p in enumerate(vyfiltrovano):
        if st.checkbox(p, key=f"p_{st.session_state.reset_key}_{i}"):
            vybrane.append(p)

with r:
    st.subheader("📝 SEZNAM")
    if vybrane:
        vysledek = "\n".join(vybrane)
        st.text_area("K odeslání:", value=vysledek, height=200)
        if st.button("🗑️ VYMAZAT"):
            st.session_state.reset_key += 1
            st.rerun()
