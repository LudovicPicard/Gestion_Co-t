import streamlit as st
import streamlit.components.v1 as components


MINDMAP_MARKDOWN = """
# Budget Book One — Mvp Livres à 1€
## 🧑‍💼 Coûts Humains
### Équipe Projet
- Sophie Lambert — Chef de Projet
- Thomas Martin — Dev Senior Backend
- Lucas Bernard — Dev Mobile Freelance
- Emma Dupont — Alternante Front-End
- Hugo Petit — UX/UI Designer
- Julien Roux — DevOps Engineer
- Léa Moreau — Stagiaire QA
### Parties Prenantes
- Marie Leroy — Responsable RH
- Pierre Duval — Product Owner
- Claire Morin — RSI / DPO
- Antoine Blanc — Direction Financière
### Consultants Externes
- Marc Fontaine — Consultant MOE
- Julie Renard — Freelance Sécurité
- Paul Girard — Auditeur Externe
### Éléments de Coûts Associés
- Avantages en nature (tickets resto, mutuelle…)
- Frais de déplacement remboursés
- Primes et bonus
## ☁️ Infra & Cloud
- Hébergement AWS (EC2)
- Base de données (RDS/PostgreSQL)
- Stockage images (S3)
- CDN (CloudFront)
- API Géolocalisation (Google Maps)
- Firebase (Notifications + Auth)
- Environnement Staging
- Auto-Scaling
- Monitoring (Cloudwatch)
## 💻 Logiciels
### Outils de Développement
- Licences IDE · Xcode · Android Studio · Postman · TestFlight
### Outils de Design
- Figma · Adobe XD · Miro
### APIs & Intégrations
- API Google Books (ISBN) · API Google Maps
## 🗂️ Outils de Gestion de Projet
### Gestion & Suivi
- Jira · Trello
### Communication
- Slack · Notion
### Collaboration Code
- Github · Gitlab · CI/CD Pipeline
## 💸 Coûts Financiers
- Assurances Startup
- Frais Juridiques
- Financement & Prêts
- Frais Bancaires Stripe
## 🔒 Coûts Paiement & Sécurité
- Stripe 1€/Transaction
- Certificat SSL
- Conformité RGPD
- Audit Sécurité
- Licences Droits d'Usage
## ⚙️ Coûts Opérationnels
### Technique
- Communication Externe
- Support Utilisateurs
- Maintenance & Monitoring
### Financier
- Gestion Des Risques
- Provisions Imprévus 10%
- Outils Tests Cypress
## 🧪 Coûts Tests & Qualité
- Tests Unitaires & Intégration
- Beta Testing Utilisateurs
- Audit Qualité Code
- Amélioration Continue
## 🚀 Coûts Déploiement & Stores
- Apple App Store (99$/an)
- Google Play (25$)
- Environnement Staging
- Monitoring Post-Launch
- Firebase Notifications Push
## 📣 Coûts Communication & Marketing
### Communication Externe
- Site Web & Landing Page
- Réseaux Sociaux
- Relations Presse
### Marketing Digital
- Meta/Google Ads
- ASO App Store
- Influenceurs
- CaC
### Branding & Design
- Logo & Charte Graphique
- Assets App Store
- Vidéo Démo
### Lancement Go-To-Market
- Événement Lancement
- Beta Testeurs
- Ambassadeurs Lecteurs
"""


