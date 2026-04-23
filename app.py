import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Simulateur LMNP vs SCI à l'IS — Artae Immobilier",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

.main-title {
    font-family: 'DM Serif Display', serif;
    font-size: 2.6rem;
    color: #1a1a2e;
    line-height: 1.1;
    margin-bottom: 0.2rem;
}

.subtitle {
    font-size: 1rem;
    color: #6b7280;
    font-weight: 300;
    margin-bottom: 2rem;
}

.result-card {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    border-radius: 16px;
    padding: 2rem;
    color: white;
    text-align: center;
    border: 1px solid rgba(255,255,255,0.08);
    box-shadow: 0 8px 32px rgba(26,26,46,0.2);
}

.result-card.winner {
    background: linear-gradient(135deg, #0f4c75 0%, #1b6ca8 100%);
    border: 1px solid rgba(100,180,255,0.3);
}

.result-label {
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    opacity: 0.7;
    margin-bottom: 0.5rem;
}

.result-value {
    font-family: 'DM Serif Display', serif;
    font-size: 2.4rem;
    font-weight: 400;
    color: #ffffff;
}

.result-delta {
    font-size: 0.85rem;
    opacity: 0.8;
    margin-top: 0.4rem;
}

.section-header {
    font-family: 'DM Serif Display', serif;
    font-size: 1.3rem;
    color: #1a1a2e;
    border-bottom: 2px solid #e5e7eb;
    padding-bottom: 0.4rem;
    margin: 1.5rem 0 1rem 0;
}

.warning-box {
    background: #fef3c7;
    border-left: 4px solid #f59e0b;
    padding: 0.8rem 1rem;
    border-radius: 0 8px 8px 0;
    font-size: 0.85rem;
    color: #92400e;
    margin: 1rem 0;
}

.info-box {
    background: #eff6ff;
    border-left: 4px solid #3b82f6;
    padding: 0.8rem 1rem;
    border-radius: 0 8px 8px 0;
    font-size: 0.85rem;
    color: #1e40af;
    margin: 0.5rem 0;
}

.stMetric {
    background: #f8fafc;
    border-radius: 10px;
    padding: 1rem;
    border: 1px solid #e2e8f0;
}

footer {
    font-size: 0.75rem;
    color: #9ca3af;
    text-align: center;
    margin-top: 3rem;
    padding-top: 1rem;
    border-top: 1px solid #e5e7eb;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────

def calcul_mensualite(capital, taux_annuel, duree_annees):
    t = taux_annuel / 12
    n = duree_annees * 12
    if t == 0:
        return capital / n
    return capital * t * (1 + t)**n / ((1 + t)**n - 1)

def tableau_emprunt_annuel(capital, taux_annuel, duree_annees, duree_detention):
    t = taux_annuel / 12
    n_total = duree_annees * 12
    mensualite = calcul_mensualite(capital, taux_annuel, duree_annees)

    resultats = []
    k_restant = capital
    for annee in range(1, duree_detention + 1):
        interets_annee = 0
        capital_rembourse_annee = 0
        for mois in range(1, 13):
            mois_global = (annee - 1) * 12 + mois
            if mois_global > n_total:
                break
            interet_mois = k_restant * t
            capital_mois = mensualite - interet_mois
            interets_annee += interet_mois
            capital_rembourse_annee += capital_mois
            k_restant -= capital_mois
        resultats.append({
            'annee': annee,
            'mensualite': mensualite,
            'capital': capital_rembourse_annee,
            'interets': interets_annee,
            'k_restant': max(0, k_restant)
        })
    return resultats, mensualite

def amortissement_lmnp(prix_acquisition, frais_notaire_pct=0.075, qp_terrain=0.15):
    prix_avec_notaire = prix_acquisition * (1 + frais_notaire_pct)
    base_amortissable = prix_avec_notaire * (1 - qp_terrain)

    composants = [
        {'nom': 'Gros œuvre',       'pct': 0.50, 'duree': 50},
        {'nom': 'Façade/Étanchéité','pct': 0.10, 'duree': 25},
        {'nom': 'Équipement IGT',   'pct': 0.20, 'duree': 15},
        {'nom': 'Agencements',      'pct': 0.20, 'duree': 10},
    ]

    amort_annuel = sum(base_amortissable * c['pct'] / c['duree'] for c in composants)
    return amort_annuel, prix_avec_notaire

def quotient_familial(situation, nb_enfants):
    base = 2.0 if situation == "Couple marié ou pacsé" else 1.0
    demi_parts_supp = nb_enfants  # simplification: 0.5 par enfant → 1 part par enfant
    return base + demi_parts_supp * 0.5

def calcul_ir_tranche(revenu_imposable):
    """Calcul IR France 2024 sur revenu par part"""
    tranches = [
        (11294, 0.0),
        (28797, 0.11),
        (82341, 0.30),
        (177106, 0.41),
        (float('inf'), 0.45),
    ]
    ir = 0
    precedent = 0
    for plafond, taux in tranches:
        if revenu_imposable <= precedent:
            break
        tranche = min(revenu_imposable, plafond) - precedent
        ir += tranche * taux
        precedent = plafond
    return max(0, ir)

def calcul_ir_lmnp_annuel(resultat_lmnp, autres_revenus, situation, nb_enfants):
    qf = quotient_familial(situation, nb_enfants)
    nb_parts = qf

    rev_par_part_sans = autres_revenus / nb_parts
    ir_sans = calcul_ir_tranche(rev_par_part_sans) * nb_parts

    if resultat_lmnp >= 0:
        rev_avec = autres_revenus + resultat_lmnp
    else:
        rev_avec = autres_revenus
    rev_par_part_avec = rev_avec / nb_parts
    ir_avec = calcul_ir_tranche(rev_par_part_avec) * nb_parts

    demi_parts_supp = nb_enfants * 0.5 * 2
    plafond_economie = demi_parts_supp * 1759 * 2

    ir_base = calcul_ir_tranche(autres_revenus / (2 if situation == "Couple marié ou pacsé" else 1))
    if situation == "Couple marié ou pacsé":
        ir_base *= 2

    return max(0, ir_avec - ir_sans)

def abattement_pv_ir(duree):
    if duree <= 5:
        return 0.0
    elif duree <= 21:
        return (duree - 5) * 0.06
    else:
        return min(1.0, 0.96 + (duree - 22) * 0.04)

def abattement_pv_ps(duree):
    if duree <= 5:
        return 0.0
    elif duree <= 21:
        return (duree - 5) * 0.0165
    elif duree <= 30:
        return 0.28 + (duree - 22) * 0.09
    else:
        return 1.0

def surtaxe_pv(pv_nette_imposable):
    if pv_nette_imposable <= 50000:
        return 0
    elif pv_nette_imposable <= 60000:
        return 0.02 * pv_nette_imposable - (60000 - pv_nette_imposable) * 0.05
    elif pv_nette_imposable <= 100000:
        return 0.02 * pv_nette_imposable
    elif pv_nette_imposable <= 110000:
        return 0.03 * pv_nette_imposable - (110000 - pv_nette_imposable) * 0.1
    elif pv_nette_imposable <= 150000:
        return 0.03 * pv_nette_imposable
    elif pv_nette_imposable <= 160000:
        return 0.04 * pv_nette_imposable - (160000 - pv_nette_imposable) * 0.15
    elif pv_nette_imposable <= 200000:
        return 0.04 * pv_nette_imposable
    elif pv_nette_imposable <= 210000:
        return 0.05 * pv_nette_imposable - (210000 - pv_nette_imposable) * 0.20
    elif pv_nette_imposable <= 250000:
        return 0.05 * pv_nette_imposable
    elif pv_nette_imposable <= 260000:
        return 0.06 * pv_nette_imposable - (260000 - pv_nette_imposable) * 0.25
    else:
        return 0.06 * pv_nette_imposable

# ─────────────────────────────────────────────
# CORE SIMULATION
# ─────────────────────────────────────────────

def simuler(prix_acq, loyer_annuel, charges_annuelles, duree_detention,
            prix_revente, montant_emprunt, duree_emprunt, taux_taeg,
            autres_revenus, situation, nb_enfants):

    frais_notaire = prix_acq * 0.075
    apport = prix_acq + frais_notaire - montant_emprunt
    amort_annuel, prix_avec_notaire = amortissement_lmnp(prix_acq)
    emprunt_data, mensualite = tableau_emprunt_annuel(montant_emprunt, taux_taeg, duree_emprunt, duree_detention)

    # ── LMNP ──────────────────────────────────────────
    lmnp_rows = []
    cumul_amort_differe = 0

    for i, emp in enumerate(emprunt_data):
        annee = emp['annee']
        interets = emp['interets']
        loyers = loyer_annuel
        charges = charges_annuelles

        resultat_avant_amort = loyers - charges - interets
        if resultat_avant_amort > 0:
            amort_deductible = amort_annuel
        else:
            amort_deductible = resultat_avant_amort + amort_annuel
            if amort_deductible < 0:
                amort_deductible = 0

        resultat_fiscal = loyers - charges - interets - amort_deductible
        amort_differe_cree = max(0, amort_annuel - amort_deductible)

        if resultat_fiscal > 0 and cumul_amort_differe > 0:
            amort_differe_utilise = min(resultat_fiscal, cumul_amort_differe)
        else:
            amort_differe_utilise = 0

        cumul_amort_differe += amort_differe_cree - amort_differe_utilise
        resultat_lmnp_def = resultat_fiscal - amort_differe_utilise

        ir_immo = calcul_ir_lmnp_annuel(resultat_lmnp_def, autres_revenus, situation, nb_enfants)

        lmnp_rows.append({
            'annee': annee,
            'loyers': loyers,
            'charges': charges,
            'interets': interets,
            'amort': amort_annuel,
            'amort_deductible': amort_deductible,
            'resultat_fiscal': resultat_fiscal,
            'amort_differe': cumul_amort_differe,
            'resultat_lmnp': resultat_lmnp_def,
            'ir': ir_immo,
            'cash_net': loyers - charges - emp['mensualite'] * 12 - ir_immo,
        })

    df_lmnp = pd.DataFrame(lmnp_rows)

    # Plus-value LMNP
    forfait_travaux = prix_acq * 0.15 if duree_detention > 5 else 0
    pv_brute_ir = max(0, prix_revente - prix_acq * 1.075 - forfait_travaux + df_lmnp['amort_differe'].iloc[-1] + cumul_amort_differe)
    abatt_ir = abattement_pv_ir(duree_detention)
    abatt_ps = abattement_pv_ps(duree_detention)
    pv_imposable_ir = pv_brute_ir * (1 - abatt_ir)
    pv_imposable_ps = pv_brute_ir * (1 - abatt_ps)
    impot_pv_ir = pv_imposable_ir * 0.19
    ps_pv = pv_imposable_ps * 0.172
    surtaxe = surtaxe_pv(pv_imposable_ir)
    impot_pv_total_lmnp = impot_pv_ir + ps_pv + surtaxe
    pv_nette_lmnp = prix_revente - impot_pv_total_lmnp - emprunt_data[-1]['k_restant']

    solde_cash_lmnp = df_lmnp['cash_net'].sum()
    net_lmnp = solde_cash_lmnp + pv_nette_lmnp - apport

    # ── SCI IS ────────────────────────────────────────
    sci_rows = []
    cumul_resultats_sci = 0
    IS_TAUX_REDUIT = 0.15
    IS_TAUX_NORMAL = 0.25
    IS_SEUIL = 42500

    for i, emp in enumerate(emprunt_data):
        annee = emp['annee']
        interets = emp['interets']
        loyers = loyer_annuel
        charges = charges_annuelles

        resultat_avant_is = loyers - charges - interets - amort_annuel
        deficit_report = min(0, cumul_resultats_sci)

        resultat_imposable = resultat_avant_is
        if resultat_imposable > 0 and deficit_report < 0:
            utilisation = min(resultat_imposable, -deficit_report)
            resultat_imposable -= utilisation

        if resultat_imposable <= 0:
            is_annuel = 0
        elif resultat_imposable <= IS_SEUIL:
            is_annuel = resultat_imposable * IS_TAUX_REDUIT
        else:
            is_annuel = IS_SEUIL * IS_TAUX_REDUIT + (resultat_imposable - IS_SEUIL) * IS_TAUX_NORMAL

        cumul_resultats_sci += resultat_avant_is - is_annuel

        sci_rows.append({
            'annee': annee,
            'loyers': loyers,
            'charges': charges,
            'interets': interets,
            'amort': amort_annuel,
            'resultat_avant_is': resultat_avant_is,
            'is': is_annuel,
            'cash_net': loyers - charges - emp['mensualite'] * 12 - is_annuel,
        })

    df_sci = pd.DataFrame(sci_rows)

    # Plus-value SCI IS
    valeur_nette_comptable = prix_acq * 1.075 - amort_annuel * duree_detention
    pv_brute_is = max(0, prix_revente - valeur_nette_comptable)
    resultat_distribuable = cumul_resultats_sci + pv_brute_is

    if resultat_distribuable <= 0:
        is_cession = 0
        flat_tax = 0
    elif pv_brute_is <= 0:
        is_cession = 0
        flat_tax = 0
    else:
        if pv_brute_is <= IS_SEUIL:
            is_cession = pv_brute_is * IS_TAUX_REDUIT
        else:
            is_cession = IS_SEUIL * IS_TAUX_REDUIT + (pv_brute_is - IS_SEUIL) * IS_TAUX_NORMAL

        dividendes = max(0, resultat_distribuable - is_cession)
        flat_tax = max(0, -dividendes * 0.30)

    k_restant = emprunt_data[-1]['k_restant']
    pv_nette_is = prix_revente - is_cession - flat_tax - k_restant

    solde_cash_sci = df_sci['cash_net'].sum()
    net_sci = solde_cash_sci + pv_nette_is - apport

    return {
        'lmnp': {
            'df': df_lmnp,
            'net_total': net_lmnp,
            'solde_cash': solde_cash_lmnp,
            'pv_nette': pv_nette_lmnp,
            'impot_pv': impot_pv_total_lmnp,
            'total_ir': df_lmnp['ir'].sum(),
            'mensualite': mensualite,
        },
        'sci': {
            'df': df_sci,
            'net_total': net_sci,
            'solde_cash': solde_cash_sci,
            'pv_nette': pv_nette_is,
            'total_is': df_sci['is'].sum(),
            'is_cession': is_cession,
            'flat_tax': flat_tax,
            'mensualite': mensualite,
        },
        'apport': apport,
        'frais_notaire': frais_notaire,
        'amort_annuel': amort_annuel,
        'emprunt_data': emprunt_data,
    }

# ─────────────────────────────────────────────
# SIDEBAR — INPUTS
# ─────────────────────────────────────────────

with st.sidebar:
    st.markdown("### 🏠 Acquisition")
    prix_acq = st.number_input("Valeur d'acquisition (€) *", value=260000, step=5000, min_value=50000,
        help="Prix d'achat incluant travaux, hors frais de notaire")
    loyer_annuel = st.number_input("Loyer annuel (€)", value=15000, step=500, min_value=0)
    charges_annuelles = st.number_input("Charges annuelles (€) *", value=5600, step=100, min_value=0,
        help="Copropriété, taxe foncière, assurance — hors intérêts d'emprunt")
    duree_detention = st.slider("Durée de détention (années)", 1, 30, 10)
    prix_revente = st.number_input("Valeur prévisionnelle de revente (€)", value=320000, step=5000)

    st.markdown("### 💰 Financement")
    montant_emprunt = st.number_input("Montant de l'emprunt (€)", value=235000, step=5000, min_value=0)
    duree_emprunt = st.slider("Durée de l'emprunt (années)", 5, 30, 20)
    taux_taeg = st.number_input("Taux TAEG (%)", value=3.0, step=0.05, min_value=0.1, max_value=15.0) / 100

    st.markdown("### 👤 Situation fiscale")
    autres_revenus = st.number_input("Autres revenus nets imposables (€)", value=60000, step=1000, min_value=0)
    situation = st.selectbox("Situation", ["Couple marié ou pacsé", "Célibataire, divorcé ou veuf"])
    nb_enfants = st.selectbox("Enfants à charge", [0, 1, 2, 3, 4], index=2)

    st.markdown("---")
    st.caption("*(1) Frais de notaire estimés à 7,5% — amortissement sur base décomposée (terrain 15%)*")
    st.caption("*(2) Copropriété, taxe foncière, assurance*")

# ─────────────────────────────────────────────
# RUN SIMULATION
# ─────────────────────────────────────────────

results = simuler(
    prix_acq, loyer_annuel, charges_annuelles, duree_detention,
    prix_revente, montant_emprunt, duree_emprunt, taux_taeg,
    autres_revenus, situation, nb_enfants
)

lmnp = results['lmnp']
sci = results['sci']
apport = results['apport']

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────

st.markdown('<div class="main-title">Simulateur LMNP vs SCI à l\'IS</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Artae Immobilier — Conseil en investissement locatif clé en main • Nord-Pas-de-Calais</div>', unsafe_allow_html=True)

st.markdown('<div class="info-box">⚠️ Chaque situation reste particulière. Ce simulateur repose sur des hypothèses fiscales générales. Consultez un expert-comptable pour une analyse personnalisée.</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# RÉSULTATS PRINCIPAUX
# ─────────────────────────────────────────────

winner_lmnp = lmnp['net_total'] >= sci['net_total']
delta = abs(lmnp['net_total'] - sci['net_total'])

col1, col2, col3 = st.columns([2, 2, 1])

with col1:
    card_class = "result-card winner" if winner_lmnp else "result-card"
    badge = " 🏆 Meilleure option" if winner_lmnp else ""
    st.markdown(f"""
    <div class="{card_class}">
        <div class="result-label">LMNP — Net perçu sur {duree_detention} ans{badge}</div>
        <div class="result-value">{lmnp['net_total']:+,.0f} €</div>
        <div class="result-delta">Cash exploitation : {lmnp['solde_cash']:+,.0f} € &nbsp;|&nbsp; PV nette : {lmnp['pv_nette']:+,.0f} €</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    card_class = "result-card winner" if not winner_lmnp else "result-card"
    badge = " 🏆 Meilleure option" if not winner_lmnp else ""
    st.markdown(f"""
    <div class="{card_class}">
        <div class="result-label">SCI à l'IS — Net perçu sur {duree_detention} ans{badge}</div>
        <div class="result-value">{sci['net_total']:+,.0f} €</div>
        <div class="result-delta">Cash exploitation : {sci['solde_cash']:+,.0f} € &nbsp;|&nbsp; PV nette : {sci['pv_nette']:+,.0f} €</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    apport_val = apport
    mensualite = results['lmnp']['mensualite']
    rentabilite_brute = (loyer_annuel / prix_acq) * 100
    st.metric("Apport nécessaire", f"{apport_val:,.0f} €")
    st.metric("Mensualité", f"{mensualite:,.0f} €")
    st.metric("Renta. brute", f"{rentabilite_brute:.2f} %")

st.markdown(f"**Écart LMNP vs SCI à l'IS : {delta:,.0f} € en faveur de {'LMNP' if winner_lmnp else 'SCI à l\\'IS'}**")

# ─────────────────────────────────────────────
# GRAPHIQUES
# ─────────────────────────────────────────────

st.markdown('<div class="section-header">📊 Analyse comparative</div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["Cash-flow annuel", "Cumul trésorerie", "Détail par année"])

with tab1:
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name='LMNP — Cash net',
        x=lmnp['df']['annee'],
        y=lmnp['df']['cash_net'],
        marker_color=['#1b6ca8' if v >= 0 else '#ef4444' for v in lmnp['df']['cash_net']],
        opacity=0.85,
    ))
    fig.add_trace(go.Bar(
        name="SCI à l'IS — Cash net",
        x=sci['df']['annee'],
        y=sci['df']['cash_net'],
        marker_color=['#10b981' if v >= 0 else '#f97316' for v in sci['df']['cash_net']],
        opacity=0.85,
    ))
    fig.add_hline(y=0, line_dash="dash", line_color="gray", line_width=1)
    fig.update_layout(
        barmode='group',
        title="Cash-flow net annuel après remboursement emprunt et impôts",
        xaxis_title='Année',
        yaxis_title='€',
        plot_bgcolor='white',
        paper_bgcolor='white',
        font_family='DM Sans',
        legend=dict(orientation='h', yanchor='bottom', y=1.02),
        height=380,
    )
    fig.update_xaxes(tickmode='linear', dtick=1)
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    cumul_lmnp = lmnp['df']['cash_net'].cumsum()
    cumul_sci = sci['df']['cash_net'].cumsum()

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=lmnp['df']['annee'], y=cumul_lmnp,
        mode='lines+markers', name='LMNP cumulé',
        line=dict(color='#1b6ca8', width=2.5),
        marker=dict(size=6),
    ))
    fig2.add_trace(go.Scatter(
        x=sci['df']['annee'], y=cumul_sci,
        mode='lines+markers', name="SCI à l'IS cumulé",
        line=dict(color='#10b981', width=2.5),
        marker=dict(size=6),
    ))
    fig2.add_hline(y=0, line_dash="dash", line_color="#9ca3af", line_width=1)
    fig2.update_layout(
        title='Trésorerie cumulée sur la période de détention (hors cession)',
        xaxis_title='Année', yaxis_title='€',
        plot_bgcolor='white', paper_bgcolor='white',
        font_family='DM Sans',
        legend=dict(orientation='h', yanchor='bottom', y=1.02),
        height=380,
    )
    fig2.update_xaxes(tickmode='linear', dtick=1)
    st.plotly_chart(fig2, use_container_width=True)

with tab3:
    col_l, col_s = st.columns(2)
    with col_l:
        st.markdown("**LMNP — Détail annuel**")
        df_display_l = lmnp['df'][['annee', 'loyers', 'charges', 'interets', 'amort', 'ir', 'cash_net']].copy()
        df_display_l.columns = ['Année', 'Loyers', 'Charges', 'Intérêts', 'Amort.', 'IR', 'Cash net']
        df_display_l = df_display_l.set_index('Année')
        st.dataframe(df_display_l.style.format("{:,.0f} €").applymap(
            lambda v: 'color: #ef4444' if isinstance(v, str) and v.startswith('-') else ''
        ), height=350)
    with col_s:
        st.markdown("**SCI à l'IS — Détail annuel**")
        df_display_s = sci['df'][['annee', 'loyers', 'charges', 'interets', 'amort', 'is', 'cash_net']].copy()
        df_display_s.columns = ['Année', 'Loyers', 'Charges', 'Intérêts', 'Amort.', 'IS', 'Cash net']
        df_display_s = df_display_s.set_index('Année')
        st.dataframe(df_display_s.style.format("{:,.0f} €"), height=350)

# ─────────────────────────────────────────────
# SYNTHÈSE FISCALE
# ─────────────────────────────────────────────

st.markdown('<div class="section-header">🧮 Synthèse fiscale & Plus-value</div>', unsafe_allow_html=True)

col_a, col_b, col_c, col_d = st.columns(4)
col_a.metric("IR total LMNP", f"{lmnp['total_ir']:,.0f} €", delta=None)
col_b.metric("IS total SCI à l'IS", f"{sci['total_is']:,.0f} €", delta=None)
col_c.metric("Impôt PV LMNP (IR+PS+surtaxe)", f"{lmnp['impot_pv']:,.0f} €", delta=None)
col_d.metric("IS cession + Flat tax SCI", f"{sci['is_cession'] + sci['flat_tax']:,.0f} €", delta=None)

col_e, col_f, col_g, col_h = st.columns(4)
col_e.metric("Amort. annuel LMNP", f"{results['amort_annuel']:,.0f} €/an")
col_f.metric("Frais de notaire estimés", f"{results['frais_notaire']:,.0f} €")
col_g.metric("Capital restant dû (fin)", f"{results['emprunt_data'][-1]['k_restant']:,.0f} €")
col_h.metric("Loyer mensuel estimé", f"{loyer_annuel/12:,.0f} €/mois")

# ─────────────────────────────────────────────
# GRAPHIQUE CAMEMBERT COMPARATIF
# ─────────────────────────────────────────────

st.markdown('<div class="section-header">💡 Répartition des flux sur la durée</div>', unsafe_allow_html=True)

col_p1, col_p2 = st.columns(2)

with col_p1:
    labels_l = ['Loyers perçus', 'Charges payées', 'Intérêts emprunt', 'IR immobilier']
    vals_l = [
        lmnp['df']['loyers'].sum(),
        lmnp['df']['charges'].sum(),
        lmnp['df']['interets'].sum(),
        lmnp['df']['ir'].sum(),
    ]
    fig_pie_l = go.Figure(go.Pie(
        labels=labels_l, values=vals_l,
        hole=0.45,
        marker_colors=['#1b6ca8', '#94a3b8', '#f97316', '#ef4444'],
    ))
    fig_pie_l.update_layout(title='LMNP — Flux cumulés sur la période', font_family='DM Sans',
                            paper_bgcolor='white', height=320,
                            legend=dict(orientation='h', y=-0.1))
    st.plotly_chart(fig_pie_l, use_container_width=True)

with col_p2:
    labels_s = ['Loyers perçus', 'Charges payées', 'Intérêts emprunt', 'IS annuel']
    vals_s = [
        sci['df']['loyers'].sum(),
        sci['df']['charges'].sum(),
        sci['df']['interets'].sum(),
        sci['df']['is'].sum(),
    ]
    fig_pie_s = go.Figure(go.Pie(
        labels=labels_s, values=vals_s,
        hole=0.45,
        marker_colors=['#10b981', '#94a3b8', '#f97316', '#f59e0b'],
    ))
    fig_pie_s.update_layout(title="SCI à l'IS — Flux cumulés sur la période", font_family='DM Sans',
                             paper_bgcolor='white', height=320,
                             legend=dict(orientation='h', y=-0.1))
    st.plotly_chart(fig_pie_s, use_container_width=True)

# ─────────────────────────────────────────────
# AVERTISSEMENT CASH-FLOW NÉGATIF
# ─────────────────────────────────────────────

nb_annees_neg_lmnp = (lmnp['df']['cash_net'] < 0).sum()
nb_annees_neg_sci = (sci['df']['cash_net'] < 0).sum()

if nb_annees_neg_lmnp > 0 or nb_annees_neg_sci > 0:
    msg = "Remarque : sur la base des hypothèses renseignées, la trésorerie générée avec les loyers ne suffit pas à couvrir les charges, le remboursement de l'emprunt et l'impôt pendant "
    details = []
    if nb_annees_neg_lmnp > 0:
        details.append(f"{nb_annees_neg_lmnp} année(s) en LMNP")
    if nb_annees_neg_sci > 0:
        details.append(f"{nb_annees_neg_sci} année(s) en SCI à l'IS")
    st.markdown(f'<div class="warning-box">⚠️ {msg}{" et ".join(details)}. Un effort de trésorerie mensuel sera nécessaire.</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────

st.markdown("""
<footer>
    <strong>Artae Immobilier</strong> — Conseil en investissement locatif clé en main • Région Nord (Lille, Arras, Douai, Lens)<br>
    Simulateur à titre indicatif. Ne constitue pas un conseil fiscal ou juridique. © 2024
</footer>
""", unsafe_allow_html=True)
