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
    .result-card h1, .result-card h3, .result-card p, .result-card span, .result-card div, .result-card small { color: #001529 !important; }

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

st.markdown("---")

# --- SIDEBAR ---
st.sidebar.header("⚙️ Profilo Sportivo")
regime_scelta = st.sidebar.radio("Regime P.IVA:", ["Start-up (5%)", "Ordinario (15%)"], index=0)
aliquota_tassa = 0.05 if "Start-up" in regime_scelta else 0.15

st.sidebar.markdown("---")
st.sidebar.subheader("🔗 Link Utili Sport")
st.sidebar.markdown("""
<div style="font-size: 0.9em;">
    <a href="https://registro.sportesalute.eu/" target="_blank">▪️ RAS (Registro Sport)</a><br>
    <a href="https://www.sport.governo.it/it/riforma-dello-sport/" target="_blank">▪️ Dipartimento Sport</a><br>
    <a href="https://www.agenziaentrate.gov.it/" target="_blank">▪️ Agenzia Entrate</a>
</div>
""", unsafe_allow_html=True)

if st.sidebar.button("Esci / Logout"):
    del st.session_state["password_correct"]
    st.rerun()

# --- MOTORE DI CALCOLO P.IVA (CORRETTO) ---

def calcoli_avanzati_piva(compenso_base, apply_rivalsa, apply_bollo, aliquota_imp):
    """
    Calcola P.IVA con logica richiesta:
    1. INPS: Calcolato su (FATTURATO LORDO - 5000). Il coefficiente non si applica qui.
    2. TASSE: Calcolate su (Fatturato * 78%) - INPS - 15000.
    """
    params = PARAMETRI_SPORT["P.IVA Forfettario"]
    
    # A. FATTURATO LORDO (Compenso + 4%)
    rivalsa_val = compenso_base * 0.04 if apply_rivalsa else 0.0
    fatturato_lordo = compenso_base + rivalsa_val
    
    # B. CALCOLO INPS (SUL FATTURATO LORDO, NON SUL REDDITO FORFETTARIO)
    # Base INPS = Fatturato Lordo - 5000 (Franchigia)
    base_inps_grezza = fatturato_lordo - params["soglia_inps"]
    if base_inps_grezza < 0: base_inps_grezza = 0
    
    # Abbattimento 50% (Riforma Sport)
    base_inps_netta = base_inps_grezza * params["abbattimento_inps"]
    inps_dovuta = base_inps_netta * params["aliquota_inps"]
    
    # C. CALCOLO REDDITO FORFETTARIO (PER IL FISCO)
    # Qui si applica il coefficiente del 78% come da norma forfettaria
    reddito_forfettario = fatturato_lordo * params["coeff_redditivita"]
    
    # D. CALCOLO TASSE
    # Imponibile = Reddito Forfettario - INPS pagata - Franchigia Fiscale 15k
    imponibile_fiscale = reddito_forfettario - inps_dovuta - params["franchigia_fiscale"]
    if imponibile_fiscale < 0: imponibile_fiscale = 0
    
    tasse = imponibile_fiscale * aliquota_imp
    
    # E. NETTO
    bollo_val = 2.0 if apply_bollo and fatturato_lordo > 77.47 else 0.0
    netto = fatturato_lordo - inps_dovuta - tasse
    
    return {
        "compenso": compenso_base,
        "rivalsa": rivalsa_val,
        "fatturato": fatturato_lordo,
        "reddito_forf": reddito_forfettario,
        "base_inps": base_inps_netta, 
        "inps": inps_dovuta,
        "franchigia_15k": params["franchigia_fiscale"],
        "base_fiscale": imponibile_fiscale,
        "tasse": tasse,
        "bollo": bollo_val,
        "netto": netto
    }

def calcolo_inverso_piva(netto_target, apply_rivalsa, apply_bollo, aliquota_imp):
    """Reverse engineering con Binary Search"""
    low = 0.0
    high = netto_target * 2.5 
    tolerance = 0.01
    
    for _ in range(100): 
        mid = (low + high) / 2
        res = calcoli_avanzati_piva(mid, apply_rivalsa, apply_bollo, aliquota_imp)
        diff = res['netto'] - netto_target
        if abs(diff) < tolerance:
            return res
        elif diff > 0:
            high = mid
        else:
            low = mid
    return calcoli_avanzati_piva(high, apply_rivalsa, apply_bollo, aliquota_imp)

def calcola_cococo(lordo):
    params = PARAMETRI_SPORT["Collaboratore (Co.co.co)"]
    eccedenza_inps = max(0, lordo - params["soglia_no_inps"])
    base_inps = eccedenza_inps * params["abbattimento_inps"]
    inps_lav = (base_inps * params["aliquota_inps_tot"]) * params["quota_lavoratore"]
    
    imponibile_fiscale = max(0, (lordo - inps_lav) - params["soglia_no_tax"])
    irpef = imponibile_fiscale * 0.23
    
    return {
        "lordo": lordo, "inps": inps_lav, "irpef": irpef, 
        "netto": lordo - inps_lav - irpef
    }

# --- FUNZIONE PDF (ANONIMA) ---
def create_pdf(dati):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Intestazione Generica
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="FATTURA PRO-FORMA / NOTA DI COMPETENZA", ln=1, align='C')
    pdf.line(10, 25, 200, 25)
    pdf.ln(10)
    
    # Dati Fornitore/Cliente
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(95, 10, txt="FORNITORE (Emittente):", border=0)
    pdf.cell(95, 10, txt="CLIENTE (Destinatario):", border=0, ln=1)
    
    pdf.set_font("Arial", '', 10)
    y_start = pdf.get_y()
    pdf.multi_cell(95, 5, txt=dati['mittente'])
    y_end_left = pdf.get_y()
    
    pdf.set_xy(105, y_start)
    pdf.multi_cell(95, 5, txt=dati['destinatario'])
    y_end_right = pdf.get_y()
    
    pdf.set_xy(10, max(y_end_left, y_end_right) + 10)
    
    # Dati Documento
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(200, 8, txt=f"Documento n. {dati['numero']} del {dati['data']}", ln=1, fill=True)
    pdf.ln(5)
    
    # Tabella
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(130, 8, txt="Descrizione", border=1)
    pdf.cell(60, 8, txt="Importo", border=1, align='R', ln=1)
    
    pdf.set_font("Arial", '', 10)
    pdf.cell(130, 8, txt=dati['descrizione'], border=1)
    pdf.cell(60, 8, txt=f"EUR {dati['compenso']:,.2f}", border=1, align='R', ln=1)
    
    if dati['rivalsa'] > 0:
        pdf.cell(130, 8, txt="Rivalsa INPS 4% (L. 662/96)", border=1)
        pdf.cell(60, 8, txt=f"EUR {dati['rivalsa']:,.2f}", border=1, align='R', ln=1)
    
    # Totali
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(130, 8, txt="TOTALE LORDO", border=0, align='R')
    pdf.cell(60, 8, txt=f"EUR {dati['totale_lordo']:,.2f}", border=1, align='R', ln=1)
    
    if dati['bollo'] > 0:
        pdf.set_font("Arial", '', 10)
        pdf.cell(130, 8, txt="Bollo (Art. 15 DPR 633/72)", border=0, align='R')
        pdf.cell(60, 8, txt=f"EUR {dati['bollo']:,.2f}", border=0, align='R', ln=1)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(130, 8, txt="TOTALE A PAGARE", border=0, align='R')
        pdf.cell(60, 8, txt=f"EUR {dati['totale_pagare']:,.2f}", border=0, align='R', ln=1)
    
    # Note Legali
    pdf.ln(20)
    pdf.set_font("Arial", '', 8)
    pdf.set_text_color(100, 100, 100)
    pdf.multi_cell(0, 4, txt="Operazione in franchigia da IVA ai sensi della Legge 190/2014 (Regime Forfettario).\nOperazione non soggetta a ritenuta alla fonte.\nPrestazione sportiva ai sensi del D.Lgs 36/2021.")
    
    return pdf.output(dest='S').encode('latin-1')

