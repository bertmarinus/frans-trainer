# ---------------- Main UI ----------------

st.title("Franse Werkwoorden Trainer")
st.markdown("Vul de ontbrekende vervoeging in. De app houdt score bij en past spaced repetition toe zodat moeilijkere zinnen vaker terugkomen.")

col1, col2 = st.columns([3, 1])

with col1:
    st.subheader(f"Oefen: {verb}")
    if not st.session_state.filtered:
        st.warning("Er zijn geen zinnen voor deze selectie. Probeer een ander werkwoord of andere tijden.")
    else:
        if st.session_state.current is None or st.session_state.current not in st.session_state.filtered:
            choose_next_item()

        current = st.session_state.current
        if current:
            zin_text = current[0]
            correct_answer = current[1]
            tijd_label = current[2]

            st.markdown(f"**Zin**  \n{zin_text}")
            st.markdown(f"_Tijd: {tijd_label}_")

            # Tekstveld met value gekoppeld aan session_state
            answer_value = "" if st.session_state.clear_input else st.session_state.answer_input
            answer = st.text_input(
                "Vervoeging invullen",
                value=answer_value,
                key="answer_input",
                placeholder="Typ hier de vervoeging"
            )

            # Clear flag resetten
            if st.session_state.clear_input:
                st.session_state.clear_input = False
                st.experimental_rerun()

            # Automatische focus
            components.html(
                """
                <script>
                    const input = window.parent.document.querySelector('input[data-testid="stTextInput"]');
                    if (input) { input.focus(); }
                </script>
                """,
                height=0,
            )

            cols = st.columns([1, 1, 1])
            with cols[0]:
                if st.button("Controleer"):
                    user_ans = (st.session_state.get("answer_input", "") or "").strip().lower()
                    st.session_state.score_total += 1
                    if user_ans == correct_answer.strip().lower():
                        st.session_state.score_good += 1
                        record_attempt(current, True)
                        st.success("✔️ Goed!")
                    else:
                        record_attempt(current, False)
                        st.error(f"✖️ Fout — juiste antwoord: {correct_answer}")

                    choose_next_item()
                    st.session_state.clear_input = True
                    st.experimental_rerun()

            with cols[1]:
                if st.button("Hint"):
                    st.info(f"Hint — juiste antwoord: {correct_answer}")

            with cols[2]:
                if st.button("Reset score"):
                    reset_score()
                    st.success("Score gereset.")

with col2:
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

st.markdown("---")
st.caption("Tip: veld leegt zich automatisch en cursor springt terug naar het invoerveld.")
