import streamlit as st
import pypdf
import re

# Nastavení stránky
st.set_page_config(page_title="SKLAD | Kritické zásoby", page_icon="⚠️")

# VLASTNÍ DESIGN - Červené zvýraznění pro to, co dochází
st.markdown("""
    <style>
    .stCheckbox { background-color: white; padding: 10px; border-radius: 5px; border: 1px solid #ddd; }
    .critical-item { color: #d32f2f; font-weight: bold; background-color: #ffebee; padding: 10px; border-radius: 5px; border-left: 5px solid #d32f2f; margin-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚠️ Skladový Revizor - Kritické zásoby")

# Inicializace paměti pro "červený seznam"
if 'critical_list' not in st.session_state:
    st.session_state.critical_list = []

# Nahrání souboru
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
        st.subheader("Položky k revizi (odškrtni, co dochází):")
        
        for i, polozka in enumerate(vsechno_zbozi):
            col1, col2 = st.columns([0.8, 0.2])
            with col1:
                # Checkbox pro označení, že zboží dochází
                is_critical = st.checkbox(f"{polozka}", key=f"crit_{i}")
            
            if is_critical:
                if polozka not in st.session_state.critical_list:
                    st.session_state.critical_list.append(polozka)
            else:
                if polozka in st.session_state.critical_list:
                    st.session_state.critical_list.remove(polozka)

        st.markdown("---")
        
        # --- SEKCE PRO ODESLÁNÍ ---
        if st.session_state.critical_list:
            st.error("🚨 SEZNAM CHYBĚJÍCÍHO ZBOŽÍ:")
            finalni_text = "\n".join(st.session_state.critical_list)
            st.text_area("Seznam k odeslání (zkopíruj si):", value=finalni_text, height=150)
            
            # Tlačítko pro vyčištění
            if st.button("🗑️ Vymazat seznam"):
                st.session_state.critical_list = []
                st.rerun()
        else:
            st.success("Zatím jsi neoznačil nic jako chybějící.")

else:
    st.info("Nahraj PDF nebo si to zkus na demo datech níže.")
    demo = ["50011210 Hrábě 6,000 ks", "36030009 Šňůra 200,000 m", "51060060 Podkladek 20,000 ks"]
    for i, p in enumerate(demo):
        if st.checkbox(p, key=f"demo_{i}"):
            if p not in st.session_state.critical_list:
                st.session_state.critical_list.append(p)
    
    if st.session_state.critical_list:
        st.text_area("Seznam k odeslání (Demo):", value="\n".join(st.session_state.critical_list))
