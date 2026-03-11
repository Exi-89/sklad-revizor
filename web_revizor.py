import streamlit as st
import pypdf
import re
import pandas as pd
import os

# Nastavení stránky
st.set_page_config(page_title="SKLAD ZZN 2026", page_icon="⚡", layout="wide")

# EXTRÉMNÍ DESIGN - Vyčištěno pro ZZN
st.markdown("""
    <style>
    /* Základní tmavé pozadí celé aplikace */
    .main { background-color: #0b0e14; }

    /* CSS pro kontejner loga (vycentrování a odstupy) */
    .logo-container {
        display: flex;
        justify-content: center;
        padding-top: 10px;
        padding-bottom: 20px;
        margin-top: 0px;
    }
    
    /* Vyhození horního bílého kontejneru */
    div.stImage > img {
        margin-top: 0px !important;
        padding-top: 0px !important;
    }

    /* Gradient pro hlavní titulek */
    h1 {
        background: linear-gradient(90deg, #00f2fe 0%, #4facfe 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5rem !important;
        text-align: center;
        margin-top: -10px;
    }
    
    /* Design karet regálů (checkboxů) */
    .stCheckbox {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px !important;
        padding: 15px !important;
        margin-bottom: 8px !important;
        transition: all 0.2s ease;
    }
    
    /* Barva pro zaškrtnutou položku */
    div[data-checked="true"] {
        background: linear-gradient(145deg, #3d0a0a, #161b22) !important;
        border: 1px solid #f85149 !important;
    }
    
    /* Barva a styl textu v regálech */
    .stCheckbox label p { font-size: 16px !important; color: #E0E0E0 !important; }
    </style>
    """, unsafe_allow_html=True)

# LOGO ZZN - Umístěno do tmavé lišty, vycentrované
st.markdown('<div class="logo-container">', unsafe_allow_html=True)
if os.path.exists("logo_zzn.png"):
    st.image("logo_zzn.png", width=450)
else:
    # Záložní text pokud logo není na GitHubu
    st.markdown("<h2 style='text-align: center; color: white;'>ZZN HOSPODÁŘSKÉ POTŘEBY</h2>", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

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
    # OPRAVENO: 'in' místo 'v'
    for n in nove_polozky: 
        kod_novy = vytahni_kod(n)
        if kod_novy and kod_novy not in existujici_kody:
            finalni.append(n)
            existujici_kody.add(kod_novy)
    pd.DataFrame({'polozka': sorted(finalni)}).to_csv(DB_FILE, index=False)
    return sorted(finalni)

if 'db' not in st.session_state: st.session_state.db = nacti_data()
if 'reset_key' not in st.session_state: st.session_state.reset_key = 0

# --- IMPORTY (ZÁLOŽKY) ---
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
    st.info("Na webu ZZN označ zboží (Ctrl+A), zkopíruj (Ctrl+C) a vlož sem.")
    web_paste = st.text_area("Vlož text z webu...", height=150)
    if st.button("Importovat z webu"):
        if web_paste:
            nalezeno = [f"{vytahni_kod(r)} {r.replace(vytahni_kod(r), '').strip()}" for r in web_paste.split('\n') if vytahni_kod(r)]
            if nalezeno:
                st.session_state.db = uloz_data(nalezeno)
                st.rerun()

with t3:
    m_kod = st.text_input("Kód")
    m_nazev = st.text_input("Název")
    if st.button("Uložit do regálu"):
        if m_kod and m_nazev:
            st.session_state.db = uloz_data([f"{m_kod} {m_nazev}"])
            st.rerun()

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
        st.info("Zatím žádný výběr.")
