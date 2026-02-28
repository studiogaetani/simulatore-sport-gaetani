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
#   INIZIO APP REALE
# ==============================================================================

# ─────────────────────────────────────────────────────────────────────────────
# PARAMETRI CONFIGURABILI
# Aggiornare SOLO questo dizionario a ogni variazione normativa annuale.
# Fonti: D.Lgs. 36/2021; INPS Circ. 27/2025; AdE CG 14/2025; L. 190/2014
# ─────────────────────────────────────────────────────────────────────────────
PARAMS = {
    # ── SOGLIE (art. 36 c.6 e art. 35 c.8-bis D.Lgs. 36/2021) ─────────────
    "soglia_fiscale":        15_000.0,   # No-tax area fiscale (multi-committente, anno solare)
    "soglia_prev":            5_000.0,   # Franchigia previdenziale INPS
    "soglia_forfettario":    85_000.0,   # Max ricavi regime forfettario (L. 190/2014)

    # ── RIDUZIONE IVS (art. 35 c.8-ter D.Lgs. 36/2021) ─────────────────────
    # ATTENZIONE: scade il 31/12/2027. Verificare rinnovo.
    "riduzione_ivs":          0.50,
    "scadenza_riduzione_ivs": date(2027, 12, 31),

    # ── ALIQUOTE PREVIDENZIALI GS (INPS Circ. 27/2025) ──────────────────────
    # Co.co.co. sportivo non assicurato altrove:
    #   IVS 25% applicata su BIC_IVS (= BIC_lorda × 50%)
    #   Aggiuntive 2,03% (DIS-COLL 1,31% + maternità 0,50% + malattia 0,22%)
    #   applicate sull'INTERA BIC_lorda (NO riduzione 50%)
    "aliq_ivs_cococo":        0.25,
    "aliq_add_cococo":        0.0203,
    "quota_lav_cococo":       1/3,        # Ripartizione: 1/3 lavoratore, 2/3 committente
    # Co.co.co. già assicurato/pensionato: IVS 24%
    "aliq_ivs_cococo_assicurato": 0.24,

    # Autonomo P.IVA sportivo non assicurato altrove:
    #   IVS 25% su BIC_IVS (= BIC_lorda × 50%)
    #   Aggiuntive 1,07% (malattia 0,22% + maternità 0,50% + ISCRO 0,35%)
    #   applicate sull'INTERA BIC_lorda (NO riduzione 50%)
    "aliq_ivs_piva":          0.25,
    "aliq_add_piva":          0.0107,

    # Massimale / minimale GS 2025 (INPS Circ. 27/2025)
    "massimale_gs":         120_607.0,
    "minimale_gs":           18_555.0,

    # ── FISCO FORFETTARIO (L. 190/2014; AdE CG 14/2025) ─────────────────────
    # NOTA AdE CG 14/2025: il coefficiente si applica ai compensi AL NETTO dei
    # 15.000 € di esenzione, non all'intero fatturato.
    # Formula corretta: reddito_lordo = (fatturato - soglia_fiscale) × coeff_redd
    "coeff_redditivita":      0.78,       # ATECO 85.51.09 (ex 85.51.00)
    "aliq_forfettario_ord":   0.15,       # Regime ordinario (> 5 anni)
    "aliq_forfettario_new":   0.05,       # Nuova attività (primi 5 anni)

    # ── IRPEF ORDINARIA – Scaglioni 2025 (TUIR art. 11, L. Bilancio 2025) ───
    # Lista di tuple: (limite_superiore, aliquota)
    # ultimo scaglione: limite = None (illimitato)
    "scaglioni_irpef": [
        (28_000.0, 0.23),
        (50_000.0, 0.35),
        (None,     0.43),
    ],

    # ── RITENUTA D'ACCONTO (art. 25 DPR 600/1973) ───────────────────────────
    "aliq_ritenuta_acconto":  0.20,       # Applicata dal committente sull'eccedenza 15k
}

# ─────────────────────────────────────────────────────────────────────────────
# UTILITY: IRPEF progressiva a scaglioni
# ─────────────────────────────────────────────────────────────────────────────
def calcola_irpef(imponibile: float) -> float:
    """
    Calcola IRPEF lorda applicando gli scaglioni progressivi configurati.
    Fonte: TUIR art. 11, aggiornato L. Bilancio 2025.
    """
    if imponibile <= 0:
        return 0.0
    imposta = 0.0
    prev = 0.0
    for limite, aliq in PARAMS["scaglioni_irpef"]:
        if limite is None:
            imposta += (imponibile - prev) * aliq
            break
        fascia = min(imponibile, limite) - prev
        if fascia <= 0:
            break
        imposta += fascia * aliq
        prev = limite
        if imponibile <= limite:
            break
    return round(imposta, 2)

# ─────────────────────────────────────────────────────────────────────────────
# UTILITY: warning scadenza riduzione IVS
# ─────────────────────────────────────────────────────────────────────────────
def check_riduzione_ivs_attiva() -> bool:
    """
    Restituisce True se la riduzione 50% IVS è ancora in vigore.
    Art. 35 c. 8-ter D.Lgs. 36/2021: valida fino al 31/12/2027.
    """
    return date.today() <= PARAMS["scadenza_riduzione_ivs"]

