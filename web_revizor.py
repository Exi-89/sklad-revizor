import streamlit as st
import sqlite3

# --- 1. KONFIGURACE ---
st.set_page_config(page_title="Skladová Revize", layout="wide")

# --- 2. STYLING (Fialový motiv) ---
st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: white; }
    [data-testid="stSidebar"] { background-color: #161b22 !important; border-right: 2px solid #7c3aed; }
    .stButton > button { background-color: #7c3aed22; color: #a855f7; border: 1px solid #7c3aed; width: 100%; }
    header { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. FUNKCE PRO PROMAZÁNÍ FORMULÁŘE ---
def reset_form():
    st.session_state.nazev_polozky = ""
    st.session_state.pocet_kusu = 0
    st.session_state.regal = ""

# Inicializace session state, pokud neexistuje
if 'nazev_polozky' not in st.session_state:
    reset_form()

# --- 4. BOČNÍ PANEL ---
with st.sidebar:
    st.title("💜 Sklad")
    st.write("---")
    st.button("📦 Aktuální sklad")
    st.button("📋 Historie revizí")

# --- 5. HLAVNÍ OBSAH ---
st.title("Revize skladu")

# --- SEKCE A: NAHRÁNÍ PDF (Jen jako úložiště) ---
st.subheader("📁 Nahrát dokumentaci (PDF)")
uploaded_file = st.file_uploader("Vyberte PDF soubor", type="pdf", label_visibility="collapsed")
if uploaded_file is not None:
    st.success(f"Soubor '{uploaded_file.name}' byl úspěšně nahrán do systému.")

st.write("---")

# --- SEKCE B: RUČNÍ PŘIDÁNÍ (S automatickým mazáním) ---
st.subheader("➕ Přidat položku do regálu")

col1, col2, col3 = st.columns(3)

with col1:
    nazev = st.text_input("Název položky", key="nazev_polozky")
with col2:
    pocet = st.number_input("Počet kusů", min_value=0, step=1, key="pocet_kusu")
with col3:
    regal = st.text_input("Číslo/Název regálu", key="regal")

if st.button("Uložit do regálu"):
    if nazev and regal:
        # ZDE BY ŠEL ZÁPIS DO DATABÁZE (sqlite3)
        st.toast(f"Položka {nazev} uložena do regálu {regal}!")
        
        # Provedeme reset políček
        reset_form()
        # Vynutíme znovunačtení stránky s prázdnými poli
        st.rerun()
    else:
        st.error("Vyplňte prosím název i regál.")

# --- SEKCE C: NÁHLED SKLADU ---
st.write("---")
st.subheader("🔍 Náhled aktuálního stavu")
# Jen ukázková tabulka
st.table([
    {"Regál": "A1", "Položka": "Motorový olej", "Ks": 5},
    {"Regál": "B3", "Položka": "Brzdové destičky", "Ks": 12}
])
