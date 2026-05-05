"""
Données de référence du projet Amazon Beta Mobile.

Choix technique : module Python pur (pas de JSON externe) pour simplifier
le déploiement et permettre l'import direct dans Streamlit sans I/O fichier.
Les structures sont des listes de dicts — compatibles pandas.DataFrame et
json.dumps pour la sérialisation en session state Streamlit.
"""

from copy import deepcopy

# ─────────────────────────────────────────────────────────────
# CONFIGURATION PROJET
# ─────────────────────────────────────────────────────────────

PROJECT_CONFIG = {
    "nom": "Book One (MVP)",
    "date_debut": "2025-01-01",
    "jours_par_semaine": 5,
    "description": "MVP Book One — Tous les livres à 1 €. Scan, Géoloc, Achat, P2P.",
}

# ─────────────────────────────────────────────────────────────
# COÛTS SATELLITES ET PROVISIONS (BUDGET GLOBAL)
# ─────────────────────────────────────────────────────────────

COUTS_SATELLITES = [
    # ── Infra & Cloud ──────────────────────────────────────────
    {"id": "SAT_AWS",  "nom": "Hébergement AWS (EC2)",              "montant": 3600, "categorie": "Infra & Cloud"},
    {"id": "SAT_RDS",  "nom": "Base de données (RDS/PostgreSQL)",   "montant": 1200, "categorie": "Infra & Cloud"},
    {"id": "SAT_S3",   "nom": "Stockage images (S3)",               "montant":  600, "categorie": "Infra & Cloud"},
    {"id": "SAT_CDN",  "nom": "CDN (CloudFront)",                   "montant":  400, "categorie": "Infra & Cloud"},
    {"id": "SAT_GEO",  "nom": "API Géolocalisation (Google Maps)",  "montant":  800, "categorie": "Infra & Cloud"},
    {"id": "SAT_FBK",  "nom": "Firebase (Notifications + Auth)",    "montant":  600, "categorie": "Infra & Cloud"},
    {"id": "SAT_STG",  "nom": "Environnement Staging",              "montant":  400, "categorie": "Infra & Cloud"},
    {"id": "SAT_CLD",  "nom": "Monitoring (Cloudwatch)",            "montant":  300, "categorie": "Infra & Cloud"},
    # ── Logiciels ──────────────────────────────────────────────
    {"id": "SAT_IDE",  "nom": "Licences IDE & Outils Dev",          "montant":  800, "categorie": "Logiciels"},
    {"id": "SAT_DES",  "nom": "Figma / Adobe XD / Miro",            "montant":  600, "categorie": "Logiciels"},
    {"id": "SAT_ISBN", "nom": "API Google Books (ISBN)",             "montant":  400, "categorie": "Logiciels"},
    # ── Outils de Gestion ──────────────────────────────────────
    {"id": "SAT_PM",   "nom": "Jira / Trello (Gestion projet)",     "montant":  400, "categorie": "Outils Gestion"},
    {"id": "SAT_COM",  "nom": "Slack / Notion (Communication)",     "montant":  240, "categorie": "Outils Gestion"},
    {"id": "SAT_GIT",  "nom": "Github / Gitlab (CI/CD Pipeline)",   "montant":  240, "categorie": "Outils Gestion"},
    # ── Paiement & Sécurité ────────────────────────────────────
    {"id": "SAT_STR",  "nom": "Stripe 1€/Transaction (commissions)","montant": 2000, "categorie": "Paiement & Sécurité"},
    {"id": "SAT_SSL",  "nom": "Certificat SSL",                     "montant":  150, "categorie": "Paiement & Sécurité"},
    {"id": "SAT_RGP",  "nom": "Conformité RGPD (audit)",            "montant": 1500, "categorie": "Paiement & Sécurité"},
    {"id": "SAT_SEC",  "nom": "Audit Sécurité",                     "montant": 2000, "categorie": "Paiement & Sécurité"},
    # ── Coûts Financiers ───────────────────────────────────────
    {"id": "SAT_ASS",  "nom": "Assurances Startup",                 "montant": 1200, "categorie": "Coûts Financiers"},
    {"id": "SAT_JUR",  "nom": "Frais Juridiques (CGU, mentions)",   "montant": 2500, "categorie": "Coûts Financiers"},
    {"id": "SAT_BAN",  "nom": "Frais Bancaires Stripe",             "montant":  300, "categorie": "Coûts Financiers"},
    # ── Communication & Marketing ──────────────────────────────
    {"id": "SAT_WEB",  "nom": "Site Web & Landing Page",            "montant": 2000, "categorie": "Communication & Marketing"},
    {"id": "SAT_ADS",  "nom": "Meta / Google Ads",                  "montant": 4000, "categorie": "Communication & Marketing"},
    {"id": "SAT_ASO",  "nom": "ASO App Store",                      "montant":  800, "categorie": "Communication & Marketing"},
    {"id": "SAT_BRA",  "nom": "Branding & Logo",                    "montant": 1500, "categorie": "Communication & Marketing"},
    {"id": "SAT_VID",  "nom": "Vidéo Démo",                         "montant": 2000, "categorie": "Communication & Marketing"},
    # ── Déploiement & Stores ───────────────────────────────────
    {"id": "SAT_APP",  "nom": "Apple App Store (99$/an)",           "montant":   99, "categorie": "Déploiement & Stores"},
    {"id": "SAT_GOO",  "nom": "Google Play (25$ one-shot)",         "montant":   25, "categorie": "Déploiement & Stores"},
    {"id": "SAT_MON",  "nom": "Monitoring Post-Launch",             "montant":  600, "categorie": "Déploiement & Stores"},
    # ── Tests & Qualité ────────────────────────────────────────
    {"id": "SAT_CYP",  "nom": "Outils Tests Cypress / TestFlight",  "montant":  600, "categorie": "Tests & Qualité"},
    {"id": "SAT_AUD",  "nom": "Audit Qualité Code",                 "montant": 1500, "categorie": "Tests & Qualité"},
]

