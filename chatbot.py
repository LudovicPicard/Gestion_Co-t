import streamlit as st
import requests
import json

MISTRAL_API_KEY = "fhlDd6kR7RGDZ9HcUiOngJQAETxm1Tln"
MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"
# Modèle rapide pour des réponses quasi-instantanées
MISTRAL_MODEL = "mistral-small-latest"

def get_system_prompt(kpis, budget_global, total_rh, total_sat, provision, config, equipe_index, taches):
    """Génère le prompt système en injectant le contexte réel du projet."""
    equipe_str = "\n".join([f"- {m['label']} ({m['type']}) : {m.get('salaire_brut_annuel', 0)}€ brut/an" for m in equipe_index.values()])
    sat_str = "\n".join([f"- {s['nom']} ({s['categorie']}) : {s['montant']}€" for s in st.session_state.couts_satellites])
    date_livraison = kpis['date_fin'].strftime('%d/%m/%Y') if kpis.get('nb_taches') else 'Non définie'

    return f"""Tu es l'Assistant IA de pilotage de projet pour le projet "{config['nom']}".
Ton rôle est d'analyser les données financières, RH et de planning pour répondre aux questions du chef de projet.
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
1. Réponds en français, de façon concise et analytique (max 5 phrases).
2. Base-toi UNIQUEMENT sur les données ci-dessus pour les chiffres.
3. Agis comme un expert PMO / Contrôleur de Gestion.
4. N'invente pas de coûts ou de ressources absentes.
"""

def stream_mistral(messages_history):
    """Appel streamé vers l'API Mistral — yield chunk par chunk."""
    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "model": MISTRAL_MODEL,
        "messages": messages_history,
        "temperature": 0.2,
        "stream": True,
    }
    try:
        with requests.post(MISTRAL_API_URL, headers=headers, json=data, stream=True, timeout=30) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if not line:
                    continue
                line = line.decode("utf-8")
                if line.startswith("data: "):
                    payload = line[6:]
                    if payload.strip() == "[DONE]":
                        break
                    try:
                        chunk = json.loads(payload)
                        delta = chunk["choices"][0]["delta"].get("content", "")
                        if delta:
                            yield delta
                    except json.JSONDecodeError:
                        continue
    except Exception as e:
        yield f"\n\n⚠️ Erreur API Mistral : {str(e)}"

@st.dialog("🤖 Assistant IA — Copilote de Projet", width="large")
def open_chatbot_dialog(kpis, budget_global, total_rh, total_sat, provision, config, equipe_index, taches):
    st.caption("Posez n'importe quelle question sur le budget, le planning ou l'équipe. L'IA connaît le contexte complet du projet en temps réel.")

    # Initialisation de l'historique
    if "messages" not in st.session_state:
        st.session_state.messages = []

    system_prompt = get_system_prompt(kpis, budget_global, total_rh, total_sat, provision, config, equipe_index, taches)

    # Affichage de l'historique
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Bouton pour effacer l'historique
    if st.session_state.messages:
        if st.button("🗑️ Effacer la conversation", key="clear_chat"):
            st.session_state.messages = []
            st.rerun()

    # Saisie utilisateur
    if prompt := st.chat_input("Posez votre question sur le projet…"):
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        api_messages = [{"role": "system", "content": system_prompt}] + st.session_state.messages

        # Streaming de la réponse
        with st.chat_message("assistant"):
            full_response = st.write_stream(stream_mistral(api_messages))

        st.session_state.messages.append({"role": "assistant", "content": full_response})
