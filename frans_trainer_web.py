# frans_trainer_streamlit.py
# Streamlit app converted from frans_trainer.py
# Usage: streamlit run frans_trainer_streamlit.py

import streamlit as st
import pandas as pd
import random
import math
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Tuple, Optional

st.set_page_config(page_title="Franse Werkwoorden Trainer", layout="centered", initial_sidebar_state="expanded")

# Builtin example sentences (matches original)
BUILTIN_DATA = [
    ("Je ___ que tu as raison. (présent)", "sais", "présent", "savoir"),
    ("Il ___ très fatigué hier. (imparfait)", "était", "imparfait", "être"),
    ("Nous ___ un bon film hier soir. (passé composé)", "avons vu", "passé composé", "voir"),
    ("Tu ___ malade la semaine dernière. (passé composé)", "as été", "passé composé", "être"),
    ("Elles ___ beaucoup de choses. (présent)", "savent", "présent", "savoir")
]

DEFAULT_FILENAME = "Frans_werkwoorden.xlsx"  # file in root if present

# ------- Utility functions -------

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
    df["Zin"] = df["Zin"].astype(str).str.strip()
    df["Vervoeging"] = df["Vervoeging"].astype(str).str.strip()
    df["Tijd"] = df["Tijd"].astype(str).str.strip()
    df["Infinitief"] = df["Infinitief"].astype(str).str.strip()
    return list(df.itertuples(index=False, name=None))

def load_initial_data():
    # Try default excel, else builtin
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

def init_session_state():
    if "data" not in st.session_state:
        st.session_state.data = load_initial_data()
    if "source" not in st.session_state:
        st.session_state.source = "default"  # default, builtin, uploaded
    if "verb" not in st.session_state:
        st.session_state.verb = ""
    if "tijden" not in st.session_state:
        st.session_state.tijden = []
    if "filtered" not in st.session_state:
        st.session_state.filtered = []
    if "current" not in st.session_state:
        st.session_state.current = None  # tuple (Zin, Vervoeging, Tijd, Infinitief)
    if "score_good" not in st.session_state:
        st.session_state.score_good = 0
    if "score_total" not in st.session_state:
        st.session_state.score_total = 0
    if "history" not in st.session_state:  # list of dicts with timestamp and correct boolean
        st.session_state.history = []
    if "meta" not in st.session_state:
        # meta keyed by unique id (index) or by tuple string, storing error_count and last_practiced datetime
        st.session_state.meta = {}  # {key: {"errors": int, "last": datetime}}
    if "rng_seed" not in st.session_state:
        st.session_state.rng_seed = random.randrange(2**30)

def make_key(item):
    # item is tuple (Zin, Vervoeging, Tijd, Infinitief)
    return f"{item[0]}||{item[1]}||{item[2]}||{item[3]}"

def ensure_meta_for_items(items):
    for it in items:
        k = make_key(it)
        if k not in st.session_state.meta:
            st.session_state.meta[k] = {"errors": 0, "last": None}

def days_since(dt: Optional[datetime]):
    if dt is None:
        return 9999.0
    delta = datetime.now() - dt
    return delta.total_seconds() / (3600 * 24)

def priority_score(item):
    # Higher score => higher chance to be picked
    k = make_key(item)
    m = st.session_state.meta.get(k, {"errors": 0, "last": None})
    errors = m["errors"]
    last = m["last"]
    days = days_since(last)
    # formula: combine errors and recency. Tuneable coefficients.
    # Items with more errors and longer not practiced get higher priority.
    score = (1 + errors) * (1 + math.log1p(days))
    # small random jitter to avoid ties
    score *= random.uniform(0.9, 1.1)
    return max(score, 0.0001)

def choose_next_item():
    items = st.session_state.filtered
    if not items:
        st.session_state.current = None
        return None
    ensure_meta_for_items(items)
    # Build weights from priority_score, then sample weighted
    weights = [priority_score(it) for it in items]
    total = sum(weights)
    if total <= 0:
        st.session_state.current = random.choice(items)
        return st.session_state.current
    pick = random.uniform(0, total)
    cum = 0.0
    for it, w in zip(items, weights):
        cum += w
        if pick <= cum:
            st.session_state.current = it
            return it
    st.session_state.current = items[-1]
    return items[-1]

