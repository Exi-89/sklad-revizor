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
    .logo-link-container { display: flex; justify-content: center; padding: 10px 0px; }
    
    .row-container {
        display: flex; align-items: center; border-radius: 8px;
        margin-bottom: 6px; background: #1c2128; border: 1px solid #30363d; overflow: hidden;
    }
    .color-strip { width: 10px; align-self: stretch; }
    
    /* Barvy kategorií */
    .cat-blue { background-color: #0072FF; }
    .cat-yellow { background-color: #FFD700; }
    .cat-green { background-color: #28a745; }
    .cat-red { background-color: #f85149; }
    .cat-orange { background-color: #ff9f43; }
    .cat-default { background-color: #444c56; }

    /* Decentní tlačítka */
    div.stButton > button:first-child {
        background-color: #30363d !important; color: #adbac7 !important;
        border: 1px solid #444c56 !important; border-radius: 8px !important;
    }
    div.stButton > button:first-child:hover {
        border-color: #58a6ff !important; color: #58a6ff !important;
    }
    </style>
    """, unsafe_allow_html=True)

# LOGO
if os.path.exists("logo_zzn.png"):
    repo_url = "https://raw.githubusercontent.com/Exi-89/sklad-revizor/main/logo_zzn.png"
    st.markdown(f'<div class="logo-link-container"><a href="https://www.zznhp.cz" target="_blank"><img src="{repo_url}" width="300"></a></div>', unsafe_allow_html=True)

# --- LOGIKA DAT ---
DB_FILE = "sklad_databaze.csv"

if 'vybrane_polozky' not in st.session_state: st.session_state.vybrane_polozky = []

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

def smaz_z_databaze(polozka_ke_smazani):
    aktualni = nacti_data()
    if polozka_ke_smazani in aktualni:
        aktualni.remove(polozka_ke_smazani)
        pd.DataFrame({'polozka': sorted(aktualni)}).to_csv(DB_FILE, index=False)
        st.session_state.db = sorted(aktualni)

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

# --- OVLÁDÁNÍ ---
col_scan, _ = st.columns([1, 1])
with col_scan:
    if st.button("📸 SPUSTIT SKENER"): skenovat()

search_query = st.selectbox("🔍 Našeptávač / Hledat v regálech:", [""] + st.session_state.db, index=0).lower()

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
    web = st.text_area("Vložit text...")
    if st.button("Importovat text"):
        if web: uloz_data([r.strip() for r in web.split('\n') if len(r) > 3]); st.rerun()
with t3:
    c1, c2 = st.columns(2)
    k, n = c1.text_input("Kód"), c2.text_input("Název")
    if st.button("Přidat zboží"):
        if k and n: uloz_data([f"{k} {n}"]); st.rerun()

# --- VÝPIS ---
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
    st.subheader("📦 REGÁLY (Databáze)")
    vyfiltrovano = [p for p in st.session_state.db if search_query in p.lower()]
    for i, p in enumerate(vyfiltrovano):
        barva = urcit_barvu(p)
        c_line, c_del_db = st.columns([0.85, 0.15])
        with c_line:
            st.markdown(f'<div class="row-container"><div class="color-strip {barva}"></div>', unsafe_allow_html=True)
            if st.checkbox(p, key=f"p_{st.session_state.reset_key}_{i}"):
                cista = re.sub(r',?\s*\d+,\d+\s*(ks|m).*', '', p).strip()
                if cista not in st.session_state.vybrane_polozky:
                    st.session_state.vybrane_polozky.append(cista)
            st.markdown('</div>', unsafe_allow_html=True)
        with c_del_db:
            if st.button("🗑️", key=f"del_db_{i}", help="Smazat trvale z regálů"):
                smaz_z_databaze(p)
                st.rerun()

with r:
    st.subheader("📝 SEZNAM K OBJEDNÁNÍ")
    smazat_idx = -1
    for idx, pol in enumerate(st.session_state.vybrane_polozky):
        cp, cd = st.columns([0.85, 0.15])
        cp.write(f"• {pol}")
        if cd.button("❌", key=f"del_list_{idx}", help="Odstranit ze seznamu"):
            smazat_idx = idx
    
    if smazat_idx != -1:
        st.session_state.vybrane_polozky.pop(smazat_idx)
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
        
        if st.button("🗑️ VYMAZAT VŠE"):
            st.session_state.vybrane_polozky = []
            st.session_state.reset_key += 1
            st.rerun()
