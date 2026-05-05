import copy
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

from calculs import calcul_cout_tache, calcul_jh_tache, date_fin_projet, build_gantt_figure, semaine_vers_date
from data import COUTS_SATELLITES, PROVISION_RISQUE_PCT

# ─────────────────────────────────────────────────────────────
# DONNÉES SIMULÉES PAR ÉTAPE (JALONS)
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
            "QA": "☀️", "STG": "☀️", "ALT": "⛈️", "FRL": "☀️"
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
            "QA": "🌧️", "STG": "🌤️", "ALT": "⛈️", "FRL": "☀️"
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
            "QA": "⛈️", "STG": "🌤️", "ALT": "☀️", "FRL": "🌧️"
        }
    }
}

def cout_tache_a_semaine(t, equipe_index, jours_par_semaine, semaine_cible):
    if semaine_cible < t["semaine"]:
        return 0
    if semaine_cible >= t["semaine"] + t["duree"] - 1:
        return calcul_cout_tache(t, equipe_index, jours_par_semaine)
    
    semaines_faites = semaine_cible - t["semaine"] + 1
    pct = semaines_faites / t["duree"]
    return calcul_cout_tache(t, equipe_index, jours_par_semaine) * pct

def build_dashboard_tab(taches, equipe_index, config):
    st.markdown("## 📈 Dashboard de Direction (Contrôle de Gestion)")
    st.markdown("Suivi budgétaire du projet complet, analyse des dérives et comparatif de plannings.")
    
    etape_selectionnee = st.radio(
        "Sélectionnez une étape de contrôle :",
        options=list(ETAPES.keys()),
        format_func=lambda x: ETAPES[x]["nom"],
        horizontal=True
    )
    
    etape_data = ETAPES[etape_selectionnee]
    sem_actuelle = etape_data["semaine_fin"]
    
    st.divider()
    
    # ── RÉSUMÉ DU PROJET ───────────────────────────────────────────
    st.markdown("### 📋 Résumé du Projet")
    total_jh = sum(calcul_jh_tache(t, config["jours_par_semaine"]) for t in taches)
    date_fin_prevue = date_fin_projet(taches, config["date_debut"])
    
    col_res1, col_res2, col_res3, col_res4 = st.columns(4)
    col_res1.metric("Date de Début", datetime.strptime(config["date_debut"], "%Y-%m-%d").strftime("%d/%m/%Y"))
    col_res2.metric("Livraison Prévue", date_fin_prevue.strftime("%d/%m/%Y"))
    col_res3.metric("Charge Totale (J/H)", f"{total_jh} jours")
    col_res4.metric("Taille de l'équipe", f"{len(equipe_index)} personnes")
    
    st.info("L'équipe IT est composée de profils spécifiques incluant notamment un **Stagiaire**, un **Alternant** et un **Freelance**. Les tâches (maquettage, API, mobile, test, déploiement) leur ont été affectées en fonction de leur expertise et sont centralisées dans le diagramme de Gantt.")
    
    st.divider()
    
    # ── 1. CALCULS GLOBAUX ──────────────────────────────────────────────
    
    # RH Initial
    bac_rh = sum(calcul_cout_tache(t, equipe_index, config["jours_par_semaine"]) for t in taches)
    pv_rh = sum(cout_tache_a_semaine(t, equipe_index, config["jours_par_semaine"], sem_actuelle) for t in taches)
    ev_rh = bac_rh * etape_data["pct_avancement_simule"]
    
    # Satellites & Provisions
    total_sat = sum(s["montant"] for s in COUTS_SATELLITES)
    provision_risques = (bac_rh + total_sat) * PROVISION_RISQUE_PCT
    
    # BAC Global (Budget Total Prévu)
    bac_global = bac_rh + total_sat + provision_risques
    
    # Météo (Surcoûts RH dus à la baisse de productivité)
    surcout_meteo_total = 0
    donnees_meteo = []
    
    for rid, profil in equipe_index.items():
        m = etape_data["meteo"].get(rid, "☀️")
        f = 1.0
        if m == "🌧️": f = 1.15
        elif m == "⛈️": f = 1.30
        
        # Le surcoût s'applique sur le travail planifié à date de la ressource
        taches_res = [t for t in taches if t["res"] == rid]
        pv_res = sum(cout_tache_a_semaine(t, equipe_index, config["jours_par_semaine"], sem_actuelle) for t in taches_res)
        
        surcout_res = (pv_res * f) - pv_res
        surcout_meteo_total += surcout_res
        
        donnees_meteo.append({
            "Profil": profil["label"],
            "Météo": m,
            "Impact Productivité": "+15%" if m == "🌧️" else ("+30%" if m == "⛈️" else "Normal"),
            "Surcoût Financier généré": f"+{int(surcout_res):,} €".replace(",", " ") if surcout_res > 0 else "-"
        })
        
    facteur_moyen_rh = 1.0 + (surcout_meteo_total / pv_rh if pv_rh > 0 else 0)
    
    # Coûts non planifiés (Risques purs)
    couts_non_planifies = etape_data["couts_non_planifies"]
    
    # AC Global (Consommé) = EV_RH * météo + Satellites Dépensés + Risques purs
    # On assume que les satellites sont lissés, donc (total_sat * % avancement)
    ac_sat = total_sat * etape_data["pct_avancement_simule"]
    ac_rh = (ev_rh * facteur_moyen_rh)
    ac_global = ac_rh + ac_sat + couts_non_planifies
    
    # EAC Global (Projection Finale) = AC + Reste à Faire (simplifié)
    # Reste à Faire RH
    etc_rh = (bac_rh - ev_rh) * facteur_moyen_rh 
    # Reste à Faire Satellites
    etc_sat = total_sat - ac_sat
    # La projection ignore la provision (elle est là pour l'absorber)
    eac_global = ac_global + etc_rh + etc_sat
    
    # Indices
    efficacite_cout = ((ev_rh + ac_sat) / ac_global) if ac_global > 0 else 1.0
    efficacite_delai = ev_rh / pv_rh if pv_rh > 0 else 1.0
    
    # ── 2. SCORECARDS ────────────────────────────────────────────
    st.markdown("### 🏦 Synthèse Financière du Projet")
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Budget Initial Réservé", f"{int(bac_global):,} €".replace(",", " "), "Dont provisions", help="Budget validé au lancement, incluant la provision pour risques.")
    c2.metric("Consommé à date", f"{int(ac_global):,} €".replace(",", " "), f"Dépense réelle constatée", delta_color="off", help="Toutes les dépenses réelles à ce jour (RH + Satellites + Factures imprévues).")
    c3.metric("Projection Finale", f"{int(eac_global):,} €".replace(",", " "), f"{(eac_global-bac_global)/bac_global*100:+.1f}% d'écart final", delta_color="inverse", help="Où on va atterrir à la fin du projet si le rythme continue.")
    
    # Reste de la provision
    provision_restante = provision_risques - (eac_global - (bac_rh + total_sat))
    is_prov_negative = provision_restante < 0
    c4.metric("Provision Risques Restante", f"{int(provision_restante):,} €".replace(",", " "), "Déficit budgétaire" if is_prov_negative else "Marge de sécurité", delta_color="normal" if not is_prov_negative else "inverse")
    
    st.markdown("<br>", unsafe_allow_html=True)
    c5, c6, c7, c8 = st.columns(4)
    
    # Jauge Efficacité Coût (ex-CPI)
    fig_cpi = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = efficacite_cout,
        title = {'text': "Efficacité Budgétaire"},
        gauge = {
            'axis': {'range': [0, 1.5]},
            'bar': {'color': "#1D9E75" if efficacite_cout >= 1 else "#E24B4A"},
            'steps': [
                {'range': [0, 1], 'color': "rgba(226, 75, 74, 0.2)"},
                {'range': [1, 1.5], 'color': "rgba(29, 158, 117, 0.2)"}
            ]
        }
    ))
    fig_cpi.update_layout(height=200, margin=dict(l=10, r=10, t=30, b=10))
    c5.plotly_chart(fig_cpi, use_container_width=True)
    st.caption("Efficacité budgétaire : > 1 = Moins cher que prévu. < 1 = Surcoûts constatés.")
    
    # Jauge Tenue des Délais (ex-SPI)
    fig_spi = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = efficacite_delai,
        title = {'text': "Tenue des Délais"},
        gauge = {
            'axis': {'range': [0, 1.5]},
            'bar': {'color': "#1D9E75" if efficacite_delai >= 1 else "#E24B4A"},
            'steps': [
                {'range': [0, 1], 'color': "rgba(226, 75, 74, 0.2)"},
                {'range': [1, 1.5], 'color': "rgba(29, 158, 117, 0.2)"}
            ]
        }
    ))
    fig_spi.update_layout(height=200, margin=dict(l=10, r=10, t=30, b=10))
    c6.plotly_chart(fig_spi, use_container_width=True)
    st.caption("Tenue des délais : > 1 = En avance. < 1 = Retard constaté.")
    
    c7.metric("Surcoût lié aux Aléas (Risques purs)", f"{int(couts_non_planifies):,} €".replace(",", " "), "Factures non prévues", delta_color="inverse")
    c8.metric("Surcoût lié à l'équipe (Météo/Temps)", f"{int(surcout_meteo_total):,} €".replace(",", " "), "Baisse de productivité", delta_color="inverse")

    st.divider()
    
    # ── 3. RISQUES ET EXPLICATION DU DÉFICIT ─────────────────────────────
    st.markdown("### 🔍 Explication des Surcoûts : Matrice des Risques & Météo de l'Équipe")
    
    col_matrice, col_meteo = st.columns([1.2, 1])
    
    with col_matrice:
        st.markdown("#### Matrice des Risques Survenus")
        df_risques = pd.DataFrame(etape_data["details_risques"])
        df_risques.columns = ["Description du Risque", "Impact Financier (€)", "Impact Planning (Jours)", "Domaine"]
        st.dataframe(df_risques.style.format({"Impact Financier (€)": "{:,}"}), use_container_width=True, hide_index=True)
        
        st.markdown(f"**Retard global du projet : <span style='color:#E24B4A'>{etape_data['retard_jours']} jours</span>**", unsafe_allow_html=True)
        
    with col_meteo:
        st.markdown("#### Météo de l'Équipe (Productivité)")
        df_meteo = pd.DataFrame(donnees_meteo)
        st.dataframe(df_meteo, use_container_width=True, hide_index=True)
        st.caption("Une baisse de productivité (Pluie, Orage) rallonge le temps de travail et génère un surcoût RH (TJM x Jours supplémentaires).")

    st.divider()

    col_gauche, col_droite = st.columns([1.2, 1])
    with col_gauche:
        st.markdown("### 📊 S-Curve : Évolution de la Valeur")
        semaines = list(range(1, 20)) # Max 19 semaines
        
        pv_curve = []
        for w in semaines:
            pv_w = sum(cout_tache_a_semaine(t, equipe_index, config["jours_par_semaine"], w) for t in taches)
            pv_curve.append(pv_w + (total_sat * (w/19))) # Lissage satellites
            
        ev_curve = [((ev_rh + ac_sat) * (w/sem_actuelle)) if w <= sem_actuelle else None for w in semaines]
        ac_curve = [(ac_global * (w/sem_actuelle)) if w <= sem_actuelle else None for w in semaines]
        
        fig_s = go.Figure()
        fig_s.add_trace(go.Scatter(x=semaines, y=pv_curve, mode='lines', name='Valeur Planifiée', line=dict(color='#534AB7', width=3)))
        fig_s.add_trace(go.Scatter(x=semaines, y=ev_curve, mode='lines', name='Valeur Acquise', line=dict(color='#1D9E75', width=3)))
        fig_s.add_trace(go.Scatter(x=semaines, y=ac_curve, mode='lines', name='Dépense Réelle (Consommé)', line=dict(color='#E24B4A', width=3, dash='dot')))
        
        fig_s.update_layout(
            xaxis_title="Semaine",
            yaxis_title="Budget cumulé (€)",
            height=350,
            margin=dict(l=20, r=20, t=10, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_s, use_container_width=True)

    with col_droite:
        st.markdown("### 📊 Composition de la Projection Finale")
        
        budget_initial_hors_prov = bac_rh + total_sat
        
        # Cascade des coûts (Waterfall)
        fig_waterfall = go.Figure(go.Waterfall(
            name="Budget",
            orientation="v",
            measure=["absolute", "relative", "relative", "total", "absolute"],
            x=["Budget (RH + Satellites)", "Surcoût Météo/Temps", "Aléas (Risques)", "Projection Finale", "Consommé à date"],
            textposition="outside",
            text=[
                f"{int(budget_initial_hors_prov):,} €", 
                f"+{int(eac_global - budget_initial_hors_prov - couts_non_planifies):,} €", 
                f"+{int(couts_non_planifies):,} €", 
                f"{int(eac_global):,} €",
                f"{int(ac_global):,} €"
            ],
            y=[budget_initial_hors_prov, (eac_global - budget_initial_hors_prov - couts_non_planifies), couts_non_planifies, eac_global, ac_global],
            connector={"line":{"color":"rgb(63, 63, 63)"}},
            decreasing={"marker":{"color":"#1D9E75"}},
            increasing={"marker":{"color":"#E24B4A"}},
            totals={"marker":{"color":"#534AB7"}}
        ))
        
        fig_waterfall.update_layout(
            height=350,
            margin=dict(l=20, r=20, t=10, b=20),
            showlegend=False
        )
        st.plotly_chart(fig_waterfall, use_container_width=True)
        st.caption("Le graphique montre comment les dérives (météo et aléas) gonflent le coût final par rapport à la base de départ.")

    st.divider()
    
    # ── 4. GANTT COMPARATIF ──────────────────────────────────────────
    st.markdown("### 📅 Comparatif des Plannings (Gantt)")
    st.markdown("Visualisation de l'impact des retards sur le calendrier du projet.")
    
    # Simulation des tâches avec retard pour le Gantt réel
    taches_simulees = copy.deepcopy(taches)
    for t in taches_simulees:
        # Si la tâche n'est pas encore terminée à la semaine actuelle, elle subit le retard accumulé
        if t["semaine"] + t["duree"] - 1 >= sem_actuelle:
            t["decalage_jours"] = etape_data["retard_jours"]
            
    fig_gantt_initial = build_gantt_figure(taches, equipe_index, config["date_debut"], config["jours_par_semaine"], afficher_deps=True)
    fig_gantt_reel = build_gantt_figure(taches_simulees, equipe_index, config["date_debut"], config["jours_par_semaine"], afficher_deps=True)
    
    # On force la même échelle de temps (x-axis) sur les deux graphiques pour voir visuellement le décalage
    min_date = min(semaine_vers_date(t["semaine"], config["date_debut"]) for t in taches) - timedelta(days=7)
    max_date = max(semaine_vers_date(t["semaine"] + t["duree"], config["date_debut"]) + timedelta(days=t.get("decalage_jours", 0)) for t in taches_simulees) + timedelta(days=14)
    
    col_gantt1, col_gantt2 = st.columns(2)
    
    with col_gantt1:
        st.markdown("#### Planning Initial (Baseline)")
        fig_gantt_initial.update_layout(height=500, margin=dict(l=0, r=0, t=30, b=0), xaxis=dict(range=[min_date, max_date]))
        st.plotly_chart(fig_gantt_initial, use_container_width=True)
        
    with col_gantt2:
        st.markdown("#### Planning Réel (Projeté avec Décalages)")
        fig_gantt_reel.update_layout(height=500, margin=dict(l=0, r=0, t=30, b=0), xaxis=dict(range=[min_date, max_date]))
        st.plotly_chart(fig_gantt_reel, use_container_width=True)
