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
    .logo-img { width: 520px; transition: transform 0.4s ease; cursor: pointer; }
    .logo-img:hover { transform: scale(1.1); filter: brightness(1.2); }
    
    button[data-baseweb="tab"] { font-weight: bold !important; font-size: 18px !important; }
    #tabs-b3-tab-0 { color: #ff4b4b !important; }
    #tabs-b3-tab-1 { color: #0072FF !important; }
    #tabs-b3-tab-2 { color: #adbac7 !important; }

    div.stButton > button.row-btn {
        text-align: left !important;
        justify-content: flex-start !important;
        background-color: #1c2128 !important;
        border: 1px solid #30363d !important;
        color: #adbac7 !important;
        padding: 10px !important;
        display: block !important;
        width: 100% !important;
    }
    </style>
    """, unsafe_allow_html=True)

# LOGO
repo_url = "https://raw.githubusercontent.com/Exi-89/sklad-revizor/main/logo_zzn.png"
st.markdown(f'<div class="logo-container"><a href="https://www.zznhp.cz" target="_blank"><img src="{repo_url}" class="logo-img"></a></div>', unsafe_allow_html=True)

# --- DATABÁZE ---
DB_FILE = "sklad_databaze.csv"

if 'vybrane' not in st.session_state: st.session_state.vybrane = set()
if 'db' not in st.session_state:
    if os.path.exists(DB_FILE):
        try: st.session_state.db = pd.read_csv(DB_FILE)['polozka'].tolist()
        except: st.session_state.db = []
    else: st.session_state.db = ["50011210 Hrábě švédské", "35020060 Hadice 1 m"]

def vycisti_a_uloz(text_list):
    nove_vycistene = []
    for radek in text_list:
        radek = radek.strip()
        # Hledá 8místný kód na začátku nebo po mezeře
        kod_match = re.search(r'(\d{8})', radek)
        if kod_match:
            kod = kod_match.group(1)
            # Vezme vše za kódem
            cast_za_kodem = radek.split(kod)[-1].strip()
            
            # AGRESIVNÍ ŘEZ: Zastaví se u ceny, měny nebo velkého množství mezer
            # Najde první výskyt ceny (např. 120,00 nebo 120.00) nebo značky Kč
            stop_body = [m.start() for m in re.finditer(r'(\d+[\s,.]+\d+|Kč|ks|bal|m\d| skladem| ks)', cast_za_kodem)]
            
            if stop_body:
                nazev = cast_za_kodem[:min(stop_body)].strip()
            else:
                nazev = cast_za_kodem.strip()
            
            # Odstraní přebytečné znaky na konci (čárky, pomlčky)
            nazev = re.sub(r'[:;,\-\s]+$', '', nazev)
            
            if len(nazev) > 1:
                nove_vycistene.append(f"{kod} {nazev}")
    
    if nove_vycistene:
        st.session_state.db = sorted(list(set(st.session_state.db + nove_vycistene)))
        pd.DataFrame({'polozka': st.session_state.db}).to_csv(DB_FILE, index=False)
        return True
    return False

# --- SKENER DIALOG ---
@st.dialog("📸 SKENOVÁNÍ")
def skenovat():
    components.html("""
        <script src="https://unpkg.com/html5-qrcode"></script>
        <div id="reader" style="width:100%; border-radius:10px; overflow:hidden;"></div>
        <script>
            const html5QrCode = new Html5Qrcode("reader");
            html5QrCode.start({ facingMode: "environment" }, { fps: 20, qrbox: 250 }, (txt) => {
                window.parent.postMessage({type: 'barcode_scanned', value: txt}, '*');
                html5QrCode.stop();
            });
        </script>
    """, height=350)

# --- PANEL OVLÁDÁNÍ ---
col_a, col_b = st.columns([0.3, 0.7])
with col_a:
    if st.button("📸 SPUSTIT SKENER", use_container_width=True): skenovat()
with col_b:
    search = st.selectbox("🔍 RYCHLÝ NAŠEPTÁVAČ:", [""] + st.session_state.db, index=0).lower()

# --- IMPORTY ---
t1, t2, t3 = st.tabs(["📄 PDF Převodka", "🌐 Import", "📝 Ruční"])
with t1:
    up = st.file_uploader("Nahraj PDF", type="pdf")
    if st.button("Uložit z PDF"):
        if up:
            lines = [r.strip() for p in pypdf.PdfReader(up).pages for r in p.extract_text().split('\n')]
            if vycisti_a_uloz(lines): st.rerun()
with t2:
    web = st.text_area("Vlož text z webu...", placeholder="Zkopíruj sem obsah košíku nebo ceníku...")
    if st.button("Importovat jen Kód + Název"):
        if web:
            if vycisti_a_uloz(web.split('\n')): st.success("Hotovo! Vyčištěno."); st.rerun()
            else: st.warning("Nepodařilo se najít žádné zboží s 8místným kódem.")
with t3:
    c1, c2 = st.columns(2)
    k, n = c1.text_input("Kód"), c2.text_input("Název")
    if st.button("Přidat ručně"):
        if k and n: 
            st.session_state.db.append(f"{k} {n}")
            uloz_db = sorted(list(set(st.session_state.db)))
            pd.DataFrame({'polozka': uloz_db}).to_csv(DB_FILE, index=False)
            st.rerun()

st.divider()

# --- VÝPIS ---
l, r = st.columns(2)

with l:
    st.subheader("📦 REGÁLY")
    filtr = [p for p in st.session_state.db if search in p.lower()]
    for p in filtr:
        is_sel = p in st.session_state.vybrane
        row_col, del_col = st.columns([0.88, 0.12])
        with row_col:
            icon = "✅" if is_sel else "⬜"
            if st.button(f"{icon} {p}", key=f"r_{p}", use_container_width=True):
                if is_sel: st.session_state.vybrane.remove(p)
                else: st.session_state.vybrane.add(p)
                st.rerun()
        with del_col:
            if st.button("🗑️", key=f"db_d_{p}"):
                st.session_state.db.remove(p)
                st.session_state.vybrane.discard(p)
                pd.DataFrame({'polozka': sorted(st.session_state.db)}).to_csv(DB_FILE, index=False)
                st.rerun()

with r:
    st.subheader("📝 SEZNAM K OBJEDNÁNÍ")
    for p in sorted(list(st.session_state.vybrane)):
        col_t, col_b = st.columns([0.88, 0.12])
        col_t.write(f"**• {p}**")
        if col_b.button("❌", key=f"k_{p}"):
            st.session_state.vybrane.remove(p)
            st.rerun()

    if st.session_state.vybrane:
        st.divider()
        copy_text = "\\n".join(sorted(list(st.session_state.vybrane)))
        components.html(f"""
            <button id="cBtn" style="width:100%; background:#1f6feb; color:white; padding:15px; border:none; border-radius:10px; font-weight:bold; cursor:pointer; font-size:16px;">📋 KOPÍROVAT SEZNAM</button>
            <script>
            document.getElementById('cBtn').onclick = () => {{
                navigator.clipboard.writeText(`{copy_text}`).then(() => alert('Zkopírováno jen kód a název!'));
            }};
            </script>
        """, height=70)
        
        if st.button("🗑️ VYMAZAT VŠE", use_container_width=True):
            st.session_state.vybrane.clear()
            st.rerun()