# ─────────────────────────────────────────────────────────────────────────────
# MOTORE DI CALCOLO P.IVA FORFETTARIA (CORRETTO)
# ─────────────────────────────────────────────────────────────────────────────
def calcoli_avanzati_piva(compenso_base: float, apply_rivalsa: bool,
                          apply_bollo: bool, aliquota_imp: float) -> dict:
    """
    Calcola il netto P.IVA forfettaria sportiva applicando la normativa corretta.

    CORREZIONI rispetto alla versione precedente:
    ──────────────────────────────────────────────
    BUG #1 – Imponibile forfettario (AdE CG 14/2025):
        VECCHIO: reddito_forf = fatturato × 0.78 → imponibile = reddito_forf - INPS - 15.000
        CORRETTO: componenti_pos = fatturato - 15.000 → reddito_forf = componenti_pos × 0.78
                  imponibile = reddito_forf - INPS
        Il vecchio metodo applicava il coeff. 78% anche sulla franchigia €15.000,
        producendo un imponibile fiscale più basso (tasse sottostimate di ~€2.500 su €30k).

    BUG #2 – Calcolo INPS (art. 35 c.8-ter D.Lgs. 36/2021):
        VECCHIO: inps = (BIC_lorda × 50%) × 26.07%
                 → sbagliato: le aggiuntive (1,07%) beneficiavano della riduzione 50%
        CORRETTO: contrib_IVS  = (BIC_lorda × 50%) × 25%      [IVS: riduzione applicata]
                  contrib_add  = BIC_lorda          × 1,07%    [aggiuntive: NO riduzione]
                  inps_totale  = contrib_IVS + contrib_add
    """
    riduzione_attiva = check_riduzione_ivs_attiva()
    riduzione = PARAMS["riduzione_ivs"] if riduzione_attiva else 1.0

    # A. FATTURATO LORDO (Compenso + eventuale rivalsa 4%)
    rivalsa_val = compenso_base * 0.04 if apply_rivalsa else 0.0
    fatturato_lordo = compenso_base + rivalsa_val

    # B. CALCOLO INPS – BASE PREVIDENZIALE
    # BIC_lorda = fatturato lordo − franchigia previdenziale €5.000 (art. 35 c.8-bis)
    BIC_lorda = max(0.0, fatturato_lordo - PARAMS["soglia_prev"])
    BIC_IVS   = BIC_lorda * riduzione                              # 50% fino al 2027

    contrib_IVS = BIC_IVS   * PARAMS["aliq_ivs_piva"]             # 25% su BIC ridotta
    contrib_add = BIC_lorda * PARAMS["aliq_add_piva"]             # 1,07% su BIC intera
    inps_totale = contrib_IVS + contrib_add                        # 100% a carico autonomo

    # C. CALCOLO REDDITO FORFETTARIO (FISCO)
    # AdE CG 14/2025: coeff. 78% sui compensi AL NETTO della franchigia fiscale €15.000
    componenti_pos    = max(0.0, fatturato_lordo - PARAMS["soglia_fiscale"])
    reddito_forfett   = componenti_pos * PARAMS["coeff_redditivita"]

    # D. IMPONIBILE FISCALE: reddito forfettario − INPS versata
    imponibile_fiscale = max(0.0, reddito_forfett - inps_totale)
    tasse = imponibile_fiscale * aliquota_imp

    # E. NETTO LAVORATORE
    bollo_val = 2.0 if apply_bollo and fatturato_lordo > 77.47 else 0.0
    netto = fatturato_lordo - inps_totale - tasse

    return {
        "compenso":         compenso_base,
        "rivalsa":          rivalsa_val,
        "fatturato":        fatturato_lordo,
        "BIC_lorda":        BIC_lorda,
        "BIC_IVS":          BIC_IVS,
        "contrib_IVS":      contrib_IVS,
        "contrib_add":      contrib_add,
        "inps":             inps_totale,
        "componenti_pos":   componenti_pos,
        "reddito_forf":     reddito_forfett,
        "imponibile_forf":  imponibile_fiscale,
        "tasse":            tasse,
        "bollo":            bollo_val,
        "netto":            netto,
        "riduzione_attiva": riduzione_attiva,
    }

# ─────────────────────────────────────────────────────────────────────────────
# CALCOLO INVERSO P.IVA (binary search – logica invariata, usa funzione corretta)
# ─────────────────────────────────────────────────────────────────────────────
def calcolo_inverso_piva(netto_target: float, apply_rivalsa: bool,
                         apply_bollo: bool, aliquota_imp: float) -> dict:
    """Reverse engineering con Binary Search."""
    low, high = 0.0, netto_target * 2.5
    for _ in range(100):
        mid = (low + high) / 2
        res = calcoli_avanzati_piva(mid, apply_rivalsa, apply_bollo, aliquota_imp)
        diff = res["netto"] - netto_target
        if abs(diff) < 0.01:
            return res
        elif diff > 0:
            high = mid
        else:
            low = mid
    return calcoli_avanzati_piva(high, apply_rivalsa, apply_bollo, aliquota_imp)

