import streamlit as st
import requests
import json
from datetime import datetime

MISTRAL_API_KEY = "fhlDd6kR7RGDZ9HcUiOngJQAETxm1Tln"
MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"

def get_system_prompt(kpis, budget_global, total_rh, total_sat, provision, config, equipe_index, taches):
    """Génère le prompt système en injectant le contexte réel du projet."""
    
    # Résumé de l'équipe
    equipe_str = "\n".join([f"- {m['label']} ({m['type']}) : {m.get('salaire_brut_annuel', 0)}€ brut/an" for m in equipe_index.values()])
    
    # Résumé des satellites
    sat_str = "\n".join([f"- {s['nom']} ({s['categorie']}) : {s['montant']}€" for s in st.session_state.couts_satellites])
    
    date_livraison = kpis['date_fin'].strftime('%d/%m/%Y') if kpis.get('nb_taches') else 'Non définie'
    
    prompt = f"""Tu es l'Assistant IA de pilotage de projet pour le projet "{config['nom']}".
Ton rôle est d'analyser les données financières, RH et de planning du projet pour répondre aux questions du directeur de projet ou des parties prenantes.
Tu as accès en temps réel aux données suivantes :

### RÉSUMÉ FINANCIER GLOBAL
- Budget Global (Projection) : {int(budget_global):,} €
- Part Ressources Humaines (RH) : {int(total_rh):,} €
- Coûts Satellites (Fixes) : {int(total_sat):,} €
- Provision pour Risques : {int(provision):,} € (Taux : {st.session_state.provision_risque_pct*100:.0f}%)

### DÉTAIL DES COÛTS SATELLITES
{sat_str}

### PLANNING ET AVANCEMENT
- Tâches totales : {kpis['nb_taches']} ({kpis.get('nb_critiques', 0)} critiques)
- Charge totale (Jours/Homme) : {kpis['total_jh']} J/H
- Durée estimée : {kpis['nb_semaines']} semaines
- Date de livraison prévue : {date_livraison}

### ÉQUIPE DU PROJET
{equipe_str}

### CONSIGNES
1. Sois professionnel, concis, précis et analytique.
2. Si on te pose une question sur les chiffres, base-toi UNIQUEMENT sur les données ci-dessus.
3. Agis comme un expert PMO / Contrôleur de Gestion.
4. N'invente jamais de coûts ou de ressources qui ne sont pas listés.
"""
    return prompt

def call_mistral_api(messages_history):
    """Appel à l'API Mistral avec l'historique de la conversation"""
    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    data = {
        "model": "mistral-large-latest",
        "messages": messages_history,
        "temperature": 0.2
    }
    
    try:
        response = requests.post(MISTRAL_API_URL, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Désolé, une erreur de communication avec l'API Mistral est survenue : {str(e)}"

def build_chatbot_tab(kpis, budget_global, total_rh, total_sat, provision, config, equipe_index, taches):
    st.markdown("### 🤖 Assistant IA - Copilote de Projet")
    st.markdown("Posez n'importe quelle question sur le budget, le planning ou l'équipe de ce projet. L'IA a accès en temps réel à l'intégralité du contexte.")
    
    # Initialisation de l'historique dans la session
    if "messages" not in st.session_state:
        st.session_state.messages = []
        
    # Génération du prompt système dynamique caché
    system_prompt = get_system_prompt(kpis, budget_global, total_rh, total_sat, provision, config, equipe_index, taches)
    
    # Affichage de l'historique des messages (en excluant le système)
    for message in st.session_state.messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # Champ de saisie utilisateur
    if prompt := st.chat_input("Que souhaitez-vous savoir sur le projet ? (ex: Pourquoi la provision est-elle si haute ?)"):
        
        # Affichage du message utilisateur
        with st.chat_message("user"):
            st.markdown(prompt)
            
        # Ajout du message utilisateur à l'historique
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Préparation des messages pour l'API (Injection du contexte système caché)
        api_messages = [{"role": "system", "content": system_prompt}] + st.session_state.messages
        
        # Appel à l'API Mistral
        with st.chat_message("assistant"):
            with st.spinner("Analyse du projet en cours..."):
                response = call_mistral_api(api_messages)
                st.markdown(response)
        
        # Ajout de la réponse à l'historique
        st.session_state.messages.append({"role": "assistant", "content": response})
