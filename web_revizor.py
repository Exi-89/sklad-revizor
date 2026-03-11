import streamlit as st
import pypdf
import re

# Nastavení stránky pro mobilní telefony
st.set_page_config(
    page_title="Skladový Revizor", 
    page_icon="📦",
    layout="centered"
)

# Styl pro zvětšení textu u checkboxů (aby se lépe klikalo prstem ve skladu)
st.markdown("""
    <style>
    .stCheckbox {
        font-size: 20px;
        padding: 10px 0px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("📦 Skladový Kontrolor")
st.write("Profesionální nástroj pro revizi převodek.")

# Nahrání souboru
uploaded_file = st.file_uploader("Vyber PDF převodku (např. Zepo)", type="pdf")

if uploaded_file is not None:
    try:
        reader = pypdf.PdfReader(uploaded_file)
        radky_zbozi = []

        for page in reader.pages:
            text = page.extract_text()
            if not text:
                continue
                
            for radek in text.split('\n'):
                # FILTR: Hledáme řádky obsahující množství v jednotkách 'ks' nebo 'm'
                # Formát: číslo,číslo následované ks/m
                if re.search(r'\d+,\d+\s*(ks|m)', radek):
                    # Vyčistíme řádek od balastu (jako "stav na skladě")
                    cisty_radek = radek.strip().split("stav na skladě")[0]
                    radky_zbozi.append(cisty_radek)

        if radky_zbozi:
            st.subheader(f"Nalezeno {len(radky_zbozi)} položek k ověření:")
            
            # Vytvoření interaktivního seznamu
            for i, polozka in enumerate(radky_zbozi):
                st.checkbox(f"{polozka}", key=f"item_{i}")
                st.divider() # Čára pro lepší přehlednost na mobilu

            if st.button("KONTROLA DOKONČENA", use_container_width=True):
                st.success("Všechno zboží bylo zkontrolováno!")
                st.balloons()
        else:
            st.warning("V nahraném PDF jsem nenašel žádné zboží. Zkontrolujte formát.")

    except Exception as e:
        st.error(f"Chyba při čtení PDF: {e}")

else:
    # --- DEMO DATA PRO TESTOVÁNÍ BEZ PDF ---
    st.divider()
    st.info("💡 Nyní běží DEMO režim. Nahrajte PDF pro skutečnou kontrolu.")
    
    demo_zbozi = [
        "50011210 Hrábě švédské drát. pevné - 6,000 ks",
        "50210086 Hrábě provzduš. oboustranné - 4,000 ks",
        "49050470 Kolík sázecí kovový Profi - 5,000 ks",
        "36030009 Šňůra PP 4mm barevná - 200,000 m",
        "50100425 Drtič kostí pákový 50cm - 1,000 ks",
        "51060060 Podkladek nelakovaný - 20,000 ks"
    ]
    
    for i, polozka in enumerate(demo_zbozi):
        st.checkbox(f"{polozka}", key=f"demo_{i}")
        st.divider()

    if st.button("TESTOVACÍ ULOŽENÍ", use_container_width=True):
        st.balloons()