PROVISION_RISQUE_PCT = 0.15 # 15% du budget total (RH + Satellites)

# ─────────────────────────────────────────────────────────────
# ÉQUIPE TECHNIQUE — 9 profils (noms issus du Mindmap)
#
# Champs :
#   id         : clé unique utilisée dans les tâches (champ `res`)
#   label      : nom affiché dans l'UI
#   type       : CDI | STAGIAIRE | ALTERNANT | FREELANCE
#   taux_jour  : coût journalier en euros (base de calcul budget)
#   couleur    : hex sans # pour Plotly
# ─────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────
# RÉFÉRENTIELS RH
# ─────────────────────────────────────────────────────────────

# Jours ouvrés de référence par an (base légale FR)
# CDI/ALTERNANT : 218 j (365 - 104 WE - 25 CP - 11 JF - 7 ponts)
# STAGIAIRE     : 151 j (convention 7 mois max / an)
# FREELANCE     : 200 j facturables typiques
JOURS_OUVRES_PAR_AN = {
    "CDI":       218,
    "STAGIAIRE": 151,
    "ALTERNANT": 218,
    "FREELANCE": 200,
}

# Statuts conventionnels et taux de charges patronales associés (base FR 2024).
# Cadre    : ~45 % (cotisations patronales hors prévoyance/retraite supplémentaire)
# ETAM     : ~42 % (Employés Techniciens Agents de Maîtrise)
# Ouvrier  : ~40 %
# Stagiaire: ~0 % (exonération totale si gratification ≤ plafond légal)
# Alternant: ~10 % (exonérations spécifiques contrat d'apprentissage)
# Freelance: ~0 % (pas de charges patronales — prestation de service)
STATUTS_CONVENTION = ["Cadre", "ETAM", "Ouvrier", "Stagiaire", "Alternant", "Freelance"]

TAUX_CHARGES_PATRONALES = {
    "Cadre":      0.45,
    "ETAM":       0.42,
    "Ouvrier":    0.40,
    "Stagiaire":  0.00,
    "Alternant":  0.10,
    "Freelance":  0.00,
}

# Correspondance type contrat → statut conventionnel par défaut
STATUT_DEFAULT_PAR_TYPE = {
    "CDI":       "Cadre",
    "STAGIAIRE": "Stagiaire",
    "ALTERNANT": "Alternant",
    "FREELANCE": "Freelance",
}

