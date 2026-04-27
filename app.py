import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import secrets as _secrets
from datetime import datetime

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
# GOOGLE SHEETS — CONNEXION ET OPÉRATIONS
# ─────────────────────────────────────────────

def get_gsheet():
    """Connexion à Google Sheets via le compte de service."""
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_info(
        st.secrets["google_service_account"],
        scopes=scopes,
    )
    client = gspread.authorize(creds)
    sheet = client.open_by_key(st.secrets["gsheets"]["sheet_id"])
    return sheet.worksheet("Emails")


def find_row_by_email(ws, email):
    """Retourne (row_index, row_data) ou (None, None) si introuvable."""
    try:
        cell = ws.find(email, in_column=1)
        if cell:
            return cell.row, ws.row_values(cell.row)
        return None, None
    except gspread.exceptions.CellNotFound:
        return None, None


def find_row_by_token(ws, token):
    """Retourne (row_index, row_data) ou (None, None) si introuvable."""
    try:
        cell = ws.find(token, in_column=5)
        if cell:
            return cell.row, ws.row_values(cell.row)
        return None, None
    except gspread.exceptions.CellNotFound:
        return None, None


def register_new_email(ws, email, token):
    """Ajoute une nouvelle ligne en_attente."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ws.append_row([email, now, "en_attente", "", token])


def update_token_for_row(ws, row_idx, token):
    """Met à jour le token pour une ligne existante (renvoi email)."""
    ws.update_cell(row_idx, 5, token)


def validate_email_by_token(ws, token):
    """Valide le token : met à jour statut + date. Retourne l'email ou None."""
    row_idx, row_data = find_row_by_token(ws, token)
    if row_idx is None:
        return None
    email = row_data[0] if row_data else ""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ws.update_cell(row_idx, 3, "validé")
    ws.update_cell(row_idx, 4, now)
    return email


# ─────────────────────────────────────────────
# ENVOI EMAIL DE VALIDATION
# ─────────────────────────────────────────────

def send_validation_email(recipient_email: str, token: str, app_url: str):
    """Envoie l'email de validation avec le lien d'activation."""
    activation_link = f"{app_url}?token={token}"
    sender = st.secrets["gmail"]["sender"]
    password = st.secrets["gmail"]["password"]

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "✅ Votre accès au Calculateur Cash-Flow Immo — par David V."
    msg["From"] = sender
    msg["To"] = recipient_email

    html = f"""
    <html>
    <body style="font-family:Arial,Helvetica,sans-serif;color:#222;max-width:560px;margin:0 auto;">
    <p>Bonjour,</p>
    <p>Merci pour votre inscription au <strong>Calculateur Cash-Flow Immo Avant Impôt</strong>.</p>
    <p>Cliquez sur le bouton ci-dessous pour valider votre email et accéder gratuitement à l'outil :</p>
    <p style="text-align:center;margin:2rem 0;">
      <a href="{activation_link}"
         style="background:#2563eb;color:white;padding:14px 28px;
                border-radius:8px;text-decoration:none;font-weight:bold;font-size:1rem;">
        ACCÉDER AU CALCULATEUR →
      </a>
    </p>
    <p style="font-size:0.85rem;color:#6b7280;">Ce lien est personnel et valable 48h.</p>
    <br>
    <p>À très vite,</p>
    <p>
      <strong>David V.</strong><br>
      Conseiller en investissement immobilier clé en main<br>
      Hauts-de-France
    </p>
    </body>
    </html>
    """
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, password)
        server.sendmail(sender, recipient_email, msg.as_string())


# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────

if "access_granted" not in st.session_state:
    st.session_state.access_granted = False
if "user_email" not in st.session_state:
    st.session_state.user_email = ""
if "token_just_validated" not in st.session_state:
    st.session_state.token_just_validated = False
if "validation_sent" not in st.session_state:
    st.session_state.validation_sent = False

# ─────────────────────────────────────────────
# VÉRIFICATION TOKEN DANS L'URL
# ─────────────────────────────────────────────

params = st.query_params
url_token = params.get("token", None)

