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
    html, body {{ width: 100%; height: 100%; background: #ffffff; overflow: hidden; }}
    #mindmap {{ width: 100%; height: 100%; }}

    /* ── Liens visibles ── */
    .markmap-link {{
      stroke-width: 2px !important;
      stroke-opacity: 0.6 !important;
    }}

    /* ── Style par défaut des nœuds (Texte sombre pour être visible sur blanc) ── */
    .markmap-foreign div {{
      display: inline-block;
      padding: 2px 8px;
      border-radius: 4px;
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      font-size: 13px;
      font-weight: 500;
      color: #1e293b !important; /* Sombre par défaut */
      transition: all 0.3s;
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
        '#4F46E5', '#059669', '#D97706', '#DB2777',
        '#0891B2', '#7C3AED', '#B45309', '#065F46',
        '#9D174D', '#1D4ED8'
      ];

      function assignColors(node, palette, parentColor, rootIdx) {{
        let color;
        if (node.depth === 0) color = '#0f172a';
        else if (node.depth === 1) {{ color = palette[rootIdx % palette.length]; rootIdx++; }}
        else color = parentColor;
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

      assignColors(root, BRANCH_COLORS, '#4F46E5', 0);

      const mm = Markmap.create('#mindmap', {{
        autoFit: true,
        fitRatio: 0.95,
        duration: 300,
        nodeMinHeight: 18,
        spacingVertical: 10,
        spacingHorizontal: 60,
        paddingX: 10,
        color: (node) => node._color || '#4F46E5',
      }}, root);

      // Appliquer les pastilles de couleur sur le texte
      function styleNodes() {{
        document.querySelectorAll('.markmap-foreign div').forEach(div => {{
          // Trouver le cercle associé (dans le même groupe g)
          let parentG = div.closest('.markmap-node');
          if (parentG) {{
            let circle = parentG.querySelector('circle');
            if (circle) {{
              let color = circle.getAttribute('fill');
              div.style.background = color;
              div.style.color = '#ffffff'; // Texte blanc sur fond coloré
              div.style.borderRadius = '12px';
              div.style.padding = '4px 12px';
              div.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
            }}
          }}
        }});
      }}

      // Répéter pour gérer le rendu asynchrone de Markmap
      setTimeout(styleNodes, 500);
      setTimeout(styleNodes, 1500);
      
      // Observer les changements pour maintenir le style lors des interactions
      const observer = new MutationObserver(styleNodes);
      observer.observe(document.getElementById('mindmap'), {{ childList: true, subtree: true }});
    }})();
  </script>
</body>
</html>
"""

    components.html(html, height=900, scrolling=False)
