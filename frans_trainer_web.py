import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Woordsoorten Trainer", layout="centered")

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

def nieuwe_zin():
    st.session_state.index = (st.session_state.index + 1) % len(st.session_state.zinnen)
    st.session_state.feedback = ""
    st.session_state.user_input = ""

st.title("🧠 Woordsoorten oefenen")

zin, correct_antwoord = st.session_state.zinnen[st.session_state.index]
st.markdown(f"<h3 style='color:#364953;'>Zin:</h3><p style='font-size:18px'>{zin}</p>", unsafe_allow_html=True)

# Uniek key voor input, veranderend elke keer (voor forcing rerender)
input_key = f"user_input_{st.session_state.index}"

user_input = st.text_input(
    "Wat is het onderwerp?",
    key=input_key,
    value=st.session_state.user_input,
    label_visibility="collapsed",
    placeholder="Typ hier je antwoord..."
)

# Knop "Controleer"
if st.button("Controleer", key=f"controleer_button_{st.session_state.index}"):
    if user_input.strip().lower() == correct_antwoord.lower():
        st.session_state.feedback = "✅ Goed gedaan!"
    else:
        st.session_state.feedback = f"❌ Fout, het juiste antwoord was: {correct_antwoord}"
    nieuwe_zin()
    # Gebruik st.experimental_rerun om volledig te herladen en focus reset
    st.experimental_rerun()

# Feedback tonen
if st.session_state.feedback:
    if "✅" in st.session_state.feedback:
        st.success(st.session_state.feedback)
    else:
        st.error(st.session_state.feedback)

# JavaScript om focus automatisch te zetten op het inputveld na renderen
focus_js = f"""
<script>
function setFocus() {{
    const input = window.parent.document.querySelector('input[id="{input_key}"]');
    if(input){{
        input.focus();
        input.selectionStart = input.selectionEnd = input.value.length;
    }} else {{
        setTimeout(setFocus, 100);
    }}
}}
setFocus();
</script>
"""
components.html(focus_js, height=0, width=0)
