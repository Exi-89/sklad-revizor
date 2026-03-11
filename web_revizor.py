import streamlit as st
import pypdf
import re
import pandas as pd
import os
from streamlit_extras.stylable_container import stylable_container

# Nastavení stránky
st.set_page_config(page_title="SKLAD PRO | Databáze", page_icon="📦", layout="wide")

# EXTRÉMNÍ DESIGN (CSS)
st.markdown("""
    <style>
    .stCheckbox {
        background-color: #1e2130;
        padding: 20px !important;
        border-radius: 12px !important;
        border: 1px solid #3d4455 !important;
        margin-bottom: 10px !important;
    }
    div[data-checked="true"] {
        background: linear-gradient(145deg, #4b0000, #2a0000) !important;
        border: 1px solid #ff4b4b !important;
    }
    .stCheckbox label p { font-size: 18px !important; color: #E0E0E0 !important; }
    
    /* Styl pro kopírovací tlačítko */
    .copy-btn {
        background-color: #0072FF;
        color: white;
        padding: 10px 20px;
        border: none;
        border-radius: 8px;
        cursor: pointer;
        font-weight: bold;
        margin-top: 10px;
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIKA PAMĚTI (UKLÁDÁNÍ) ---
DB_FILE = "moje_zbozi.csv"

def nacti_databazi():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)['polozka'].tolist()
    return []

def uloz_do_databaze(novy_seznam):
    stary_seznam = nacti_databazi()
    # Spojíme oba seznamy a odstraníme duplicity
    kombinovany = list(set(stary_seznam + novy_seznam))
    pd.DataFrame({'polozka': kombinovany}).to_csv(DB_FILE, index=False)
    return kombinovany

# Inicializace paměti v aplikaci
if 'seznam_skladem' not in st.session_state:
    st.session_state.seznam_skladem = nacti_databazi()

if 'critical_list' not in st.session_state:
    st.session_state.critical_list = []

st.title("🛡️ SKLAD PRO REVIZOR + PAMĚŤ")

# Horní panel pro nahrávání
uploaded_file = st.file_uploader("📤 NAHRAJ DALŠÍ PDF (Zboží se přidá k existujícímu)", type="pdf")

def vytahni_zbozi_z_pdf(file):
    reader = pypdf.PdfReader(file)
    nalezene = []
    for page in reader.pages:
        text = page.extract_text()
        for radek in text.split('\n'):
            if re.search(r'\d+,\d+\s*(ks|m)', radek):
                cisty = radek.strip().split("stav na skladě")[0]
                nalezene.append(cisty)
    return nalezene

if uploaded_file is not None:
    novinky = vytahni_zbozi_z_pdf(uploaded_file)
    if novinky:
        st.session_state.seznam_skladem = uloz_do_databaze(novinky)
        st.success(f"Přidáno {len(novinky)} položek do tvé databáze!")

# Rozdělení plochy
left_col, right_col = st.columns([1, 1])

with left_col:
    st.subheader("📦 MOJE DATABÁZE ZBOŽÍ")
    if st.session_state.seznam_skladem:
        for i, polozka in enumerate(sorted(st.session_state.seznam_skladem)):
            if st.checkbox(polozka, key=f"check_{i}"):
                if polozka not in st.session_state.critical_list:
                    st.session_state.critical_list.append(polozka)
            else:
                if polozka in st.session_state.critical_list:
                    st.session_state.critical_list.remove(polozka)
    else:
        st.info("Databáze je prázdná. Nahraj první PDF převodku.")

with right_col:
    st.subheader("📋 SEZNAM K OBJEDNÁNÍ")
    if st.session_state.critical_list:
        final_text = "\n".join(st.session_state.critical_list)
        
        # Textové pole
        st.text_area("Chybějící zboží:", value=final_text, height=300, id="seznam_text")
        
        # SKRYTÝ JAVASCRIPT PRO KOPÍROVÁNÍ
        copy_code = f"""
        <button class="copy-btn" onclick="copyToClipboard()">📋 KOPÍROVAT SEZNAM</button>
        <script>
        function copyToClipboard() {{
            const text = `{final_text}`;
            navigator.clipboard.writeText(text).then(function() {{
                alert('Zkopírováno do schránky!');
            }});
        }}
        </script>
        """
        st.components.v1.html(copy_code, height=70)

        if st.button("🗑️ VYMAZAT VÝBĚR"):
            st.session_state.critical_list = []
            st.rerun()
            
    if st.button("⚠️ SMAZAT CELOU DATABÁZI (CSV)"):
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)
            st.session_state.seznam_skladem = []
            st.rerun()
