import streamlit as st

# ─────────────────────────────────────────────
# CONFIGURATION DE LA PAGE
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Calculateur Cash-Flow Immo — David V.",
    page_icon="🏠",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Titre principal */
.main-title {
    font-size: 2rem;
    font-weight: 700;
    color: #111827;
    line-height: 1.2;
    margin-bottom: 0.25rem;
}

.subtitle {
    font-size: 0.95rem;
    color: #6b7280;
    font-weight: 400;
    margin-bottom: 0.5rem;
}

/* Section headers */
.section-title {
    font-size: 1.1rem;
    font-weight: 600;
    color: #1f2937;
    border-left: 4px solid #2563eb;
    padding-left: 0.75rem;
    margin-top: 1.75rem;
    margin-bottom: 0.75rem;
}

/* Carte résultat principale */
.result-main {
    border-radius: 14px;
    padding: 1.75rem 2rem;
    text-align: center;
    margin: 0.5rem 0;
}
.result-main.positive {
    background: linear-gradient(135deg, #065f46 0%, #059669 100%);
    color: white;
}
.result-main.negative {
    background: linear-gradient(135deg, #7f1d1d 0%, #dc2626 100%);
    color: white;
}
.result-main.neutral {
    background: linear-gradient(135deg, #1e3a5f 0%, #2563eb 100%);
    color: white;
}
.result-main-label {
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    opacity: 0.85;
    margin-bottom: 0.4rem;
}
.result-main-value {
    font-size: 3rem;
    font-weight: 700;
    line-height: 1;
}
.result-main-unit {
    font-size: 1.1rem;
    opacity: 0.9;
    margin-top: 0.2rem;
}

/* Cartes métriques secondaires */
.metric-card {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 1rem 1.2rem;
    text-align: center;
}
.metric-label {
    font-size: 0.75rem;
    color: #6b7280;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 0.3rem;
}
.metric-value {
    font-size: 1.35rem;
    font-weight: 600;
    color: #111827;
}
.metric-value.green { color: #059669; }
.metric-value.red   { color: #dc2626; }

/* Bouton CTA */
.cta-container {
    text-align: center;
    margin: 2rem 0 1rem 0;
}
.cta-btn {
    display: inline-block;
    background: #2563eb;
    color: white !important;
    font-weight: 600;
    font-size: 1rem;
    padding: 0.85rem 2rem;
    border-radius: 10px;
    text-decoration: none !important;
    letter-spacing: 0.01em;
    box-shadow: 0 4px 14px rgba(37, 99, 235, 0.35);
    transition: background 0.2s;
}
.cta-btn:hover {
    background: #1d4ed8;
    color: white !important;
}

/* Note info */
.note {
    font-size: 0.8rem;
    color: #9ca3af;
    margin-top: 0.25rem;
}

/* Ligne séparatrice résultats */
.divider {
    border: none;
    border-top: 1px solid #e5e7eb;
    margin: 1.25rem 0;
}

/* Écran email */
.email-card {
    max-width: 480px;
    margin: 3rem auto;
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 16px;
    padding: 2.5rem 2rem;
    box-shadow: 0 4px 24px rgba(0,0,0,0.06);
    text-align: center;
}
.email-title {
    font-size: 1.6rem;
    font-weight: 700;
    color: #111827;
    margin-bottom: 0.4rem;
}
.email-sub {
    font-size: 0.9rem;
    color: #6b7280;
    margin-bottom: 1.5rem;
}
.email-legal {
    font-size: 0.72rem;
    color: #9ca3af;
    margin-top: 1rem;
    line-height: 1.5;
}

footer {
    font-size: 0.73rem;
    color: #9ca3af;
    text-align: center;
    margin-top: 3rem;
    padding-top: 1rem;
    border-top: 1px solid #f0f0f0;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# FONCTIONS DE CALCUL
# ─────────────────────────────────────────────

def calcul_mensualite(emprunt: float, taeg_annuel: float, duree_ans: int) -> float:
    """Mensualité d'un prêt amortissable (formule standard)."""
    t = taeg_annuel / 12
    n = duree_ans * 12
    if t == 0 or emprunt <= 0:
        return emprunt / n if n > 0 else 0.0
    return emprunt * t / (1 - (1 + t) ** (-n))


def capital_restant_du(emprunt: float, taeg_annuel: float, duree_ans: int, annee_n: int) -> float:
    """Capital restant dû (CRD) après annee_n années."""
    t = taeg_annuel / 12
    n = duree_ans * 12
    k = annee_n * 12
    if t == 0 or emprunt <= 0:
        return max(0.0, emprunt * (1 - k / n)) if n > 0 else 0.0
    M = emprunt * t / (1 - (1 + t) ** (-n))
    crd = emprunt * (1 + t) ** k - M * ((1 + t) ** k - 1) / t
    return max(0.0, crd)


def capital_rembourse(emprunt: float, taeg_annuel: float, duree_ans: int, annee_n: int) -> float:
    """Capital remboursé à l'année N (différence avec CRD initial)."""
    if annee_n <= 0 or annee_n > duree_ans:
        return 0.0
    crd = capital_restant_du(emprunt, taeg_annuel, duree_ans, annee_n)
    return emprunt - crd


# ─────────────────────────────────────────────
# GESTION SESSION STATE
# ─────────────────────────────────────────────

if "access_granted" not in st.session_state:
    st.session_state.access_granted = False
if "user_email" not in st.session_state:
    st.session_state.user_email = ""

# ─────────────────────────────────────────────
# ÉCRAN EMAIL (GATE)
# ─────────────────────────────────────────────

if not st.session_state.access_granted:
    st.markdown("""
    <div class="email-card">
        <div class="email-title">🏠 Calculateur Cash-Flow Immo<br>Avant Impôt</div>
        <div class="email-sub">par David V., conseiller en investissement clé en main</div>
    </div>
    """, unsafe_allow_html=True)

    with st.form("email_form"):
        st.markdown("**Entrez votre email pour accéder gratuitement à l'outil :**")
        email_input = st.text_input(
            "Email",
            placeholder="vous@exemple.com",
            label_visibility="collapsed",
        )
        submitted = st.form_submit_button("Accéder au calculateur →", use_container_width=True, type="primary")

        if submitted:
            email_clean = email_input.strip()
            if "@" in email_clean and "." in email_clean.split("@")[-1]:
                st.session_state.user_email = email_clean
                st.session_state.access_granted = True
                st.rerun()
            else:
                st.error("Veuillez saisir une adresse email valide.")

    st.markdown(
        '<p class="email-legal">En renseignant votre email, vous acceptez d\'être recontacté par David V.</p>',
        unsafe_allow_html=True,
    )
    st.stop()

# ─────────────────────────────────────────────
# CALCULATEUR PRINCIPAL
# ─────────────────────────────────────────────

# ── En-tête ──────────────────────────────────
st.markdown('<div class="main-title">🏠 Calculateur Cash-Flow Immo<br>Avant Impôt</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">par David V. — investissement locatif clé en main • Nord-Pas-de-Calais</div>', unsafe_allow_html=True)

# ── Bouton CTA (en haut) ──────────────────────
st.markdown("""
<div class="cta-container">
    <a class="cta-btn" href="https://calendly.com/david-v" target="_blank">
        📅 Prendre rendez-vous avec David V. — Investissement clé en main
    </a>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ─────────────────────────────────────────────
# SECTION 1 — ACQUISITION
# ─────────────────────────────────────────────
st.markdown('<div class="section-title">1. Acquisition</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    prix_negocie = st.number_input(
        "Prix négocié FAI (€)",
        min_value=0, value=150_000, step=1_000,
        format="%d",
    )
    frais_notaire_pct = st.number_input(
        "Frais de notaire (%)",
        min_value=0.0, max_value=20.0, value=8.5, step=0.1,
        format="%.1f",
        help="Calculés automatiquement à 8,5% du prix négocié — modifiable",
    )
    frais_notaire = round(prix_negocie * frais_notaire_pct / 100)
    st.markdown(f"<div class='note'>→ Frais de notaire : <strong>{frais_notaire:,} €</strong></div>", unsafe_allow_html=True)

with col2:
    frais_dossier = st.number_input(
        "Frais de dossier bancaires (€)",
        min_value=0, value=750, step=50,
        format="%d",
    )
    travaux = st.number_input(
        "Montant des travaux (€)",
        min_value=0, value=0, step=1_000,
        format="%d",
    )
    mobilier = st.number_input(
        "Mobilier / Ameublement (€)",
        min_value=0, value=0, step=500,
        format="%d",
    )

# ─────────────────────────────────────────────
# SECTION 2 — FINANCEMENT
# ─────────────────────────────────────────────
st.markdown('<div class="section-title">2. Financement</div>', unsafe_allow_html=True)

col3, col4 = st.columns(2)

with col3:
    apport = st.number_input(
        "Apport (€)",
        min_value=0, value=0, step=1_000,
        format="%d",
    )
    duree_emprunt = st.number_input(
        "Durée d'emprunt (ans)",
        min_value=1, max_value=30, value=20, step=1,
        format="%d",
    )

with col4:
    taeg = st.number_input(
        "TAEG — taux tout compris assurance incluse (%)",
        min_value=0.0, max_value=20.0, value=3.5, step=0.05,
        format="%.2f",
    )

# Calculs financement
# Les frais de garantie dépendent de l'emprunt → on calcule en 2 passes
# Emprunt provisoire sans frais garantie pour amorcer le calcul
total_sans_garantie = prix_negocie + frais_notaire + frais_dossier + travaux + mobilier
emprunt_provisoire = max(0, total_sans_garantie - apport)
frais_garantie = round(emprunt_provisoire * 0.012)
total_projet = total_sans_garantie + frais_garantie
emprunt = max(0, total_projet - apport)
# 2e passe (frais garantie sur emprunt final — converge en 1 itération)
frais_garantie = round(emprunt * 0.012)
total_projet = total_sans_garantie + frais_garantie
emprunt = max(0, total_projet - apport)

taeg_decimal = taeg / 100
mensualite = calcul_mensualite(emprunt, taeg_decimal, duree_emprunt)

# Affichage récapitulatif financement
c_a, c_b, c_c, c_d = st.columns(4)
c_a.metric("Total Projet", f"{total_projet:,} €")
c_b.metric("Frais de garantie (1,2%)", f"{frais_garantie:,} €")
c_c.metric("Emprunt", f"{emprunt:,} €")
c_d.metric("Mensualité emprunt", f"{mensualite:,.0f} €/mois")

# ─────────────────────────────────────────────
# SECTION 3 — REVENUS
# ─────────────────────────────────────────────
st.markdown('<div class="section-title">3. Revenus</div>', unsafe_allow_html=True)

loyer_mensuel = st.number_input(
    "Loyer mensuel HC (€)",
    min_value=0, value=800, step=50,
    format="%d",
)
loyer_annuel = loyer_mensuel * 12

# ─────────────────────────────────────────────
# SECTION 4 — CHARGES ANNUELLES
# ─────────────────────────────────────────────
st.markdown('<div class="section-title">4. Charges annuelles</div>', unsafe_allow_html=True)

col5, col6 = st.columns(2)

with col5:
    gestion_pct = st.number_input(
        "Gestion locative (%)",
        min_value=0.0, max_value=30.0, value=0.0, step=0.5,
        format="%.1f",
        help="Appliqué sur le loyer annuel. Mettre 0 si gestion en direct.",
    )
    taxe_fonciere = st.number_input(
        "Taxe foncière (€/an)",
        min_value=0, value=800, step=50,
        format="%d",
    )
    assurance_pno = st.number_input(
        "Assurance PNO (€/an)",
        min_value=0, value=150, step=10,
        format="%d",
        help="150 €/lot habitation · 350 €/lot commerce",
    )
    st.markdown("<div class='note'>150 €/lot habitation — 350 €/lot commerce</div>", unsafe_allow_html=True)

with col6:
    charges_copro = st.number_input(
        "Charges de copropriété (€/an)",
        min_value=0, value=0, step=100,
        format="%d",
        help="0 € si maison individuelle",
    )
    charges_fluides = st.number_input(
        "Électricité / eau / internet (€/an)",
        min_value=0, value=0, step=100,
        format="%d",
        help="0 € si charges à la charge du locataire",
    )

# Calcul charges
gestion_montant = round(loyer_annuel * gestion_pct / 100)
total_charges = gestion_montant + taxe_fonciere + assurance_pno + charges_copro + charges_fluides

st.markdown(f"<div class='note'>→ Gestion locative : <strong>{gestion_montant:,} €/an</strong> &nbsp;|&nbsp; Total charges annuelles : <strong>{total_charges:,} €</strong></div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SECTION 5 — RÉSULTATS
# ─────────────────────────────────────────────
st.markdown('<div class="section-title">5. Résultats</div>', unsafe_allow_html=True)

# Calculs résultats
rendement_brut = (loyer_annuel / total_projet * 100) if total_projet > 0 else 0.0
rendement_net = ((loyer_annuel - total_charges) / total_projet * 100) if total_projet > 0 else 0.0
cashflow_mensuel = loyer_mensuel - mensualite - (total_charges / 12)

cap_10 = capital_rembourse(emprunt, taeg_decimal, duree_emprunt, 10) if duree_emprunt >= 10 else None
cap_20 = capital_rembourse(emprunt, taeg_decimal, duree_emprunt, 20) if duree_emprunt >= 20 else None

# Carte cashflow principal
cf_class = "positive" if cashflow_mensuel > 0 else ("negative" if cashflow_mensuel < 0 else "neutral")
cf_sign = "+" if cashflow_mensuel >= 0 else ""

st.markdown(f"""
<div class="result-main {cf_class}">
    <div class="result-main-label">Cash-flow mensuel net avant impôt</div>
    <div class="result-main-value">{cf_sign}{cashflow_mensuel:,.0f}</div>
    <div class="result-main-unit">€ / mois</div>
</div>
""", unsafe_allow_html=True)

# Métriques secondaires
st.markdown("<hr class='divider'>", unsafe_allow_html=True)

r1, r2 = st.columns(2)
with r1:
    rn_color = "green" if rendement_net >= 0 else "red"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Rendement brut</div>
        <div class="metric-value">{rendement_brut:.2f} %</div>
    </div>
    """, unsafe_allow_html=True)
with r2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Rendement net de charges</div>
        <div class="metric-value {rn_color}">{rendement_net:.2f} %</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='margin-top:0.75rem'></div>", unsafe_allow_html=True)

r3, r4 = st.columns(2)
with r3:
    val_10 = f"{cap_10:,.0f} €" if cap_10 is not None else "—"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Capital remboursé à 10 ans</div>
        <div class="metric-value">{val_10}</div>
    </div>
    """, unsafe_allow_html=True)
with r4:
    val_20 = f"{cap_20:,.0f} €" if cap_20 is not None else "—"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Capital remboursé à 20 ans</div>
        <div class="metric-value">{val_20}</div>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# CTA BAS DE PAGE
# ─────────────────────────────────────────────
st.markdown("""
<div class="cta-container" style="margin-top: 2.5rem;">
    <a class="cta-btn" href="https://calendly.com/david-v" target="_blank">
        📅 Prendre rendez-vous avec David V. — Investissement clé en main
    </a>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
st.markdown("""
<footer>
    David V. — Conseiller en investissement locatif clé en main · Nord-Pas-de-Calais<br>
    Simulateur indicatif avant impôt. Ne constitue pas un conseil fiscal ou financier.
</footer>
""", unsafe_allow_html=True)
