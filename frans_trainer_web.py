import streamlit as st
import pandas as pd
import random
import datetime

st.set_page_config(page_title="Frans Trainer", layout="wide")

# --- Helper functies ---
def load_data(file=None):
    if file is not None:
        df = pd.read_csv(file)
    else:
        # voorbeelddata
        df = pd.DataFrame([
            {"Werkwoord": "avoir", "Zin": "J'___ un chat.", "Vervoeging": "ai", "Hint": "Vervoeging van avoir, 1e persoon enkelvoud"},
            {"Werkwoord": "être", "Zin": "Tu ___ content.", "Vervoeging": "es", "Hint": "Vervoeging van être, 2e persoon enkelvoud"},
            {"Werkwoord": "savoir", "Zin": "Ils ___ la réponse.", "Vervoeging": "savent", "Hint": "Vervoeging van savoir, 3e persoon meervoud"}
        ])
    return df

def select_zin():
    # kies een zin uit de gefilterde dataframe
    if "df_filtered" not in st.session_state or st.session_state.df_filtered.empty:
        return None
    return random.choice(st.session_state.df_filtered.to_dict(orient="records"))

# --- Session state initialisatie ---
if "bestand" not in st.session_state:
    st.session_state.bestand = None
if "df" not in st.session_state:
    st.session_state.df = load_data()
if "df_filtered" not in st.session_state:
    st.session_state.df_filtered = st.session_state.df
if "huidige" not in st.session_state:
    st.session_state.huidige = select_zin()
if "score" not in st.session_state:
    st.session_state.score = {"goed": 0, "totaal": 0, "log": []}
if "herhaling" not in st.session_state:
    st.session_state.herhaling = {}
if "naar_volgende" not in st.session_state:
    st.session_state.naar_volgende = False

# --- Bestandsupload ---
bestand = st.file_uploader("Upload een CSV bestand (optioneel)", type=["csv"])
if bestand is not None:
    st.session_state.df = load_data(bestand)
    st.session_state.df_filtered = st.session_state.df
    st.session_state.huidige = select_zin()
    if "antwoord_input" in st.session_state:
        del st.session_state["antwoord_input"]

# --- Dropdown werkwoorden ---
werkwoorden = st.session_state.df["Werkwoord"].unique().tolist()
gekozen_werkwoord = st.selectbox("Kies een werkwoord", werkwoorden)

# Filter dataframe op gekozen werkwoord
st.session_state.df_filtered = st.session_state.df[st.session_state.df["Werkwoord"] == gekozen_werkwoord]
if st.session_state.huidige not in st.session_state.df_filtered.to_dict(orient="records"):
    st.session_state.huidige = select_zin()
    if "antwoord_input" in st.session_state:
        del st.session_state["antwoord_input"]

# --- Huidige oefening ---
if st.session_state.huidige is not None:
    st.write(f"**Zin:** {st.session_state.huidige['Zin']}")

    antwoord = st.text_input("Vul de juiste vervoeging in:", value="", key="antwoord_input")

    # Hint-knop
    if st.button("Hint"):
        st.info(st.session_state.huidige["Hint"])

    if st.button("Controleer"):
        juist = antwoord.strip().lower() == st.session_state.huidige["Vervoeging"].lower()
        st.session_state.score["totaal"] += 1
        if juist:
            st.session_state.score["goed"] += 1
            st.success("✅ Goed!")
        else:
            st.error(f"❌ Fout! Het juiste antwoord is: {st.session_state.huidige['Vervoeging']}")

        # log voor herhaling
        zin = st.session_state.huidige["Zin"]
        st.session_state.herhaling[zin] = st.session_state.herhaling.get(zin, 0) + (0 if juist else 1)
        st.session_state.score["log"].append((datetime.date.today(), int(juist), 1))

        # markeer dat we naar de volgende zin moeten
        st.session_state.naar_volgende = True

# --- Volgende zin afhandeling ---
if st.session_state.naar_volgende:
    st.session_state.huidige = select_zin()
    st.session_state.naar_volgende = False
    # reset inputveld veilig
    if "antwoord_input" in st.session_state:
        del st.session_state["antwoord_input"]
    # input opnieuw renderen
    st.text_input("Vul de juiste vervoeging in:", value="", key="antwoord_input")

# --- Score overzicht ---
st.write(f"Score: {st.session_state.score['goed']} / {st.session_state.score['totaal']}")
