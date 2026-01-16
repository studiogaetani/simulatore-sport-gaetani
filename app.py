import streamlit as st
import pandas as pd
from datetime import date
from fpdf import FPDF
import base64

# --- 1. CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Studio Gaetani | Sport Advisor", page_icon="🏅", layout="wide")

# --- 2. GESTIONE LOGIN ---
def check_password():
    """Gestisce il login."""
    def password_entered():
        if st.session_state["username"] in st.secrets["passwords"] and \
           st.session_state["password"] == st.secrets["passwords"][st.session_state["username"]]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.markdown("""
        <style>
        .stApp {background: linear-gradient(180deg, #001529 0%, #001e3c 100%);}
        h1, h3 {color: white; text-align: center; font-family: 'Helvetica Neue', sans-serif;}
        .stTextInput > label {color: #D4AF37 !important; font-weight: bold;}
        .stButton > button {background-color: #D4AF37; color: #001529; width: 100%; font-weight: bold; border: none;}
        #MainMenu, header, footer {visibility: hidden;}
        </style>
        """, unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.markdown("<h1 style='font-size: 60px; text-align:center;'>🏅</h1>", unsafe_allow_html=True)
            st.markdown("<h1 style='text-align:center;'>STUDIO GAETANI</h1>", unsafe_allow_html=True)
            st.markdown("<h3 style='color: #D4AF37; text-align:center;'>Sport Tax Advisor</h3>", unsafe_allow_html=True)
            st.text_input("Username", key="username")
            st.text_input("Password", type="password", key="password")
            st.button("ACCEDI ALL'AREA RISERVATA", on_click=password_entered)
        return False
    elif not st.session_state["password_correct"]:
        st.error("⛔ Credenziali non valide.")
        st.text_input("Username", key="username")
        st.text_input("Password", type="password", key="password")
        st.button("Riprova", on_click=password_entered)
        return False
    else:
        return True

if not check_password():
    st.stop()

# ==============================================================================
#                 INIZIO APP REALE
# ==============================================================================

# --- PARAMETRI SPORTIVI ---
PARAMETRI_SPORT = {
    "P.IVA Forfettario": {
        "coeff_redditivita": 0.78, 
        "soglia_inps": 5000.0,          # Franchigia contributiva
        "aliquota_inps": 0.2607,        # Aliquota Gestione Separata
        "abbattimento_inps": 0.50,      # Abbattimento base imp. INPS (fino al 2027)
        "franchigia_fiscale": 15000.0   # Franchigia fiscale
    },
    "Collaboratore (Co.co.co)": {
        "soglia_no_tax": 15000.0,  
        "soglia_no_inps": 5000.0,  
        "aliquota_inps_tot": 0.25, 
        "quota_lavoratore": 1.0/3.0, 
        "abbattimento_inps": 0.50  
    }
}

# --- CSS LUXURY ---
st.markdown("""
    <style>
    .stApp { background: linear-gradient(180deg, #001529 0%, #001e3c 100%); }
    #MainMenu, header, footer, [data-testid="stToolbar"] {visibility: hidden; display: none;}
    h1, h2, h3, h4, h5, h6, p, li, div, label, span { color: #ffffff; font-family: 'Helvetica Neue', sans-serif; }
    .sport-header { color: #D4AF37; text-transform: uppercase; letter-spacing: 2px; font-weight: 800; border-bottom: 2px solid #D4AF37; padding-bottom: 10px; margin-bottom: 20px; }
    a { color: #D4AF37 !important; text-decoration: none; font-weight: bold; }
    .stNumberInput > label, .stTextInput > label, .stSelectbox > label, .stDateInput > label, .stCheckbox > label { color: #D4AF37 !important; font-weight: bold; }
    
    div[data-baseweb="select"] > div, div[data-baseweb="input"] > div { background-color: #002a52 !important; color: white !important; border: 2px solid #D4AF37 !important; }
    div[data-baseweb="select"] span, input { color: white !important; }
    div[data-baseweb="select"] svg { fill: white !important; }
    div[data-baseweb="popover"] div, ul[data-baseweb="menu"] { background-color: #001529 !important; border: 1px solid #D4AF37 !important; }
    li[data-baseweb="option"] { color: white !important; }
    li[data-baseweb="option"]:hover { background-color: #D4AF37 !important; color: #001529 !important; }

    .stButton>button { background-color: #D4AF37; color: #001529 !important; font-weight: bold; border: none; padding: 0.8rem 1rem; width: 100%; text-transform: uppercase; }
    .stButton>button:hover { background-color: #ffffff; }

    .result-card { background-color: #ffffff; padding: 20px; border-radius: 10px; border-left: 8px solid #D4AF37; margin-bottom: 20px; }
    .result-card h1, .result-card h3, .result-card p, .result-card span, .result-card div
