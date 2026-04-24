# Calculateur Cash-Flow Immo Avant Impôt

Application Streamlit de simulation de cash-flow immobilier avant impôt, par David V.

---

## Déploiement sur Streamlit Cloud (5 étapes)

### Prérequis
- Un compte GitHub (gratuit) → [github.com](https://github.com)
- Un compte Streamlit Cloud (gratuit) → [share.streamlit.io](https://share.streamlit.io)

---

### Étape 1 — Créer le dépôt GitHub

1. Connectez-vous sur [github.com](https://github.com)
2. Cliquez sur **"New repository"** (bouton vert en haut à droite)
3. Nom du repo : `cashflow-immo`
4. Visibilité : **Public**
5. Cliquez **"Create repository"**

---

### Étape 2 — Déposer les fichiers

Dans votre nouveau repo, uploadez ces 2 fichiers (bouton **"Add file" → "Upload files"**) :
- `app.py`
- `requirements.txt`

Cliquez **"Commit changes"** pour confirmer.

---

### Étape 3 — Connecter Streamlit Cloud

1. Rendez-vous sur [share.streamlit.io](https://share.streamlit.io)
2. Cliquez **"Sign in with GitHub"**
3. Autorisez l'accès à votre compte GitHub

---

### Étape 4 — Déployer l'application

1. Cliquez **"New app"**
2. Sélectionnez votre repo : `cashflow-immo`
3. Branch : `main`
4. Main file path : `app.py`
5. Cliquez **"Deploy!"**

Le déploiement prend 1 à 2 minutes.

---

### Étape 5 — Récupérer l'URL

Votre URL ressemblera à :
```
https://cashflow-immo.streamlit.app
```
ou
```
https://[votre-pseudo]-cashflow-immo-app-[id].streamlit.app
```

Partagez cette URL sur Instagram, ManyChat, etc.

---

## Personnalisation

### Lien Calendly

Dans `app.py`, remplacez les 2 occurrences de :
```
https://calendly.com/david-v
```
par votre vrai lien Calendly (ou autre outil de prise de rendez-vous).

---

## Lancer en local (optionnel)

```bash
pip install streamlit
streamlit run app.py
```

---

## Structure du projet

```
cashflow-immo/
├── app.py           # Application Streamlit
├── requirements.txt # Dépendances Python
└── README.md        # Ce fichier
```

---

## Fonctionnalités (V1)

- Écran email (gate d'accès)
- Section Acquisition avec calcul automatique frais de notaire et frais de garantie
- Section Financement avec calcul mensualité en temps réel
- Section Revenus & Charges
- Résultats en temps réel : cash-flow mensuel, rendement brut/net, capital remboursé à 10 et 20 ans
- Cash-flow affiché en vert (positif) ou rouge (négatif)
- Bouton de prise de rendez-vous