EQUIPE = [
    # ── Équipe Projet (Mindmap) ──────────────────────────────────
    {"id": "PM",  "label": "Sophie Lambert — Chef de Projet",    "type": "CDI",       "statut": "Cadre",     "salaire_brut_annuel": 70000,  "couleur": "7F77DD"},
    {"id": "TL",  "label": "Thomas Martin — Dev Senior Backend", "type": "CDI",       "statut": "Cadre",     "salaire_brut_annuel": 80000,  "couleur": "534AB7"},
    {"id": "MOB", "label": "Lucas Bernard — Dev Mobile",        "type": "FREELANCE", "statut": "Freelance", "salaire_brut_annuel": 120000, "couleur": "378ADD"},
    {"id": "ALT", "label": "Emma Dupont — Alternante Front-End", "type": "ALTERNANT", "statut": "Alternant", "salaire_brut_annuel": 18000,  "couleur": "B4B2A9"},
    {"id": "UX",  "label": "Hugo Petit — UX/UI Designer",       "type": "CDI",       "statut": "ETAM",      "salaire_brut_annuel": 52000,  "couleur": "BA7517"},
    {"id": "BE",  "label": "Julien Roux — DevOps Engineer",     "type": "CDI",       "statut": "ETAM",      "salaire_brut_annuel": 58000,  "couleur": "1D9E75"},
    {"id": "STG", "label": "Léa Moreau — Stagiaire QA",         "type": "STAGIAIRE", "statut": "Stagiaire", "salaire_brut_annuel": 7800,   "couleur": "888780"},
    # ── Consultants Externes (Mindmap) ──────────────────────────
    {"id": "MOE", "label": "Marc Fontaine — Consultant MOE",    "type": "FREELANCE", "statut": "Freelance", "salaire_brut_annuel": 150000, "couleur": "E24B4A"},
    {"id": "FRL", "label": "Julie Renard — Freelance Sécurité", "type": "FREELANCE", "statut": "Freelance", "salaire_brut_annuel": 120000, "couleur": "D4537E"},
]

# Index rapide : id -> dict ressource
EQUIPE_INDEX = {m["id"]: m for m in EQUIPE}


def calcul_taux_jour(membre: dict) -> int:
    """
    Taux journalier = (salaire_brut_annuel / jours_ouvres) * (1 + taux_charges).
    Arrondi à 10 € par excès pour rester conservateur.

    C'est le coût réel employeur par jour travaillé — c'est cette valeur
    qui alimente le calcul du budget projet, pas le salaire brut seul.
    """
    jours      = JOURS_OUVRES_PAR_AN.get(membre["type"], 218)
    taux_ch    = TAUX_CHARGES_PATRONALES.get(membre.get("statut", "ETAM"), 0.42)
    cout_jour  = (membre["salaire_brut_annuel"] / jours) * (1 + taux_ch)
    return max(1, round(cout_jour / 10) * 10)  # arrondi à 10 €

# ─────────────────────────────────────────────────────────────
# TÂCHES ÉLÉMENTAIRES — 28 tâches
#
# Champs :
#   id         : entier unique, utilisé pour les dépendances
#   cat        : catégorie fonctionnelle
#   nom        : libellé de la tâche
#   res        : id ressource (clé dans EQUIPE_INDEX)
#   semaine    : semaine de début (1 = semaine 1 du projet)
#   duree      : durée en semaines
#   critique   : bool — appartient au chemin critique
#   deps       : liste d'ids de tâches dont celle-ci dépend
#   complexite : Faible | Moyenne | Haute
# ─────────────────────────────────────────────────────────────