def record_attempt(item, correct: bool):
    k = make_key(item)
    meta = st.session_state.meta.setdefault(k, {"errors": 0, "last": None})
    if not correct:
        meta["errors"] += 1
    else:
        # on success, decrease recent error count slowly (spaced repetition reinforcement)
        meta["errors"] = max(0, meta["errors"] - 1)
    meta["last"] = datetime.now()
    st.session_state.history.append({"timestamp": datetime.now(), "correct": bool(correct)})

def reset_score():
    st.session_state.score_good = 0
    st.session_state.score_total = 0
    st.session_state.history = []

# ------- Initialize session state -------
init_session_state()

# ------- Sidebar: Data source and selection -------
st.sidebar.title("Bron en selectie")

# Data source radio
source = st.sidebar.radio("Databron", ("Standaard bestand (Frans_werkwoorden.xlsx)", "Ingebouwde voorbeeldzinnen", "Upload Excel/CSV"))

if source.startswith("Standaard"):
    # Try to load DEFAULT_FILENAME if not already loaded from that file
    if st.session_state.source != "default_loaded":
        p = Path(DEFAULT_FILENAME)
        if p.exists():
            data = read_data_from_file(p)
            if data:
                st.session_state.data = data
                st.session_state.source = "default_loaded"
        else:
            # Keep whatever was already loaded (likely builtin)
            st.session_state.source = "default"
    st.sidebar.write(f"Standaard bestand: {DEFAULT_FILENAME}")
elif source.startswith("Ingebouwde"):
    st.session_state.data = BUILTIN_DATA
    st.session_state.source = "builtin"
    st.sidebar.write("Ingebouwde voorbeeldzinnen geselecteerd.")
else:
    uploaded = st.sidebar.file_uploader("Upload Excel (.xlsx/.xls/.csv)", type=["xlsx", "xls", "csv"])
    if uploaded is not None:
        try:
            # Use pandas to read uploaded file
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
                st.session_state.source = "uploaded"
                st.sidebar.success(f"Gelaad: {uploaded.name} ({len(st.session_state.data)} rijen)")
        except Exception as e:
            st.sidebar.error(f"Fout bij inlezen: {e}")

# Prepare data options
data = st.session_state.data
infinitieven = sorted(set(row[3] for row in data))
if not infinitieven:
    st.error("Geen werkwoorden gevonden in de dataset.")
    st.stop()

# Select verb and tijden
verb = st.sidebar.selectbox("Kies werkwoord (infinitief)", options=infinitieven, index=0 if st.session_state.verb == "" else max(0, infinitieven.index(st.session_state.verb)) if st.session_state.verb in infinitieven else 0)
# Build list of tijden from data for this verb
all_tijden_set = sorted(set(row[2] for row in data if row[3] == verb), key=lambda s: s.lower())
# Provide a sensible order if present
tijd_order = ["présent", "imparfait", "passé composé", "futur"]
tijden_ordered = [t for t in tijd_order if t in all_tijden_set] + [t for t in all_tijden_set if t not in tijd_order]
tijd_options = ["Alle tijden"] + tijden_ordered

tijden = st.sidebar.multiselect("Kies één of meerdere tijden", options=tijd_options, default=st.session_state.tijden if st.session_state.tijden else ["Alle tijden"])

# Persist selection
st.session_state.verb = verb
st.session_state.tijden = tijden

# Update filtered dataset
st.session_state.filtered = filter_data(data, verb, tijden)
ensure_meta_for_items(st.session_state.filtered)

# ------- Main area -------
st.title("Franse Werkwoorden Trainer")
st.markdown("Vul de ontbrekende vervoeging in. De app houdt score bij en past spaced repetition toe zodat moeilijkere zinnen vaker terugkomen.")

# Expander: Handleiding
with st.expander("Handleiding"):
    st.markdown("""
- Kies een databron: standaardbestand, ingebouwde voorbeelden of upload een Excel/CSV-bestand (4 kolommen: Zin, Vervoeging, Tijd, Infinitief).
- Kies een werkwoord (infinitief) en één of meerdere tijden (of 'Alle tijden').
- Er verschijnt een zin met een invulveld. Typ de vervoeging en klik 'Controleer' of druk Enter.
- Gebruik 'Hint' om het juiste antwoord te zien.
- De score wordt live bijgehouden. De grafiek toont voortgang per dag.
- Spaced repetition: zinnen die vaker fout worden beantwoord of langer niet geoefend zijn, krijgen voorrang.
""")

