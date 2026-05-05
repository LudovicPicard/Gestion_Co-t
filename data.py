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
    "nom": "Amazon Beta Mobile",
    "date_debut": "2025-09-01",   # format ISO, parseé par datetime
    "jours_par_semaine": 5,        # jours ouvrés par semaine
    "description": "Beta de l'application mobile Amazon — périmètre : recherche produit, panier, paiement, livraison.",
}

# ─────────────────────────────────────────────────────────────
# ÉQUIPE TECHNIQUE — 9 profils
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
    # taux_jour = (salaire_brut_jour) * (1 + taux_charges)
    # salaire_brut_jour = salaire_brut_annuel / jours_ouvres_par_an
    {"id": "PM",  "label": "Chef de projet",      "type": "CDI",       "statut": "Cadre",     "salaire_brut_annuel": 70000,  "couleur": "7F77DD"},
    {"id": "TL",  "label": "Tech Lead",            "type": "CDI",       "statut": "Cadre",     "salaire_brut_annuel": 80000,  "couleur": "534AB7"},
    {"id": "BE",  "label": "Dev Back-End",         "type": "CDI",       "statut": "ETAM",      "salaire_brut_annuel": 55000,  "couleur": "1D9E75"},
    {"id": "MOB", "label": "Dev Mobile",           "type": "CDI",       "statut": "ETAM",      "salaire_brut_annuel": 58000,  "couleur": "378ADD"},
    {"id": "UX",  "label": "UX Designer",          "type": "CDI",       "statut": "ETAM",      "salaire_brut_annuel": 52000,  "couleur": "BA7517"},
    {"id": "QA",  "label": "QA Engineer",          "type": "CDI",       "statut": "ETAM",      "salaire_brut_annuel": 48000,  "couleur": "D4537E"},
    {"id": "STG", "label": "Stagiaire Dev",        "type": "STAGIAIRE", "statut": "Stagiaire", "salaire_brut_annuel": 7800,   "couleur": "888780"},
    {"id": "ALT", "label": "Alternant Dev",        "type": "ALTERNANT", "statut": "Alternant", "salaire_brut_annuel": 18000,  "couleur": "B4B2A9"},
    {"id": "FRL", "label": "Freelance UX / Sécu", "type": "FREELANCE", "statut": "Freelance", "salaire_brut_annuel": 155000, "couleur": "E24B4A"},
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
    # ── Architecture ───────────────────────────────────────
    {"id":  1, "cat": "Architecture",    "nom": "Définition architecture technique",     "res": "TL",  "semaine": 1,  "duree": 3, "critique": True,  "deps": [],       "complexite": "Haute"},
    {"id":  2, "cat": "Architecture",    "nom": "Setup repo & CI/CD pipeline",           "res": "TL",  "semaine": 1,  "duree": 2, "critique": False, "deps": [],       "complexite": "Moyenne"},
    {"id":  3, "cat": "Architecture",    "nom": "Spécifications fonctionnelles",         "res": "STG", "semaine": 1,  "duree": 4, "critique": False, "deps": [],       "complexite": "Faible"},
    # ── Authentification ───────────────────────────────────
    {"id":  4, "cat": "Authentification","nom": "Maquettes UX login / register",         "res": "FRL", "semaine": 4,  "duree": 3, "critique": True,  "deps": [3],      "complexite": "Moyenne"},
    {"id":  5, "cat": "Authentification","nom": "API Auth (register, login, JWT)",       "res": "BE",  "semaine": 4,  "duree": 4, "critique": True,  "deps": [1],      "complexite": "Haute"},
    {"id":  6, "cat": "Authentification","nom": "Intégration OAuth (Google, Apple)",    "res": "BE",  "semaine": 6,  "duree": 3, "critique": False, "deps": [5],      "complexite": "Moyenne"},
    # ── Catalogue produits ─────────────────────────────────
    {"id":  7, "cat": "Catalogue",       "nom": "Modèle de données produits",            "res": "BE",  "semaine": 4,  "duree": 2, "critique": True,  "deps": [1],      "complexite": "Haute"},
    {"id":  8, "cat": "Catalogue",       "nom": "API recherche produits + filtres",      "res": "BE",  "semaine": 6,  "duree": 4, "critique": True,  "deps": [7],      "complexite": "Haute"},
    {"id":  9, "cat": "Catalogue",       "nom": "Écran liste produits (mobile)",         "res": "MOB", "semaine": 7,  "duree": 3, "critique": True,  "deps": [4, 8],   "complexite": "Moyenne"},
    {"id": 10, "cat": "Catalogue",       "nom": "Écran fiche produit détail",            "res": "MOB", "semaine": 8,  "duree": 3, "critique": True,  "deps": [9],      "complexite": "Moyenne"},
    {"id": 11, "cat": "Catalogue",       "nom": "Moteur de recommandations simplifié",   "res": "ALT", "semaine": 9,  "duree": 4, "critique": False, "deps": [8],      "complexite": "Haute"},
    # ── Panier / Commande ──────────────────────────────────
    {"id": 12, "cat": "Panier",          "nom": "API panier (CRUD)",                     "res": "BE",  "semaine": 8,  "duree": 3, "critique": True,  "deps": [5, 7],   "complexite": "Moyenne"},
    {"id": 13, "cat": "Panier",          "nom": "Écran panier & récap commande",         "res": "MOB", "semaine": 10, "duree": 3, "critique": True,  "deps": [10, 12], "complexite": "Moyenne"},
    {"id": 14, "cat": "Panier",          "nom": "Gestion des promotions / codes promo",  "res": "BE",  "semaine": 9,  "duree": 3, "critique": False, "deps": [12],     "complexite": "Faible"},
    # ── Paiement ───────────────────────────────────────────
    {"id": 15, "cat": "Paiement",        "nom": "Intégration Stripe / paiement carte",   "res": "FRL", "semaine": 10, "duree": 4, "critique": True,  "deps": [12],     "complexite": "Haute"},
    {"id": 16, "cat": "Paiement",        "nom": "Écran récap & confirmation paiement",   "res": "MOB", "semaine": 12, "duree": 2, "critique": True,  "deps": [13, 15], "complexite": "Moyenne"},
    {"id": 17, "cat": "Paiement",        "nom": "Audit sécurité flux paiement",          "res": "FRL", "semaine": 13, "duree": 2, "critique": True,  "deps": [15],     "complexite": "Haute"},
    # ── Livraison ──────────────────────────────────────────
    {"id": 18, "cat": "Livraison",       "nom": "API suivi livraison (carrier mock)",    "res": "BE",  "semaine": 10, "duree": 3, "critique": False, "deps": [12],     "complexite": "Moyenne"},
    {"id": 19, "cat": "Livraison",       "nom": "Écran suivi commande / livraison",      "res": "MOB", "semaine": 12, "duree": 2, "critique": False, "deps": [13, 18], "complexite": "Moyenne"},
    # ── Profil utilisateur ─────────────────────────────────
    {"id": 20, "cat": "Profil",          "nom": "API profil utilisateur (CRUD)",         "res": "BE",  "semaine": 6,  "duree": 2, "critique": False, "deps": [5],      "complexite": "Moyenne"},
    {"id": 21, "cat": "Profil",          "nom": "Écran profil, adresses, historique",    "res": "MOB", "semaine": 8,  "duree": 3, "critique": False, "deps": [4, 20],  "complexite": "Moyenne"},
    # ── QA / Tests ─────────────────────────────────────────
    {"id": 22, "cat": "QA",             "nom": "Tests unitaires back-end",              "res": "ALT", "semaine": 8,  "duree": 5, "critique": False, "deps": [5, 8, 12],"complexite": "Moyenne"},
    {"id": 23, "cat": "QA",             "nom": "Tests intégration & E2E",              "res": "QA",  "semaine": 11, "duree": 3, "critique": True,  "deps": [13, 16], "complexite": "Haute"},
    # ── DevOps / Infra ─────────────────────────────────────
    {"id": 24, "cat": "DevOps",          "nom": "Config environnements staging/prod",    "res": "TL",  "semaine": 6,  "duree": 2, "critique": False, "deps": [2],      "complexite": "Moyenne"},
    {"id": 25, "cat": "DevOps",          "nom": "Monitoring & alertes",                 "res": "STG", "semaine": 8,  "duree": 3, "critique": False, "deps": [24],     "complexite": "Faible"},
    # ── Lancement beta ─────────────────────────────────────
    {"id": 26, "cat": "Lancement",       "nom": "Beta testing interne & correction bugs","res": "QA",  "semaine": 13, "duree": 2, "critique": True,  "deps": [23, 17], "complexite": "Haute"},
    {"id": 27, "cat": "Lancement",       "nom": "Documentation technique",              "res": "STG", "semaine": 10, "duree": 4, "critique": False, "deps": [8, 12],  "complexite": "Faible"},
    {"id": 28, "cat": "Lancement",       "nom": "Préparation store (screenshots, copy)","res": "UX",  "semaine": 12, "duree": 2, "critique": False, "deps": [4],      "complexite": "Faible"},
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
# CONSTANTES DE PRÉSENTATION
# ─────────────────────────────────────────────────────────────

CATEGORIES = [
    "Architecture", "Authentification", "Catalogue",
    "Panier", "Paiement", "Livraison", "Profil",
    "QA", "DevOps", "Lancement",
]

CAT_COULEURS = {
    "Architecture":    "#534AB7",
    "Authentification":"#185FA5",
    "Catalogue":       "#0F6E56",
    "Panier":          "#BA7517",
    "Paiement":        "#D4537E",
    "Livraison":       "#378ADD",
    "Profil":          "#1D9E75",
    "QA":              "#E24B4A",
    "DevOps":          "#5F5E5A",
    "Lancement":       "#993C1D",
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
    "COMPLEXITE_COULEURS", "TYPE_RESSOURCE_OPTIONS",
]