TACHES_DEFAULT = [
    # ── M1 — Cadrage & Architecture ──────────────────────────
    {"id":  1, "cat": "Cadrage & Architecture", "nom": "Specs fonctionnelles & backlog", "res": "PM",  "semaine": 1, "duree": 2, "critique": True,  "deps": [], "complexite": "Moyenne"},
    {"id":  2, "cat": "Cadrage & Architecture", "nom": "Architecture technique",         "res": "TL",  "semaine": 1, "duree": 2, "critique": True,  "deps": [], "complexite": "Haute"},
    {"id":  3, "cat": "Cadrage & Architecture", "nom": "Setup repo & CI/CD",             "res": "STG", "semaine": 3, "duree": 1, "critique": False, "deps": [2], "complexite": "Moyenne"},
    {"id":  4, "cat": "Cadrage & Architecture", "nom": "Config cloud",                   "res": "TL",  "semaine": 3, "duree": 1, "critique": False, "deps": [2], "complexite": "Moyenne"},
    
    # ── M2 — UX/UI & Maquettage ──────────────────────────────
    {"id":  5, "cat": "UX/UI & Maquettage", "nom": "Maquettes Auth & Catalogue",     "res": "UX",  "semaine": 2, "duree": 2, "critique": True,  "deps": [1], "complexite": "Moyenne"},
    {"id":  6, "cat": "UX/UI & Maquettage", "nom": "Maquettes Scan & Dépôt",         "res": "UX",  "semaine": 4, "duree": 2, "critique": False, "deps": [5], "complexite": "Moyenne"},
    {"id":  7, "cat": "UX/UI & Maquettage", "nom": "Maquettes Messagerie & Notifs",  "res": "UX",  "semaine": 6, "duree": 2, "critique": False, "deps": [6], "complexite": "Moyenne"},
    
    # ── M3 — Authentification & Compte ───────────────────────
    {"id":  8, "cat": "Authentification & Compte", "nom": "API Auth (register, login, JWT)", "res": "BE",  "semaine": 4, "duree": 2, "critique": True,  "deps": [2], "complexite": "Moyenne"},
    {"id":  9, "cat": "Authentification & Compte", "nom": "Mode invité catalogue",           "res": "MOB", "semaine": 4, "duree": 2, "critique": False, "deps": [5], "complexite": "Faible"},
    {"id": 19, "cat": "Authentification & Compte", "nom": "Écran Auth mobile",               "res": "MOB", "semaine": 6, "duree": 2, "critique": True,  "deps": [5, 8], "complexite": "Moyenne"},
    
    # ── M4 — Catalogue & Géolocalisation ─────────────────────
    {"id": 10, "cat": "Catalogue & Géolocalisation", "nom": "Modèle données livres",         "res": "BE",  "semaine": 4, "duree": 2, "critique": True,  "deps": [2], "complexite": "Moyenne"},
    {"id": 11, "cat": "Catalogue & Géolocalisation", "nom": "API catalogue + géoloc",        "res": "BE",  "semaine": 6, "duree": 3, "critique": True,  "deps": [10], "complexite": "Haute"},
    {"id": 13, "cat": "Catalogue & Géolocalisation", "nom": "API favoris (CRUD)",            "res": "STG", "semaine": 6, "duree": 2, "critique": False, "deps": [8], "complexite": "Faible"},
    {"id": 20, "cat": "Catalogue & Géolocalisation", "nom": "Écran catalogue mobile",        "res": "MOB", "semaine": 9, "duree": 3, "critique": True,  "deps": [11], "complexite": "Haute"},
    {"id": 22, "cat": "Catalogue & Géolocalisation", "nom": "Écran favoris mobile",          "res": "FRL", "semaine": 8, "duree": 2, "critique": False, "deps": [13], "complexite": "Moyenne"},
    
    # ── M5 — Scan & Dépôt de livres ──────────────────────────
    {"id": 12, "cat": "Scan & Dépôt de livres", "nom": "API scan ISBN + dépôt", "res": "ALT", "semaine": 6, "duree": 2, "critique": True,  "deps": [10], "complexite": "Haute"},
    {"id": 21, "cat": "Scan & Dépôt de livres", "nom": "Écran scan mobile",     "res": "MOB", "semaine": 8, "duree": 3, "critique": True,  "deps": [6, 12], "complexite": "Haute"},
    
    # ── M6 — Paiement & Transaction ──────────────────────────
    {"id": 15, "cat": "Paiement & Transaction", "nom": "API paiement Stripe (1€)",          "res": "FRL", "semaine": 8,  "duree": 3, "critique": True,  "deps": [8], "complexite": "Haute"},
    {"id": 16, "cat": "Paiement & Transaction", "nom": "API confirmation remise",           "res": "ALT", "semaine": 11, "duree": 2, "critique": True,  "deps": [15], "complexite": "Moyenne"},
    {"id": 24, "cat": "Paiement & Transaction", "nom": "Écran paiement mobile",             "res": "MOB", "semaine": 13, "duree": 2, "critique": True,  "deps": [15, 16], "complexite": "Moyenne"},
    
    # ── M7 — Messagerie & RDV ────────────────────────────────
    {"id": 14, "cat": "Messagerie & RDV", "nom": "API messagerie acheteur/vendeur", "res": "BE",  "semaine": 9,  "duree": 3, "critique": False, "deps": [8], "complexite": "Haute"},
    {"id": 23, "cat": "Messagerie & RDV", "nom": "Écran messagerie mobile",         "res": "MOB", "semaine": 11, "duree": 3, "critique": False, "deps": [7, 14], "complexite": "Moyenne"},
    
    # ── M8 — Notifications & Souhaits ────────────────────────
    {"id": 17, "cat": "Notifications & Souhaits", "nom": "API notifications push", "res": "BE",  "semaine": 11, "duree": 2, "critique": False, "deps": [10], "complexite": "Moyenne"},
    {"id": 18, "cat": "Notifications & Souhaits", "nom": "API souhaits livres",    "res": "STG", "semaine": 8,  "duree": 2, "critique": False, "deps": [10], "complexite": "Faible"},
    {"id": 25, "cat": "Notifications & Souhaits", "nom": "Écran souhaits & notifs","res": "MOB", "semaine": 13, "duree": 2, "critique": False, "deps": [17, 18], "complexite": "Moyenne"},
    
    # ── M9 — Tests & QA ──────────────────────────────────────
    {"id": 26, "cat": "Tests & QA", "nom": "Tests unitaires & intégration", "res": "ALT", "semaine": 14, "duree": 3, "critique": False, "deps": [11, 14, 15], "complexite": "Moyenne"},
    {"id": 27, "cat": "Tests & QA", "nom": "Beta testing & bugs",           "res": "STG",  "semaine": 16, "duree": 3, "critique": True,  "deps": [24, 25, 26], "complexite": "Haute"},
    
    # ── M10 — Déploiement ────────────────────────────────────
    {"id": 28, "cat": "Déploiement", "nom": "Déploiement iOS & Android", "res": "PM", "semaine": 19, "duree": 2, "critique": True, "deps": [27], "complexite": "Moyenne"},
]


