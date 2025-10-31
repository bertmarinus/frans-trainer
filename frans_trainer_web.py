# frans_trainer_streamlit.py
# Streamlit app: Franse werkwoorden trainer (één bestand)
# Run: streamlit run frans_trainer_streamlit.py

import streamlit as st
import pandas as pd
import random
import math
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Optional

st.set_page_config(page_title="Franse Werkwoorden Trainer", layout="centered", initial_sidebar_state="expanded")

# Builtin example sentences
BUILTIN_DATA = [
    ("Je ___ que tu as raison. (présent)", "sais", "présent", "savoir"),
    ("Il ___ très fatigué hier. (imparfait)", "était", "imparfait", "être"),
    ("Nous ___ un bon film hier soir. (passé composé)", "avons vu", "passé composé", "voir"),
    ("Tu ___ malade la semaine dernière. (passé composé)", "as été", "passé composé", "être"),
    ("Elles ___ beaucoup de choses. (présent)", "savent", "présent", "savoir")
]

DEFAULT_FILENAME = "Frans_werkwoorden.xlsx"

# ---------------- Normalization helper ----------------
def normalize(text: str) -> str:
    if text is None:
        return ""
    return "".join(str(text).lower().split())

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
    for col in ["Zin", "Vervoeging", "Tijd", "Infinitief"]:
        df[col] = df[col].astype(str).str.strip()
    return list(df.itertuples(index=False, name=None))

def load_data() -> List[Tuple[str, str, str, str]]:
    """Lees altijd het standaardbestand bij elke rerun"""
    p = Path(DEFAULT_FILENAME)
    if p.exists():
        data = read_data_from_file(p)
        if data:
            return data
    return BUILTIN_DATA

def filter_data(data, infinitief: str, tijden: List[str]):
    sel_inf_norm = normalize(infinitief)
    selected_all = not tijden or ("Alle tijden" in tijden)
    tijden_norm_set = {normalize(t) for t in tijden} if not selected_all else set()

    filtered = []
    for row in data:
        zin, vervoeging, tijd, infinitief_row = row
        if normalize(infinitief_row) != sel_inf_norm:
            continue
        if selected_all or normalize(tijd) in tijden_norm_set:
            filtered.append(row)
    return filtered

def make_key(item):
    return f"{item[0]}||{item[1]}||{item[2]}||{item[3]}"

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
    pick = random.uniform(0, total) if total > 0 else 0
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
st.session_state.setdefault("verb", "")
st.session_state.setdefault("tijden", [])
st.session_state.setdefault("current", None)
st.session_state.setdefault("score_good", 0)
st.session_state.setdefault("score_total", 0)
st.session_state.setdefault("history", [])
st.session_state.setdefault("meta", {})
st.session_state.setdefault("answer_input", "")

# ---------------- Sidebar: Data source and selection ----------------
st.sidebar.title("Bron en selectie")

# Automatisch standaarddata laden
data = load_data()
st.session_state.source = "default_loaded" if data != BUILTIN_DATA else "default"
st.sidebar.write(f"Standaardbestand: {DEFAULT_FILENAME}")

# Upload optie (overschrijft automatisch)
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
            data = list(df.itertuples(index=False, name=None))
            st.session_state.source = "uploaded"
            st.sidebar.success(f"Gelaad: {uploaded.name} ({len(data)} rijen)")
    except Exception as e:
        st.sidebar.error(f"Fout bij inlezen: {e}")

# ---------------- Verb selection ----------------
infinitieven_all = sorted(set(row[3] for row in data), key=lambda s: s.lower())
if not infinitieven_all:
    st.error("Geen werkwoorden gevonden in de dataset.")
    st.stop()

inf_norm_to_display = {normalize(inf): inf for inf in infinitieven_all}
default_verb_display = inf_norm_to_display.get(normalize(st.session_state.verb), infinitieven_all[0])
verb_display = st.sidebar.selectbox("Kies werkwoord (infinitief)", options=infinitieven_all, index=infinitieven_all.index(default_verb_display))
st.session_state.verb = verb_display

# ---------------- Tijden selection ----------------
all_tijden_for_verb = []
seen_norms = set()
for row in data:
    if normalize(row[3]) == normalize(verb_display):
        t_norm = normalize(row[2])
        if t_norm not in seen_norms:
            seen_norms.add(t_norm)
            all_tijden_for_verb.append(row[2].strip())

tijd_order = ["présent", "imparfait", "passé composé", "futur"]
def tijd_sort_key(t):
    try:
        idx = [normalize(x) for x in tijd_order].index(normalize(t))
        return (0, idx)
    except ValueError:
        return (1, t.lower())
all_tijden_for_verb = sorted(all_tijden_for_verb, key=tijd_sort_key)
tijd_options = ["Alle tijden"] + all_tijden_for_verb
default_tijden = st.session_state.tijden if st.session_state.tijden else ["Alle tijden"]
tijden_selected = st.sidebar.multiselect("Kies één of meerdere tijden", options=tijd_options, default=default_tijden)
st.session_state.tijden = tijden_selected

# ---------------- Filter dataset ----------------
st.session_state.filtered = filter_data(data, st.session_state.verb, st.session_state.tijden)
ensure_meta_for_items(st.session_state.filtered)

# ---------------- Main UI ----------------
st.title("Franse Werkwoorden Trainer")
st.markdown("Vul de ontbrekende vervoeging in. De app houdt score bij en past spaced repetition toe.")

with st.expander("Handleiding"):
    st.markdown("""
- Kies een databron: standaardbestand of upload een Excel/CSV-bestand.
- Kies een werkwoord en tijden (of 'Alle tijden').
- Typ de vervoeging in en druk op Enter of 'Controleer'.
- Score wordt bijgehouden en moeilijke items verschijnen vaker.
""")

if not st.session_state.filtered:
    st.warning("Geen zinnen gevonden voor dit werkwoord/tijden-combinatie.")
    st.stop()

if st.session_state.current is None:
    choose_next_item()

item = st.session_state.current
zin, correct_answer, tijd, infinitief = item

st.markdown(f"**Tijd:** {tijd}")
st.markdown(f"**Zin:** {zin.replace('___', '_____')}")

answer_input = st.text_input("Vervoeging:", value=st.session_state.answer_input, key="answer_input")
submitted = st.button("Controleer") or st.session_state.answer_input != ""

if submitted:
    user_ans_norm = normalize(answer_input)
    correct_norm = normalize(correct_answer)
    is_correct = user_ans_norm == correct_norm
    record_attempt(item, is_correct)
    st.session_state.score_total += 1
    if is_correct:
        st.session_state.score_good += 1
        st.success(f"Correct! {correct_answer}")
        st.session_state.answer_input = ""
        choose_next_item()
    else:
        st.error(f"Fout. Correct antwoord: {correct_answer}")
        st.session_state.answer_input = ""
        choose_next_item()

# ---------------- Score display ----------------
st.markdown(f"**Score:** {st.session_state.score_good} / {st.session_state.score_total}")

if st.button("Reset score"):
    reset_score()
