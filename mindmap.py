import streamlit as st
import os

def build_mindmap_tab():
    st.markdown("### 🧠 Mindmap du Projet")
    
    # Chemin vers l'image copiée
    image_path = "mindmap.png"
    
    if os.path.exists(image_path):
        # On utilise une largeur personnalisée pour que ce soit bien lisible
        st.image(image_path, caption="Structure détaillée des coûts — Book One", use_container_width=True)
        
        with st.expander("🔍 Zoom sur l'image"):
            st.markdown(f'<a href="https://raw.githubusercontent.com/LudovicPicard/Gestion_Co-t/main/mindmap.png" target="_blank">Cliquez ici pour ouvrir l\'image en plein écran</a>', unsafe_allow_html=True)
    else:
        st.error("L'image mindmap.png est introuvable à la racine du projet.")
        st.info("Assurez-vous que le fichier mindmap.png a bien été poussé sur le dépôt.")
