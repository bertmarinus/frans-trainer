# frans_trainer_streamlit.py
import streamlit as st
import pandas as pd
import random
import math
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Optional
import streamlit.components.v1 as components
import time

st.set_page_config(page_title="Franse Werkwoorden Trainer", layout="centered", initial_sidebar_state="expanded")

BUILTIN_DATA = [
    ("Je ___ que tu as raison. (présent)", "sais", "présent", "savoir"),
    ("Il ___ très fatigué hier. (imparfait)", "était", "imparfait", "être"),
    ("Nous ___ un bon film hier soir. (passé composé)", "avons vu", "passé composé", "voir"),
    ("Tu ___ malade la semaine dernière. (passé composé)", "as été", "passé composé", "être"),
    ("Elles ___ beaucoup de choses. (présent)", "savent", "présent", "savoir")
]

DEFAULT_FILENAME = "Frans_werkwoorden.xlsx"

# ---------------- Utility functions ----------------
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

def make_key(item):
    return f"{item[0]}\n{item[1]}\n{item[2]}\n{item[3]}"

def ensure_meta_for_items(items):
    for it in items:
        k = make_key(it)
        if k not in st.session_state.meta:
            st.session_state.meta[k] = {"errors": 0, "last": None}

def days_since(dt: Optional[datetime]):
    if dt is None:
        return 9999.0
    return (datetime.now() - dt).total_seconds() / (3600 * 24)

def priority_score(item):
    k = make_key(item)
    m = st.session_state.meta.get(k, {"errors": 0, "last": None})
    errors = m["errors"]
    last = m["last"]
    days = days_since(last)
    score = (1 + errors) * (1 + math.log1p(days))
    score *= random.uniform(0.9, 1.1)
    return max(score, 0.0001)

def choose_next_item():
    items = st.session_state.filtered
    if not items:
        st.session_state.current = None
        return None
    ensure_meta_for_items(items)
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
        meta["errors"] = max(0, meta["errors"] - 1)
    meta["last"] = datetime.now()
    st.session_state.history.append({"timestamp": datetime.now(), "correct": bool(correct)})

def reset_score():
    st.session_state.score_good = 0
    st.session_state.score_total = 0
    st.session_state.history = []

# ---------------- Session state init ----------------
def init_session_state():
    st.session_state.setdefault("data", load_initial_data())
    st.session_state.setdefault("source", "default")
    st.session_state.setdefault("verb", "")
    st.session_state.setdefault("tijden", [])
    st.session_state.setdefault("filtered", [])
    st.session_state.setdefault("current", None)
    st.session_state.setdefault("score_good", 0)
    st.session_state.setdefault("score_total", 0)
    st.session_state.setdefault("history", [])
    st.session_state.setdefault("meta", {})
init_session_state()

# ---------------- Sidebar ----------------
st.sidebar.title("Bron en selectie")
source = st.sidebar.radio("Databron", ("Standaard bestand (Frans_werkwoorden.xlsx)", "Ingebouwde voorbeeldzinnen", "Upload Excel/CSV"))
if source.startswith("Standaard"):
    p = Path(DEFAULT_FILENAME)
    if p.exists():
        data_try = read_data_from_file(p)
        if data_try:
            st.session_state.data = data_try
            st.session_state.source = "default_loaded"
    st.sidebar.write(f"Standaardbestand: {DEFAULT_FILENAME}")
elif source.startswith("Ingebouwde"):
    st.session_state.data = BUILTIN_DATA
    st.session_state.source = "builtin"
    st.sidebar.write("Ingebouwde voorbeeldzinnen geselecteerd.")
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
                st.session_state.source = "uploaded"
                st.sidebar.success(f"Gelaad: {uploaded.name} ({len(st.session_state.data)} rijen)")
        except Exception as e:
            st.sidebar.error(f"Fout bij inlezen: {e}")

data = st.session_state.data
infinitieven = sorted(set(row[3] for row in data))
if not infinitieven:
    st.error("Geen werkwoorden gevonden in de dataset.")
    st.stop()

verb = st.sidebar.selectbox("Kies werkwoord (infinitief)", options=infinitieven)
all_tijden_set = sorted(set(row[2] for row in data if row[3] == verb), key=lambda s: s.lower())
tijd_order = ["présent", "imparfait", "passé composé", "futur"]
tijden_ordered = [t for t in tijd_order if t in all_tijden_set] + [t for t in all_tijden_set if t not in tijd_order]
tijd_options = ["Alle tijden"] + tijden_ordered
tijden = st.sidebar.multiselect("Kies één of meerdere tijden", options=tijd_options, default=["Alle tijden"])

