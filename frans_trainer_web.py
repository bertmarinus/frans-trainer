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

# Dropdowns voor werkwoorden en tijden
infinitieven = sorted(df["Infinitief"].unique())
werkwoord = st.selectbox("Kies werkwoord:", infinitieven)
tijden = sorted(df[df["Infinitief"] == werkwoord]["Tijd"].unique())
selectie_tijden = st.multiselect("Kies tijden:", tijden, default=tijden)

filtered = df[(df["Infinitief"] == werkwoord) & (df["Tijd"].isin(selectie_tijden))]

# Session state initiëren
if "score" not in st.session_state:
    st.session_state.score = {"goed": 0, "totaal": 0, "log": []}

if "herhaling" not in st.session_state:
    st.session_state.herhaling = {}

if "bezochte_zinnen" not in st.session_state:
    st.session_state.bezochte_zinnen = set()

# Functie om volgende zin te selecteren
def select_zin():
    kandidaten = filtered.copy()
    kandidaten["HerhalingScore"] = kandidaten["Zin"].apply(lambda z: st.session_state.herhaling.get(z, 0))
    
    # Filter uit bezochte zinnen
    overgebleven = kandidaten[~kandidaten["Zin"].isin(st.session_state.bezochte_zinnen)]
    
    # Als alles bezocht is, reset bezochte zinnen
    if overgebleven.empty:
        st.session_state.bezochte_zinnen = set()
        overgebleven = kandidaten.copy()
        overgebleven["HerhalingScore"] = overgebleven["Zin"].apply(lambda z: st.session_state.herhaling.get(z, 0))
    
    # Sorteer op HerhalingScore en kies de eerste
    overgebleven = overgebleven.sort_values("HerhalingScore")
    volgende = overgebleven.iloc[0]
    
    # Markeer als bezocht
    st.session_state.bezochte_zinnen.add(volgende["Zin"])
    
    return volgende

if "huidige" not in st.session_state:
    st.session_state.huidige = select_zin()

# Oefening tonen
st.subheader("Oefening")
st.write(f"**Zin:** {st.session_state.huidige['Zin']}")
st.write(f"**Tijd:** {st.session_state.huidige['Tijd']}")

# Gebruik een unieke key zodat Streamlit het veld goed beheert
antwoord = st.text_input("Vul de juiste vervoeging in:", key="antwoord_field")

controleer = st.button("Controleer")
hint = st.button("Hint")

if controleer:
    st.session_state.score["totaal"] += 1
    juist = antwoord.strip().lower() == st.session_state.huidige["Vervoeging"].lower()
    if juist:
        st.session_state.score["goed"] += 1
        st.success("✅ Goed!")
    else:
        st.error(f"❌ Fout! Het juiste antwoord is: {st.session_state.huidige['Vervoeging']}")
    
    # Herhalingsscore bijwerken
    zin = st.session_state.huidige["Zin"]
    st.session_state.herhaling[zin] = st.session_state.herhaling.get(zin, 0) + (0 if juist else 1)
    st.session_state.score["log"].append((datetime.date.today(), int(juist), 1))
    
    # Volgende zin selecteren
    st.session_state.huidige = select_zin()
    
    # Antwoordveld resetten via key (Streamlit doet dit automatisch bij rerun)
    st.experimental_rerun()

if hint:
    st.info(f"Hint: {st.session_state.huidige['Vervoeging']}")

st.write(f"**Score:** {st.session_state.score['goed']} / {st.session_state.score['totaal']}")

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
