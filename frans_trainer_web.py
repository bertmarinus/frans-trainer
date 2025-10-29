import streamlit as st
import pandas as pd
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

# Data laden
df = load_data()
if df.empty:
    st.warning("Geen gegevens beschikbaar.")
    st.stop()

# Session state initiëren
if "score" not in st.session_state:
    st.session_state.score = {"goed": 0, "totaal": 0, "log": []}
if "herhaling" not in st.session_state:
    st.session_state.herhaling = {}
if "huidige" not in st.session_state:
    st.session_state.huidige = None
if "antwoord" not in st.session_state:
    st.session_state.antwoord = ""

# Functie om zin te selecteren
def select_zin(filtered_df):
    kandidaten = filtered_df.copy()
    kandidaten["HerhalingScore"] = kandidaten["Zin"].apply(lambda z: st.session_state.herhaling.get(z, 0))
    kandidaten = kandidaten.sort_values("HerhalingScore")
    return kandidaten.iloc[0] if not kandidaten.empty else None

# Dropdown werkwoorden en tijden
infinitieven = sorted(df["Infinitief"].unique())
werkwoord = st.selectbox("Kies werkwoord:", infinitieven)

tijden = sorted(df[df["Infinitief"] == werkwoord]["Tijd"].unique())
selectie_tijden = st.multiselect("Kies tijden:", tijden, default=tijden)

filtered = df[(df["Infinitief"] == werkwoord) & (df["Tijd"].isin(selectie_tijden))]

# Als er geen huidige zin is of werkwoord/tijden gewijzigd -> selecteer nieuwe zin
if st.session_state.huidige is None or st.session_state.huidige["Infinitief"] != werkwoord or st.session_state.huidige["Tijd"] not in selectie_tijden:
    st.session_state.huidige = select_zin(filtered)
    st.session_state.antwoord = ""  # Reset inputveld

# Oefening tonen
st.subheader("Oefening")
if st.session_state.huidige is not None:
    st.write(f"**Zin:** {st.session_state.huidige['Zin']}")
    st.write(f"**Tijd:** {st.session_state.huidige['Tijd']}")
else:
    st.info("Geen zinnen beschikbaar voor deze selectie.")
    st.stop()

# Input en controle
antwoord = st.text_input("Vul de juiste vervoeging in:", key="antwoord")

if st.button("Controleer"):
    juist = st.session_state.antwoord.strip().lower() == st.session_state.huidige["Vervoeging"].lower()
    st.session_state.score["totaal"] += 1
    if juist:
        st.session_state.score["goed"] += 1
        st.success("✅ Goed!")
    else:
        st.error(f"❌ Fout! Het juiste antwoord is: {st.session_state.huidige['Vervoeging']}")

    # Update herhaling en log
    zin = st.session_state.huidige["Zin"]
    st.session_state.herhaling[zin] = st.session_state.herhaling.get(zin, 0) + (0 if juist else 1)
    st.session_state.score["log"].append((datetime.date.today(), int(juist), 1))

    # Volgende zin en input resetten
    st.session_state.huidige = select_zin(filtered)
    st.session_state.antwoord = ""

# Hint
if st.button("Hint"):
    st.info(f"Hint: {st.session_state.huidige['Vervoeging']}")

# Score
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