st.session_state.verb = verb
st.session_state.tijden = tijden
st.session_state.filtered = filter_data(data, verb, tijden)
ensure_meta_for_items(st.session_state.filtered)

# ---------------- Main UI ----------------
st.title("Franse Werkwoorden Trainer")
st.markdown("Vul de ontbrekende vervoeging in. De app houdt score bij en past spaced repetition toe zodat moeilijkere zinnen vaker terugkomen.")

st.subheader(f"Oefen: {verb}")
if not st.session_state.filtered:
    st.warning("Er zijn geen zinnen voor deze selectie. Probeer een ander werkwoord of andere tijden.")
else:
    if st.session_state.current is None or st.session_state.current not in st.session_state.filtered:
        choose_next_item()
    current = st.session_state.current
    if current:
        zin_text, correct_answer, tijd_label, _ = current
        st.markdown(f"**Zin** \n{zin_text}")
        st.markdown(f"_Tijd: {tijd_label}_")

        with st.form(key="answer_form", clear_on_submit=True):
            answer = st.text_input("Vervoeging invullen", key=f"answer_{hash(current[0])}", placeholder="Typ hier de vervoeging")
            submitted = st.form_submit_button("Controleer")

        if submitted:
            user_ans = (answer or "").strip().lower()
            st.session_state.score_total += 1
            if user_ans == correct_answer.strip().lower():
                st.session_state.score_good += 1
                record_attempt(current, True)
                st.success("✔️ Goed!")
            else:
                record_attempt(current, False)
                st.error(f"✖️ Fout — juiste antwoord: {correct_answer}")

            time.sleep(2)
            choose_next_item()
            st.rerun()

        cols = st.columns([1, 1])
        with cols[0]:
            if st.button("Hint"):
                st.info(f"Hint — juiste antwoord: {correct_answer}")
        with cols[1]:
            if st.button("Reset score"):
                reset_score()
                st.success("Score gereset.")

        st.markdown("---")
        st.subheader("Status")
        st.metric("Score (goed / totaal)", f"{st.session_state.score_good} / {st.session_state.score_total}")
        total_items = len(st.session_state.filtered)
        st.write(f"Zinnen in selectie: {total_items}")

        meta_items = []
        for it in st.session_state.filtered:
            k = make_key(it)
            m = st.session_state.meta.get(k, {"errors": 0, "last": None})
            meta_items.append({"Zin": it[0], "Vervoeging": it[1], "Tijd": it[2], "Infinitief": it[3], "errors": m["errors"], "last": m["last"]})
        if meta_items:
            df_meta = pd.DataFrame(meta_items)
            df_hard = df_meta.sort_values(["errors", "last"], ascending=[False, True]).head(5)
            st.write("Moeilijkste zinnen (top 5)")
            st.table(df_hard[["Zin", "errors", "last"]])

# ---------------- Progress chart ----------------
st.subheader("Voortgang per dag")
if st.session_state.history:
    hist_df = pd.DataFrame(st.session_state.history)
    hist_df["timestamp"] = pd.to_datetime(hist_df["timestamp"])
    hist_df["date"] = hist_df["timestamp"].dt.date
    agg = hist_df.groupby("date")["correct"].agg(['sum', 'count']).reset_index()
    agg["accuracy"] = (agg["sum"] / agg["count"]) * 100
    agg = agg.sort_values("date")
    st.line_chart(data=agg.set_index("date")[["accuracy"]])
    st.bar_chart(data=agg.set_index("date")[["count"]])
    st.write("Legenda: lijn = accuracy (%) per dag, balk = aantal pogingen per dag")
else:
    st.info("Nog geen oefenpogingen geregistreerd.")

# ---------------- Focus fix (blijft stabiel) ----------------
components.html("""
<script>
setTimeout(() => {
  const tryFocus = () => {
    const input = window.parent.document.querySelector('input[type="text"]');
    if (input) {
      input.focus();
    } else {
      setTimeout(tryFocus, 200);
    }
  };
  tryFocus();
}, 200);
</script>
""", height=0)

st.markdown("---")
st.markdown("Tip: Voor het beste effect oefen dagelijks. De spaced repetition zorgt dat moeilijkheden terugkomen.")
