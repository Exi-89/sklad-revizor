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
    
    /* Barvy kategorií */
    .cat-blue { background-color: #0072FF; }
    .cat-yellow { background-color: #FFD700; }
    .cat-green { background-color: #28a745; }
    .cat-red { background-color: #f85149; }
    .cat-orange { background-color: #ff9f43; }
    .cat-default { background-color: #30363d; }

    /* Skenovací tlačítko */
    div.stButton > button.scan-btn {
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
if st.button("📸 SKENOVAT ČÁROVÝ KÓD", css_class="scan-btn"):
    skenovat()

# NASEPTAVAC VE VYHLEDAVANI
search_query = st.selectbox("🔍 Hledat nebo vybrat z databáze:", [""] + st.session_state.db, index=0).lower()

# --- ZÁLOŽKY PRO IMPORT ---
t1, t2, t3 = st.tabs(["📄 PDF Převodka", "🌐 Import", "📝 Ruční přidání"])

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
    c1, c2 = st.columns(2)
    k = c1.text_input("Kód")
    n = c2.text_input("Název")
    if st.button("Přidat do databáze"):
        if k and n:
            uloz_data([f"{k} {n}"])
            st.rerun()

# --- VÝPIS A KOPÍROVÁNÍ ---
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
vybrane = []

with l:
    st.subheader("📦 REGÁLY")
    vyfiltrovano = [p for p in st.session_state.db if search_query in p.lower()]
    for i, p in enumerate(vyfiltrovano):
        barva = urcit_barvu(p)
        st.markdown(f'<div class="row-container"><div class="color-strip {barva}"></div>', unsafe_allow_html=True)
        if st.checkbox(p, key=f"p_{st.session_state.reset_key}_{i}"):
            vybrane.append(re.sub(r',?\s*\d+,\d+\s*(ks|m).*', '', p).strip())
        st.markdown('</div>', unsafe_allow_html=True)

with r:
    st.subheader("📝 SEZNAM K OBJEDNÁNÍ")
    if vybrane:
        vysledek_text = "\n".join(vybrane)
        st.text_area("Seznam:", value=vysledek_text, height=250)
        
        # TLAČÍTKO PRO KOPÍROVÁNÍ
        vysledek_js = "\\n".join(vybrane)
        st.components.v1.html(f"""
            <button id="cpBtn" style="width:100%; background:linear-gradient(90deg, #0072FF, #00C6FF); color:white; padding:15px; border:none; border-radius:10px; font-size:18px; font-weight:bold; cursor:pointer;">📋 KOPÍROVAT PRO ZZN</button>
            <script>
            document.getElementById('cpBtn').addEventListener('click', function() {{
                navigator.clipboard.writeText(`{vysledek_js}`).then(() => alert('Zkopírováno do schránky!'));
            }});
            </script>
        """, height=70)
        
        if st.button("🗑️ VYMAZAT VÝBĚR"):
            st.session_state.reset_key += 1
            st.rerun()