# ─────────────────────────────────────────────────────────────────────────────
# MOTORE DI CALCOLO CO.CO.CO. (CORRETTO)
# ─────────────────────────────────────────────────────────────────────────────
def calcola_cococo(lordo: float, gia_assicurato: bool = False) -> dict:
    """
    Calcola il netto co.co.co. sportivo dilettantistico con normativa corretta.

    CORREZIONI rispetto alla versione precedente:
    ──────────────────────────────────────────────
    BUG #3 – Aliquota INPS co.co.co. incompleta:
        VECCHIO: aliquota_inps_tot = 25% applicata su BIC_IVS (50% di BIC_lorda)
                 → mancavano le aliquote aggiuntive DIS-COLL + malattia + maternità (2,03%)
        CORRETTO: contrib_IVS = BIC_IVS   × 25%    [solo IVS beneficia della riduzione 50%]
                  contrib_add = BIC_lorda × 2,03%   [aggiuntive su base intera]

    BUG #4 – IRPEF flat 23%:
        VECCHIO: irpef = imponibile × 0.23 (scaglione unico)
        CORRETTO: scaglioni progressivi 23% / 35% / 43% (TUIR art.11, L. Bilancio 2025)

    AGGIUNTO: costo_committente = lordo + quota_committente_INPS (2/3 dei contributi totali)
    """
    riduzione_attiva = check_riduzione_ivs_attiva()
    riduzione = PARAMS["riduzione_ivs"] if riduzione_attiva else 1.0

    aliq_ivs = (PARAMS["aliq_ivs_cococo_assicurato"] if gia_assicurato
                else PARAMS["aliq_ivs_cococo"])

    # B. CALCOLO INPS
    BIC_lorda = max(0.0, lordo - PARAMS["soglia_prev"])
    BIC_IVS   = BIC_lorda * riduzione                     # 50% fino al 2027

    contrib_IVS = BIC_IVS   * aliq_ivs                   # 25% (o 24%) su BIC ridotta
    contrib_add = BIC_lorda * PARAMS["aliq_add_cococo"]  # 2,03% su BIC intera
    contrib_tot  = contrib_IVS + contrib_add

    quota_lav   = contrib_tot * PARAMS["quota_lav_cococo"]   # 1/3 lavoratore
    quota_comm  = contrib_tot * (1 - PARAMS["quota_lav_cococo"])  # 2/3 committente

    # C. CALCOLO FISCALE
    # Soglia €15.000 sul lordo + deduzione INPS quota lavoratore (art. 10 TUIR)
    imponibile_irpef = max(0.0, lordo - PARAMS["soglia_fiscale"] - quota_lav)
    ritenuta_acconto = max(0.0, lordo - PARAMS["soglia_fiscale"]) * PARAMS["aliq_ritenuta_acconto"]
    irpef_lorda      = calcola_irpef(imponibile_irpef)
    saldo_irpef      = max(0.0, irpef_lorda - ritenuta_acconto)

    # D. NETTO E COSTO COMMITTENTE
    netto            = lordo - quota_lav - irpef_lorda
    costo_committente = lordo + quota_comm

    return {
        "lordo":              lordo,
        "BIC_lorda":          BIC_lorda,
        "BIC_IVS":            BIC_IVS,
        "contrib_IVS":        contrib_IVS,
        "contrib_add":        contrib_add,
        "contrib_tot":        contrib_tot,
        "quota_lav":          quota_lav,
        "quota_comm":         quota_comm,
        "imponibile_irpef":   imponibile_irpef,
        "ritenuta_acconto":   ritenuta_acconto,
        "irpef_lorda":        irpef_lorda,
        "saldo_irpef":        saldo_irpef,
        "netto":              netto,
        "costo_committente":  costo_committente,
        "riduzione_attiva":   riduzione_attiva,
    }

# ─────────────────────────────────────────────────────────────────────────────
# FUNZIONE PDF (invariata – solo aggiornato testo note legali)
# ─────────────────────────────────────────────────────────────────────────────
def create_pdf(dati):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="FATTURA PRO-FORMA / NOTA DI COMPETENZA", ln=1, align='C')
    pdf.line(10, 25, 200, 25)
    pdf.ln(10)
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
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(200, 8, txt=f"Documento n. {dati['numero']} del {dati['data']}", ln=1, fill=True)
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(130, 8, txt="Descrizione", border=1)
    pdf.cell(60, 8, txt="Importo", border=1, align='R', ln=1)
    pdf.set_font("Arial", '', 10)
    pdf.cell(130, 8, txt=dati['descrizione'], border=1)
    pdf.cell(60, 8, txt=f"EUR {dati['compenso']:,.2f}", border=1, align='R', ln=1)
    if dati['rivalsa'] > 0:
        pdf.cell(130, 8, txt="Rivalsa INPS 4% (L. 662/96)", border=1)
        pdf.cell(60, 8, txt=f"EUR {dati['rivalsa']:,.2f}", border=1, align='R', ln=1)
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
    pdf.ln(20)
    pdf.set_font("Arial", '', 8)
    pdf.set_text_color(100, 100, 100)
    pdf.multi_cell(0, 4, txt=(
        "Operazione in franchigia da IVA ai sensi della Legge 190/2014 (Regime Forfettario).\n"
        "Operazione non soggetta a ritenuta alla fonte ai sensi dell'art. 1 c. 67 L. 190/2014.\n"
        "Prestazione sportiva ai sensi del D.Lgs. 36/2021 e successive modificazioni.\n"
        "Compensi soggetti alla franchigia fiscale di € 15.000 (art. 36 c. 6 D.Lgs. 36/2021)."
    ))
    return pdf.output(dest='S').encode('latin-1')

