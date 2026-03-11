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

st.title("⚡ SKLAD REVIZOR PRO")

DB_FILE = "sklad_databaze.csv"

def ocisti_pro_objednavku(text):
    text = re.sub(r',?\s*\d+,\d+\s*(ks|m).*', '', text)
    text = text.replace('|', '').strip()
    return text

def nacti_data():
    if os.path.exists(DB_FILE): 
        return pd.read_csv(DB_FILE)['polozka'].tolist()
    return [
        "50011210 Hrábě švédské drát.pevné 6,000 ks",
        "50210086 Hrábě provzduš. oboustranné 4,000 ks",
        "49050470 Kolík sázecí kovový Profi 5,000 ks",
        "36030009 Šňůra PP 4mm barevná 200,000 m",
        "50100425 Drtič kostí pákový 50cm 1,000 ks"
    ]

# Inicializace stavů
if 'db' not in st.session_state:
    st.session_state.db = nacti_data()

# Klíčová oprava: Resetovací klíč pro checkboxy
if 'reset_key' not in st.session_state:
    st.session_state.reset_key = 0

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
            aktualni = nacti_data()
            sjednoceno = sorted(list(set(aktualni + texty)))
            pd.DataFrame({'polozka': sjednoceno}).to_csv(DB_FILE, index=False)
            st.session_state.db = sjednoceno
            st.success("Nahráno!")
            st.rerun()

# --- HLAVNÍ PLOCHA ---
l, r = st.columns([1, 1])
vybrane_polozky = []

with l:
    st.subheader("📦 REGÁLY")
    # Každý checkbox má unikátní klíč, který se při resetu změní
    for i, pol in enumerate(st.session_state.db):
        cista = ocisti_pro_objednavku(pol)
        if st.checkbox(pol, key=f"cb_{st.session_state.reset_key}_{i}"):
            vybrane_polozky.append(cista)

with r:
    st.subheader("📝 SEZNAM K OBJEDNÁNÍ")
    if vybrane_polozky:
        vysledek_text = "\n".join(vybrane_polozky)
        st.text_area("K objednání:", value=vysledek_text, height=300)
        
        # Kopírovací tlačítko
        vysledek_js = "\\n".join(vybrane_polozky)
        html_button = f"""
            <button id="copyBtn" style="width:100%; background:linear-gradient(90deg, #0072FF, #00C6FF); color:white; padding:20px; border:none; border-radius:15px; font-size:20px; font-weight:bold; cursor:pointer;">📋 KOPÍROVAT SEZNAM</button>
            <script>
            document.getElementById('copyBtn').addEventListener('click', function() {{
                navigator.clipboard.writeText(`{vysledek_js}`).then(() => alert('Zkopírováno!'));
            }});
            </script>
        """
        st.components.v1.html(html_button, height=100)

        # TOHLE TLAČÍTKO TEĎ BUDE FUNGOVAT
        if st.button("🗑️ VYMAZAT VÝBĚR"):
            st.session_state.reset_key += 1  # Změnou klíče vynutíme odškrtnutí všech checkboxů
            st.rerun()
    else:
        st.info("Seznam je prázdný.")

if st.sidebar.button("⚠️ Resetovat celou databázi"):
    if os.path.exists(DB_FILE): os.remove(DB_FILE)
    st.session_state.db = nacti_data()
    st.session_state.reset_key += 1
    st.rerun()
