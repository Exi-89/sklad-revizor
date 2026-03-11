import streamlit as st
import pypdf
import re
import pandas as pd
import os

# Nastavení stránky
st.set_page_config(page_title="SKLAD PRO 2026", page_icon="⚡", layout="wide")

# DESIGN
st.markdown("""
    <style>
    .main { background-color: #0b0e14; }
    h1 {
        background: linear-gradient(90deg, #00f2fe 0%, #4facfe 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5rem !important;
        text-align: center;
        margin-bottom: 0px;
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
    .stCheckbox label p { font-size: 16px !important; color: #E0E0E0 !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚡ SKLAD REVIZOR PRO")

DB_FILE = "sklad_databaze.csv"

def ocisti_pro_objednavku(text):
    text = re.sub(r',?\s*\d+,\d+\s*(ks|m).*', '', text)
    return text.replace('|', '').strip()

def vytahni_kod(text):
    match = re.search(r'(\d{8})', text)
    return match.group(1) if match else text

def nacti_data():
    if os.path.exists(DB_FILE): 
        try:
            return pd.read_csv(DB_FILE)['polozka'].tolist()
        except:
            return []
    return ["50011210 Hrábě švédské drát.pevné", "36030009 Šňůra PP 4mm barevná"]

def uloz_data(nove_polozky):
    aktualni = nacti_data()
    existujici_kody = {vytahni_kod(p) for p in aktualni}
    finalni = list(aktualni)
    
    for n in nove_polozky: # TADY BYLA TA CHYBA - opraveno na 'in'
        kod_novy = vytahni_kod(n)
        if kod_novy not in existujici_kody:
            finalni.append(n)
            existujici_kody.add(kod_novy)
            
    pd.DataFrame({'polozka': sorted(finalni)}).to_csv(DB_FILE, index=False)
    return sorted(finalni)

# Inicializace
if 'db' not in st.session_state: st.session_state.db = nacti_data()
if 'reset_key' not in st.session_state: st.session_state.reset_key = 0

# --- PANEL NAHRÁVÁNÍ A PŘIDÁVÁNÍ ---
col_pdf, col_manual = st.columns(2)

with col_pdf:
    with st.expander("➕ NAHRÁT PDF"):
        up = st.file_uploader("Vyber převodku", type="pdf")
        if up:
            reader = pypdf.PdfReader(up)
            z_pdf = []
            for p in reader.pages:
                for r in p.extract_text().split('\n'):
                    if re.search(r'\d+,\d+\s*(ks|m)', r):
                        z_pdf.append(r.strip().split("stav na skladě")[0])
            if z_pdf:
                st.session_state.db = uloz_data(z_pdf)
                st.success("PDF zpracováno!")
                st.rerun()

with col_manual:
    with st.expander("📝 PŘIDAT RUČNĚ"):
        m_kod = st.text_input("Kód (8 čísel)", key="manual_kod")
        m_nazev = st.text_input("Název zboží", key="manual_nazev")
        if st.button("Uložit do regálu"):
            if m_kod and m_nazev:
                nova = f"{m_kod} {m_nazev}"
                st.session_state.db = uloz_data([nova])
                st.success("Uloženo!")
                st.rerun()

# --- VYHLEDÁVÁNÍ ---
search_query = st.text_input("🔍 Vyhledat kód nebo název zboží...", "").lower()

# --- HLAVNÍ PLOCHA ---
l, r = st.columns([1, 1])
vybrane = []

with l:
    st.subheader("📦 REGÁLY")
    filtered_db = [p for p in st.session_state.db if search_query in p.lower()]
    
    for i, pol in enumerate(filtered_db):
        cista = ocisti_pro_objednavku(pol)
        if st.checkbox(pol, key=f"cb_{st.session_state.reset_key}_{i}"):
            vybrane.append(cista)

with r:
    st.subheader("📝 K OBJEDNÁNÍ")
    if vybrane:
        vysledek_text = "\n".join(vybrane)
        st.text_area("Seznam:", value=vysledek_text, height=300)
        
        vysledek_js = "\\n".join(vybrane)
        st.components.v1.html(f"""
            <button id="copyBtn" style="width:100%; background:linear-gradient(90deg, #0072FF, #00C6FF); color:white; padding:20px; border:none; border-radius:15px; font-size:18px; font-weight:bold; cursor:pointer;">📋 KOPÍROVAT SEZNAM</button>
            <script>
            document.getElementById('copyBtn').addEventListener('click', function() {{
                navigator.clipboard.writeText(`{vysledek_js}`).then(() => alert('Zkopírováno!'));
            }});
            </script>
        """, height=100)

        if st.button("🗑️ VYMAZAT VÝBĚR"):
            st.session_state.reset_key += 1
            st.rerun()
    else:
        st.info("Nic nevybráno.")

if st.sidebar.button("⚠️ Resetovat vše"):
    if os.path.exists(DB_FILE): os.remove(DB_FILE)
    st.session_state.db = nacti_data()
    st.session_state.reset_key += 1
    st.rerun()
