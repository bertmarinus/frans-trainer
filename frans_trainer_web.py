import streamlit as st
import pandas as pd
import random
import datetime
import matplotlib.pyplot as plt

st.set_page_config(page_title="🇫🇷 Franse Werkwoordentrainer", layout="centered")
st.title("🇫🇷 Franse Werkwoordentrainer")

# 📥 Gegevens inladen
@st.cache_data
def load_default_data():
    try:
        df = pd.read_excel("Frans_werkwoorden.xlsx", engine="openpyxl")
        df.columns = ["Zin", "Vervoeging", "Tijd", "Infinitief"]
        return df.dropna()
    except Exception:
        return pd.DataFrame()

source = st.radio("Kies gegevensbron:", ["Ingebouwde zinnen", "Upload Excel/CSV"])
df = pd.DataFrame()

if source == "Upload Excel/CSV":
    file = st.file_uploader("Upload bestand", type=["xlsx", "csv"])
    if file:
        try:
            df = pd.read_csv(file) if file.name.endswith(".csv") else pd.read_excel(file, engine="openpyxl")
            df.columns = ["Zin", "Vervoeging", "Tijd", "Infinitief"]
        except Exception as e:
            st.error(f"Fout bij inlezen: {e}")
else:
    df = load_default_data()

if df.empty:
    st.warning("Geen gegevens beschikbaar.")
    st.stop()

# 🧠 Session state
for key in ["score", "herhaling", "huidige_zin", "antwoord_temp"]:
    if key not in st.session_state:
        st.session_state[key] = {"goed": 0, "totaal": 0, "log": []} if key == "score" else {}

# 🔍 Selectie
infinitieven = sorted(df["Infinitief"].unique())
werkwoord = st.selectbox("Kies werkwoord:", infinitieven)
tijden = sorted(df[df["Infinitief"] == werkwoord]["Tijd"].unique())
geselecteerde_tijden = st.multiselect("Kies tijden:", tijden, default=tijden)

filtered = df[(df["Infinitief"] == werkwoord) & (df["Tijd"].isin(geselecteerde_tijden))]

# 🎯 Zin selecteren
def selecteer_nieuwe_zin():
    kandidaten = filtered.copy()
    kandidaten["HerhalingScore"] = kandidaten["Zin"].apply(lambda z: st.session_state["herhaling"].get(z, 0))
    kandidaten = kandidaten.sort_values("HerhalingScore")
    return kandidaten.iloc[0] if not kandidaten.empty else None

if not st.session_state["huidige_zin"] or st.session_state["huidige_zin"].get("Infinitief") != werkwoord:
    st.session_state["huidige_zin"] = selecteer_nieuwe_zin()
    st.session_state["antwoord_temp"] = ""

# 📝 Oefening
zin_data = st.session_state["huidige_zin"]
if zin_data:
    st.subheader("Oefening")
    st.write(f"**Zin:** {zin_data['Zin']}")
    st.write(f"**Tijd:** {zin_data['Tijd']}")
    antwoord = st.text_input("Vul de juiste vervoeging in:", value="", key="antwoord_temp")

    if st.button("Controleer"):
        st.session_state["score"]["totaal"] += 1
        juist = antwoord.strip().lower() == zin_data["Vervoeging"].lower()
        if juist:
            st.session_state["score"]["goed"] += 1
            st.success("✅ Goed!")
        else:
            st.error(f"❌ Fout! Het juiste antwoord is: {zin_data['Vervoeging']}")
        zin = zin_data["Zin"]
        st.session_state["herhaling"][zin] = st.session_state["herhaling"].get(zin, 0) + (0 if juist else 1)
        st.session_state["score"]["log"].append((datetime.date.today(), int(juist), 1))
        st.session_state["huidige_zin"] = selecteer_nieuwe_zin()
        st.session_state["antwoord_temp"] = ""

    if st.button("Hint"):
        st.info(f"Hint: {zin_data['Vervoeging']}")

# 📊 Score en voortgang
st.write(f"**Score:** {st.session_state['score']['goed']} / {st.session_state['score']['totaal']}")

if st.button("Toon voortgangsgrafiek"):
    log_df = pd.DataFrame(st.session_state["score"]["log"], columns=["Datum", "Goed", "Totaal"])
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