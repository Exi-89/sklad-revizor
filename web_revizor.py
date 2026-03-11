import streamlit as st
import pypdf
import re
import pandas as pd
import os

# Nastavení stránky
st.set_page_config(page_title="SKLAD ZZN 2026", page_icon="⚡", layout="wide")

# DESIGN - Čistý tmavý styl ladící k logu ZZN
st.markdown("""
    <style>
    .main { background-color: #0b0e14; }
    .logo-container {
        display: flex;
        justify-content: center;
        padding: 20px;
        background-color: #ffffff;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    h1 {
        background: linear-gradient(90deg, #00f2fe 0%, #4facfe 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.2rem !important;
        text-align: center;
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
    </style>
    """, unsafe_allow_html=True)

# LOGO - Načte se ze souboru logo_zzn.png, který nahraješ na GitHub
if os.path.exists("logo_zzn.png"):
    st.markdown('<div class="logo-container">', unsafe_allow_html=True)
    st.image("logo_zzn.png", width=400)
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.markdown("<h2 style='text-align: center; color: white;'>ZZN HOSPODÁŘSKÉ POTŘEBY</h2>", unsafe_allow_html=True)

st.title("⚡ SKLAD REVIZOR ZZN PRO")

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
    for n in nove_polozky: # OPRAVA: 'in' místo 'v'
        kod_novy = vytahni_kod(n)
        if kod_novy and kod_novy not in existujici_kody:
            finalni.append(n)
            existujici_kody.add(kod_novy)
    pd.DataFrame({'polozka': sorted(finalni)}).to_csv(DB_FILE, index=False)
    return sorted(finalni)

if 'db' not in st.session_state: st.session_state.db = nacti_data()
if 'reset_key' not in st.session_state: st.session_state.reset_key = 0

# --- IMPORTY ---
t1, t2, t3 = st.tabs(["📄 PDF Převodka", "🌐 Import z webu ZZN", "📝 Ruční zápis"])

with t1:
    up = st.file_uploader("Nahraj PDF převodku", type="pdf")
    if up:
        reader = pypdf.PdfReader(up)
        z_pdf = [r.strip().split("stav na skladě")[0] for p in reader.pages for r in p.extract_text().split('\n') if re.search(r'\d+,\d+\s*(ks|m)', r)]
        if z_pdf:
            st.session_state.db = uloz_data(z_pdf)
            st.success("PDF nahráno!")
            st.rerun()

with t2:
    st.info("Na webu ZZN označ zboží (Ctrl+A), zkopíruj (Ctrl+C) a vlož sem.")
    web_paste = st.text_area("Vložit text z webu...", height=150)
    if st.button("Importovat z webu"):
        if web_paste:
            nalezeno = [f"{vytahni_kod(r)} {r.replace(vytahni_kod(r), '').strip()}" for r in web_paste.split('\n') if vytahni_kod(r)]
            if nalezeno:
                st.session_state.db = uloz_data(nalezeno)
                st.success(f"Přidáno {len(nalezeno)} položek!")
                st.rerun()

with t3:
    m_kod = st.text_input("Kód (8 čísel)")
    m_nazev = st.text_input("Název")
    if st.button("Uložit do skladu"):
        if m_kod and m_nazev:
            st.session_state.db = uloz_data([f"{m_kod} {m_nazev}"])
            st.rerun()

# --- FILTR A VÝBĚR ---
search_query = st.text_input("🔍 Vyhledat v regálech ZZN...", "").lower()
l, r = st.columns([1, 1])
vybrane = []

with l:
    st.subheader("📦 REGÁLY SIBL")
    filtered_db = [p for p in st.session_state.db if search_query in p.lower()]
    for i, pol in enumerate(filtered_db):
        cista = ocisti_pro_objednavku(pol)
        if st.checkbox(pol, key=f"cb_{st.session_state.reset_key}_{i}"):
            vybrane.append(cista)

with r:
    st.subheader("📝 SEZNAM K OBJEDNÁNÍ")
    if vybrane:
        st.text_area("Kopie seznamu:", value="\n".join(vybrane), height=300)
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
    else:
        st.info("Zatím nic nevybráno.")
