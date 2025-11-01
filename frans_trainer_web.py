import streamlit as st
import streamlit.components.v1 as components

# Pagina-instellingen
st.set_page_config(page_title="Woordsoorten Trainer", layout="centered")

# Initialiseer session_state
if "zinnen" not in st.session_state:
    st.session_state.zinnen = [
        ("De hond rent in de tuin.", "hond"),
        ("De jongen leest een boek.", "jongen"),
        ("De kat vangt een muis.", "kat"),
        ("Pieter speelt gitaar.", "Pieter"),
        ("Mijn moeder kookt soep.", "moeder"),
        ("De vis zwemt in de vijver.", "vis"),
        ("Het meisje tekent een huis.", "meisje"),
        ("De man werkt in de tuin.", "man"),
        ("De vogel vliegt hoog.", "vogel"),
        ("De baby slaapt rustig.", "baby"),
    ]

if "index" not in st.session_state:
    st.session_state.index = 0
if "feedback" not in st.session_state:
    st.session_state.feedback = ""
if "user_input" not in st.session_state:
    st.session_state.user_input = ""

# Functie om naar volgende zin te gaan en input te resetten
def nieuwe_zin():
    st.session_state.index = (st.session_state.index + 1) % len(st.session_state.zinnen)
    st.session_state.feedback = ""
    st.session_state.user_input = ""

# Titel en zin tonen
st.title("🧠 Woordsoorten oefenen")
zin, correct_antwoord = st.session_state.zinnen[st.session_state.index]
st.markdown(f"<h3 style='color:#364953;'>Zin:</h3><p style='font-size:18px'>{zin}</p>", unsafe_allow_html=True)

# Tekstinput voor antwoord
user_input = st.text_input(
    "Wat is het onderwerp?",
    key="user_input",
    label_visibility="collapsed",
    placeholder="Typ hier je antwoord..."
)

# Controleer-knop
col1, col2 = st.columns([1, 3])
with col1:
    if st.button("Controleer", key="controleer_button"):
        if user_input.strip().lower() == correct_antwoord.lower():
            st.session_state.feedback = "✅ Goed gedaan!"
        else:
            st.session_state.feedback = f"❌ Fout, het juiste antwoord was: {correct_antwoord}"
        nieuwe_zin()
        st.experimental_rerun()

# Feedback tonen
if st.session_state.feedback:
    if "✅" in st.session_state.feedback:
        st.success(st.session_state.feedback)
    else:
        st.error(st.session_state.feedback)

# Automatisch focus terug in inputveld met JavaScript interval
focus_script = """
<script>
const interval = setInterval(() => {
    const input = window.parent.document.querySelector('input[type=text]');
    if (input) {
        input.focus();
        clearInterval(interval);
    }
}, 100);
</script>
"""
components.html(focus_script, height=0, width=0)
