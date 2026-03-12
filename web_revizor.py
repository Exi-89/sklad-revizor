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
    .logo-container { display: flex; justify-content: center; padding: 25px 0px; }
    .logo-img { width: 520px; transition: transform 0.4s ease, filter 0.4s ease; cursor: pointer; }
    .logo-img:hover { transform: scale(1.05); filter: brightness(1.2); }
    button[data-baseweb="tab"] { font-weight: bold !important; font-size: 18px !important; }
    div.stButton > button {
        text-align: left !important;
        background-color: #1c2128 !important;
        border: 1px solid #30363d !important;
        color: #adbac7 !important;
        padding: 10px !important;
        width: 100% !important;
    }
    div.stButton > button:hover { border-color: #58a6ff !important; }
    .stNumberInput input, .stTextInput input {
        background-color: #1c2128 !important;
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

# LOGO
repo_url = "https://raw.githubusercontent.com/Exi-89/sklad-revizor/main/logo_zzn.png"
st.markdown(f'''
    <div class="logo-container">
        <a href="https://www.zznhp.cz" target="_blank">
            <img src="{repo_url}" class="logo-img">
        </a>
    </div>
    ''', unsafe_allow_html=True)

# --- DATABÁZE ---
DB_FILE = "sklad_databaze.csv"

if 'k_input' not in st.session_state: st.session_state.k_input = ""
if 'n_input' not in st.session_state: st.session_state.n_input = ""
if 'vybrane' not in st.session_state: st.session_state.vybrane = {}

if 'db' not in st.session_state:
    if os.path.exists(DB_FILE):
        try: st.session_state.db = pd.read_csv(DB_FILE)['polozka'].tolist()
        except: st.session_state.db = []
    else:
        st.session_state.db = ["35020060 Hadice 1 m"]

def uloz_do_db(seznam_polozek):
    st.session_state.db = sorted(list(set(st.session_state.db + seznam_polozek)))
    pd.DataFrame({'polozka': st.session_state.db}).to_csv(DB_FILE, index=False)

# --- OVLÁDÁNÍ ---
search = st.selectbox("🔍 NAŠEPTÁVAČ:", [""] + st.session_state.db, index=0).lower()

t1, t2 = st.tabs(["📄 PDF Převodka", "📝 Ruční přidání"])

with t1:
    up = st.file_uploader("Nahraj PDF", type="pdf")
    if st.button("Uložit z PDF"):
        if up:
            lines_found = []
            try:
                reader = pypdf.PdfReader(up)
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        for radek in text.split('\n'):
                            # Hledá kód (8-13 číslic) a pak název zboží
                            match = re.search(r'(\d{8,13})\s+(.*)', radek)
                            if match:
                                kodd, nazevv = match.groups()
                                # Očistí název od cen a jednotek na konci řádku
                                nazevv = re.split(r'(\d+[\s,.]+\d+|Kč|ks|bal|m\d)', nazevv)[0].strip()
                                if nazevv:
                                    lines_found.append(f"{kodd} {nazevv}")
                
                if lines_found:
                    uloz_do_db(lines_found)
                    st.success(f"Úspěšně vytěženo {len(lines_found)} položek z PDF!")
                    st.rerun()
                else:
                    st.warning("V PDF nebyl nalezen žádný formát odpovídající Kódu a Názvu.")
            except Exception as e:
                st.error(f"Chyba při čtení PDF: {e}")

with t2:
    c1, c2 = st.columns(2)
    k = c1.text_input("Kód", key="k_input")
    n = c2.text_input("Název", key="n_input")
    
    if st.button("Uložit do regálů"):
        if k and n:
            uloz_do_db([f"{k} {n}"])
            st.session_state.k_input = ""
            st.session_state.n_input = ""
            st.rerun()
        else:
            st.warning("Musíš vyplnit Kód i Název!")

st.divider()

# --- VÝPIS REGÁLŮ A SEZNAMU ---
l, r = st.columns(2)

with l:
    st.subheader("📦 REGÁLY")
    filtr = [p for p in st.session_state.db if search in p.lower()]
    for p in filtr:
        is_sel = p in st.session_state.vybrane
        c_row, c_del = st.columns([0.88, 0.12])
        with c_row:
            ikona = "✅" if is_sel else "⬜"
            if st.button(f"{ikona} {p}", key=f"r_{p}", use_container_width=True):
                if is_sel: del st.session_state.vybrane[p]
                else: st.session_state.vybrane[p] = 1
                st.rerun()
        with c_del:
            if st.button("🗑️", key=f"d_{p}"):
                st.session_state.db.remove(p)
                if p in st.session_state.vybrane: del st.session_state.vybrane[p]
                pd.DataFrame({'polozka': sorted(st.session_state.db)}).to_csv(DB_FILE, index=False)
                st.rerun()

with r:
    st.subheader("📝 SEZNAM K OBJEDNÁNÍ")
    for p in sorted(list(st.session_state.vybrane.keys())):
        c_name, c_qty, c_kill = st.columns([0.65, 0.23, 0.12])
        c_name.write(f"**{p}**")
        st.session_state.vybrane[p] = c_qty.number_input("ks", min_value=1, value=st.session_state.vybrane[p], key=f"qty_{p}", label_visibility="collapsed")
        if c_kill.button("❌", key=f"x_{p}"):
            del st.session_state.vybrane[p]
            st.rerun()

    if st.session_state.vybrane:
        st.divider()
        txt_list = [f"{p} - {qty}ks" for p, qty in st.session_state.vybrane.items()]
        txt_copy = "\\n".join(sorted(txt_list))
        components.html(f"""
            <button id="cp" style="width:100%; background:#1f6feb; color:white; padding:15px; border:none; border-radius:10px; font-weight:bold; cursor:pointer; font-size:16px;">📋 KOPÍROVAT SEZNAM ({len(st.session_state.vybrane)} pol.)</button>
            <script>
                document.getElementById('cp').onclick = () => {{
                    navigator.clipboard.writeText(`{txt_copy}`).then(() => alert('Zkopírováno!'));
                }};
            </script>
        """, height=70)
        if st.button("🗑️ VYMAZAT VŠE", use_container_width=True):
            st.session_state.vybrane = {}
            st.rerun()
