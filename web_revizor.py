import streamlit as st
import pypdf
import re
import pandas as pd
import os

# Nastavení stránky - ODSTRANĚNA IKONA VLEVO
st.set_page_config(page_title="SKLAD ZZN 2026", layout="wide")

# DESIGN - Čistý tmavý styl
st.markdown("""
    <style>
    .main { background-color: #0b0e14; }
    
    /* Kontejner pro hlavní klikací logo */
    .logo-link-container {
        display: flex;
        justify-content: center;
        padding: 20px 0px;
        transition: transform 0.3s;
    }
    .logo-link-container:hover {
        transform: scale(1.02);
    }

    .stCheckbox {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px !important;
        padding: 15px !important;
        margin-bottom: 8px !important;
    }

    div[data-checked="true"] {
        background: linear-gradient(145deg, #3d0a0a, #161b22) !important;
        border: 1px solid #f85149 !important;
    }
    
    .block-container {
        padding-top: 1rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

# HLAVNÍ LOGO JAKO ODKAZ NA WEB ZZN
if os.path.exists("logo_zzn.png"):
    # Cesta k obrázku na tvém GitHubu pro zobrazení v HTML odkazu
    repo_url = "https://raw.githubusercontent.com/Exi-89/sklad-revizor/main/logo_zzn.png"
    st.markdown(
        f"""
        <div class="logo-link-container">
            <a href="https://www.zznhp.cz" target="_blank">
                <img src="{repo_url}" width="500">
            </a>
        </div>
        """, 
        unsafe_allow_html=True
    )
else:
    st.title("ZZN HOSPODÁŘSKÉ POTŘEBY")

# --- LOGIKA DATABÁZE ---
DB_FILE = "sklad_databaze.csv"

def ocisti_pro_objednavku(text):
    text = re.sub(r',?\s*\d+,\d+\s*(ks|m).*', '', text)
    return text.replace('|', '').strip()

def vytahni_kod(text):
    match = re.search(r'(\d{8})', text)
    return match.group(1) if match else None

def nacti_data():
    if os.path.exists(DB_FILE): 
        try: return pd.read_csv(DB_FILE)['polozka'].tolist()
        except: return []
    return ["50011210 Hrábě švédské drát.pevné", "35020060 Hadice 1 m"]

def uloz_data(nove_polozky):
    aktualni = nacti_data()
    existujici_kody = {vytahni_kod(p) for p in aktualni if vytahni_kod(p)}
    finalni = list(aktualni)
    for n in nove_polozky:
        kod_novy = vytahni_kod(n)
        if kod_novy and kod_novy not in existujici_kody:
            finalni.append(n)
            existujici_kody.add(kod_novy)
    pd.DataFrame({'polozka': sorted(finalni)}).to_csv(DB_FILE, index=False)
    return sorted(finalni)

if 'db' not in st.session_state: st.session_state.db = nacti_data()
if 'reset_key' not in st.session_state: st.session_state.reset_key = 0

# --- FUNKČNÍ SEKCE ---
t1, t2, t3 = st.tabs(["📄 PDF Převodka", "🌐 Import z webu ZZN", "📝 Ruční zápis"])

with t1:
    up = st.file_uploader("Nahraj PDF", type="pdf")
    if up:
        reader = pypdf.PdfReader(up)
        z_pdf = [r.strip().split("stav na skladě")[0] for p in reader.pages for r in p.extract_text().split('\n') if re.search(r'\d+,\d+\s*(ks|m)', r)]
        if z_pdf:
            st.session_state.db = uloz_data(z_pdf)
            st.rerun()

with t2:
    web_paste = st.text_area("Vlož text z webu ZZN...", height=150)
    if st.button("Importovat"):
        if web_paste:
            nalezeno = [f"{vytahni_kod(r)} {r.replace(vytahni_kod(r), '').strip()}" for r in web_paste.split('\n') if vytahni_kod(r)]
            if nalezeno:
                st.session_state.db = uloz_data(nalezeno)
                st.rerun()

with t3:
    m_kod = st.text_input("Kód")
    m_nazev = st.text_input("Název")
    if st.button("Uložit"):
        if m_kod and m_nazev:
            st.session_state.db = uloz_data([f"{m_kod} {m_nazev}"])
            st.rerun()

search_query = st.text_input("🔍 Hledat v regálech...", "").lower()

l, r = st.columns([1, 1])
vybrane = []

with l:
    st.subheader("📦 Položka")
    filtered_db = [p for p in st.session_state.db if search_query in p.lower()]
    for i, pol in enumerate(filtered_db):
        cista = ocisti_pro_objednavku(pol)
        if st.checkbox(pol, key=f"cb_{st.session_state.reset_key}_{i}"):
            vybrane.append(cista)

with r:
    st.subheader("📝 SEZNAM K OBJEDNÁNÍ")
    if vybrane:
        st.text_area("K odeslání:", value="\n".join(vybrane), height=300)
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

