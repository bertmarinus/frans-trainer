import streamlit as st
import time
import random

# =========================================
# Instellingen
# =========================================
st.set_page_config(page_title="Woordsoorten Trainer", layout="centered")

if "zinnen" not in st.session_state:
    st.session_state.zinnen = [
        ("De hond rent in de tuin.", "hond"),
        ("De jongen leest een boek.", "jongen"),
        ("De kat vangt een muis.", "kat"),
        ("Pieter speelt gitaar.", "Pieter"),
        ("Mijn moeder kookt soep.", "moeder"),
    ]

if "index" not in st.session_state:
    st.session_state.index = 0

if "feedback" not in st.session_state:
    st.session_state.feedback = ""

# =========================================
# Functie om nieuwe zin te tonen
# =========================================
def nieuwe_zin():
    st.session_state.index = (st.session_state.index + 1) % len(st.session_state.zinnen)
    st.session_state.feedback = ""
    st.session_state.user_input = ""
    st.rerun()

# =========================================
# UI layout
# =========================================
st.title("🧠 Woordsoorten oefenen")

zin, correct_antwoord = st.session_state.zinnen[st.session_state.index]
st.write(f"**Zin:** {zin}")

# Invulveld met unieke ID
user_input = st.text_input(
    "Wat is het onderwerp?",
    key="user_input",
    label_visibility="collapsed",
)

# =========================================
# Controleer-knop
# =========================================
col1, col2 = st.columns([1, 3])
with col1:
    if st.button("Controleer", key="controleer_button"):
        if user_input.strip().lower() == correct_antwoord.lower():
            st.session_state.feedback = "✅ Goed gedaan!"
        else:
            st.session_state.feedback = f"❌ Fout, het juiste antwoord was: {correct_antwoord}"
        time.sleep(2)
        nieuwe_zin()

# =========================================
# Feedback tonen
# =========================================
if st.session_state.feedback:
    st.success(st.session_state.feedback) if "✅" in st.session_state.feedback else st.error(st.session_state.feedback)

# =========================================
# Automatisch focus op tekstveld herstellen
# =========================================
focus_script = """
<script>
function refocusInput(){
    const field = window.parent.document.querySelector('input[type="text"][aria-label="Wat is het onderwerp?"]');
    if (field){
        field.focus();
    } else {
        // probeer het nog een paar keer als het veld nog niet geladen is
        setTimeout(refocusInput, 200);
    }
}
// wacht even tot streamlit alles geladen heeft
setTimeout(refocusInput, 600);
</script>
"""
st.markdown(focus_script, unsafe_allow_html=True)
