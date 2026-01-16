import streamlit as st
import pandas as pd
from datetime import date
import time

# --- 1. CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Studio Gaetani | Sport Advisor", page_icon="🏅", layout="wide")

# --- 2. GESTIONE LOGIN (AREA RISERVATA) ---
def check_password():
    """Ritorna True se l'utente è loggato correttamente."""

    def password_entered():
        """Controlla se utente e password corrispondono."""
        if st.session_state["username"] in st.secrets["passwords"] and \
           st.session_state["password"] == st.secrets["passwords"][st.session_state["username"]]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # GRAFICA LOGIN
        st.markdown("""
        <style>
        .stApp {background: linear-gradient(180deg, #001529 0%, #001e3c 100%);}
        h1, h3 {color: white; text-align: center; font-family: 'Helvetica Neue', sans-serif;}
        .stTextInput > label {color: #D4AF37 !important; font-weight: bold;}
        .stButton > button {background-color: #D4AF37; color: #001529; width: 100%; font-weight: bold; border: none;}
        .stButton > button:hover {background-color: white;}
        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
        footer {visibility: hidden;}
        </style>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.markdown("<h1 style='font-size: 60px;'>🏅</h1>", unsafe_allow_html=True)
            st.markdown("<h1>STUDIO GAETANI</h1>", unsafe_allow_html=True)
            st.markdown("<h3 style='color: #D4AF37;'>Sport Tax Advisor</h3>", unsafe_allow_html=True)
            st.markdown("---")
            st.text_input("Username", key="username")
            st.text_input("Password", type="password", key="password")
            st.button("ACCEDI ALL'AREA RISERVATA", on_click=password_entered)
            st.markdown("<br><center style='color: #888;'>Software protetto da credenziali.</center>", unsafe_allow_html=True)
        return False
    
    elif not st.session_state["password_correct"]:
        st.markdown("""<style>.stApp {background: #001529;}</style>""", unsafe_allow_html=True)
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

# --- DATABASE PARAMETRI SPORTIVI ---
PARAMETRI_SPORT = {
    "P.IVA Forfettario": {
        "coeff_redditivita": 0.78, 
        "soglia_inps": 5000.0,     
        "aliquota_inps": 0.2607,   
        "abbattimento_inps": 0.50, 
    },
    "Collaboratore (Co.co.co Sportivo)": {
        "soglia_no_tax": 15000.0,  
        "soglia_no_inps": 5000.0,  
        "aliquota_inps_tot": 0.25, 
        "quota_lavoratore": 1.0/3.0, 
        "abbattimento_inps": 0.50  
    }
}

# --- CSS LUXURY & WHITE LABEL ---
st.markdown("""
    <style>
    /* SFONDO GENERALE */
    .stApp {
        background: linear-gradient(180deg, #001529 0%, #001e3c 100%);
    }

    /* NASCONDI MENU STREAMLIT */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stToolbar"] {visibility: hidden; display: none;}

    /* TYPOGRAPHY */
    h1, h2, h3, h4, h5, h6, p, li, div, label, span {
        color: #ffffff;
        font-family: 'Helvetica Neue', sans-serif;
    }
    
    .sport-header {
        color: #D4AF37;
        text-transform: uppercase;
        letter-spacing: 2px;
        font-weight: 800;
        border-bottom: 2px solid #D4AF37;
        padding-bottom: 10px;
        margin-bottom: 20px;
    }

    /* LINK ORO */
    a { color: #D4AF37 !important; text-decoration: none; font-weight: bold; }
    a:hover { color: #ffffff !important; text-decoration: underline; }

    /* INPUT FIELDS */
    .stNumberInput > label, .stTextInput > label, .stSelectbox > label, .stDateInput > label {
        color: #D4AF37 !important;
        font-weight: bold;
    }
    
    /* Forza Selectbox Scure */
    div[data-baseweb="select"] > div {
        background-color: #002a52 !important;
        color: white !important;
        border: 2px solid #D4AF37 !important;
    }
    div[data-baseweb="select"] span { color: white !important; }
    div[data-baseweb="select"] svg { fill: white !important; stroke: white !important; }
    
    div[data-baseweb="popover"] div, ul[data-baseweb="menu"] {
        background-color: #001529 !important;
        border: 1px solid #D4AF37 !important;
    }
    li[data-baseweb="option"] { color: white !important; }
    li[data-baseweb="option"]:hover { background-color: #D4AF37 !important; color: #001529 !important; }

    div[data-baseweb="input"] > div {
        background-color: #002a52 !important;
        color: white !important;
        border: 1px solid #D4AF37 !important;
    }
    input { color: white !important; }

    /* PULSANTI */
    .stButton>button {
        background-color: #D4AF37;
        color: #001529 !important;
        font-weight: bold;
        border: none;
        border-radius: 5px;
        padding: 0.8rem 1rem;
        width: 100%;
        text-transform: uppercase;
    }
    .stButton>button:hover {
        background-color: #ffffff;
        box-shadow: 0 0 15px rgba(212, 175, 55, 0.8);
    }

    /* CARD RISULTATI */
    .result-card {
        background-color: rgba(255, 255, 255, 0.95);
        padding: 20px;
        border-radius: 10px;
        border-left: 8px solid #D4AF37;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        margin-bottom: 20px;
    }
    .result-card h1, .result-card h3, .result-card p, .result-card span, .result-card div {
        color: #001529 !important;
    }

    /* FATTURA DI CORTESIA */
    .invoice-box {
        background-color: white;
        padding: 40px;
        border: 1px solid #ddd;
        box-shadow: 0 0 10px rgba(0, 0, 0, 0.15);
        font-family: 'Helvetica', sans-serif;
        color: #333 !important;
    }
    .invoice-box h1, .invoice-box h2, .invoice-box p, .invoice-box td {
        color: #333 !important;
    }
    
    /* TABELLE E SIDEBAR */
    .dataframe { background-color: white; color: #333 !important; border-radius: 5px; }
    .dataframe th { background-color: #D4AF37 !important; color: #001529 !important; }
    .dataframe td { color: #333 !important; }
    [data-testid="stSidebar"] { background-color: #000f1f; border-right: 1px solid #D4AF37; }
    </style>
""", unsafe_allow_html=True)

# --- HEADER ---
col_head1, col_head2 = st.columns([1, 4])
with col_head1:
    st.image("https://images.unsplash.com/photo-1517836357463-d25dfeac3438?ixlib=rb-4.0.3&auto=format&fit=crop&w=150&q=80", width=120) 
with col_head2:
    st.title("STUDIO GAETANI")
    st.markdown("<h3 style='color: #D4AF37;'>Sport Tax Advisor & Management</h3>", unsafe_allow_html=True)
    try:
        user_name = st.secrets["passwords"].get('user_display_name', 'Cliente')
        st.caption(f"Utente connesso: {user_name}")
    except:
        st.caption("Utente connesso")

st.markdown("---")

# --- SIDEBAR ---
# QUESTA È LA RIGA CHE DAVA ERRORE - ORA È CORRETTA
st.sidebar.header("⚙️ Profilo Sportivo")

regime_scelta = st.sidebar.radio("Regime P.IVA:", ["Start-up (5%)", "Ordinario (15%)"], index=0)
aliquota_tassa = 0.05 if "Start-up" in regime_scelta else 0.15

st.sidebar.markdown("---")
st.sidebar.subheader("🔗 Link Utili Sport")
st.sidebar.markdown("""
<div style="font-size: 0.9em;">
    <a href="https://registro.sportesalute.eu/" target="_blank">▪️ Registro Naz. Attività Sportive</a><br>
    <a href="https://www.sport.governo.it/it/riforma-dello-sport/" target="_blank">▪️ Dipartimento per lo Sport</a><br>
    <a href="https://www.coni.it/it/" target="_blank">▪️ CONI</a>
</div>
""", unsafe_allow_html=True)

if st.sidebar.button("Esci / Logout"):
    del st.session_state["password_correct"]
    st.rerun()

# --- FUNZIONI DI CALCOLO ---
def calcola_piva_sport(lordo, aliquota_imp):
    params = PARAMETRI_SPORT["P.IVA Forfettario"]
    reddito_forfettario = lordo * params["coeff_redditivita"]
    
    imponibile_inps = reddito_forfettario - params["soglia_inps"]
    if imponibile_inps < 0: imponibile_inps = 0
    imponibile_inps_ridotto = imponibile_inps * params["abbattimento_inps"]
    contributi_inps = imponibile_inps_ridotto * params["aliquota_inps"]
    
    imponibile_fiscale = reddito_forfettario - contributi_inps
    if imponibile_fiscale < 0: imponibile_fiscale = 0
    
    imposta = imponibile_fiscale * aliquota_imp
    netto = lordo - contributi_inps - imposta
    
    return {"lordo": lordo, "reddito": reddito_forfettario, "inps": contributi_inps, "tasse": imposta, "netto": netto}

def calcola_cococo_sport(lordo):
    params = PARAMETRI_SPORT["Collaboratore (Co.co.co Sportivo)"]
    
    eccedenza_inps = lordo - params["soglia_no_inps"]
    if eccedenza_inps < 0: eccedenza_inps = 0
    base_inps = eccedenza_inps * params["abbattimento_inps"]
    inps_totale = base_inps * params["aliquota_inps_tot"]
    inps_lavoratore = inps_totale * params["quota_lavoratore"]
    
    imponibile_fiscale = (lordo - inps_lavoratore) - params["soglia_no_tax"]
    if imponibile_fiscale < 0: imponibile_fiscale = 0
    
    irpef = imponibile_fiscale * 0.23 
    netto = lordo - inps_lavoratore - irpef
    
    return {"lordo": lordo, "inps_lav": inps_lavoratore, "irpef": irpef, "netto": netto}

# --- TABS ---
tab1, tab2, tab3, tab4 = st.tabs(["📊 Analisi P.IVA Sport", "🤝 Assunzione Co.co.co", "⚖️ Confronto", "📝 Genera Fattura"])

with tab1:
    st.markdown("<div class='sport-header'>Simulazione Partita IVA Sportiva</div>", unsafe_allow_html=True)
    st.info("ℹ️ Regole applicate: Coeff. 78% | Franchigia INPS 5.000€ | Abbattimento base INPS 50%")
    col_in1, col_in2 = st.columns(2)
    with col_in1:
        lordo_piva = st.number_input("Compensi Annui P.IVA (€)", value=20000.0, step=1000.0)
    
    if st.button("Calcola Netto P.IVA", key="btn_piva"):
        res =
