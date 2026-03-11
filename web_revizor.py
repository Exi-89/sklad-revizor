import streamlit as st
import pypdf
import re

# Celkové nastavení a styl aplikace
st.set_page_config(page_title="SKLAD PRO | Revizor", page_icon="📦", layout="wide")

# EXTRÉMNÍ DESIGN (CSS)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Hlavní kontejner */
    .main {
        background-color: #0e1117;
    }

    /* Nadpis */
    h1 {
        color: #FFFFFF;
        font-weight: 700;
        text-align: center;
        background: linear-gradient(90deg, #00C6FF 0%, #0072FF 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        padding-bottom: 20px;
    }

    /* Styl pro karty (Checkboxy) */
    .stCheckbox {
        background-color: #1e2130;
        padding: 24px !important;
        border-radius: 16px !important;
        border: 1px solid #3d4455 !important;
        margin-bottom: 12px !important;
        transition: all 0.3s ease;
    }

    /* Zvýraznění při najetí (hover) */
    .stCheckbox:hover {
        border-color: #0072FF !important;
        transform: translateY(-2px);
    }

    /* Text v kartě */
    .stCheckbox label p {
        font-size: 20px !important;
        color: #E0E0E0 !important;
        letter-spacing: 0.5px;
    }

    /* Barva, když je ZAŠKRTNUTO (Kritický stav) */
    div[data-checked="true"] {
        background: linear-gradient(145deg, #3d0000, #2a0000) !important;
        border: 1px solid #ff4b4b !important;
        box-shadow: 0px 4px 15px rgba(255, 75, 75, 0.3);
    }
    
    div[data-checked="true"] label p {
        color: #ff4b4b !important;
        font-weight: bold !important;
    }

    /* Skrytí standardního ošklivého čtverečku */
    [data-testid="stCheckbox"] [data-testid="stWidgetLabel"] span:first-child {
        display: none;
    }

    /* Styl pro textovou oblast (seznam k odeslání) */
    textarea {
        background-color: #0e1117 !important;
        color: #00FF00 !important;
        font-family: 'Courier New', monospace !important;
        border: 1px solid #3d4455 !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ SKLAD PRO REVIZOR")

if 'critical_list' not in st.session_state:
    st.session_state.critical_list = []

# Horní panel pro nahrávání
with st.container():
    uploaded_file = st.file_uploader("📤 VLOŽTE PDF PŘEVODKU ZEZA", type="pdf")

def filter_zepo_data(text):
    radky = []
    for radek in text.split('\n'):
        if re.search(r'\d+,\d+\s*(ks|m)', radek):
            cisty = radek.strip().split("stav na skladě")[0]
            radky.append(cisty)
    return radky

# Rozdělení na sloupce pro lepší vzhled na tabletu/PC
left_col, right_col = st.columns([1, 1])

if uploaded_file is not None:
    reader = pypdf.PdfReader(uploaded_file)
    vsechno_zbozi = []
    for page in reader.pages:
        vsechno_zbozi.extend(filter_zepo_data(page.extract_text()))

    if vsechno_zbozi:
        with left_col:
            st.subheader("📦 POLOŽKY V PŘEVODCE")
            st.caption("Kliknutím označíš položku jako DOCHÁZEJÍCÍ")
            for i, polozka in enumerate(vsechno_zbozi):
                if st.checkbox(polozka, key=f"crit_{i}"):
                    if polozka not in st.session_state.critical_list:
                        st.session_state.critical_list.append(polozka)
                else:
                    if polozka in st.session_state.critical_list:
                        try: st.session_state.critical_list.remove(polozka)
                        except: pass

        with right_col:
            st.subheader("📋 SEZNAM K OBJEDNÁNÍ")
            if st.session_state.critical_list:
                finalni_text = "\n".join(st.session_state.critical_list)
                st.text_area("Hlášenka:", value=finalni_text, height=400)
                if st.button("🚀 ODESLAT / VYMAZAT", use_container_width=True):
                    st.session_state.critical_list = []
                    st.success("Seznam vyčištěn!")
                    st.rerun()
            else:
                st.info("Zatím jsi nic neoznačil. Procházej sklad a klikej na položky vlevo.")

else:
    # DEMO
    st.markdown("---")
    st.subheader("💡 DEMO UKÁZKA (VYZKOUŠEJ SI TO)")
    demo = ["50011210 Hrábě | 6,000 ks", "36030009 Šňůra | 200,000 m", "51060060 Podkladek | 20,000 ks"]
    d_left, d_right = st.columns(2)
    with d_left:
        for i, p in enumerate(demo):
            if st.checkbox(p, key=f"demo_{i}"):
                if p not in st.session_state.critical_list:
                    st.session_state.critical_list.append(p)
    with d_right:
        if st.session_state.critical_list:
            st.text_area("Demo hlášenka:", value="\n".join(st.session_state.critical_list), height=150)