def get_taches_default() -> list[dict]:
    """
    Retourne une copie profonde des tâches par défaut.
    Utilisé pour initialiser le session_state Streamlit sans mutation de la source.
    """
    return deepcopy(TACHES_DEFAULT)


def get_equipe_default() -> list[dict]:
    """Retourne une copie profonde de l'équipe par défaut."""
    return deepcopy(EQUIPE)


# ─────────────────────────────────────────────────────────────
# JALONS ET ÉTAPES DE CONTRÔLE (SIMULATION)
# ─────────────────────────────────────────────────────────────

ETAPES = {
    "Etape 1": {
        "nom": "Étape 1 — Kick-off (Semaine 5)",
        "semaine_fin": 5,
        "pct_avancement_simule": 0.18, 
        "retard_jours": 3,
        "couts_non_planifies": 4000,
        "details_risques": [
            {"risque": "Librairie OCR plus complexe que prévu", "impact_fin": 4000, "impact_tps": "0", "domaine": "Tech"},
            {"risque": "Refonte du flux d'onboarding Invité", "impact_fin": 0, "impact_tps": "+3 j", "domaine": "UX"}
        ],
        "meteo": {
            "PM": "☀️", "TL": "🌤️", "BE": "🌤️", "MOB": "☀️", "UX": "🌧️", 
            "STG": "☀️", "ALT": "⛈️", "FRL": "☀️"
        }
    },
    "Etape 2": {
        "nom": "Étape 2 — Mi-parcours (Semaine 10)",
        "semaine_fin": 10,
        "pct_avancement_simule": 0.40, 
        "retard_jours": 9,
        "couts_non_planifies": 15000, 
        "details_risques": [
            {"risque": "Lenteurs géolocalisation spatiale", "impact_fin": 6000, "impact_tps": "0", "domaine": "Tech"},
            {"risque": "Ajout des souhaits en urgence", "impact_fin": 5000, "impact_tps": "0", "domaine": "MOA"},
            {"risque": "Absence Alternant (partiels)", "impact_fin": 0, "impact_tps": "+6 j", "domaine": "RH"},
            {"risque": "Librairie OCR (Héritage étape 1)", "impact_fin": 4000, "impact_tps": "+0", "domaine": "Tech"}
        ],
        "meteo": {
            "PM": "🌤️", "TL": "⛈️", "BE": "🌧️", "MOB": "🌤️", "UX": "☀️", 
            "STG": "🌤️", "ALT": "⛈️", "FRL": "☀️"
        }
    },
    "Etape 3": {
        "nom": "Étape 3 — Livraison (Semaine 18)",
        "semaine_fin": 18,
        "pct_avancement_simule": 0.85, 
        "retard_jours": 16,
        "couts_non_planifies": 30500, 
        "details_risques": [
            {"risque": "Blocage KYC Stripe P2P", "impact_fin": 8000, "impact_tps": "0", "domaine": "Paiement"},
            {"risque": "Refus Apple Store", "impact_fin": 2500, "impact_tps": "+7 j", "domaine": "Store"},
            {"risque": "Desynchro WebSocket", "impact_fin": 5000, "impact_tps": "0", "domaine": "MOA"},
            {"risque": "Héritage (Risques précédents)", "impact_fin": 15000, "impact_tps": "0", "domaine": "Projet"}
        ],
        "meteo": {
            "PM": "🌧️", "TL": "⛈️", "BE": "⛈️", "MOB": "🌧️", "UX": "☀️", 
            "STG": "🌤️", "ALT": "☀️", "FRL": "🌧️"
        }
    }
}

