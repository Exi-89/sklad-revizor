import streamlit as st
import pypdf
import re
import pandas as pd
import os
import streamlit.components.v1 as components

# Nastavení stránky
st.set_page_config(page_title="SKLAD ZZN 2026", layout="wide")

# --- DESIGN A DYNAMICKÉ BARVY ---
st.markdown("""
    <style>
    .main { background-color: #0b0e14; }
    .logo-link-container { display: flex; justify-content: center; padding: 15px 0px; }
    
    /* Karty položek v regálech */
    .stCheckbox { 
        border-radius: 10px; 
        padding: 10px; 
        margin-bottom: 5px; 
        border-left: 12px solid #30363d; /* Výchozí šedá */
        background: #161b22;
        transition: 0.2s;
    }
    
    /* Dynamické barvení podle klíčových slov v textu */
    div[data-testid="stMarkdownContainer"]:contains("Hadice") { border-left-color: #0072FF !important; }
    div[data-testid="stMarkdownContainer"]:contains("Hrábě") { border-left-color: #FFD700 !important; }
    div[data-testid="stMarkdownContainer"]:contains("Postřik") { border-left-color: #28a745 !important; }
    div[data-testid="stMarkdownContainer"]:contains("Pletivo") { border-left-color: #f85149 !important; }
    div[data-testid="stMarkdownContainer"]:contains("Nářadí") { border-left-color: #ff9f43 !important; }

    /* Zvýraznění vybraného řádku */
    div[data-checked="true"] { background: #1f2937 !important; border-top: 1px solid #4facfe !important; }
    
    #reader { width: 100%; border-radius: 12px; overflow: hidden; border: 2px solid #30363d; }
    </style>
    """, unsafe_allow_html=True)

# LOGO S ODKAZEM
if os.path.exists("logo_zzn.png"):
    repo_url = "https://raw.githubusercontent.com/Exi-89/sklad-revizor/main/logo_zzn.png"
    st.markdown(f'<div class="logo-link-container"><a href="https://www.zznhp.cz" target="_blank"><img src="{repo_url}" width="400"></a></div>', unsafe_allow_html=True)

# --- LOGIKA DATABÁZE ---
DB_FILE = "sklad_databaze.csv"

def nacti_data():
    if os.path.exists(DB_FILE): 
        try: return pd.read_csv(DB_FILE)['polozka'].tolist()
        except: return []
    return ["50011210 Hrábě švédské drát.pevné", "35020060 Hadice 1 m"]

def vytahni_kod(text):
    match = re.search(r'(\d{8,13})', text) # Upraveno pro 8 až 13 čísel
    return match.group(1) if match else None

def uloz_data(nove_polozky):
    aktualni = nacti_data()
    existujici_kody = {vytahni_kod(p) for p in aktualni if vytahni_kod(p)}
    finalni = list(aktualni)
    for n in nove_polozky:
        kod_novy = vytahni_kod(n)
        if kod_novy and kod_novy not in existujici_kody:
            finalni.append(n)
    pd.DataFrame({'polozka': sorted(finalni)}).to_csv(DB_FILE, index=False)
    return sorted(finalni)

if 'db' not in st.session_state: st.session_state.db = nacti_data()
if 'reset_key' not in st.session_state: st.session_state.reset_key = 0

# --- SPECIÁLNÍ EAN-13 ČTEČKA ---
st.subheader("📸 Skenovat EAN-13")

# Tento kousek kódu vytvoří v aplikaci okno s foťákem
components.html(
    """
    <script src="https://unpkg.com/html5-qrcode"></script>
    <div id="reader"></div>
    <script>
        function onScanSuccess(decodedText) {
            // Předání kódu zpět do Streamlitu
            window.parent.postMessage({type: 'barcode_result', value: decodedText}, '*');
        }

        const html5QrCode = new Html5Qrcode("reader");
        const config = { 
            fps: 20, 
            qrbox: { width: 300, height: 150 },
            aspectRatio: 1.0
        };

        // Nastavení pouze pro EAN-13 a EAN-8 pro vyšší rychlost
        html5QrCode.start(
            { facingMode: "environment" }, 
            config, 
            onScanSuccess
        ).catch(err => console.error(err));
    </script>
    """,
    height=320,
)

# Textové pole, kam čtečka "vysype" výsledek
search_query = st.text_input("🔍 Vyhledat nebo výsledek skenu:", key="search_input").lower()

# --- ZÁLOŽKY ---
t1, t2, t3 = st.tabs(["📄 PDF Převodka", "🌐 Import z webu", "📝 Ruční zápis"])

with t3:
    naseptavac = st.selectbox("Našeptávač zboží:", [""] + sorted(st.session_state.db))
    c1, c2 = st.columns(2)
    with c1:
        k_in = st.text_input("Kód", value=vytahni_kod(naseptavac) if naseptavac else "")
    with c2:
        n_in = st.text_input("Název", value=naseptavac.replace(vytahni_kod(naseptavac) or "", "").strip() if naseptavac else "")
    if st.button("Uložit do skladu"):
        if k_in and n_in:
            st.session_state.db = uloz_data([f"{k_in} {n_in}"])
            st.rerun()

# --- REGÁLY ---
l, r = st.columns([1, 1])
vybrane = []

with l:
    st.subheader("📦 REGÁLY SIBL")
    filtered_db = [p for p in st.session_state.db if search_query in p.lower()]
    for i, pol in enumerate(filtered_db):
        cista = re.sub(r',?\s*\d+,\d+\s*(ks|m).*', '', pol).strip()
        if st.checkbox(pol, key=f"cb_{st.session_state.reset_key}_{i}"):
            vybrane.append(cista)

with r:
    st.subheader("📝 SEZNAM K OBJEDNÁNÍ")
    if vybrane:
        st.text_area("Seznam:", value="\n".join(vybrane), height=300)
        vysledek_js = "\\n".join(vybrane)
        st.components.v1.html(f"""
            <button id="copyBtn" style="width:100%; background:linear-gradient(90deg, #0072FF, #00C6FF); color:white; padding:15px; border:none; border-radius:10px; font-size:18px; font-weight:bold; cursor:pointer;">📋 KOPÍROVAT PRO ZZN</button>
            <script>
            document.getElementById('copyBtn').addEventListener('click', function() {{
                navigator.clipboard.writeText(`{vysledek_js}`).then(() => alert('Zkopírováno!'));
            }});
            </script>
        """, height=70)
        if st.button("🗑️ VYMAZAT VÝBĚR"):
            st.session_state.reset_key += 1
            st.rerun()
