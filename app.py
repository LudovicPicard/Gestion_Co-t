"""
Application Streamlit — Pilotage RH par les coûts : Amazon Beta Mobile.
"""

import copy
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

from data import (
    get_taches_default, get_equipe_default,
    PROJECT_CONFIG, CATEGORIES, CAT_COULEURS,
    COMPLEXITE_OPTIONS, COMPLEXITE_COULEURS, TYPE_RESSOURCE_OPTIONS,
    JOURS_OUVRES_PAR_AN, STATUTS_CONVENTION, TAUX_CHARGES_PATRONALES,
    STATUT_DEFAULT_PAR_TYPE, calcul_taux_jour,
)
from calculs import (
    calcul_kpis, build_gantt_figure, build_budget_chart,
    build_cat_chart, build_charge_chart, build_budget_dataframe,
    calcul_cout_tache, calcul_jh_tache,
)
from dashboard import build_dashboard_tab

st.set_page_config(
    page_title="Pilotage RH — Amazon Beta Mobile",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
[data-testid="metric-container"] {
    background: #F4F6FA;
    border: 1px solid #E2E6F0;
    border-radius: 8px;
    padding: 12px 16px;
}
[data-testid="stMetricDelta"] { font-size: 12px; }
.stAlert { border-radius: 8px; }
div[data-testid="stExpander"] { border: 1px solid #E2E6F0; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

if "taches" not in st.session_state:
    st.session_state.taches = get_taches_default()
if "equipe" not in st.session_state:
    st.session_state.equipe = get_equipe_default()
if "config" not in st.session_state:
    st.session_state.config = copy.deepcopy(PROJECT_CONFIG)

equipe_index      = {m["id"]: m for m in st.session_state.equipe}
ids_ressources    = [m["id"] for m in st.session_state.equipe]
labels_ressources = {m["id"]: m["label"] for m in st.session_state.equipe}

# ── SIDEBAR ──────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Paramètres projet")
    st.session_state.config["nom"] = st.text_input(
        "Nom du projet", value=st.session_state.config["nom"])
    st.session_state.config["date_debut"] = st.date_input(
        "Date de début",
        value=pd.to_datetime(st.session_state.config["date_debut"]),
        format="DD/MM/YYYY",
    ).strftime("%Y-%m-%d")
    st.session_state.config["jours_par_semaine"] = st.slider(
        "Jours ouvrés par semaine", min_value=3, max_value=5,
        value=st.session_state.config["jours_par_semaine"])

    st.divider()
    st.markdown("### 🔍 Filtres & affichage Gantt")

    tri_gantt = st.radio(
        "Tri des tâches",
        options=["numero", "date"],
        format_func=lambda x: "Par numéro (#1 → #28)" if x == "numero" else "Par date de début",
        horizontal=True,
    )
    afficher_deps = st.checkbox("Afficher les dépendances", value=True,
                                 help="Flèches entre tâches. Rouge = chemin critique.")
    filtre_cat = st.multiselect("Catégorie(s)", options=CATEGORIES, default=[], placeholder="Toutes")
    filtre_res = st.multiselect(
        "Ressource(s)", options=ids_ressources,
        format_func=lambda x: labels_ressources.get(x, x),
        default=[], placeholder="Toutes")
    filtre_critique = st.checkbox("Chemin critique uniquement", value=False)

    sem_max_projet = max(t["semaine"] + t["duree"] for t in st.session_state.taches)
    filtre_sem = st.slider(
        "Plage de semaines",
        min_value=1, max_value=sem_max_projet,
        value=(1, sem_max_projet),
        format="S%d",
    )

    st.divider()
    if st.button("🔄 Réinitialiser toutes les données", use_container_width=True):
        st.session_state.taches = get_taches_default()
        st.session_state.equipe = get_equipe_default()
        st.session_state.config = copy.deepcopy(PROJECT_CONFIG)
        st.rerun()

# ── FILTRAGE ─────────────────────────────────────────────────
taches_filtrees = st.session_state.taches
if filtre_cat:
    taches_filtrees = [t for t in taches_filtrees if t["cat"] in filtre_cat]
if filtre_res:
    taches_filtrees = [t for t in taches_filtrees if t["res"] in filtre_res]
if filtre_critique:
    taches_filtrees = [t for t in taches_filtrees if t.get("critique")]
taches_filtrees = [
    t for t in taches_filtrees
    if t["semaine"] <= filtre_sem[1] and t["semaine"] + t["duree"] - 1 >= filtre_sem[0]
]

# ── KPIs dynamiques ──────────────────────────────────────────
kpis_filtres = calcul_kpis(
    taches_filtrees, equipe_index,
    st.session_state.config["date_debut"],
    st.session_state.config["jours_par_semaine"],
)
kpis_total = calcul_kpis(
    st.session_state.taches, equipe_index,
    st.session_state.config["date_debut"],
    st.session_state.config["jours_par_semaine"],
)
filtre_actif = bool(filtre_cat or filtre_res or filtre_critique
                    or filtre_sem != (1, sem_max_projet))

# ── EN-TÊTE ───────────────────────────────────────────────────
st.markdown(f"# 📋 {st.session_state.config['nom']}")
if filtre_actif:
    st.caption(
        f"**Vue filtrée** : {kpis_filtres['nb_taches']} tâches sur {kpis_total['nb_taches']} — "
        "KPIs ci-dessous reflètent la sélection active"
    )
else:
    st.caption("Pilotage RH par les coûts — vue complète")

kpis = kpis_filtres
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Tâches", kpis["nb_taches"],
          f"/{kpis_total['nb_taches']} total" if filtre_actif else f"{kpis['nb_critiques']} critiques")
c2.metric("Jours / Homme", f"{kpis['total_jh']} j/h",
          f"/{kpis_total['total_jh']} total" if filtre_actif else None)
c3.metric("Durée", f"{kpis['nb_semaines']} semaines")
c4.metric("Date de livraison", kpis["date_fin"].strftime("%d/%m/%Y") if kpis["nb_taches"] else "—")
c5.metric("Budget RH", f"{int(kpis['total_cout']):,} €".replace(",", " "),
          f"/{int(kpis_total['total_cout']):,} total".replace(",", " ") if filtre_actif else None)

st.divider()

tab_gantt, tab_taches, tab_budget, tab_equipe, tab_dashboard = st.tabs([
    "📊 Gantt", "📝 Tâches", "💰 Budget", "👥 Équipe", "📈 Dashboard"
])

# ════════════════════════════════════════════════════════════
# GANTT
# ════════════════════════════════════════════════════════════
with tab_gantt:
    if not taches_filtrees:
        st.info("Aucune tâche ne correspond aux filtres actifs.")
    else:
        fig_gantt = build_gantt_figure(
            taches_filtrees, equipe_index,
            st.session_state.config["date_debut"],
            st.session_state.config["jours_par_semaine"],
            tri=tri_gantt,
            afficher_deps=afficher_deps,
        )
        st.plotly_chart(fig_gantt, use_container_width=True)

    with st.expander("🔴 Chemin critique — détail séquentiel"):
        taches_crit = sorted(
            [t for t in st.session_state.taches if t.get("critique")],
            key=lambda t: t["semaine"],
        )
        if taches_crit:
            st.markdown("`" + " → ".join(f"#{t['id']} {t['nom']}" for t in taches_crit) + "`")
            st.caption(
                f"{len(taches_crit)} tâches critiques · "
                f"{sum(calcul_jh_tache(t, st.session_state.config['jours_par_semaine']) for t in taches_crit)} j/h "
                f"· {int(sum(calcul_cout_tache(t, equipe_index, st.session_state.config['jours_par_semaine']) for t in taches_crit)):,} €"
            )

    with st.expander("📈 Charge hebdomadaire"):
        st.plotly_chart(
            build_charge_chart(
                st.session_state.taches, equipe_index,
                st.session_state.config["date_debut"],
                st.session_state.config["jours_par_semaine"],
            ), use_container_width=True,
        )

# ════════════════════════════════════════════════════════════
# TÂCHES
# ════════════════════════════════════════════════════════════
with tab_taches:
    st.markdown("### Gestion des tâches")
    st.caption("Modifiez une tâche : Gantt, budget et KPIs se mettent à jour automatiquement.")

    with st.expander("➕ Ajouter une tâche"):
        nc1, nc2, nc3 = st.columns(3)
        new_nom  = nc1.text_input("Nom de la tâche", key="new_nom")
        new_cat  = nc1.selectbox("Catégorie", CATEGORIES, key="new_cat")
        new_res  = nc2.selectbox("Ressource", ids_ressources,
                                  format_func=lambda x: labels_ressources.get(x, x), key="new_res")
        new_sem  = nc2.number_input("Semaine de début", min_value=1, max_value=52, value=1, key="new_sem")
        new_dur  = nc3.number_input("Durée (semaines)", min_value=1, max_value=20, value=2, key="new_dur")
        new_cplx = nc3.selectbox("Complexité", COMPLEXITE_OPTIONS, key="new_cplx")
        new_crit = nc3.checkbox("Chemin critique", key="new_crit")
        new_deps_raw = nc1.text_input("Dépendances (ids, ex: 1,3)", value="", key="new_deps")
        if st.button("Ajouter la tâche", type="primary"):
            if not new_nom.strip():
                st.error("Le nom est obligatoire.")
            else:
                deps = [int(d.strip()) for d in new_deps_raw.split(",") if d.strip().isdigit()]
                nid  = max((t["id"] for t in st.session_state.taches), default=0) + 1
                st.session_state.taches.append({
                    "id": nid, "cat": new_cat, "nom": new_nom.strip(), "res": new_res,
                    "semaine": int(new_sem), "duree": int(new_dur),
                    "critique": new_crit, "deps": deps, "complexite": new_cplx,
                })
                st.success(f"Tâche #{nid} ajoutée.")
                st.rerun()

    for cat in sorted(set(t["cat"] for t in st.session_state.taches)):
        taches_cat  = [t for t in st.session_state.taches if t["cat"] == cat]
        couleur_cat = CAT_COULEURS.get(cat, "#888")
        nb_jh_cat   = sum(calcul_jh_tache(t, st.session_state.config["jours_par_semaine"]) for t in taches_cat)
        cout_cat    = sum(calcul_cout_tache(t, equipe_index, st.session_state.config["jours_par_semaine"]) for t in taches_cat)
        st.markdown(
            f"<span style='color:{couleur_cat};font-weight:600;font-size:15px'>▶ {cat}</span> "
            f"<span style='color:#888;font-size:12px'>{len(taches_cat)} tâches · {nb_jh_cat} j/h · {int(cout_cat):,} €</span>",
            unsafe_allow_html=True,
        )
        for t in taches_cat:
            res_info = equipe_index.get(t["res"], {})
            jh   = calcul_jh_tache(t, st.session_state.config["jours_par_semaine"])
            cout = calcul_cout_tache(t, equipe_index, st.session_state.config["jours_par_semaine"])
            badge = "🔴 CRITIQUE" if t.get("critique") else ""
            with st.expander(f"#{t['id']} · {t['nom']} · {res_info.get('label','?')} · {jh} j/h · {int(cout):,} €  {badge}"):
                e1, e2, e3 = st.columns(3)
                kp = f"t_{t['id']}"
                t_nom  = e1.text_input("Nom", value=t["nom"], key=f"{kp}_nom")
                t_cat  = e1.selectbox("Catégorie", CATEGORIES,
                                       index=CATEGORIES.index(t["cat"]) if t["cat"] in CATEGORIES else 0,
                                       key=f"{kp}_cat")
                t_res  = e2.selectbox("Ressource", ids_ressources,
                                       index=ids_ressources.index(t["res"]) if t["res"] in ids_ressources else 0,
                                       format_func=lambda x: labels_ressources.get(x, x), key=f"{kp}_res")
                t_sem  = e2.number_input("Semaine début", min_value=1, max_value=52, value=t["semaine"], key=f"{kp}_sem")
                t_dur  = e2.number_input("Durée (sem.)", min_value=1, max_value=20, value=t["duree"], key=f"{kp}_dur")
                t_cplx = e3.selectbox("Complexité", COMPLEXITE_OPTIONS,
                                       index=COMPLEXITE_OPTIONS.index(t["complexite"]) if t["complexite"] in COMPLEXITE_OPTIONS else 1,
                                       key=f"{kp}_cplx")
                t_crit = e3.checkbox("Chemin critique", value=t.get("critique", False), key=f"{kp}_crit")
                t_deps_raw = e3.text_input("Dépendances (ids)",
                                            value=",".join(str(d) for d in t["deps"]), key=f"{kp}_deps")
                bc1, bc2 = st.columns([1, 5])
                if bc1.button("Enregistrer", key=f"{kp}_save", type="primary"):
                    deps = [int(d.strip()) for d in t_deps_raw.split(",") if d.strip().isdigit()]
                    idx  = next(i for i, x in enumerate(st.session_state.taches) if x["id"] == t["id"])
                    st.session_state.taches[idx].update({
                        "nom": t_nom.strip(), "cat": t_cat, "res": t_res,
                        "semaine": int(t_sem), "duree": int(t_dur),
                        "complexite": t_cplx, "critique": t_crit, "deps": deps,
                    })
                    st.rerun()
                if bc2.button("🗑 Supprimer", key=f"{kp}_del"):
                    st.session_state.taches = [x for x in st.session_state.taches if x["id"] != t["id"]]
                    st.rerun()
        st.markdown("---")

# ════════════════════════════════════════════════════════════
# BUDGET
# ════════════════════════════════════════════════════════════
with tab_budget:
    st.markdown("### Décomposition du budget RH")
    total_c  = kpis_total["total_cout"]
    cout_cdi = sum(
        calcul_cout_tache(t, equipe_index, st.session_state.config["jours_par_semaine"])
        for t in st.session_state.taches
        if equipe_index.get(t["res"], {}).get("type") == "CDI"
    )
    cout_ext = total_c - cout_cdi
    b1, b2, b3, b4 = st.columns(4)
    b1.metric("Budget total", f"{int(total_c):,} €".replace(",", " "))
    b2.metric("Part CDI", f"{int(cout_cdi):,} €".replace(",", " "),
              f"{cout_cdi/total_c*100:.0f}%" if total_c else "")
    b3.metric("Part externe", f"{int(cout_ext):,} €".replace(",", " "),
              f"{cout_ext/total_c*100:.0f}%" if total_c else "")
    b4.metric("Coût moyen/j/h",
              f"{int(total_c/kpis_total['total_jh']):,} €".replace(",", " ") if kpis_total["total_jh"] else "—")

    gb1, gb2 = st.columns(2)
    with gb1:
        st.markdown("**Coût par profil**")
        st.plotly_chart(build_budget_chart(st.session_state.taches, equipe_index,
                                            st.session_state.config["jours_par_semaine"]),
                        use_container_width=True)
    with gb2:
        st.markdown("**Répartition par module**")
        st.plotly_chart(build_cat_chart(st.session_state.taches, equipe_index,
                                         st.session_state.config["jours_par_semaine"]),
                        use_container_width=True)

    st.markdown("**Tableau récapitulatif**")
    df_budget = build_budget_dataframe(st.session_state.taches, equipe_index,
                                        st.session_state.config["jours_par_semaine"])
    def style_total(row):
        return ["font-weight:bold;background:#E8EAF2"]*len(row) if row["Profil"]=="TOTAL" else [""]*len(row)
    st.dataframe(
        df_budget.style.apply(style_total, axis=1).format({"Coût (€)":"{:,}","Part (%)":"{:.1f}"}),
        use_container_width=True, hide_index=True,
    )

# ════════════════════════════════════════════════════════════
# ÉQUIPE
# ════════════════════════════════════════════════════════════
with tab_equipe:
    st.markdown("### Composition de l'équipe technique")
    st.caption("Source de vérité : salaire brut annuel + statut → charges patronales → taux/j employeur.")

    types_presents = {m["type"] for m in st.session_state.equipe}
    manquants = [r for r in ["STAGIAIRE","ALTERNANT","FREELANCE"] if r not in types_presents]
    if manquants:
        st.warning(f"Contrainte non respectée : profil(s) manquant(s) → {', '.join(manquants)}")
    else:
        st.success("Contrainte respectée : au moins 1 stagiaire, 1 alternant et 1 freelance présents.")

    def charges_annuelles(m):
        return int(m["salaire_brut_annuel"] * TAUX_CHARGES_PATRONALES.get(m.get("statut","ETAM"), 0.42))

    df_equipe = pd.DataFrame([{
        "Profil":                m["label"],
        "Type":                  m["type"],
        "Statut":                m.get("statut","—"),
        "Salaire brut/an (€)":   m["salaire_brut_annuel"],
        "Taux charges":          f"{TAUX_CHARGES_PATRONALES.get(m.get('statut','ETAM'),0)*100:.0f} %",
        "Charges patron. (€)":   charges_annuelles(m),
        "Coût employeur/an (€)": m["salaire_brut_annuel"] + charges_annuelles(m),
        "Taux/j employeur (€)":  calcul_taux_jour(m),
        "Jours ref/an":          JOURS_OUVRES_PAR_AN.get(m["type"], 218),
    } for m in st.session_state.equipe])
    st.dataframe(
        df_equipe.style.format({
            "Salaire brut/an (€)":   "{:,}",
            "Charges patron. (€)":   "{:,}",
            "Coût employeur/an (€)": "{:,}",
            "Taux/j employeur (€)":  "{:,}",
        }),
        use_container_width=True, hide_index=True,
    )
    st.caption("Taux/j = (Brut + Charges) ÷ jours ouvrés/an. Cadre 45% · ETAM 42% · Ouvrier 40% · Alternant 10% · Stagiaire & Freelance 0%.")

    st.markdown("#### Éditer un profil")
    for m in st.session_state.equipe:
        tj_actuel   = calcul_taux_jour(m)
        sal_actuel  = m["salaire_brut_annuel"]
        charges_act = charges_annuelles(m)
        with st.expander(
            f"{m['label']} · {m.get('statut','—')} · {sal_actuel:,} €/an brut "
            f"· +{charges_act:,} € charges · {tj_actuel} €/j employeur"
        ):
            kp = f"eq_{m['id']}"
            c1, c2, c3 = st.columns(3)
            new_label  = c1.text_input("Libellé", value=m["label"], key=f"{kp}_lbl")
            new_type   = c2.selectbox("Type de contrat", TYPE_RESSOURCE_OPTIONS,
                index=TYPE_RESSOURCE_OPTIONS.index(m["type"]) if m["type"] in TYPE_RESSOURCE_OPTIONS else 0,
                key=f"{kp}_type")
            statut_def = m.get("statut", STATUT_DEFAULT_PAR_TYPE.get(m["type"], "ETAM"))
            new_statut = c3.selectbox("Statut conventionnel", STATUTS_CONVENTION,
                index=STATUTS_CONVENTION.index(statut_def) if statut_def in STATUTS_CONVENTION else 0,
                key=f"{kp}_statut")

            st.markdown("**Rémunération**")
            r1, r2, r3, r4 = st.columns(4)
            new_salaire   = r1.number_input("Salaire brut/an (€)", min_value=100, max_value=500_000,
                                             value=m["salaire_brut_annuel"], step=500, key=f"{kp}_sal")
            taux_ch_new   = TAUX_CHARGES_PATRONALES.get(new_statut, 0.42)
            charges_calc  = int(new_salaire * taux_ch_new)
            cout_emp_calc = new_salaire + charges_calc
            jours_ref     = JOURS_OUVRES_PAR_AN.get(new_type, 218)
            tj_calc       = max(1, round((cout_emp_calc / jours_ref) / 10) * 10)
            r2.metric("Taux charges", f"{taux_ch_new*100:.0f} %")
            r3.metric("Charges (€/an)", f"{charges_calc:,} €")
            r4.metric("Taux/j employeur", f"{tj_calc} €/j")
            st.caption(f"Coût employeur : {cout_emp_calc:,} € ({new_salaire:,} brut + {charges_calc:,} charges) ÷ {jours_ref} j = {tj_calc} €/j")

            if st.button("Enregistrer", key=f"{kp}_save"):
                idx = next(i for i, x in enumerate(st.session_state.equipe) if x["id"] == m["id"])
                st.session_state.equipe[idx]["label"]               = new_label.strip()
                st.session_state.equipe[idx]["type"]                = new_type
                st.session_state.equipe[idx]["statut"]              = new_statut
                st.session_state.equipe[idx]["salaire_brut_annuel"] = int(new_salaire)
                st.rerun()

    st.markdown("#### ➕ Ajouter un profil")
    na1, na2, na3 = st.columns(3)
    new_eid   = na1.text_input("ID unique (ex: BA2)", key="new_eid")
    new_elbl  = na2.text_input("Libellé", key="new_elbl")
    new_etype = na3.selectbox("Type", TYPE_RESSOURCE_OPTIONS, key="new_etype")
    na4, na5  = st.columns(2)
    new_estat = na4.selectbox("Statut conventionnel", STATUTS_CONVENTION,
        index=STATUTS_CONVENTION.index(STATUT_DEFAULT_PAR_TYPE.get("CDI","Cadre")), key="new_estat")
    new_esal  = na5.number_input("Salaire brut/an (€)", min_value=100, max_value=500_000,
                                  value=45000, step=500, key="new_esal")
    tch_p = TAUX_CHARGES_PATRONALES.get(new_estat, 0.42)
    tj_p  = max(1, round((new_esal*(1+tch_p)/JOURS_OUVRES_PAR_AN.get(new_etype,218))/10)*10)
    st.caption(f"Taux/j calculé : {tj_p} €/j · Charges : {tch_p*100:.0f} %")

    if st.button("Ajouter le profil", type="primary"):
        if not new_eid.strip() or not new_elbl.strip():
            st.error("ID et libellé obligatoires.")
        elif new_eid.strip().upper() in {m["id"] for m in st.session_state.equipe}:
            st.error(f"L'ID '{new_eid}' existe déjà.")
        else:
            st.session_state.equipe.append({
                "id": new_eid.strip().upper(), "label": new_elbl.strip(),
                "type": new_etype, "statut": new_estat,
                "salaire_brut_annuel": int(new_esal), "couleur": "888780",
            })
            st.rerun()

    st.markdown("#### Charge & coût par ressource")
    rows_charge = []
    for m in st.session_state.equipe:
        tr   = [t for t in st.session_state.taches if t["res"] == m["id"]]
        jh   = sum(calcul_jh_tache(t, st.session_state.config["jours_par_semaine"]) for t in tr)
        cout = sum(calcul_cout_tache(t, equipe_index, st.session_state.config["jours_par_semaine"]) for t in tr)
        rows_charge.append({
            "Profil": m["label"], "Statut": m.get("statut","—"),
            "Taux/j (€)": calcul_taux_jour(m),
            "Nb tâches": len(tr), "J/H total": jh, "Coût total (€)": int(cout),
        })
    st.dataframe(
        pd.DataFrame(rows_charge).sort_values("J/H total", ascending=False),
        use_container_width=True, hide_index=True,
    )

# ════════════════════════════════════════════════════════════
# DASHBOARD
# ════════════════════════════════════════════════════════════
with tab_dashboard:
    build_dashboard_tab(st.session_state.taches, equipe_index, st.session_state.config)