# ─────────────────────────────────────────────────────────────
# CONSTANTES DE PRÉSENTATION
# ─────────────────────────────────────────────────────────────

CATEGORIES = [
    "Cadrage & Architecture", "UX/UI & Maquettage", "Authentification & Compte",
    "Catalogue & Géolocalisation", "Scan & Dépôt de livres", "Paiement & Transaction",
    "Messagerie & RDV", "Notifications & Souhaits", "Tests & QA", "Déploiement"
]

CAT_COULEURS = {
    "Cadrage & Architecture":    "#534AB7",
    "UX/UI & Maquettage":        "#BA7517",
    "Authentification & Compte": "#185FA5",
    "Catalogue & Géolocalisation":"#378ADD",
    "Scan & Dépôt de livres":    "#D4537E",
    "Paiement & Transaction":    "#0F6E56",
    "Messagerie & RDV":          "#1D9E75",
    "Notifications & Souhaits":  "#E24B4A",
    "Tests & QA":                "#888780",
    "Déploiement":               "#5F5E5A",
}

COMPLEXITE_OPTIONS = ["Faible", "Moyenne", "Haute"]
COMPLEXITE_COULEURS = {"Faible": "#1D9E75", "Moyenne": "#BA7517", "Haute": "#E24B4A"}
TYPE_RESSOURCE_OPTIONS = ["CDI", "STAGIAIRE", "ALTERNANT", "FREELANCE"]
# Réexporté pour usage dans app.py sans import circulaire
__all__ = [
    "PROJECT_CONFIG", "JOURS_OUVRES_PAR_AN", "STATUTS_CONVENTION",
    "TAUX_CHARGES_PATRONALES", "STATUT_DEFAULT_PAR_TYPE",
    "EQUIPE", "EQUIPE_INDEX", "TACHES_DEFAULT",
    "get_taches_default", "get_equipe_default", "calcul_taux_jour",
    "CATEGORIES", "CAT_COULEURS", "COMPLEXITE_OPTIONS",
    "COMPLEXITE_COULEURS", "TYPE_RESSOURCE_OPTIONS", "ETAPES",
]
