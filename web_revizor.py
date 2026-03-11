import streamlit as st
import pypdf
import re
import pandas as pd
import os

# Nastavení stránky
st.set_page_config(page_title="SKLAD ZZN 2026", layout="wide")

# --- DESIGN S BAREVNÝMI KATEGORIEMI ---
st.markdown("""
    <style>
    .main { background-color: #0b0e14; }
    .logo-link-container { display: flex; justify-content: center; padding: 15px 0px; }
    
    /* Základní styl checkboxu */
    .stCheckbox {
        border-radius: 12px !important;
        padding: 12px !important;
        margin-bottom: 6px !important;
        border: 1px solid #30363d;
    }

    /* BAREVNÉ ROZLIŠENÍ PODLE KATEGORIÍ */
    /* Modrá pro hadice a vodu */
    div[data-testid="stMarkdownContainer"]:contains("Hadice"), 
    div[data-testid="stMarkdownContainer"]:contains("voda") {
        border-left: 8px solid #0072FF !important;
    }
    /* Žlutá pro nářadí a kov */
    div[data-testid="stMarkdownContainer"]:contains("Hrábě"),
    div[data-testid="stMarkdownContainer"]:contains("Nářadí") {
        border-left: 8px solid #FFD700 !important;
    }
    /* Zelená pro zahradu a chemii */
    div[data-testid="stMarkdownContainer"]:contains("Postřik"),
    div[data-testid="stMarkdownContainer"]:contains("Hnojivo") {
        border-left: 8px solid #28a745 !important;
    }

    /* Styl pro vybranou (zaškrtnutou) položku */
    div[data-checked="true"] {
        background: linear-gradient(145deg, #2e0505, #161b22) !important;
        border: 1px solid #f85149 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# HLAVNÍ LOGO (ODKAZ NA WEB)
if os.path.exists("logo_zzn.png"):
    repo_url = "https://raw.githubusercontent.com/Exi-89/sklad-revizor/main/logo_zzn.png"
    st.markdown(f'<div class="logo-link-container"><a href="https://www.zznhp.cz" target="_blank"><img src="{repo_url}" width="450"></a></div>', unsafe_allow_html=True)

# --- LOGIKA DATABÁZE ---
DB_FILE = "sklad_databaze.csv"

def nacti_data():
    if os.path.exists(DB_FILE): 
        try: return pd.read_csv(DB_FILE)['polozka'].tolist()
        except: return []
    return ["50011210 Hrábě švédské drát.pevné", "35020060 Hadice 1 m"]

def vytahni_kod(text):
    match = re.search(r'(\d{8})', text)
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

# --- FUNKČNÍ ZÁLOŽKY ---
t1, t2, t3 = st.tabs(["📄 PDF Převodka", "🌐 Import z webu ZZN", "⚡ Sken / Ruční zápis"])

with t1:
    up = st.file_uploader("Nahraj PDF", type="pdf")
    if up:
        reader = pypdf.PdfReader(up)
        z_pdf = [r.strip().split("stav na skladě")[0] for p in reader.pages for r in p.extract_text().split('\n') if re.search(r'\d+,\d+\s*(ks|m)', r)]
        if z_pdf:
            st.session_state.db = uloz_data(z_pdf)
            st.success("Data z PDF uložena!")
            st.rerun()

with t3:
    st.subheader("BOD 3: Našeptávač")
    # Tady začneš psát a ono ti to samo nabízí zboží z tvé historie
    naseptavac = st.selectbox("Hledej zboží (kód nebo název):", [""] + sorted(st.session_state.db))
    
    col1, col2 = st.columns(2)
    with col1:
        kod_input = st.text_input("Kód", value=vytahni_kod(naseptavac) if naseptavac else "")
    with col2:
        nazev_input = st.text_input("Název", value=naseptavac.replace(vytahni_kod(naseptavac) or "", "").strip() if naseptavac else "")
    
    if st.button("Uložit do regálů"):
        if kod_input and nazev_input:
            st.session_state.db = uloz_data([f"{kod_input} {nazev_input}"])
            st.rerun()

# --- HLAVNÍ FILTR (BOD 2: ČTEČKA) ---
st.divider()
search_query = st.text_input("🔍 KLIKNI SEM PRO SKENOVÁNÍ (Čtečka telefonu):", placeholder="Zde pípni kód nebo piš...", help="Pokud máš v mobilu zapnutou čtečku v prohlížeči, stačí kliknout sem.").lower()

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
                navigator.clipboard.writeText(`{vysledek_js}`).then(() => alert('Zkopírováno do schránky!'));
            }});
            </script>
        """, height=70)
        if st.button("🗑️ VYMAZAT VÝBĚR"):
            st.session_state.reset_key += 1
            st.rerun()
