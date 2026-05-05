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
    st.caption("Visualisation interactive de l'ensemble des coûts et de l'organisation du projet. Utilisez la molette pour zoomer, cliquez-glissez pour naviguer.")

    html = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8" />
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    html, body {{ width: 100%; height: 100vh; background: #0f172a; }}
    #mindmap {{ width: 100%; height: 100vh; }}
    .markmap-foreign {{ display: flex; align-items: center; justify-content: center; }}
    /* Scrollbar dark */
    ::-webkit-scrollbar {{ width: 6px; height: 6px; background: #1e293b; }}
    ::-webkit-scrollbar-thumb {{ background: #475569; border-radius: 3px; }}
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
      
      const transformer = new Transformer();
      
      const markdown = {repr(MINDMAP_MARKDOWN)};
      
      const {{ root, features }} = transformer.transform(markdown);
      const {{ styles, scripts }} = transformer.getUsedAssets(features);
      
      if (styles) loadCSS(styles);
      if (scripts) await loadJS(scripts, {{ getMarkmap: () => window.markmap }});
      
      const mm = Markmap.create('#mindmap', {{
        autoFit: true,
        fitRatio: 0.95,
        duration: 400,
        nodeMinHeight: 22,
        spacingVertical: 8,
        spacingHorizontal: 80,
        paddingX: 12,
        color: (node) => {{
          const palette = [
            '#818CF8', '#34D399', '#FB923C', '#F472B6',
            '#38BDF8', '#A78BFA', '#FBBF24', '#6EE7B7',
            '#F87171', '#4ADE80'
          ];
          return palette[node.depth % palette.length];
        }},
      }}, root);
      
      // Dark background for SVG
      const svg = document.getElementById('mindmap');
      svg.style.background = '#0f172a';
    }})();
  </script>
</body>
</html>
"""

    components.html(html, height=750, scrolling=False)
