"""
Moteur de calcul du projet.

Choix technique : module pur (sans Streamlit) pour permettre
les tests unitaires et la réutilisation hors contexte UI.
Toutes les fonctions prennent les données en paramètre (pas de
state global) — pattern fonctionnel, compatible avec le
recalcul systématique déclenché par Streamlit à chaque interaction.
"""

from datetime import datetime, timedelta
import pandas as pd
import plotly.graph_objects as go
from data import EQUIPE_INDEX, COMPLEXITE_COULEURS, CAT_COULEURS, calcul_taux_jour


# ─────────────────────────────────────────────────────────────
# UTILITAIRES DATE
# ─────────────────────────────────────────────────────────────

def semaine_vers_date(semaine: int, date_debut: str) -> datetime:
    """Convertit un numéro de semaine (1-based) en datetime absolu."""
    debut = datetime.strptime(date_debut, "%Y-%m-%d")
    return debut + timedelta(weeks=semaine - 1)


def date_fin_projet(taches: list[dict], date_debut: str) -> datetime:
    """
    Retourne la date de fin estimée = fin de la dernière tâche.
    Utilisé pour l'affichage de la date de livraison.
    """
    if not taches:
        return datetime.strptime(date_debut, "%Y-%m-%d")
    semaine_max = max(t["semaine"] + t["duree"] for t in taches)
    return semaine_vers_date(semaine_max, date_debut)


# ─────────────────────────────────────────────────────────────
# CALCULS BUDGET & KPI
# ─────────────────────────────────────────────────────────────

def calcul_jh_tache(tache: dict, jours_par_semaine: int = 5) -> int:
    """Jours/homme d'une tâche = durée_semaines × jours_ouvrés."""
    return tache["duree"] * jours_par_semaine

def calcul_cout_tache(tache: dict, equipe_index: dict, jours_par_semaine: int = 5) -> float:
    """
    Coût d'une tâche = jours/homme × taux journalier coût-employeur.

    Choix : on appelle calcul_taux_jour(res) plutôt que res["taux_jour"] pour
    que le coût soit toujours calculé depuis (salaire_brut_annuel, statut,
    taux_charges) — source de vérité unique. Le champ taux_jour n'est plus
    stocké dans EQUIPE ; toute modification du salaire ou du statut se propage
    automatiquement sans re-sync manuelle.
    """
    res = equipe_index.get(tache["res"])
    if not res:
        return 0.0
    return calcul_jh_tache(tache, jours_par_semaine) * calcul_taux_jour(res)

def calcul_kpis(taches: list[dict], equipe_index: dict,
                date_debut: str, jours_par_semaine: int = 5) -> dict:
    """
    Calcule tous les KPIs du projet à partir de l'état courant des tâches.
    Retourne un dict utilisé directement dans l'affichage des métriques Streamlit.
    """
    total_jh     = sum(calcul_jh_tache(t, jours_par_semaine) for t in taches)
    total_cout   = sum(calcul_cout_tache(t, equipe_index, jours_par_semaine) for t in taches)
    nb_critiques = sum(1 for t in taches if t.get("critique"))
    semaine_max  = max((t["semaine"] + t["duree"] for t in taches), default=1)
    date_fin     = date_fin_projet(taches, date_debut)

    # Répartition par ressource
    par_res = {}
    for t in taches:
        rid = t["res"]
        par_res.setdefault(rid, {"jh": 0, "cout": 0})
        par_res[rid]["jh"]   += calcul_jh_tache(t, jours_par_semaine)
        par_res[rid]["cout"] += calcul_cout_tache(t, equipe_index, jours_par_semaine)

    # Répartition par catégorie
    par_cat = {}
    for t in taches:
        cat = t["cat"]
        par_cat.setdefault(cat, {"jh": 0, "cout": 0, "nb": 0})
        par_cat[cat]["jh"]   += calcul_jh_tache(t, jours_par_semaine)
        par_cat[cat]["cout"] += calcul_cout_tache(t, equipe_index, jours_par_semaine)
        par_cat[cat]["nb"]   += 1

    return {
        "total_jh":      total_jh,
        "total_cout":    total_cout,
        "nb_taches":     len(taches),
        "nb_critiques":  nb_critiques,
        "nb_semaines":   semaine_max - 1,
        "date_fin":      date_fin,
        "par_res":        par_res,
        "par_cat":        par_cat,
    }


