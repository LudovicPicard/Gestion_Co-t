import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

from calculs import calcul_cout_tache, calcul_jh_tache, date_fin_projet

# ─────────────────────────────────────────────────────────────
# DONNÉES SIMULÉES PAR ÉTAPE (JALONS)
# ─────────────────────────────────────────────────────────────

ETAPES = {
    "Etape 1": {
        "nom": "Étape 1 — Kick-off (Semaine 5)",
        "semaine_fin": 5,
        "pct_avancement_simule": 0.35, # 35% d'avancement
        "retard_jours": 2,
        "couts_non_planifies": 3500, # Retard Freelance
        "details_risques": [
            "🔴 **RH** : Freelance UX indisponible 1 sem. (+ 3 500 €)",
            "🟡 **Tech** : Migration auth plus longue que prévu (+ 2 jours)"
        ],
        "meteo": {
            "PM": "☀️", "TL": "🌤️", "BE": "🌤️", "MOB": "☀️", "UX": "🌧️", 
            "QA": "☀️", "STG": "☀️", "ALT": "☀️", "FRL": "⛈️"
        }
    },
    "Etape 2": {
        "nom": "Étape 2 — Mi-parcours (Semaine 9)",
        "semaine_fin": 9,
        "pct_avancement_simule": 0.65, # 65% d'avancement
        "retard_jours": 8,
        "couts_non_planifies": 16500, # 3500 + 8000 + 5000
        "details_risques": [
            "🔴 **MOA** : Demande changement spec panier (+ 8 000 €)",
            "🔴 **Tech** : Bug critique Stripe (+ 5 000 €)",
            "🟡 **RH** : Stagiaire arrêt maladie 2 sem. (+ 6 jours retard)"
        ],
        "meteo": {
            "PM": "🌤️", "TL": "⛈️", "BE": "🌧️", "MOB": "🌤️", "UX": "☀️", 
            "QA": "🌧️", "STG": "⛈️", "ALT": "🌤️", "FRL": "☀️"
        }
    },
    "Etape 3": {
        "nom": "Étape 3 — Livraison (Semaine 14)",
        "semaine_fin": 14,
        "pct_avancement_simule": 0.95, # 95% d'avancement (reste des bugs)
        "retard_jours": 15,
        "couts_non_planifies": 36000, # 16500 + 12000 + 1500 + 6000
        "details_risques": [
            "🔴 **Sécu** : Audit sécurité échoué (+ 12 000 €)",
            "🟡 **Store** : Refus Apple Store (+ 1 500 €, + 1 sem.)",
            "🔴 **MOA** : Recette MOA non conforme (+ 6 000 €)"
        ],
        "meteo": {
            "PM": "🌧️", "TL": "⛈️", "BE": "⛈️", "MOB": "🌧️", "UX": "☀️", 
            "QA": "⛈️", "STG": "🌤️", "ALT": "☀️", "FRL": "🌧️"
        }
    }
}