if url_token and not st.session_state.access_granted:
    with st.spinner("Validation de votre email en cours…"):
        try:
            ws = get_gsheet()
            validated_email = validate_email_by_token(ws, url_token)
            if validated_email:
                st.session_state.access_granted = True
                st.session_state.user_email = validated_email
                st.session_state.token_just_validated = True
                st.query_params.clear()
                st.rerun()
            else:
                st.error("❌ Lien invalide ou déjà utilisé. Veuillez saisir votre email pour recevoir un nouveau lien.")
        except Exception as e:
            st.error(f"Erreur lors de la validation : impossible de contacter la base de données. Réessayez dans quelques instants.")

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

    # Affichage du message selon le statut en cours
    if st.session_state.validation_sent:
        st.success("📧 Un email de validation vous a été envoyé. Cliquez sur le lien pour accéder au calculateur.")
        st.info("Vous n'avez pas reçu l'email ? Vérifiez vos spams ou saisissez à nouveau votre adresse ci-dessous.")

    with st.form("email_form"):
        st.markdown("**Entrez votre email pour accéder gratuitement à l'outil :**")
        email_input = st.text_input(
            "Email",
            placeholder="vous@exemple.com",
            label_visibility="collapsed",
        )
        submitted = st.form_submit_button("Accéder au calculateur →", use_container_width=True, type="primary")

        if submitted:
            email_clean = email_input.strip().lower()
            if not ("@" in email_clean and "." in email_clean.split("@")[-1]):
                st.error("Veuillez saisir une adresse email valide.")
            else:
                app_url = st.secrets.get("app", {}).get("url", "https://votre-app.streamlit.app")
                try:
                    ws = get_gsheet()
                    row_idx, row_data = find_row_by_email(ws, email_clean)

                    if row_data:
                        statut = row_data[2] if len(row_data) > 2 else ""

                        if statut == "validé":
                            # CAS B — email validé → accès direct
                            st.session_state.user_email = email_clean
                            st.session_state.access_granted = True
                            st.rerun()
                        else:
                            # CAS C — email connu mais en_attente → renvoi
                            new_token = _secrets.token_urlsafe(32)
                            update_token_for_row(ws, row_idx, new_token)
                            send_validation_email(email_clean, new_token, app_url)
                            st.session_state.validation_sent = True
                            st.rerun()
                    else:
                        # CAS A — nouvel email → inscription + envoi
                        new_token = _secrets.token_urlsafe(32)
                        register_new_email(ws, email_clean, new_token)
                        send_validation_email(email_clean, new_token, app_url)
                        st.session_state.validation_sent = True
                        st.rerun()

                except smtplib.SMTPException as e:
                    st.error("Erreur lors de l'envoi de l'email. Veuillez réessayer dans quelques instants.")
                except Exception as e:
                    st.error("Erreur de connexion à la base de données. Veuillez réessayer dans quelques instants.")

    st.markdown(
        '<p class="email-legal">En renseignant votre email, vous acceptez d\'être recontacté par David V.</p>',
        unsafe_allow_html=True,
    )
    st.stop()

# ─────────────────────────────────────────────
# CALCULATEUR PRINCIPAL
# ─────────────────────────────────────────────

# Bandeau de confirmation si validation vient d'avoir lieu
if st.session_state.token_just_validated:
    st.success("✅ Email validé ! Bienvenue dans le calculateur.")
    st.session_state.token_just_validated = False

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
total_sans_garantie = prix_negocie + frais_notaire + frais_dossier + travaux + mobilier
emprunt_provisoire = max(0, total_sans_garantie - apport)
frais_garantie = round(emprunt_provisoire * 0.012)
total_projet = total_sans_garantie + frais_garantie
emprunt = max(0, total_projet - apport)
# 2e passe (convergence)
frais_garantie = round(emprunt * 0.012)
total_projet = total_sans_garantie + frais_garantie
emprunt = max(0, total_projet - apport)

taeg_decimal = taeg / 100
mensualite = calcul_mensualite(emprunt, taeg_decimal, duree_emprunt)

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

rendement_brut = (loyer_annuel / total_projet * 100) if total_projet > 0 else 0.0
rendement_net = ((loyer_annuel - total_charges) / total_projet * 100) if total_projet > 0 else 0.0
cashflow_mensuel = loyer_mensuel - mensualite - (total_charges / 12)

cap_10 = capital_rembourse(emprunt, taeg_decimal, duree_emprunt, 10) if duree_emprunt >= 10 else None
cap_20 = capital_rembourse(emprunt, taeg_decimal, duree_emprunt, 20) if duree_emprunt >= 20 else None

cf_class = "positive" if cashflow_mensuel > 0 else ("negative" if cashflow_mensuel < 0 else "neutral")
cf_sign = "+" if cashflow_mensuel >= 0 else ""

st.markdown(f"""
<div class="result-main {cf_class}">
    <div class="result-main-label">Cash-flow mensuel net avant impôt</div>
    <div class="result-main-value">{cf_sign}{cashflow_mensuel:,.0f}</div>
    <div class="result-main-unit">€ / mois</div>
</div>
""", unsafe_allow_html=True)

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