def build_budget_dataframe(taches: list[dict], equipe_index: dict,
                            jours_par_semaine: int = 5) -> pd.DataFrame:
    """
    Construit le DataFrame budget par profil affiché dans l'onglet Budget.
    Colonnes : Profil | Type | J/H | Taux/j | Coût total | Part (%)
    """
    rows = []
    total_cout = sum(calcul_cout_tache(t, equipe_index, jours_par_semaine) for t in taches)

    par_res: dict[str, dict] = {}
    for t in taches:
        rid = t["res"]
        par_res.setdefault(rid, {"jh": 0, "cout": 0})
        par_res[rid]["jh"]   += calcul_jh_tache(t, jours_par_semaine)
        par_res[rid]["cout"] += calcul_cout_tache(t, equipe_index, jours_par_semaine)

    for rid, vals in sorted(par_res.items(), key=lambda x: -x[1]["cout"]):
        res = equipe_index.get(rid, {})
        pct = (vals["cout"] / total_cout * 100) if total_cout else 0
        rows.append({
            "Profil":      res.get("label", rid),
            "Type":        res.get("type", "—"),
            "Statut":      res.get("statut", "—"),
            "J/H":         vals["jh"],
            "Taux/j (€)":  calcul_taux_jour(res) if res else 0,
            "Coût (€)":    int(vals["cout"]),
            "Part (%)":    round(pct, 1),
        })

    rows.append({
        "Profil": "TOTAL",
        "Type": "",
        "J/H": sum(r["J/H"] for r in rows),
        "Taux/j (€)": "",
        "Coût (€)": int(total_cout),
        "Part (%)": 100.0,
    })
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────────────────────
# GANTT PLOTLY
# ─────────────────────────────────────────────────────────────