def build_dashboard_tab(taches, equipe_index, config):
    """
    Rendu du 5ème onglet (Dashboard Opérationnel)
    """
    st.markdown("## 📈 Dashboard Opérationnel - Suivi Budgétaire")
    st.markdown("Suivi des aléas, crises et KPIs clés à 3 étapes du projet.")
    
    # ── SÉLECTION DE L'ÉTAPE ───────────────────────────────────────
    etape_selectionnee = st.radio(
        "Sélectionnez une étape de contrôle :",
        options=list(ETAPES.keys()),
        format_func=lambda x: ETAPES[x]["nom"],
        horizontal=True
    )
    
    etape_data = ETAPES[etape_selectionnee]
    sem_actuelle = etape_data["semaine_fin"]
    
    st.divider()
    
    # ── CALCUL DES DONNÉES DE BASE POUR L'ÉTAPE ─────────────────────
    
    # 1. Tâches prévues vs achevées jusqu'à cette semaine
    taches_prevues_etape = [t for t in taches if t["semaine"] <= sem_actuelle]
    taches_achevees_reelles = [t for t in taches if t["semaine"] + t["duree"] - 1 <= sem_actuelle]
    
    nb_prevues = len(taches_prevues_etape)
    
    # On simule qu'à cause des retards, toutes les tâches prévues ne sont pas finies
    # On utilise le pct_avancement_simule pour déterminer les tâches réellement achevées
    nb_achevees_simule = int(len(taches) * etape_data["pct_avancement_simule"])
    # On borne pour ne pas dépasser le nombre de tâches du projet
    nb_achevees_simule = min(nb_achevees_simule, len(taches))
    
    # 2. Coûts planifiés totaux
    cout_planifie_total = sum(calcul_cout_tache(t, equipe_index, config["jours_par_semaine"]) for t in taches)
    
    # Coût planifié à date (au prorata des tâches)
    cout_planifie_date = sum(calcul_cout_tache(t, equipe_index, config["jours_par_semaine"]) for t in taches_prevues_etape)
    
    # 3. Coûts réels = Coût planifié des tâches achevées + coûts non planifiés (risques) + dérive
    couts_non_planifies = etape_data["couts_non_planifies"]
    cout_reel_total = cout_planifie_total + couts_non_planifies # Projection
    cout_reel_date = cout_planifie_date + couts_non_planifies
    
    # ── 10 KPIs ─────────────────────────────────────────────────────
    st.markdown("### 📊 Indicateurs de Performance (10 KPIs)")
    
    c1, c2, c3, c4 = st.columns(4)
    
    # KPI 1: % de tâches terminées
    pct_acheve = (nb_achevees_simule / nb_prevues * 100) if nb_prevues > 0 else 0
    c1.metric(
        "1. % Tâches terminées / prévues", 
        f"{pct_acheve:.1f}%",
        f"{nb_achevees_simule} achevées sur {nb_prevues} prévues"
    )
    
    # KPI 2: Jours d'avance / retard
    retard = etape_data["retard_jours"]
    c2.metric(
        "2. Avance / Retard", 
        f"{retard} jours",
        "- Retard accumulé" if retard > 0 else "Avance",
        delta_color="inverse"
    )
    
    # KPI 3: Nombre de tâches achevées
    c3.metric(
        "3. Tâches achevées (Total)", 
        f"{nb_achevees_simule}",
        f"sur {len(taches)} au total au backlog"
    )
    
    # KPI 8: Taux d'achèvement dans les délais
    # On simule que plus on avance, plus les tâches sont en retard
    pct_dans_delai = max(10, 100 - (retard * 4)) 
    c4.metric(
        "8. Tâches dans les délais", 
        f"{pct_dans_delai:.1f}%",
        "En baisse suite aux aléas" if retard > 0 else "Optimal"
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    c5, c6, c7, c8 = st.columns(4)
    
    # KPI 4: Coût réel du projet (Projection)
    c5.metric(
        "4. Coût réel projet (Projeté)", 
        f"{int(cout_reel_total):,} €".replace(",", " "),
        f"vs {int(cout_planifie_total):,} € (Initial)",
        delta_color="inverse"
    )
    
    # KPI 5: Coûts non planifiés
    c6.metric(
        "5. Coûts non planifiés", 
        f"{int(couts_non_planifies):,} €".replace(",", " "),
        "Risques matérialisés",
        delta_color="inverse"
    )
    
    # KPI 6: Taux conso budget RH
    taux_conso = (cout_reel_date / cout_planifie_total * 100) if cout_planifie_total > 0 else 0
    c7.metric(
        "6. Conso. budget RH à date", 
        f"{taux_conso:.1f}%",
        f"Objectif étape: {(cout_planifie_date/cout_planifie_total*100):.1f}%",
        delta_color="inverse"
    )
    
    # KPI 10: Coût moyen par tâche
    cout_moyen = (cout_reel_total / len(taches)) if len(taches) > 0 else 0
    c8.metric(
        "10. Coût moyen / tâche", 
        f"{int(cout_moyen):,} €".replace(",", " "),
        f"Initial: {int(cout_planifie_total/len(taches)):,} €",
        delta_color="inverse"
    )
    
    st.divider()
    
    # ── RISQUES & MÉTÉO ─────────────────────────────────────────────
    col_gauche, col_droite = st.columns([1, 1.2])
    
    with col_gauche:
        st.markdown("### ⚠️ Nouveaux risques survenus")
        for risque in etape_data["details_risques"]:
            st.error(risque)
            
        # Graphique des coûts
        labels = ['Planifié à date', 'Réel à date (avec aléas)']
        values = [cout_planifie_date, cout_reel_date]
        
        fig = go.Figure([go.Bar(
            x=labels, 
            y=values, 
            marker_color=['#1D9E75', '#E24B4A'],
            text=[f"{int(v):,} €".replace(',', ' ') for v in values],
            textposition='auto'
        )])
        fig.update_layout(
            title="Comparatif des Coûts à date",
            yaxis_title="Euros (€)",
            height=300,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_droite:
        st.markdown("### 👥 7 & 9. Météo et Coût par ressource")
        st.caption("Le coût réel inclut une répartition des coûts non planifiés.")
        
        # Préparation des données pour le tableau KPI 7 & 9
        donnees_ressources = []
        for rid, m in equipe_index.items():
            # Coût planifié pour cette ressource
            taches_res = [t for t in taches if t["res"] == rid]
            cout_plan = sum(calcul_cout_tache(t, equipe_index, config["jours_par_semaine"]) for t in taches_res)
            
            # Simulation du coût réel (Planifié + part des risques si météo mauvaise)
            meteo = etape_data["meteo"].get(rid, "☀️")
            surcout_facteur = 1.0
            if meteo == "🌧️": surcout_facteur = 1.15
            elif meteo == "⛈️": surcout_facteur = 1.30
            
            cout_reel = cout_plan * surcout_facteur
            
            donnees_ressources.append({
                "Profil": m.get("label", rid),
                "9. Météo": meteo,
                "Coût Planifié": f"{int(cout_plan):,} €".replace(",", " "),
                "7. Coût Réel Estimé": f"{int(cout_reel):,} €".replace(",", " "),
                "Dérive": f"+{int(cout_reel - cout_plan):,} €".replace(",", " ") if (cout_reel - cout_plan) > 0 else "-"
            })
            
        df_meteo = pd.DataFrame(donnees_ressources)
        st.dataframe(df_meteo, use_container_width=True, hide_index=True)

    st.divider()
    st.markdown("### 📊 Analyse Visuelle Avancée")
    
    col_graph1, col_graph2 = st.columns(2)
    
    with col_graph1:
        # Cascade des coûts (Waterfall) pour le budget global
        fig_waterfall = go.Figure(go.Waterfall(
            name="Budget",
            orientation="v",
            measure=["absolute", "relative", "total"],
            x=["Budget Initial", "Risques & Aléas", "Budget Projeté"],
            textposition="outside",
            text=[f"{int(cout_planifie_total):,} €", f"+{int(couts_non_planifies):,} €", f"{int(cout_reel_total):,} €"],
            y=[cout_planifie_total, couts_non_planifies, cout_reel_total],
            connector={"line":{"color":"rgb(63, 63, 63)"}},
            decreasing={"marker":{"color":"#1D9E75"}},
            increasing={"marker":{"color":"#E24B4A"}},
            totals={"marker":{"color":"#534AB7"}}
        ))
        
        fig_waterfall.update_layout(
            title="Composition du Budget Global",
            height=350,
            margin=dict(l=20, r=20, t=40, b=20),
            showlegend=False
        )
        st.plotly_chart(fig_waterfall, use_container_width=True)
        
    with col_graph2:
        # Pie chart répartition des tâches
        nb_retard = max(0, nb_prevues - nb_achevees_simule)
        nb_a_venir = max(0, len(taches) - nb_achevees_simule - nb_retard)
        
        labels_tasks = ['Achevées', 'En Retard', 'À Venir']
        values_tasks = [nb_achevees_simule, nb_retard, nb_a_venir]
        colors_tasks = ['#1D9E75', '#E24B4A', '#E8EAF0']
        
        fig_pie = go.Figure(data=[go.Pie(
            labels=labels_tasks, 
            values=values_tasks, 
            hole=.4,
            marker=dict(colors=colors_tasks)
        )])
        
        fig_pie.update_layout(
            title="Avancement des Tâches",
            height=350,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    # ── GRAPHIQUE PAR RESSOURCE ──
    st.markdown("<br>", unsafe_allow_html=True)
    
    noms_res = []
    couts_plan_res = []
    couts_reel_res = []
    
    for rid, m in equipe_index.items():
        taches_res = [t for t in taches if t["res"] == rid]
        c_plan = sum(calcul_cout_tache(t, equipe_index, config["jours_par_semaine"]) for t in taches_res)
        
        meteo = etape_data["meteo"].get(rid, "☀️")
        facteur = 1.0
        if meteo == "🌧️": facteur = 1.15
        elif meteo == "⛈️": facteur = 1.30
        c_reel = c_plan * facteur
        
        if c_plan > 0:
            noms_res.append(m.get("label", rid))
            couts_plan_res.append(c_plan)
            couts_reel_res.append(c_reel)
            
    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(
        y=noms_res,
        x=couts_plan_res,
        name='Coût Planifié',
        orientation='h',
        marker=dict(color='#1D9E75'),
        text=[f"{int(v):,} €".replace(',', ' ') for v in couts_plan_res],
        textposition='auto'
    ))
    fig_bar.add_trace(go.Bar(
        y=noms_res,
        x=couts_reel_res,
        name='Coût Réel (Estimé)',
        orientation='h',
        marker=dict(color='#E24B4A'),
        text=[f"{int(v):,} €".replace(',', ' ') for v in couts_reel_res],
        textposition='auto'
    ))
    
    fig_bar.update_layout(
        title="Répartition des coûts par membre de l'équipe (Planifié vs Réel)",
        barmode='group',
        height=400,
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis_title="Coût en Euros (€)",
        yaxis={'categoryorder':'total ascending'}
    )
    st.plotly_chart(fig_bar, use_container_width=True)
