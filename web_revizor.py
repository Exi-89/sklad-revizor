import streamlit as st
import pypdf
import re

st.set_page_config(page_title="SKLAD | Kritické zásoby", layout="centered")

# NOVÝ DESIGN - Pořádná tlačítka pro chlapy do skladu
st.markdown("""
    <style>
    /* Kontejner pro checkbox - uděláme z něj velkou kartu */
    .stCheckbox {
        background-color: #eeeeee;
        padding: 20px !important;
        border-radius: 12px !important;
        border: 2px solid #cccccc !important;
        margin-bottom: 15px !important;
        width: 100%;
    }
    /* Text uvnitř checkboxu - velký a černý */
    .stCheckbox label p {
        font-size: 22px !important;
        font-weight: bold !important;
        color: #000000 !important;
    }
    /* Barva, když je zaškrtnuto (dochází) - Změní se na červenou */
    div[data-checked="true"] {
        background-color: #ff4b4b !important;
        border-color: #990000 !important;
    }
    div[data-checked="true"] label p {
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("⚠️ Skladový Revizor")

if 'critical_list' not in st.session_state:
    st.session_state.critical_list = []

uploaded_file = st.file_uploader("📂 Nahrajte PDF převodku", type="pdf")

def filter_zepo_data(text):
    radky = []
    for radek in text.split('\n'):
        if re.search(r'\d+,\d+\s*(ks|m)', radek):
            cisty = radek.strip().split("stav na skladě")[0]
            radky.append(cisty)
    return radky

if uploaded_file is not None:
    reader = pypdf.PdfReader(uploaded_file)
    vsechno_zbozi = []
    for page in reader.pages:
        vsechno_zbozi.extend(filter_zepo_data(page.extract_text()))

    if vsechno_zbozi:
        st.subheader("Klikni na to, co DOCHÁZÍ:")
        for i, polozka in enumerate(vsechno_zbozi):
            # Checkboxy teď vypadají jako velké karty
            if st.checkbox(polozka, key=f"crit_{i}"):
                if polozka not in st.session_state.critical_list:
                    st.session_state.critical_list.append(polozka)
            else:
                if polozka in st.session_state.critical_list:
                    try: st.session_state.critical_list.remove(polozka)
                    except: pass
    
    st.markdown("---")
    if st.session_state.critical_list:
        st.error("🚨 SEZNAM K OBJEDNÁNÍ:")
        st.text_area("Zkopíruj a pošli:", value="\n".join(st.session_state.critical_list), height=200)
        if st.button("🗑️ Vymazat vše"):
            st.session_state.critical_list = []
            st.rerun()

else:
    # DEMO UKÁZKA
    st.info("💡 Takhle to bude vypadat (zkus si kliknout):")
    demo = ["50011210 Hrábě 6,000 ks", "36030009 Šňůra 200,000 m", "51060060 Podkladek 20,000 ks"]
    for i, p in enumerate(demo):
        if st.checkbox(p, key=f"demo_{i}"):
            if p not in st.session_state.critical_list:
                st.session_state.critical_list.append(p)