def build_gantt_figure(taches: list[dict], equipe_index: dict,
                        date_debut: str, jours_par_semaine: int = 5,
                        tri: str = "numero",
                        afficher_deps: bool = True) -> go.Figure:
    """
    Gantt via px.timeline — v4.

    Corrections apportées :
    ① Tri : category_orders est ignoré par px.timeline qui réordonne selon
       l'ordre d'apparition dans le DataFrame. Solution : construire le
       DataFrame dans l'ordre INVERSE du rendu voulu (car yaxis est reversed),
       puis forcer categoryorder="array" + categoryarray sur le yaxis.
    ② Dépendances : yref="paper" avec la formule 1-(i+0.5)/n ne correspond
       pas aux positions réelles des barres (px.timeline ajoute des marges).
       Solution : yref="y" avec le label string exact de chaque tâche —
       Plotly résout alors la position via le même axe catégoriel que les barres.
    """
    import plotly.express as px

    # ── Tri : ordre d'affichage top→bottom ───────────────────
    # autorange="reversed" retourne l'axe Y : le DERNIER élément du
    # categoryarray est affiché EN HAUT. Pour avoir #1 en haut en mode
    # "numero", il faut donc placer #1 EN DERNIER dans categoryarray.
    if tri == "date":
        taches_triees = sorted(taches, key=lambda t: (t["semaine"], t["id"]))
    else:
        taches_triees = sorted(taches, key=lambda t: t["id"])

    # labels dans l'ordre du tri (#1 en premier pour tri numéro)
    labels_y_asc  = [f"#{t['id']} {t['nom']}" for t in taches_triees]
    # labels_y_cat supprimé — on utilise reversed(labels_y_asc) directement dans update_layout

    # Map label → tâche pour accès rapide dans la boucle dépendances
    label_par_id  = {t["id"]: f"#{t['id']} {t['nom']}" for t in taches_triees}
    n = len(taches_triees)

    # ── Construction du DataFrame ────────────────────────────
    rows = []
    for t in taches_triees:
        res      = equipe_index.get(t["res"], {})
        debut_dt = semaine_vers_date(t["semaine"], date_debut)
        fin_dt   = semaine_vers_date(t["semaine"] + t["duree"], date_debut)
        jh       = calcul_jh_tache(t, jours_par_semaine)
        cout     = calcul_cout_tache(t, equipe_index, jours_par_semaine)
        deps_str = ", ".join(f"#{d}" for d in t["deps"]) if t["deps"] else "—"

        rows.append({
            "Tâche":    label_par_id[t["id"]],
            "Début":    debut_dt,
            "Fin":      fin_dt,
            "Couleur":  "#" + res.get("couleur", "888780"),
            "Critique": t.get("critique", False),
            "Tooltip":  (
                f"<b>{t['nom']}</b><br>"
                f"Catégorie : {t['cat']}<br>"
                f"Ressource : {res.get('label', t['res'])}<br>"
                f"Complexité : {t.get('complexite', '—')}<br>"
                f"Début : S{t['semaine']} ({debut_dt.strftime('%d/%m/%Y')})<br>"
                f"Fin : S{t['semaine'] + t['duree']} ({fin_dt.strftime('%d/%m/%Y')})<br>"
                f"Durée : {t['duree']} sem. — {jh} j/h<br>"
                f"Coût estimé : {int(cout):,} €<br>"
                f"Dépendances : {deps_str}"
                + ("<br><b>⚡ Chemin critique</b>" if t.get("critique") else "")
            ),
        })

    df = pd.DataFrame(rows)

    fig = px.timeline(
        df,
        x_start="Début",
        x_end="Fin",
        y="Tâche",
        color="Tâche",
        custom_data=["Tooltip"],
    )

    # Couleurs + styles
    couleur_map  = {row["Tâche"]: row["Couleur"]  for row in rows}
    critique_map = {row["Tâche"]: row["Critique"] for row in rows}

    for trace in fig.data:
        nom  = trace.name
        col  = couleur_map.get(nom, "#888780")
        crit = critique_map.get(nom, False)
        trace.marker.color      = col
        trace.marker.opacity    = 1.0 if crit else 0.75
        trace.marker.line.color = "#E24B4A" if crit else col
        trace.marker.line.width = 2.0 if crit else 0.5
        trace.hovertemplate     = "%{customdata[0]}<extra></extra>"
        trace.showlegend        = False

    # ── Dépendances : yref="y" avec label string ─────────────
    # En passant yref="y" et y0/y1 = label string de la tâche,
    # Plotly résout la position via l'axe catégoriel — alignement
    # garanti avec les barres, indépendant des marges internes.
    if afficher_deps and n > 0:
        ids_visibles = {t["id"] for t in taches_triees}

        dates_par_id: dict[int, dict] = {}
        for t in taches:
            dates_par_id[t["id"]] = {
                "debut": semaine_vers_date(t["semaine"], date_debut),
                "fin":   semaine_vers_date(t["semaine"] + t["duree"], date_debut),
            }

        taches_par_id = {t["id"]: t for t in taches}

        for t in taches_triees:
            if not t["deps"]:
                continue
            label_cible   = label_par_id[t["id"]]
            x_debut_cible = dates_par_id[t["id"]]["debut"]

            for dep_id in t["deps"]:
                if dep_id not in ids_visibles:
                    continue
                label_src  = label_par_id.get(dep_id)
                if label_src is None:
                    continue

                x_fin_src = dates_par_id[dep_id]["fin"]
                t_src     = taches_par_id.get(dep_id)
                lien_crit = t.get("critique") and t_src and t_src.get("critique")
                col_lien  = "#E24B4A" if lien_crit else "#888780"
                dash_lien = "solid"   if lien_crit else "dot"

                # Ligne : xref="x" (date), yref="y" (label catégoriel)
                fig.add_shape(
                    type="line",
                    xref="x", yref="y",
                    x0=x_fin_src,     y0=label_src,
                    x1=x_debut_cible, y1=label_cible,
                    line=dict(color=col_lien, width=1.5, dash=dash_lien),
                    layer="above",
                )
                # Pointe : annotation ancrée sur la cible, flèche en pixels
                # axref/ayref="pixel" est le seul mode compatible Plotly 5.x
                # quand yref mixe date+catégoriel. ax=-10,ay=0 donne une
                # flèche pointant horizontalement vers la droite sur l'arrivée.
                fig.add_annotation(
                    xref="x", yref="y",
                    x=x_debut_cible, y=label_cible,
                    ax=-14, ay=0,
                    axref="pixel", ayref="pixel",
                    showarrow=True,
                    arrowhead=3,
                    arrowsize=1.0,
                    arrowwidth=1.5,
                    arrowcolor=col_lien,
                    text="",
                    standoff=2,
                )

    # Ligne "aujourd'hui"
    today         = datetime.today()
    debut_dt_proj = datetime.strptime(date_debut, "%Y-%m-%d")
    fin_dt_proj   = date_fin_projet(taches, date_debut)
    if debut_dt_proj <= today <= fin_dt_proj:
        fig.add_vline(
            x=today.timestamp() * 1000,
            line=dict(color="#E24B4A", width=1.5, dash="dot"),
            annotation_text="Aujourd'hui",
            annotation_font_size=10,
        )

    fig.update_layout(
        height=max(420, n * 32 + 100),
        xaxis=dict(
            title="",
            tickformat="%d %b %Y",
            gridcolor="#E8EAF0",
            showgrid=True,
        ),
        yaxis=dict(
            title="",
            # Sans autorange="reversed" : categoryarray liste les catégories
            # de BAS en HAUT dans Plotly. Pour avoir #1 EN HAUT on met
            # labels_y_asc inversé : le dernier de la liste = affiché en haut.
            # labels_y_asc = [#1, #2, ... #28] → inversé = [#28, ... #1]
            # → Plotly affiche #1 tout en haut, #28 tout en bas.
            categoryorder="array",
            categoryarray=list(reversed(labels_y_asc)),
            tickfont=dict(size=11),
            # PAS de autorange="reversed" — c'était la source de confusion
        ),
        margin=dict(l=10, r=20, t=20, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="sans-serif", size=12),
        hoverlabel=dict(bgcolor="white", font_size=12, bordercolor="#ccc"),
    )
    return fig


