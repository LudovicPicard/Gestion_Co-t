import streamlit as st

@st.dialog("Test Dialog")
def show_chat():
    for msg in st.session_state.get("msgs", []):
        st.chat_message(msg["role"]).write(msg["content"])
    if p := st.chat_input("Msg"):
        st.session_state.setdefault("msgs", []).append({"role": "user", "content": p})
        st.rerun()

if st.button("Open"):
    show_chat()
