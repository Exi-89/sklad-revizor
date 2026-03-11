import streamlit as st
import pypdf

st.set_page_config(page_title="Skladový Revizor", layout="centered")

st.title("📦 Skladový Kontrolor")
st.info("Nahraj PDF převodku a odškrtej přijaté zboží.")

uploaded_file = st.file_uploader("Vyber PDF soubor", type="pdf")

if uploaded_file is not None:
    reader = pypdf.PdfReader(uploaded_file)
    cely_text = ""
    for page in reader.pages:
        cely_text += page.extract_text() + "\n"
    
    # Rozdělíme na řádky a vyhodíme prázdné
    radky = [r.strip() for r in cely_text.split('\n') if len(r.strip()) > 3]

    st.subheader("Položky k ověření:")
    
    # Vytvoření seznamu s checkboxy
    for i, polozka in enumerate(radky):
        st.checkbox(f"{polozka}", key=f"item_{i}")

    if st.button("ULOŽIT PROTOKOL"):
        st.success("Kontrola byla uložena do systému!")
        st.balloons()