def build_budget_chart(taches: list[dict], equipe_index: dict,
                        jours_par_semaine: int = 5) -> go.Figure:
    """
    Bar chart horizontal : coût total par profil.
    Choix go.Bar horizontal pour un affichage compact multi-profil.
    """
    par_res: dict[str, float] = {}
    for t in taches:
        rid = t["res"]
        par_res[rid] = par_res.get(rid, 0) + calcul_cout_tache(t, equipe_index, jours_par_semaine)

    items = sorted(par_res.items(), key=lambda x: x[1])
    labels = [equipe_index.get(r, {}).get("label", r) for r, _ in items]
    values = [v for _, v in items]
    colors = ["#" + equipe_index.get(r, {}).get("couleur", "888780") for r, _ in items]

    fig = go.Figure(go.Bar(
        x=values,
        y=labels,
        orientation="h",
        marker_color=colors,
        text=[f"{int(v):,} €" for v in values],
        textposition="outside",
        hovertemplate="%{y} : %{x:,.0f} €<extra></extra>",
    ))
    fig.update_layout(
        height=340,
        xaxis=dict(title="Coût (€)", gridcolor="#E8EAF0", showgrid=True),
        yaxis=dict(title=""),
        margin=dict(l=10, r=80, t=10, b=30),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(size=12),
    )
    return fig


def build_cat_chart(taches: list[dict], equipe_index: dict,
                    jours_par_semaine: int = 5) -> go.Figure:
    """
    Donut chart : répartition du budget par catégorie fonctionnelle.
    """
    par_cat: dict[str, float] = {}
    for t in taches:
        cat = t["cat"]
        par_cat[cat] = par_cat.get(cat, 0) + calcul_cout_tache(t, equipe_index, jours_par_semaine)

    labels = list(par_cat.keys())
    values = list(par_cat.values())
    colors = [CAT_COULEURS.get(c, "#888780") for c in labels]

    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=0.5,
        marker=dict(colors=colors),
        hovertemplate="%{label} : %{value:,.0f} € (%{percent})<extra></extra>",
        textinfo="percent",
        textfont_size=11,
    ))
    fig.update_layout(
        height=320,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(font_size=11),
        font=dict(size=12),
    )
    return fig


def build_charge_chart(taches: list[dict], equipe_index: dict,
                        date_debut: str, jours_par_semaine: int = 5) -> go.Figure:
    """
    Histogramme de charge hebdomadaire (j/h cumulés par semaine).
    Permet d'identifier les semaines de surcharge.
    """
    semaine_max = max(t["semaine"] + t["duree"] for t in taches) if taches else 2
    charge: dict[int, float] = {s: 0 for s in range(1, semaine_max)}

    for t in taches:
        for s in range(t["semaine"], t["semaine"] + t["duree"]):
            charge[s] = charge.get(s, 0) + jours_par_semaine  # 1 ressource = 5j/sem

    semaines  = list(charge.keys())
    dates_x   = [semaine_vers_date(s, date_debut).strftime("%d %b") for s in semaines]
    values    = list(charge.values())
    moy       = sum(values) / len(values) if values else 0

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=dates_x, y=values,
        marker_color="#378ADD",
        name="Charge (j/h)",
        hovertemplate="S%{customdata} — %{y} j/h<extra></extra>",
        customdata=semaines,
    ))
    fig.add_hline(y=moy, line=dict(color="#E24B4A", dash="dot", width=1.5),
                  annotation_text=f"Moy. {moy:.0f} j/h", annotation_font_size=10)

    fig.update_layout(
        height=280,
        xaxis=dict(title="Semaine", tickfont_size=10),
        yaxis=dict(title="J/H par semaine", gridcolor="#E8EAF0"),
        margin=dict(l=10, r=20, t=10, b=30),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        font=dict(size=11),
    )
    return fig
