import streamlit as st
import pypdf
import re
import pandas as pd
import os
import streamlit.components.v1 as components

# Nastavení stránky
st.set_page_config(page_title="SKLAD ZZN 2026", layout="wide")

# --- STYLE A BARVY ---
st.markdown("""
    <style>
    .main { background-color: #0b0e14; }
    .logo-link-container { display: flex; justify-content: center; padding: 10px 0px; }
    
    .row-container {
        display: flex;
        align-items: center;
        border-radius: 10px;
        margin-bottom: 8px;
        background: #161b22;
        border: 1px solid #30363d;
        overflow: hidden;
    }
    .color-strip { width: 15px; align-self: stretch; }
    
    /* Definice barev */
    .cat-blue { background-color: #0072FF; }
    .cat-yellow { background-color: #FFD700; }
    .cat-green { background-color: #28a745; }
    .cat-red { background-color: #f85149; }
    .cat-orange { background-color: #ff9f43; }
    .cat-default { background-color: #30363d; }

    div.stButton > button:first-child {
        background: linear-gradient(90deg, #f85149, #d73a49);
        color: white; height: 3.5em; width: 100%; font-weight: bold; border-radius: 12px; border: none;
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

def vytahni_kod(text):
    match = re.search(r'(\d{8,13})', text)
    return match.group(1) if match else ""

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
                window.parent.document.querySelector('input[aria-label*="Hledat"]').value = txt;
                const ke = new KeyboardEvent('keydown', { bubbles: true, keyCode: 13 });
                window.parent.document.querySelector('input[aria-label*="Hledat"]').dispatchEvent(ke);
                html5QrCode.stop();
            });
        </script>
    """, height=350)

# --- OVLÁDÁNÍ ---
col_btn, _ = st.columns([1, 1])
with col_btn:
    if st.button("📸 SKENOVAT ČÁROVÝ KÓD"):
        skenovat()

search_query = st.text_input("🔍 Hledat v regálech (kód/název)...", value="").lower()

# --- ZÁLOŽKY ---
t1, t2, t3 = st.tabs(["📄 PDF Převodka", "🌐 Import", "📝 Našeptávač / Ruční"])

with t1:
    up = st.file_uploader("Nahraj PDF", type="pdf")
    if st.button("Uložit z PDF"):
        if up:
            reader = pypdf.PdfReader(up)
            z_pdf = [r.strip() for p in reader.pages for r in p.extract_text().split('\n') if len(r) > 5]
            uloz_data(z_pdf)
            st.rerun()

with t2:
    web = st.text_area("Vlož text z webu...")
    if st.button("Importovat web"):
        if web:
            uloz_data([r.strip() for r in web.split('\n') if len(r) > 3])
            st.rerun()

with t3:
    st.subheader("BOD 3: Našeptávač")
    volba = st.selectbox("Vyber zboží:", [""] + sorted(st.session_state.db))
    c1, c2 = st.columns(2)
    with c1:
        novy_kod = st.text_input("Kód", value=vytahni_kod(volba) if volba else "")
    with c2:
        novy_nazev = st.text_input("Název", value=volba.replace(vytahni_kod(volba), "").strip() if volba else "")
    if st.button("➕ Přidat do regálu"):
        if novy_kod and novy_nazev:
            uloz_data([f"{novy_kod} {novy_nazev}"])
            st.rerun()

# --- VÝPIS S BARVAMI ---
st.divider()

def urcit_barvu(text):
    text = text.lower()
    if any(x in text for x in ["hadice", "voda", "postřikovač"]): return "cat-blue"
    if any(x in text for x in ["hrábě", "lopat", "násada"]): return "cat-yellow"
    if any(x in text for x in ["hnojiv", "substrát", "postřik"]): return "cat-green"
    if any(x in text for x in ["pletivo", "drát", "hřebík"]): return "cat-red"
    if any(x in text for x in ["nářadí", "kladiv", "kleště"]): return "cat-orange"
    return "cat-default"

l, r = st.columns(2)
with l:
    st.subheader("📦 REGÁLY")
    vyfiltrovano = [p for p in st.session_state.db if search_query in p.lower()]
    vybrane = []
    for i, p in enumerate(vyfiltrovano):
        barva = urcit_barvu(p)
        st.markdown(f'<div class="row-container"><div class="color-strip {barva}"></div>', unsafe_allow_html=True)
        if st.checkbox(p, key=f"p_{st.session_state.reset_key}_{i}"):
            vybrane.append(re.sub(r',?\s*\d+,\d+\s*(ks|m).*', '', p).strip())
        st.markdown('</div>', unsafe_allow_html=True)

with r:
    st.subheader("📝 SEZNAM")
    if vybrane:
        st.text_area("K odeslání:", value="\n".join(vybrane), height=300)
        if st.button("🗑️ VYMAZAT VÝBĚR"):
            st.session_state.reset_key += 1
            st.rerun()
