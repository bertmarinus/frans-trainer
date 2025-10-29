import streamlit as st
import pandas as pd
import random
import datetime
import matplotlib.pyplot as plt

st.set_page_config(page_title='Franse Werkwoordentrainer', layout='centered')
st.title('🇫🇷 Franse Werkwoordentrainer')

@st.cache_data
def load_data():
    try:
        df = pd.read_excel("Frans_werkwoorden.xlsx", engine="openpyxl")
        df = df.dropna()
        df.columns = ["Zin", "Vervoeging", "Tijd", "Infinitief"]
        return df
    except Exception:
        return pd.DataFrame()

# Gegevensbron kiezen
source = st.radio("Kies gegevensbron:", ["Ingebouwde zinnen", "Upload Excel/CSV"])

df = pd.DataFrame()
if source == "Upload Excel/CSV":
    uploaded_file = st.file_uploader("Upload je bestand", type=["xlsx", "csv"])
    if uploaded_file:
        try:
            if uploaded_file.name.endswith(".csv"):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file, engine="openpyxl")
            df.columns = ["Zin", "Vervoeging", "Tijd", "Infinitief"]
        except Exception as e:
            st.error(f"Fout bij inlezen: {e}")
else:
    df = load_data()

if df.empty:
    st.warning("Geen gegevens beschikbaar.")
    st.stop()

# Session state initialiseren
if "score" not in st.session_state:
    st.session_state.score = {"goed": 0, "totaal": 0, "log": []}

if "herhaling" not in st.session_state:
    st.session_state.herhaling = {}

if "huidige" not in st.session_state:
    st.session_state.huidige = None

# Werkwoord en tijden selecteren
infinitieven = sorted(df["Infinitief"].unique())
werkwoord = st.selectbox("Kies werkwoord:", infinitieven, key="select_werkwoord")

tijden = sorted(df[df["Infinitief"] == werkwoord]["Tijd"].unique())
selectie_tijden = st.multiselect("Kies tijden:", tijden, default=tijden, key="select_tijden")

filtered = df[(df["Infinitief"] == werkwoord) & (df["Tijd"].isin(selectie_tijden))]

# Functie om volgende zin te selecteren
def select_zin():
    kandidaten = filtered.copy()
    kandidaten["HerhalingScore"] = kandidaten["Zin"].apply(lambda z: st.session_state.herhaling.get(z, 0))
    kandidaten = kandidaten.sort_values("HerhalingScore")
    if not kandidaten.empty:
        return kandidaten.iloc[0]
    return None

# Update huidige zin bij werkwoord- of tijdwijziging
if st.session_state.huidige is None or st.session_state.huidige["Infinitief"] != werkwoord:
    st.session_state.huidige = select_zin()
    st.session_state.antwoord_input = ""  # inputveld leeg maken

# Functie om naar volgende zin te gaan
def volgende_zin():
    st.session_state.huidige = select_zin()
    st.session_state.antwoord_input = ""  # inputveld leeg maken

st.subheader("Oefening")
if st.session_state.huidige is not None:
    st.write(f"**Zin:** {st.session_state.huidige['Zin']}")
    st.write(f"**Tijd:** {st.session_state.huidige['Tijd']}")

antwoord = st.text_input("Vul de juiste vervoeging in:", value=st.session_state.get("antwoord_input", ""), key="antwoord_input")

# Controleer antwoord
if st.button("Controleer"):
    if st.session_state.huidige is not None:
        st.session_state.score["totaal"] += 1
        juist = antwoord.strip().lower() == st.session_state.huidige["Vervoeging"].lower()
        if juist:
            st.session_state.score["goed"] += 1
            st.success("✅ Goed!")
        else:
            st.error(f"❌ Fout! Het juiste antwoord is: {st.session_state.huidige['Vervoeging']}")
        zin = st.session_state.huidige["Zin"]
        st.session_state.herhaling[zin] = st.session_state.herhaling.get(zin, 0) + (0 if juist else 1)
        st.session_state.score["log"].append((datetime.date.today(), int(juist), 1))
        volgende_zin()

# Hint knop
if st.button("Hint"):
    if st.session_state.huidige is not None:
        st.info(f"Hint: {st.session_state.huidige['Vervoeging']}")

st.write(f"**Score:** {st.session_state.score['goed']} / {st.session_state.score['totaal']}")

# Voortgangsgrafiek
if st.button("Toon voortgangsgrafiek"):
    log_df = pd.DataFrame(st.session_state.score["log"], columns=["Datum", "Goed", "Totaal"])
    if not log_df.empty:
        grafiek = log_df.groupby("Datum").sum()
        grafiek["Percentage"] = grafiek["Goed"] / grafiek["Totaal"] * 100
        fig, ax = plt.subplots()
        grafiek["Percentage"].plot(ax=ax, marker='o', color='blue')
        ax.set_title("Voortgang per dag")
        ax.set_ylabel("Score (%)")
        ax.set_xlabel("Datum")
        ax.grid(True)
        st.pyplot(fig)
    else:
        st.info("Nog geen voortgang beschikbaar.")
