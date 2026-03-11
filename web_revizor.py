import streamlit as st
import pypdf
import re
import pandas as pd
import os

# Nastavení stránky
st.set_page_config(page_title="SKLAD PRO 2026", page_icon="⚡", layout="wide")

# EXTRÉMNÍ DESIGN (CSS)
st.markdown("""
    <style>
    .main { background-color: #0b0e14; }
    h1 {
        background: linear-gradient(90deg, #00f2fe 0%, #4facfe 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5rem !important;
        text-align: center;
    }
    .stCheckbox {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 15px !important;
        padding: 20px !important;
        margin-bottom: 10px !important;
    }
    div[data-checked="true"] {
        background: linear-gradient(145deg, #3d0a0a, #161b22) !important;
        border: 1px solid #f85149 !important;
    }
    .stCheckbox label p { font-size: 18px !important; color: #E0E0E0 !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚡ SKLAD")

# --- DATABÁZE ---
DB_FILE = "sklad_databaze.csv"

def nacti_data():
    if os.path.exists(DB_FILE): return pd.read_csv(DB_FILE)['polozka'].tolist()
    return []

def uloz_data(nove):
    aktualni = nacti_data()
    sjednoceno = sorted(list(set(aktualni + nove)))
    pd.DataFrame({'polozka': sjednoceno}).to_csv(DB_FILE, index=False)
    return sjednoceno

if 'db' not in st.session_state: st.session_state.db = nacti_data()
if 'kosik' not in st.session_state: st.session_state.kosik = []

# --- NAHRÁVÁNÍ ---
with st.expander("➕ PŘIDAT NOVÉ PDF"):
    up = st.file_uploader("Nahraj převodku", type="pdf")
    if up:
        reader = pypdf.PdfReader(up)
        texty = []
        for p in reader.pages:
            for r in p.extract_text().split('\n'):
                if re.search(r'\d+,\d+\s*(ks|m)', r):
                    texty.append(r.strip().split("stav na skladě")[0])
        if texty:
            st.session_state.db = uloz_data(texty)
            st.success(f"Nahráno {len(texty)} položek!")

# --- HLAVNÍ PLOCHA ---
l, r = st.columns([1, 1])

with l:
    st.subheader("📦 ZBOŽÍ")
    for i, pol in enumerate(st.session_state.db):
        if st.checkbox(pol, key=f"c_{i}"):
            if pol not in st.session_state.kosik: st.session_state.kosik.append(pol)
        else:
            if pol in st.session_state.kosik: st.session_state.kosik.remove(pol)

with r:
    st.subheader("📝 SEZNAM K OBJEDNÁNÍ")
    if st.session_state.kosik:
        vysledek = "\\n".join(st.session_state.kosik)
        
        # Zobrazení seznamu
        st.text_area("Položky:", value="\n".join(st.session_state.kosik), height=250)
        
        # --- TLAČÍTKO PRO KOPÍROVÁNÍ (Magie s JS) ---
        html_button = f"""
            <button id="copyBtn" style="
                width: 100%;
                background-color: #0072FF;
                color: white;
                padding: 15px;
                border: none;
                border-radius: 10px;
                font-size: 18px;
                font-weight: bold;
                cursor: pointer;
            ">📋 KOPÍROVAT VŠE</button>

            <script>
            document.getElementById('copyBtn').addEventListener('click', function() {{
                const textToCopy = `{vysledek}`;
                navigator.clipboard.writeText(textToCopy).then(() => {{
                    alert('Zkopírováno do schránky!');
                }}).catch(err => {{
                    console.error('Chyba při kopírování: ', err);
                }});
            }});
            </script>
        """
        st.components.v1.html(html_button, height=80)

        if st.button("🗑️ VYMAZAT VÝBĚR"):
            st.session_state.kosik = []
            st.rerun()
    else:
        st.info("Označ vlevo, co chybí.")