# --- TABS ---
tab_piva, tab_cococo, tab_confronto, tab_fattura = st.tabs(["📊 P.IVA Sportiva", "🤝 Assunzione Co.co.co", "⚖️ Confronto", "📝 Genera Fattura PDF"])

# === TAB 1: P.IVA SPORTIVA ===
with tab_piva:
    st.markdown("<div class='sport-header'>Gestione P.IVA Sportiva</div>", unsafe_allow_html=True)
    mode = st.radio("Modalità:", ["Dal Lordo al Netto", "Dal Netto al Lordo (Reverse)"], horizontal=True)
    
    c1, c2 = st.columns(2)
    with c1:
        val_input = st.number_input("Inserisci Importo (€)", value=20000.0, step=500.0)
    with c2:
        flag_riv = st.checkbox("Rivalsa INPS 4%", value=True)
        flag_bol = st.checkbox("Bollo € 2,00", value=True)

    if st.button("CALCOLA", key="btn_piva"):
        if "Lordo" in mode:
            res = calcoli_avanzati_piva(val_input, flag_riv, flag_bol, aliquota_tassa)
            titolo = "Netto Disponibile"
        else:
            res = calcolo_inverso_piva(val_input, flag_riv, flag_bol, aliquota_tassa)
            titolo = "Compenso da Chiedere"
            
        st.markdown(f"""
        <div class="result-card">
            <h3>{titolo}:</h3>
            <h1 style="color: #002a52 !important;">€ {res['netto'] if 'Lordo' in mode else res['compenso']:,.2f}</h1>
            <small>Fatturato Reale Incassato: € {res['fatturato']:,.2f}</small>
        </div>
        """, unsafe_allow_html=True)
        
        # DATI NUMERICI DETTAGLIATI
        df = pd.DataFrame({
            "Voce": [
                "1. Compenso Base", 
                "2. Rivalsa INPS 4%", 
                "👉 FATTURATO LORDO",
                "4. Base Calcolo INPS (Fatturato - 5k)",
                f"5. INPS ({PARAMETRI_SPORT['P.IVA Forfettario']['aliquota_inps']*100:.2f}% su base ridotta 50%)",
                f"6. Reddito Forfettario ({int(PARAMETRI_SPORT['P.IVA Forfettario']['coeff_redditivita']*100)}% del Fatturato)",
                "7. Franchigia Fiscale (-15.000€)",
                "8. Base Imponibile Fiscale (Reddito - INPS - 15k)",
                f"9. Imposta Sostitutiva ({int(aliquota_tassa*100)}%)",
                "💰 NETTO REALE"
            ],
            "Importo (€)": [
                res['compenso'], 
                res['rivalsa'], 
                res['fatturato'], 
                "Logica Lordo-5k",
                -res['inps'], 
                res['reddito_forf'],
                -res['franchigia_15k'],
                res['base_fiscale'],
                -res['tasse'], 
                res['netto']
            ]
        })
        st.table(df)