# Layout columns for responsive UI
col1, col2 = st.columns([3, 1])

with col1:
    st.subheader(f"Oefen: {verb}")
    if not st.session_state.filtered:
        st.warning("Er zijn geen zinnen voor deze selectie. Probeer een ander werkwoord of andere tijden.")
    else:
        # If no current item or filtered changed, choose next
        if st.session_state.current is None or st.session_state.current not in st.session_state.filtered:
            choose_next_item()

        current = st.session_state.current
        if current:
            zin_text = current[0]
            correct_answer = current[1]
            tijd_label = current[2]
            st.markdown(f"**Zin**  \n{zin_text}")
            st.markdown(f"_Tijd: {tijd_label}_")
            # Input and buttons
            # Use a single form to allow Enter submit
            with st.form(key="answer_form", clear_on_submit=False):
                answer = st.text_input("Vervoeging invullen", key="answer_input", placeholder="Typ hier de vervoeging", value="")
                submitted = st.form_submit_button("Controleer")
                hint_btn = st.form_submit_button("Hint")
                reset_btn = st.form_submit_button("Reset score")
                # Note: Streamlit forms submit all buttons; we check which was clicked by order.
            # Handle actions
            # Hint
            if hint_btn:
                st.info(f"Hint — juiste antwoord: {correct_answer}")
            # Reset
            if reset_btn:
                reset_score()
                st.success("Score gereset.")
            # Check (from submit)
            if submitted:
                user_ans = (answer or "").strip().lower()
                st.session_state.score_total += 1
                if user_ans == correct_answer.strip().lower():
                    st.session_state.score_good += 1
                    st.success("✔️ Goed!")
                    record_attempt(current, True)
                else:
                    st.session_state.score_good = st.session_state.score_good  # unchanged
                    st.error(f"✖️ Fout — juiste antwoord: {correct_answer}")
                    record_attempt(current, False)
                # After recording, select next item with small bias to avoid immediate repeat
                choose_next_item()
                # Clear text_input by rerunning; we set session_state answer_input to ""
                st.session_state["answer_input"] = ""

with col2:
    st.subheader("Status")
    st.metric("Score (goed / totaal)", f"{st.session_state.score_good} / {st.session_state.score_total}")
    # Show progress summary
    total_items = len(st.session_state.filtered)
    st.write(f"Zinnen in selectie: {total_items}")
    # Show mini table of top 'hard' items (most errors)
    meta_items = []
    for it in st.session_state.filtered:
        k = make_key(it)
        m = st.session_state.meta.get(k, {"errors": 0, "last": None})
        meta_items.append({"Zin": it[0], "Vervoeging": it[1], "Tijd": it[2], "Infinitief": it[3],
                           "errors": m["errors"], "last": m["last"]})
    if meta_items:
        df_meta = pd.DataFrame(meta_items)
        df_hard = df_meta.sort_values(["errors", "last"], ascending=[False, True]).head(5)
        st.write("Moeilijkste zinnen (top 5)")
        st.table(df_hard[["Zin", "errors", "last"]])

# ------- Progress chart -------
st.subheader("Voortgang per dag")
if st.session_state.history:
    hist_df = pd.DataFrame(st.session_state.history)
    hist_df["date"] = hist_df["timestamp"].dt.date
    agg = hist_df.groupby("date")["correct"].agg(['sum', 'count']).reset_index()
    agg["accuracy"] = (agg["sum"] / agg["count"]) * 100
    agg = agg.sort_values("date")
    # Display chart of accuracy and attempts
    st.line_chart(data=agg.set_index("date")[["accuracy"]])
    st.bar_chart(data=agg.set_index("date")[["count"]])
    st.write("Legenda: lijn = accuracy (%) per dag, balk = aantal pogingen per dag")
else:
    st.info("Nog geen oefenpogingen geregistreerd.")

# ------- Footer / Tips -------
st.markdown("---")
st.markdown("Tip: Voor het beste effect oefen dagelijks. De spaced repetition zorgt dat moeilijkheden terugkomen.")

# ------- Keyboard shortcuts / accessibility note -------
st.caption("Opmerking: In Streamlit kun je Enter gebruiken om het formulier te verzenden nadat je 'Controleer' hebt geklikt in het form-veld. Gebruik de Hint-knop om snel het juiste antwoord te zien.")

# End of file