# ─────────────────────────────────────────────────────────────────────────────
# CSS LUXURY (invariato)
# ─────────────────────────────────────────────────────────────────────────────
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
    .result-card h1, .result-card h3, .result-card h4, .result-card p, .result-card span, .result-card div, .result-card small { color: #001529 !important; }
    .warn-card { background-color: #fff3cd; padding: 14px 18px; border-radius: 8px; border-left: 6px solid #FFC107; margin-bottom: 16px; }
    .warn-card p, .warn-card span, .warn-card div { color: #664d03 !important; font-size: 0.9em; }
    .dataframe { background-color: white; color: #333 !important; border-radius: 5px; }
    .dataframe th { background-color: #D4AF37 !important; color: #001529 !important; }
    .dataframe td { color: #333 !important; }
    [data-testid="stSidebar"] { background-color: #000f1f; border-right: 1px solid #D4AF37; }
    </style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────────
col_head1, col_head2 = st.columns([1, 4])
with col_head1:
    st.image("https://images.unsplash.com/photo-1517836357463-d25dfeac3438?ixlib=rb-4.0.3&auto=format&fit=crop&w=150&q=80", width=120)
with col_head2:
    st.title("STUDIO GAETANI")
    st.markdown("<h3 style='color: #D4AF37;'>Sport Tax Advisor & Management</h3>", unsafe_allow_html=True)

st.markdown("---")

# ─────────────────────────────────────────────────────────────────────────────
# BANNER DI SISTEMA – warning riduzione IVS in scadenza / scaduta
# ─────────────────────────────────────────────────────────────────────────────
if not check_riduzione_ivs_attiva():
    st.error(
        "⚠️ **ATTENZIONE – Riduzione IVS scaduta**  \n"
        "La riduzione del 50% sulla base imponibile IVS (art. 35 c. 8-ter D.Lgs. 36/2021) "
        f"era valida fino al {PARAMS['scadenza_riduzione_ivs'].strftime('%d/%m/%Y')}.  \n"
        "I calcoli previdenziali potrebbero non essere aggiornati. "
        "Verificare la normativa vigente e aggiornare il parametro `riduzione_ivs` in `PARAMS`."
    )
elif (PARAMS["scadenza_riduzione_ivs"] - date.today()).days < 180:
    st.warning(
        f"ℹ️ La riduzione del 50% IVS (art. 35 c. 8-ter D.Lgs. 36/2021) scade il "
        f"**{PARAMS['scadenza_riduzione_ivs'].strftime('%d/%m/%Y')}**. "
        "Monitorare eventuali proroghe."
    )

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
st.sidebar.header("⚙️ Profilo Sportivo")
regime_scelta = st.sidebar.radio("Regime P.IVA:", ["Start-up (5%)", "Ordinario (15%)"], index=0)
aliquota_tassa = PARAMS["aliq_forfettario_new"] if "Start-up" in regime_scelta else PARAMS["aliq_forfettario_ord"]

gia_assicurato = st.sidebar.checkbox(
    "Già assicurato / pensionato",
    value=False,
    help="Se il lavoratore è già coperto da altra posizione previdenziale (es. dipendente), "
         "l'aliquota IVS co.co.co. è 24% invece di 25% (INPS Circ. 27/2025)."
)

st.sidebar.markdown("---")
st.sidebar.subheader("🔗 Link Utili Sport")
st.sidebar.markdown("""
<div style="font-size: 0.9em;">
    <a href="https://registro.sportesalute.eu/" target="_blank">▪️ RAS (Registro Sport)</a><br>
    <a href="https://www.sport.governo.it/it/riforma-dello-sport/" target="_blank">▪️ Dipartimento Sport</a><br>
    <a href="https://www.agenziaentrate.gov.it/" target="_blank">▪️ Agenzia Entrate</a><br>
    <a href="https://www.inps.it/" target="_blank">▪️ INPS – Gestione Separata</a>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("---")
st.sidebar.caption(
    "⚖️ Normativa di riferimento:  \n"
    "D.Lgs. 36/2021 (riforma sport)  \n"
    "INPS Circ. 27/2025  \n"
    "AdE CG 14/2025  \n"
    "L. Bilancio 2025"
)

if st.sidebar.button("Esci / Logout"):
    del st.session_state["password_correct"]
    st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────────────────────────────────────
tab_piva, tab_cococo, tab_confronto, tab_fattura = st.tabs([
    "📊 P.IVA Sportiva", "🤝 Assunzione Co.co.co", "⚖️ Confronto", "📝 Genera Fattura PDF"
])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 – P.IVA SPORTIVA
# ═══════════════════════════════════════════════════════════════════════════════
with tab_piva:
    st.markdown("<div class='sport-header'>Gestione P.IVA Sportiva – Regime Forfettario</div>", unsafe_allow_html=True)

    # Note informative
    with st.expander("ℹ️ Come funzionano i calcoli – fonti normative"):
        st.markdown("""
        **Soglia fiscale €15.000** (art. 36 c. 6 D.Lgs. 36/2021):  
        I compensi percepiti da ASD/SSD/FSN non concorrono al reddito imponibile fino a €15.000 
        complessivi nell'anno solare (criterio di cassa, multi-committente cumulativo).

        **Imponibile forfettario** (AdE Consulenza Giuridica 14/2025):  
        Il coefficiente di redditività (78%) si applica ai compensi **al netto** dei €15.000.  
        Formula: `(fatturato − €15.000) × 78% − INPS versata`

        **INPS – Riduzione 50% IVS** (art. 35 c. 8-ter D.Lgs. 36/2021):  
        Fino al **31/12/2027** l'aliquota IVS (25%) si applica solo al **50% della base contributiva**.  
        Le aliquote aggiuntive (malattia 0,22% + maternità 0,50% + ISCRO 0,35% = 1,07%) si applicano 
        sull'**intera base** (no riduzione 50%).

        **Franchigia previdenziale** €5.000 (art. 35 c. 8-bis): nessun contributo INPS 
        sui primi €5.000 annui.
        """)

    # Avviso soglia forfettario
    st.markdown(f"""
    <div class='warn-card'>
    <p>⚠️ <b>Soglia regime forfettario: €{PARAMS['soglia_forfettario']:,.0f}</b> – 
    L'intero fatturato (inclusa la fascia esente €15.000) concorre al test.
    Se superi questa soglia, seleziona la modalità P.IVA Ordinaria nella Tab Confronto.</p>
    </div>
    """, unsafe_allow_html=True)

    mode = st.radio("Modalità:", ["Dal Lordo al Netto", "Dal Netto al Lordo (Reverse)"], horizontal=True)
    c1, c2 = st.columns(2)
    with c1:
        val_input = st.number_input("Inserisci Importo (€)", value=20000.0, step=500.0, min_value=0.0)
    with c2:
        flag_riv = st.checkbox("Rivalsa INPS 4%", value=True,
                               help="La rivalsa 4% è facoltativa per gli autonomi in GS (L. 662/96). "
                                    "Aggiungi al compenso da fatturare al committente.")
        flag_bol = st.checkbox("Bollo € 2,00", value=True,
                               help="Obbligatorio su fatture esenti IVA superiori a €77,47.")

    # Validazione soglia forfettario
    if val_input > PARAMS["soglia_forfettario"]:
        st.error(
            f"⛔ L'importo inserito (€{val_input:,.0f}) supera la soglia del regime forfettario "
            f"(€{PARAMS['soglia_forfettario']:,.0f}). Il regime forfettario non è applicabile. "
            "Usa la Tab Confronto con P.IVA Ordinaria."
        )
    elif st.button("CALCOLA", key="btn_piva"):
        if "Lordo" in mode:
            res = calcoli_avanzati_piva(val_input, flag_riv, flag_bol, aliquota_tassa)
            titolo, val_show = "Netto Disponibile", res['netto']
        else:
            res = calcolo_inverso_piva(val_input, flag_riv, flag_bol, aliquota_tassa)
            titolo, val_show = "Compenso da Chiedere", res['compenso']

        st.markdown(f"""
        <div class="result-card">
            <h3>{titolo}:</h3>
            <h1 style="color: #002a52 !important;">€ {val_show:,.2f}</h1>
            <small>Fatturato Reale Incassato: € {res['fatturato']:,.2f}</small>
        </div>
        """, unsafe_allow_html=True)

        rid_label = "SÌ (50% – art. 35 c.8-ter, fino 31/12/2027)" if res['riduzione_attiva'] else "NO (scaduta)"

        df = pd.DataFrame({
            "Voce": [
                "1. Compenso Base",
                "2. Rivalsa INPS 4% (facoltativa)",
                "👉 FATTURATO LORDO",
                "── CALCOLO PREVIDENZIALE ──────────────",
                f"3. Franchigia prev. (−€{PARAMS['soglia_prev']:,.0f} – art.35 c.8-bis)",
                "4. BIC lorda (base imponibile contributi)",
                f"5. Riduzione 50% IVS applicata: {rid_label}",
                "6. BIC ridotta (base IVS)",
                f"7. Contributi IVS ({PARAMS['aliq_ivs_piva']*100:.0f}% su BIC ridotta)",
                f"8. Contrib. aggiuntive ({PARAMS['aliq_add_piva']*100:.2f}% su BIC intera)",
                "9. INPS TOTALE (a carico lavoratore)",
                "── CALCOLO FISCALE ────────────────────",
                f"10. Franchigia fiscale (−€{PARAMS['soglia_fiscale']:,.0f} – art.36 c.6)",
                "11. Componenti positivi (fatturato − €15k)",
                f"12. Reddito forfettario ({int(PARAMS['coeff_redditivita']*100)}% su comp. positivi – AdE CG 14/2025)",
                "13. Deduci INPS versata",
                "14. Imponibile fiscale netto",
                f"15. Imposta sostitutiva ({int(aliquota_tassa*100)}%)",
                "── NETTO ──────────────────────────────",
                "💰 NETTO REALE LAVORATORE",
            ],
            "Importo (€)": [
                f"{res['compenso']:,.2f}",
                f"{res['rivalsa']:,.2f}",
                f"{res['fatturato']:,.2f}",
                "─────────────────",
                f"−{PARAMS['soglia_prev']:,.2f}",
                f"{res['BIC_lorda']:,.2f}",
                rid_label,
                f"{res['BIC_IVS']:,.2f}",
                f"−{res['contrib_IVS']:,.2f}",
                f"−{res['contrib_add']:,.2f}",
                f"−{res['inps']:,.2f}",
                "─────────────────",
                f"−{PARAMS['soglia_fiscale']:,.2f}",
                f"{res['componenti_pos']:,.2f}",
                f"{res['reddito_forf']:,.2f}",
                f"−{res['inps']:,.2f}",
                f"{res['imponibile_forf']:,.2f}",
                f"−{res['tasse']:,.2f}",
                "─────────────────",
                f"€ {res['netto']:,.2f}",
            ]
        })
        st.table(df)

        aliq_eff = (res['inps'] + res['tasse']) / res['fatturato'] * 100 if res['fatturato'] > 0 else 0
        st.markdown(f"""
        <div class="result-card">
            <p>📊 <b>Pressione fiscale + contributiva effettiva:</b> {aliq_eff:.1f}%
            &nbsp;|&nbsp; INPS: €{res['inps']:,.2f}
            &nbsp;|&nbsp; Imposta: €{res['tasse']:,.2f}</p>
        </div>
        """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 – CO.CO.CO.
# ═══════════════════════════════════════════════════════════════════════════════
with tab_cococo:
    st.markdown("<div class='sport-header'>Assunzione Co.co.co Sportivo Dilettantistico</div>", unsafe_allow_html=True)

    with st.expander("ℹ️ Come funzionano i calcoli – fonti normative"):
        st.markdown("""
        **Soglia fiscale €15.000** (art. 36 c. 6): stessa del forfettario. Ritenuta d'acconto 
        20% (art. 25 DPR 600/1973) applicata solo sulla parte eccedente.

        **INPS – Ripartizione** (art. 35 D.Lgs. 36/2021):  
        I contributi si ripartiscono: **1/3 lavoratore** e **2/3 committente**.  
        Il costo reale per l'ASD/SSD è quindi **lordo + 2/3 dei contributi totali**.

        **Aliquote INPS co.co.co.** (INPS Circ. 27/2025):  
        - IVS 25% (o 24% se già assicurato) sul 50% della base contributiva  
        - Aggiuntive 2,03% (DIS-COLL + malattia + maternità) sull'intera base contributiva  

        **IRPEF**: scaglioni progressivi 23%/35%/43% (TUIR art. 11, L. Bilancio 2025).
        """)

    lordo_dip = st.number_input("Compenso Lordo Annuo (€)", value=20000.0, step=500.0, min_value=0.0)

    if st.button("CALCOLA", key="btn_dip"):
        res = calcola_cococo(lordo_dip, gia_assicurato=gia_assicurato)
        rid_label = "Sì (50%)" if res['riduzione_attiva'] else "No (scaduta)"
        aliq_ivs_label = PARAMS['aliq_ivs_cococo_assicurato'] if gia_assicurato else PARAMS['aliq_ivs_cococo']

        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"""
            <div class="result-card">
                <h3>💰 Netto Lavoratore:</h3>
                <h1 style="color: #002a52 !important;">€ {res['netto']:,.2f}</h1>
                <small>Al netto di INPS quota lavoratore + IRPEF</small>
            </div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div class="result-card" style="border-left-color: #b8860b;">
                <h3>🏢 Costo Committente (ASD/SSD):</h3>
                <h1 style="color: #002a52 !important;">€ {res['costo_committente']:,.2f}</h1>
                <small>Lordo €{res['lordo']:,.0f} + INPS quota committente €{res['quota_comm']:,.2f}</small>
            </div>""", unsafe_allow_html=True)

        df = pd.DataFrame({
            "Voce": [
                "1. Compenso Lordo",
                "── CALCOLO PREVIDENZIALE ──────────────",
                f"2. Franchigia prev. (−€{PARAMS['soglia_prev']:,.0f})",
                "3. BIC lorda",
                f"4. Riduzione 50% IVS: {rid_label}",
                "5. BIC ridotta (base IVS)",
                f"6. Contributi IVS ({aliq_ivs_label*100:.0f}% su BIC ridotta)",
                f"7. Contrib. aggiuntive ({PARAMS['aliq_add_cococo']*100:.2f}% su BIC intera)",
                "8. CONTRIBUTI TOTALI",
                "9. Quota lavoratore (1/3)",
                "10. Quota committente (2/3)",
                "── CALCOLO FISCALE ────────────────────",
                f"11. Soglia no-tax (−€{PARAMS['soglia_fiscale']:,.0f})",
                "12. Deduci INPS quota lavoratore",
                "13. Imponibile IRPEF",
                "14. Ritenuta d'acconto (20% su eccedenza)",
                "15. IRPEF lorda (scaglioni progressivi)",
                "16. Saldo IRPEF in dichiarazione",
                "── RIEPILOGO ──────────────────────────",
                "💰 NETTO LAVORATORE",
                "🏢 COSTO COMMITTENTE",
            ],
            "Importo (€)": [
                f"{res['lordo']:,.2f}",
                "─────────────────",
                f"−{PARAMS['soglia_prev']:,.2f}",
                f"{res['BIC_lorda']:,.2f}",
                rid_label,
                f"{res['BIC_IVS']:,.2f}",
                f"−{res['contrib_IVS']:,.2f}",
                f"−{res['contrib_add']:,.2f}",
                f"{res['contrib_tot']:,.2f}",
                f"−{res['quota_lav']:,.2f}",
                f"+{res['quota_comm']:,.2f} (a carico ASD)",
                "─────────────────",
                f"−{PARAMS['soglia_fiscale']:,.2f}",
                f"−{res['quota_lav']:,.2f}",
                f"{res['imponibile_irpef']:,.2f}",
                f"−{res['ritenuta_acconto']:,.2f} (anticipo)",
                f"−{res['irpef_lorda']:,.2f}",
                f"−{res['saldo_irpef']:,.2f}",
                "─────────────────",
                f"€ {res['netto']:,.2f}",
                f"€ {res['costo_committente']:,.2f}",
            ]
        })
        st.table(df)

        st.markdown(f"""
        <div class='warn-card'>
        <p>📋 <b>Adempimenti committente:</b> Il committente (ASD/SSD) deve versare i contributi (quota 2/3)
        tramite F24 entro il 16 del mese successivo al pagamento del compenso.
        Applicare la ritenuta d'acconto 20% sull'eccedenza dei €15.000 solo se il lavoratore
        presenta autocertificazione (art. 36 c. 6-bis D.Lgs. 36/2021).</p>
        </div>
        """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 – CONFRONTO
# ═══════════════════════════════════════════════════════════════════════════════
with tab_confronto:
    st.markdown("<div class='sport-header'>Confronto P.IVA Forfettaria vs Co.co.co Sportivo</div>", unsafe_allow_html=True)

    st.markdown("""
    <div class='warn-card'>
    <p>⚠️ Il confronto usa la stessa cifra come <b>compenso base</b> per entrambi i regimi.
    Per la P.IVA, il costo committente coincide col compenso (nessun onere contributivo diretto).
    Per il co.co.co., il costo committente è maggiore (include 2/3 dei contributi INPS).</p>
    </div>
    """, unsafe_allow_html=True)

    budget = st.number_input("Compenso / Budget Lordo (€)", value=25000.0, step=500.0, min_value=0.0)

    if budget > PARAMS["soglia_forfettario"]:
        st.warning(f"⚠️ Budget > €{PARAMS['soglia_forfettario']:,.0f}: il regime forfettario non è applicabile.")

    if st.button("CONFRONTA", key="btn_conf"):
        piva = calcoli_avanzati_piva(budget, False, False, aliquota_tassa)
        dip  = calcola_cococo(budget, gia_assicurato=gia_assicurato)

        # ── Netto lavoratore ────────────────────────────────────────────────
        st.subheader("Dal punto di vista del Lavoratore")
        c1, c2 = st.columns(2)
        with c1:
            delta_piva = ((piva['netto'] / budget) - 1) * 100 if budget > 0 else 0
            st.markdown(f"""
            <div class="result-card" style="border-left-color: #002a52;">
                <h4>🏃 P.IVA Forfettaria ({int(aliquota_tassa*100)}%)</h4>
                <h2>Netto: € {piva['netto']:,.0f}</h2>
                <small>INPS: €{piva['inps']:,.0f} | Tasse: €{piva['tasse']:,.0f}</small><br>
                <small>Pressione effettiva: {(piva['inps']+piva['tasse'])/budget*100:.1f}%</small>
            </div>""", unsafe_allow_html=True)
        with c2:
            delta_dip = ((dip['netto'] / budget) - 1) * 100 if budget > 0 else 0
            st.markdown(f"""
            <div class="result-card" style="border-left-color: #b8860b;">
                <h4>📝 Co.co.co Sportivo</h4>
                <h2>Netto: € {dip['netto']:,.0f}</h2>
                <small>INPS quota lav.: €{dip['quota_lav']:,.0f} | IRPEF: €{dip['irpef_lorda']:,.0f}</small><br>
                <small>Pressione effettiva: {(dip['quota_lav']+dip['irpef_lorda'])/budget*100:.1f}%</small>
            </div>""", unsafe_allow_html=True)

        # ── Costo committente ────────────────────────────────────────────────
        st.subheader("Dal punto di vista del Committente (ASD/SSD)")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"""
            <div class="result-card" style="border-left-color: #002a52;">
                <h4>🏃 Se usa P.IVA</h4>
                <h2>Costo: € {budget:,.0f}</h2>
                <small>Nessun onere contributivo aggiuntivo.<br>
                Il lavoratore versa INPS in proprio.</small>
            </div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div class="result-card" style="border-left-color: #b8860b;">
                <h4>📝 Se usa Co.co.co.</h4>
                <h2>Costo: € {dip['costo_committente']:,.0f}</h2>
                <small>+€{dip['quota_comm']:,.0f} di INPS quota committente (2/3).<br>
                Versamento F24 entro il 16 del mese succ.</small>
            </div>""", unsafe_allow_html=True)

        # ── Tabella comparativa sintetica ────────────────────────────────────
        vincitore_lav   = "P.IVA" if piva['netto'] >= dip['netto'] else "Co.co.co."
        vincitore_comm  = "P.IVA" if budget <= dip['costo_committente'] else "Co.co.co."
        diff_netto      = abs(piva['netto'] - dip['netto'])
        diff_costo      = abs(budget - dip['costo_committente'])

        df_comp = pd.DataFrame({
            "Voce": [
                "Compenso lordo",
                "INPS totale lavoratore",
                "IRPEF / Imposta sostitutiva",
                "NETTO LAVORATORE",
                "COSTO COMMITTENTE",
                "Pressione fiscale+prev. (lavoratore)",
            ],
            "P.IVA Forfettaria": [
                f"€ {budget:,.0f}",
                f"€ {piva['inps']:,.0f}",
                f"€ {piva['tasse']:,.0f}",
                f"€ {piva['netto']:,.0f}",
                f"€ {budget:,.0f}",
                f"{(piva['inps']+piva['tasse'])/budget*100:.1f}%",
            ],
            "Co.co.co. Sportivo": [
                f"€ {budget:,.0f}",
                f"€ {dip['quota_lav']:,.0f} (quota 1/3)",
                f"€ {dip['irpef_lorda']:,.0f}",
                f"€ {dip['netto']:,.0f}",
                f"€ {dip['costo_committente']:,.0f}",
                f"{(dip['quota_lav']+dip['irpef_lorda'])/budget*100:.1f}%",
            ],
        })
        st.table(df_comp)

        st.info(
            f"📌 **Convenienza lavoratore:** {vincitore_lav} (+€{diff_netto:,.0f} di netto)  \n"
            f"📌 **Convenienza committente:** {vincitore_comm} (−€{diff_costo:,.0f} di costo)"
        )

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4 – FATTURA PDF
# ═══════════════════════════════════════════════════════════════════════════════
with tab_fattura:
    st.markdown("<div class='sport-header'>Generatore Fattura / Nota di Competenza</div>", unsafe_allow_html=True)
    with st.form("form_pdf"):
        c1, c2 = st.columns(2)
        with c1:
            mitt = st.text_area("Tuoi Dati", "Nome Cognome\nIndirizzo\nP.IVA")
            num  = st.text_input("Numero", f"{date.today().year}/001")
        with c2:
            dest = st.text_area("Cliente", "ASD Esempio\nIndirizzo")
            data = st.date_input("Data", date.today())
        desc = st.text_input("Descrizione", "Prestazione sportiva ai sensi del D.Lgs. 36/2021")
        imp  = st.number_input("Compenso (€)", value=1000.0, min_value=0.0)
        riv  = st.checkbox("Rivalsa 4%", value=True)
        bol  = st.checkbox("Bollo €2", value=True)
        if st.form_submit_button("SCARICA PDF"):
            val_riv  = imp * 0.04 if riv else 0.0
            tot_lordo = imp + val_riv
            val_bol  = 2.0 if bol and tot_lordo > 77.47 else 0.0
            tot_pag  = tot_lordo + val_bol
            dati = {
                "mittente": mitt, "destinatario": dest,
                "numero": num, "data": data.strftime("%d/%m/%Y"),
                "descrizione": desc, "compenso": imp,
                "rivalsa": val_riv, "totale_lordo": tot_lordo,
                "bollo": val_bol, "totale_pagare": tot_pag
            }
            try:
                pdf_bytes = create_pdf(dati)
                b64  = base64.b64encode(pdf_bytes).decode()
                href = (
                    f'<a href="data:application/octet-stream;base64,{b64}" '
                    f'download="Fattura_{num.replace("/","_")}.pdf" '
                    f'style="background-color: #D4AF37; color: #001529; padding: 10px 20px; '
                    f'text-decoration: none; border-radius: 5px; font-weight: bold;">📥 SCARICA PDF</a>'
                )
                st.markdown(href, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Errore generazione PDF: {e}")

st.markdown("<br><center style='color: #D4AF37; font-size: 0.8em;'>Studio Gaetani © 2025 | Normativa aggiornata al 2025 | D.Lgs. 36/2021</center>", unsafe_allow_html=True)
