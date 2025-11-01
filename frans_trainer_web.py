import streamlit as st
import pandas as pd
import random
import math
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Optional
import time

# =========================================
# PAGINA-INSTELLINGEN
# =========================================
st.set_page_config(page_title="Franse Werkwoorden Trainer", layout="centered", initial_sidebar_state="expanded")

# =========================================
# DATA EN CONSTANTEN
# =========================================
BUILTIN_DATA = [
    ("Je ___ que tu as raison. (présent)", "sais", "présent", "savoir"),
    ("Il ___ très fatigué hier. (imparfait)", "était", "imparfait", "être"),
    ("Nous ___ un bon film hier soir. (passé composé)", "avons vu", "passé composé", "voir"),
    ("Tu ___ malade la semaine dernière. (passé composé)", "as été", "passé composé", "être"),
    ("Elles ___ beaucoup de choses. (présent)", "savent", "présent", "savoir")
]
DEFAULT_FILENAME = "Frans_werkwoorden.xlsx"

# =========================================
# FUNCTIES VOOR DATA
# =========================================
def read_data_from_file(path: Path) -> Optional[List[Tuple[str, str, str, str]]]:
    try:
        df = pd.read_excel(path, engine="openpyxl")
    except Exception:
        try:
            df = pd.read_csv(path)
        except Exception as e:
            st.warning(f"Kan bestand niet inlezen: {e}")
            return None
    if df.shape[1] < 4:
        st.warning("Het bestand moet minimaal 4 kolommen hebben: Zin, Vervoeging, Tijd, Infinitief.")
        return None
    df = df.iloc[:, :4].dropna()
    df.columns = ["Zin", "Vervoeging", "Tijd", "Infinitief"]
    df = df.astype(str).apply(lambda col: col.str.strip())
    return list(df.itertuples(index=False, name=None))

def load_initial_data():
    p = Path(DEFAULT_FILENAME)
    if p.exists():
        data = read_data_from_file(p)
        if data:
            return data
    return BUILTIN_DATA

def filter_data(data, infinitief: str, tijden: List[str]):
    filtered = [row for row in data if row[3].lower() == infinitief.lower()]
    if not tijden or ("Alle tijden" in tijden):
        return filtered
    tijden_lower = [t.lower() for t in tijden]
    return [row for row in filtered if row[2].lower() in tijden_lower]

# =========================================
# SESSION STATE INIT
# =========================================
def init_session_state():
    st.session_state.setdefault("data", load_initial_data())
    st.session_state.setdefault("verb", "")
    st.session_state.setdefault("tijden", [])
    st.session_state.setdefault("filtered", [])
    st.session_state.setdefault("current", None)
    st.session_state.setdefault("score_good", 0)
    st.session_state.setdefault("score_total", 0)
    st.session_state.setdefault("history", [])
init_session_state()

# =========================================
# SIDEBAR
# =========================================
st.sidebar.title("Bron en selectie")
source = st.sidebar.radio("Databron", ("Standaard bestand (Frans_werkwoorden.xlsx)", "Ingebouwde voorbeeldzinnen", "Upload Excel/CSV"))
if source.startswith("Standaard"):
    p = Path(DEFAULT_FILENAME)
    if p.exists():
        data_try = read_data_from_file(p)
        if data_try:
            st.session_state.data = data_try
elif source.startswith("Ingebouwde"):
    st.session_state.data = BUILTIN_DATA
else:
    uploaded = st.sidebar.file_uploader("Upload Excel (.xlsx/.xls/.csv)", type=["xlsx", "xls", "csv"])
    if uploaded is not None:
        try:
            if uploaded.name.lower().endswith(".csv"):
                df = pd.read_csv(uploaded)
            else:
                df = pd.read_excel(uploaded, engine="openpyxl")
            if df.shape[1] < 4:
                st.sidebar.error("Het bestand moet minimaal 4 kolommen hebben: Zin, Vervoeging, Tijd, Infinitief.")
            else:
                df = df.iloc[:, :4].dropna()
                df.columns = ["Zin", "Vervoeging", "Tijd", "Infinitief"]
                df = df.astype(str).apply(lambda col: col.str.strip())
                st.session_state.data = list(df.itertuples(index=False, name=None))
                st.sidebar.success(f"Gelaad: {uploaded.name} ({len(st.session_state.data)} rijen)")
        except Exception as e:
            st.sidebar.error(f"Fout bij inlezen: {e}")

data = st.session_state.data
infinitieven = sorted(set(row[3].strip().lower() for row in data))
verb = st.sidebar.selectbox("Kies werkwoord (infinitief)", options=infinitieven)
tijd_order = ["présent", "imparfait", "passé composé", "futur"]
all_tijden_set = sorted(set(row[2].strip().lower() for row in data if row[3].strip().lower() == verb))
tijden_ordered = [t for t in tijd_order if t in all_tijden_set] + [t for t in all_tijden_set if t not in tijd_order]
tijd_options = ["Alle tijden"] + tijden_ordered
tijden = st.sidebar.multiselect("Kies één of meerdere tijden", options=tijd_options, default=["Alle tijden"])
st.session_state.verb = verb
st.session_state.tijden = tijden
st.session_state.filtered = filter_data(data, verb, tijden)

# =========================================
# MAIN UI
# =========================================
st.title("Franse Werkwoorden Trainer")
st.markdown("Vul de ontbrekende vervoeging in. De app houdt score bij en past spaced repetition toe.")

if not st.session_state.filtered:
    st.warning("Er zijn geen zinnen voor deze selectie.")
else:
    if st.session_state.current is None or st.session_state.current not in st.session_state.filtered:
        st.session_state.current = random.choice(st.session_state.filtered)
    current = st.session_state.current
    zin_text = current[0]
    correct_answer = current[1]
    tijd_label = current[2]

    st.markdown(f"**Zin**\n{zin_text}")
    st.markdown(f"_Tijd: {tijd_label}_")

    # ✅ FORM voor Enter + autofocus na elke vraag
    with st.form(key="answer_form", clear_on_submit=True):
        answer = st.text_input("Vervoeging invullen", key=f"answer_{hash(current[0])}", placeholder="Typ hier de vervoeging")

        # ✅ Betere focus na elke nieuwe vraag
        st.components.v1.html("""
        <script>
        const observer = new MutationObserver((mutations, obs) => {
          const input = window.parent.document.querySelector('input[type="text"]');
          if (input) {
            input.focus();
            obs.disconnect();
          }
        });
        observer.observe(window.parent.document, { childList: true, subtree: true });
        </script>
        """, height=0)

        cols = st.columns([1, 1, 1])
        with cols[0]:
            submitted = st.form_submit_button("Controleer")
        with cols[1]:
            hint_clicked = st.form_submit_button("Hint")
        with cols[2]:
            reset_clicked = st.form_submit_button("Reset score")

        if submitted:
            user_ans = (answer or "").strip().lower()
            st.session_state.score_total += 1
            if user_ans == correct_answer.strip().lower():
                st.session_state.score_good += 1
                st.success("✔️ Goed!")
            else:
                st.error(f"✖️ Fout — juiste antwoord: {correct_answer}")
            time.sleep(2)
            st.session_state.current = random.choice(st.session_state.filtered)
            st.rerun()

        if hint_clicked:
            st.info(f"Hint — juiste antwoord: {correct_answer}")
        if reset_clicked:
            st.session_state.score_good = 0
            st.session_state.score_total = 0
            st.success("Score gereset.")

    st.markdown("---")
    st.subheader("Status")
    st.metric("Score (goed / totaal)", f"{st.session_state.score_good} / {st.session_state.score_total}")
``
