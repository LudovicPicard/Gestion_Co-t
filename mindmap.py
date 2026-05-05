import streamlit as st
import streamlit.components.v1 as components


MINDMAP_MARKDOWN = """
# Coûts associés au projet Book One
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
- Claire Morin — RSSI / DPO
- Antoine Blanc — Direction Financière
### Consultants Externes
- Marc Fontaine — Consultant MOE
- Julie Renard — Freelance Sécurité
- Paul Girard — Auditeur Externe
### Éléments de Coûts Associés
- Avantages en nature (Tickets Resto, Mutuelle…)
- Frais de déplacement remboursés
- Primes et Bonus
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
- Licences IDE · Xcode · Android Studio · Postman · Testflight
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
## 🚀 Coûts Déploiement & Stores
- Apple App Store 99$/an
- Google Play 25$
- Environnement Staging
- Monitoring Post-Launch
- Firebase Notifications Push
## 🧪 Coûts Tests & Qualité
- Outils Tests Cypress
- Tests Unitaires & Intégration
- Beta Testing Utilisateurs
- Audit Qualité Code
- Amélioration Continue
## ⚙️ Coûts Opérationnels
### Fonctionnement Quotidien
- Communication Externe
- Support Utilisateurs
### Technique
- Maintenance & Monitoring
- Gestion Des Risques
### Financier
- Provisions Imprévus 10%
## 🔒 Coûts Paiement & Sécurité
- Stripe 1€/Transaction
- Certificat SSL
- Conformité RGPD
- Audit Sécurité
- Licences Droits d'Usage
## 💸 Coûts Financiers
- Assurances Startup
- Frais Juridiques
- Financement & Prêts
- Frais Bancaires Stripe
"""


def build_mindmap_tab():
    st.markdown("### 🧠 Mindmap — Budget Book One")
    st.caption("Visualisation interactive. Cliquez sur un nœud pour déplier/replier une branche. Molette pour zoomer.")

    html = f'''
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
      stroke-opacity: 0.5 !important;
    }}

    /* ── Style par défaut des nœuds ── */
    .markmap-foreign div {{
      display: inline-block;
      padding: 2px 8px;
      border-radius: 4px;
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      font-size: 11px;
      font-weight: 500;
      color: #1e293b !important;
      transition: all 0.2s;
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

      // Couleurs basées sur l'image fournie
      const BRANCH_COLORS = [
        '#8b5cf6', // Humains (Violet)
        '#d946ef', // Infra (Magenta)
        '#f43f5e', // Logiciels (Rose/Rouge)
        '#f97316', // Gestion (Orange)
        '#3b82f6', // Marketing (Bleu)
        '#06b6d4', // Stores (Cyan)
        '#10b981', // QA (Vert)
        '#84cc16', // Opé (Lime)
        '#eab308', // Paiement (Jaune)
        '#f59e0b'  // Finance (Or)
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
        nodeMinHeight: 16,
        spacingVertical: 8,
        spacingHorizontal: 50,
        paddingX: 8,
        color: (node) => node._color || '#4F46E5',
      }}, root);

      function styleNodes() {{
        document.querySelectorAll('.markmap-foreign div').forEach(div => {{
          let parentG = div.closest('.markmap-node');
          if (parentG) {{
            let circle = parentG.querySelector('circle');
            if (circle) {{
              let color = circle.getAttribute('fill');
              div.style.background = color;
              div.style.color = '#ffffff';
              div.style.borderRadius = '10px';
              div.style.padding = '3px 10px';
              div.style.boxShadow = '0 1px 3px rgba(0,0,0,0.1)';
              div.style.fontSize = '11px';
            }}
          }}
        }});
      }}

      setTimeout(styleNodes, 500);
      setTimeout(styleNodes, 1500);
      
      const observer = new MutationObserver(styleNodes);
      observer.observe(document.getElementById('mindmap'), {{ childList: true, subtree: true }});
    }})();
  </script>
</body>
</html>
'''

    components.html(html, height=900, scrolling=False)