# === TAB 2: CO.CO.CO ===
with tab_cococo:
    st.markdown("<div class='sport-header'>Assunzione Co.co.co Sportivo</div>", unsafe_allow_html=True)
    lordo_dip = st.number_input("Compenso Lordo (€)", value=20000.0, step=500.0)
    if st.button("CALCOLA", key="btn_dip"):
        res = calcola_cococo(lordo_dip)
        st.markdown(f"""
        <div class="result-card">
            <h3>Netto in Busta:</h3>
            <h1 style="color: #002a52 !important;">€ {res['netto']:,.2f}</h1>
        </div>""", unsafe_allow_html=True)
        st.table(pd.DataFrame({
            "Voce": ["Lordo", "Trattenute INPS", "Trattenute IRPEF (Franchigia 15k)", "NETTO"],
            "Importo (€)": [res['lordo'], -res['inps'], -res['irpef'], res['netto']]
        }))

# === TAB 3: CONFRONTO ===
with tab_confronto:
    st.markdown("<div class='sport-header'>Confronto P.IVA vs Co.co.co</div>", unsafe_allow_html=True)
    budget = st.number_input("Budget Lordo (€)", value=25000.0, step=500.0)
    if st.button("CONFRONTA", key="btn_conf"):
        # P.IVA (Considerando il budget come Fatturato Lordo inclusivo di tutto)
        # Se budget = 25.000, calcoliamo P.IVA partendo da quello come Lordo (compenso + rivalsa implicita)
        # Per semplicità usiamo il budget come Compenso Base nel confronto
        piva = calcoli_avanzati_piva(budget, False, False, aliquota_tassa)
        dip = calcola_cococo(budget)
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"""<div class="result-card" style="border-left-color: #002a52;"><h4>🏃‍♂️ P.IVA</h4><h2>Netto: € {piva['netto']:,.0f}</h2><small>Base INPS su Fatturato</small></div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""<div class="result-card" style="border-left-color: #b8860b;"><h4>📝 Assunzione</h4><h2>Netto: € {dip['netto']:,.0f}</h2><small>Base INPS su Eccedenza 5k</small></div>""", unsafe_allow_html=True)

# === TAB 4: FATTURA PDF ===
with tab_fattura:
    st.markdown("<div class='sport-header'>Generatore Fattura</div>", unsafe_allow_html=True)
    with st.form("form_pdf"):
        c1, c2 = st.columns(2)
        with c1:
            mitt = st.text_area("Tuoi Dati", "Nome Cognome\nIndirizzo\nP.IVA")
            num = st.text_input("Numero", f"{date.today().year}/001")
        with c2:
            dest = st.text_area("Cliente", "ASD Esempio\nIndirizzo")
            data = st.date_input("Data", date.today())
        
        desc = st.text_input("Descrizione", "Prestazione sportiva...")
        imp = st.number_input("Compenso (€)", value=1000.0)
        riv = st.checkbox("Rivalsa 4%", value=True)
        bol = st.checkbox("Bollo €2", value=True)
        
        if st.form_submit_button("SCARICA PDF"):
            val_riv = imp * 0.04 if riv else 0.0
            tot_lordo = imp + val_riv
            val_bol = 2.0 if bol and tot_lordo > 77.47 else 0.0
            tot_pag = tot_lordo + val_bol
            
            dati = {
                "mittente": mitt, "destinatario": dest, "numero": num, "data": data.strftime("%d/%m/%Y"),
                "descrizione": desc, "compenso": imp, "rivalsa": val_riv, 
                "totale_lordo": tot_lordo, "bollo": val_bol, "totale_pagare": tot_pag
            }
            try:
                pdf_bytes = create_pdf(dati)
                b64 = base64.b64encode(pdf_bytes).decode()
                href = f'<a href="data:application/octet-stream;base64,{b64}" download="Fattura_{num.replace("/","_")}.pdf" style="background-color: #D4AF37; color: #001529; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold;">📥 SCARICA PDF</a>'
                st.markdown(href, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Errore: {e}")

st.markdown("<br><center style='color: #D4AF37; font-size: 0.8em;'>Studio Gaetani © 2024</center>", unsafe_allow_html=True)
