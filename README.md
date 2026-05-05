# Pilotage RH par les coûts — Amazon Beta Mobile

Application Streamlit de pilotage de projet en temps réel.

## Structure

```
amazon_rh_app/
├── app.py          # Interface Streamlit principale
├── calculs.py      # Moteur de calcul : KPIs, Gantt Plotly, budget
├── data.py         # Données de référence (tâches, équipe, config)
├── requirements.txt
└── README.md
```

## Installation

```bash
# 1. Créer un environnement virtuel (recommandé)
python3 -m venv .venv
source .venv/bin/activate        # Linux / macOS
# .venv\Scripts\activate         # Windows

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Lancer l'application
streamlit run app.py
```

L'application s'ouvre sur http://localhost:8501

## Fonctionnalités

| Onglet    | Contenu                                                                |
|-----------|------------------------------------------------------------------------|
| Gantt     | Diagramme Plotly interactif, filtres catégorie/ressource/critique      |
| Tâches    | Édition inline de chaque tâche, ajout, suppression                     |
| Budget    | Décomposition par profil et module, modification des taux journaliers  |
| Équipe    | Gestion des 9 profils, ajout de ressources, stats de charge            |

## Réactivité

Toute modification (durée d'une tâche, taux journalier, ressource affectée)
déclenche un recalcul immédiat du Gantt, des KPIs et du budget.

Le bouton "Réinitialiser" (sidebar) restaure les données initiales du projet.