def build_mindmap_tab():
    st.markdown("### 🧠 Mindmap — Budget Book One")
    st.caption("Visualisation interactive. Cliquez sur un nœud pour déplier/replier une branche. Molette pour zoomer.")

    html = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8" />
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    html, body {{ width: 100%; height: 100%; background: #F8FAFF; overflow: hidden; }}
    #mindmap {{ width: 100%; height: 100%; }}

    /* ── Liens visibles et épais ── */
    .markmap-link {{
      stroke-width: 2.5px !important;
      stroke-opacity: 0.85 !important;
    }}

    /* ── Nœuds avec fond coloré (pilule) ── */
    .markmap-foreign > div {{
      display: inline-block;
      padding: 3px 10px;
      border-radius: 20px;
      font-family: 'Segoe UI', Arial, sans-serif;
      font-size: 12px;
      font-weight: 600;
      color: #fff !important;
      white-space: nowrap;
    }}
  </style>
</head>
<body>
  <svg id="mindmap"></svg>

  <script src="https://cdn.jsdelivr.net/npm/d3@7"></script>
  <script src="https://cdn.jsdelivr.net/npm/markmap-view@0.17"></script>
  <script src="https://cdn.jsdelivr.net/npm/markmap-lib@0.17"></script>
  <script>
    (async () => {{
      const {{ Markmap, loadCSS, loadJS }} = window.markmap;
      const {{ Transformer }} = window.markmap;

      const BRANCH_COLORS = [
        '#4F46E5', // indigo (racine)
        '#059669', // vert émeraude
        '#D97706', // ambre
        '#DB2777', // rose fuchsia
        '#0891B2', // cyan
        '#7C3AED', // violet
        '#B45309', // brun doré
        '#065F46', // vert forêt
        '#9D174D', // bordeaux
        '#1D4ED8', // bleu royal
        '#B91C1C', // rouge
        '#0369A1', // bleu acier
      ];

      // Colorier toutes les cellules d'un sous-arbre de la même couleur de branche
      function assignColors(node, palette, parentColor, rootIdx) {{
        let color;
        if (node.depth === 0) {{
          color = '#1e1b4b'; // nœud central très foncé
        }} else if (node.depth === 1) {{
          color = palette[rootIdx % palette.length];
          rootIdx++;
        }} else {{
          color = parentColor;
        }}
        node._color = color;
        if (node.children) {{
          node.children.forEach((child, i) => assignColors(child, palette, color, node.depth === 0 ? i : rootIdx));
        }}
      }}

      const transformer = new Transformer();
      const markdown = {repr(MINDMAP_MARKDOWN)};
      const {{ root, features }} = transformer.transform(markdown);
      const {{ styles, scripts }} = transformer.getUsedAssets(features);

      if (styles) loadCSS(styles);
      if (scripts) await loadJS(scripts, {{ getMarkmap: () => window.markmap }});

      // Attribuer les couleurs
      assignColors(root, BRANCH_COLORS, '#4F46E5', 0);

      const mm = Markmap.create('#mindmap', {{
        autoFit: true,
        fitRatio: 0.98,
        duration: 350,
        nodeMinHeight: 20,
        spacingVertical: 5,
        spacingHorizontal: 70,
        paddingX: 8,
        color: (node) => node._color || '#4F46E5',
      }}, root);

      // Colorier les fonds des nœuds en SVG foreignObject après rendu
      function colorNodes() {{
        document.querySelectorAll('.markmap-node').forEach(g => {{
          const foreignEl = g.querySelector('foreignObject > div > div');
          if (!foreignEl) return;
          // Récupérer la couleur du cercle de ce nœud
          const circle = g.querySelector('circle');
          if (!circle) return;
          const fill = circle.getAttribute('fill') || circle.style.fill || '#4F46E5';
          foreignEl.style.background = fill;
          foreignEl.style.color = '#fff';
          foreignEl.style.borderRadius = '20px';
          foreignEl.style.padding = '2px 10px';
          foreignEl.style.fontWeight = '600';
          foreignEl.style.fontSize = '12px';
        }});
      }}

      // Lancer après un court délai (rendu asynchrone)
      setTimeout(colorNodes, 600);
      setTimeout(colorNodes, 1200);

      // Rafraîchir les couleurs à chaque clic (déplier/replier)
      document.getElementById('mindmap').addEventListener('click', () => setTimeout(colorNodes, 400));
    }})();
  </script>
</body>
</html>
"""

    components.html(html, height=900, scrolling=False)
