"""
FairGrade AI — Multi-Agent Examination Evaluation, Feedback & Appeal System
Run with: streamlit run app.py
"""

import streamlit as st
import json
import agents
import ui

st.set_page_config(page_title="FairGrade AI", page_icon="📝", layout="wide")
ui.inject_theme()

# ---------------------------------------------------------------------------
# LOGIN CREDENTIALS
# Demo-grade role gate (shared passcode per role, not per-user accounts).
# Override defaults by setting these in Streamlit Cloud -> Settings -> Secrets:
#   TEACHER_PASSCODE = "yourpasscode"
#   STUDENT_PASSCODE = "yourpasscode"
# ---------------------------------------------------------------------------
TEACHER_PASSCODE = st.secrets.get("TEACHER_PASSCODE", "teach123")
STUDENT_PASSCODE = st.secrets.get("STUDENT_PASSCODE", "learn456")

# ---------------------------------------------------------------------------
# SESSION STATE
# ---------------------------------------------------------------------------
if "records" not in st.session_state:
    st.session_state.records = {}   # student_name -> dict of all agent outputs
if "difficulty" not in st.session_state:
    st.session_state.difficulty = None
if "role" not in st.session_state:
    st.session_state.role = None

# ---------------------------------------------------------------------------
# LOGIN SCREEN
# ---------------------------------------------------------------------------
def show_login():
    ui.login_hero()
    login_tab_t, login_tab_s = st.tabs(["👨‍🏫 Teacher Login", "🎓 Student Login"])

    with login_tab_t:
        pw = st.text_input("Teacher Passcode", type="password", key="teacher_pw")
        if st.button("Login as Teacher"):
            if pw == TEACHER_PASSCODE:
                st.session_state.role = "teacher"
                st.rerun()
            else:
                st.error("Incorrect passcode.")

    with login_tab_s:
        pw = st.text_input("Student Passcode", type="password", key="student_pw")
        if st.button("Login as Student"):
            if pw == STUDENT_PASSCODE:
                st.session_state.role = "student"
                st.rerun()
            else:
                st.error("Incorrect passcode.")


if st.session_state.role is None:
    show_login()
    st.stop()

ui.inject_theme(st.session_state.role)

# ---------------------------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------------------------
st.sidebar.title("📝 FairGrade AI")
st.sidebar.success(f"Logged in as: **{st.session_state.role.title()}**")
if st.sidebar.button("Log out"):
    st.session_state.role = None
    st.rerun()

api_key = st.secrets.get("GROQ_API_KEY", "")
if not api_key:
    api_key = st.sidebar.text_input("Groq API Key", type="password",
                                     help="Get a free key at console.groq.com")
else:
    st.sidebar.caption("✅ Groq API key loaded from app secrets.")

st.sidebar.caption(
    "Multi-agent examination evaluator: dual independent grading, "
    "a moderator that resolves disagreements, personalized feedback, "
    "difficulty analysis, and a student appeal system."
)
st.sidebar.markdown("---")
st.sidebar.caption("⚠️ Demo tip: paste typed answers, or use a clearly printed/scanned sheet "
                    "for the image path. Messy handwriting can reduce OCR accuracy.")

# ---------------------------------------------------------------------------
# ROLE-BASED TABS
# ---------------------------------------------------------------------------
if st.session_state.role == "teacher":
    tab_teacher, tab_results, tab_appeal, tab_difficulty = st.tabs(
        ["👨‍🏫 Teacher: Evaluate", "📊 Results", "🎓 Appeals (view)", "📈 Difficulty Analysis"]
    )
else:
    tab_results, tab_appeal = st.tabs(["📊 My Results", "🎓 Submit Appeal"])
    tab_teacher = None
    tab_difficulty = None

# ---------------------------------------------------------------------------
# TEACHER TAB (teacher role only)
# ---------------------------------------------------------------------------
if tab_teacher is not None:
    with tab_teacher:
        st.header("Set Up & Run Evaluation")

        student_name = st.text_input("Student Name / ID", value="Student 1")

        col1, col2 = st.columns(2)
        with col1:
            question_paper = st.text_area("Question Paper", height=150,
                                           placeholder="Paste the exam questions here...")
            answer_key = st.text_area("Answer Key / Model Answers", height=150,
                                       placeholder="Paste the expected/model answers here...")
        with col2:
            rubric = st.text_area("Grading Rubric / Instructions", height=150,
                                   placeholder="E.g. Definition (2 marks), Example (2 marks), "
                                               "Application (4 marks), Conclusion (2 marks)...")

        st.subheader("Student's Answer Sheet")
        input_mode = st.radio("Input method", ["Paste text", "Upload image (beta OCR)"], horizontal=True)

        student_answer = ""
        if input_mode == "Paste text":
            student_answer = st.text_area("Student's Answers", height=200,
                                           placeholder="Paste the student's written answers here...")
        else:
            uploaded = st.file_uploader("Upload a clear photo/scan of the answer sheet",
                                         type=["png", "jpg", "jpeg"])
            if uploaded and st.button("🔍 Extract Text (OCR Agent)"):
                if not api_key:
                    st.error("Enter your Groq API key in the sidebar first.")
                else:
                    with st.spinner("OCR Agent reading the answer sheet..."):
                        try:
                            extracted = agents.ocr_extract_text(api_key, uploaded.getvalue(),
                                                                 mime_type=uploaded.type)
                            st.session_state["_ocr_result"] = extracted
                        except Exception as e:
                            st.error(f"OCR failed: {e}")
            if "_ocr_result" in st.session_state:
                student_answer = st.text_area(
                    "Extracted text (please review & correct before grading)",
                    value=st.session_state["_ocr_result"], height=200
                )

        st.markdown("---")
        if st.button("🚀 Run Full Multi-Agent Evaluation", type="primary", use_container_width=True):
            if not api_key:
                st.error("Enter your Groq API key in the sidebar first.")
            elif not (question_paper and answer_key and rubric and student_answer):
                st.error("Please fill in the question paper, answer key, rubric, and student answer.")
            else:
                progress = st.progress(0, text="Starting evaluation...")

                progress.progress(10, text="Evaluator A grading independently...")
                primary_eval, primary_err = agents.run_evaluator(
                    api_key, "Evaluator A", question_paper, answer_key, rubric, student_answer)

                progress.progress(35, text="Evaluator B grading independently...")
                secondary_eval, secondary_err = agents.run_evaluator(
                    api_key, "Evaluator B", question_paper, answer_key, rubric, student_answer)

                if primary_err or secondary_err:
                    st.error("One of the evaluator agents returned an unexpected format. "
                             "Try again, or check the raw output below.")
                    st.code(primary_err or "")
                    st.code(secondary_err or "")
                else:
                    progress.progress(60, text="Moderator Agent reconciling both evaluations...")
                    final_eval, mod_err = agents.run_moderator(
                        api_key, question_paper, rubric, primary_eval, secondary_eval)

                    if mod_err:
                        st.error("Moderator Agent returned an unexpected format.")
                        st.code(mod_err)
                    else:
                        progress.progress(85, text="Feedback Agent writing personalized report...")
                        feedback, fb_err = agents.run_feedback(api_key, final_eval, student_answer)

                        progress.progress(100, text="Done!")

                        st.session_state.records[student_name] = {
                            "question_paper": question_paper,
                            "rubric": rubric,
                            "student_answer": student_answer,
                            "primary_eval": primary_eval,
                            "secondary_eval": secondary_eval,
                            "final_eval": final_eval,
                            "feedback": feedback if not fb_err else None,
                        }
                        st.success(f"Evaluation complete for {student_name}! Check the Results tab.")

# ---------------------------------------------------------------------------
# RESULTS TAB
# ---------------------------------------------------------------------------
with tab_results:
    st.header("Evaluation Results")
    if not st.session_state.records:
        st.info("No evaluations yet. Run one from the Teacher tab.")
    else:
        selected = st.selectbox("Select student", list(st.session_state.records.keys()))
        record = st.session_state.records[selected]
        final = record["final_eval"]

        total_awarded = final.get("total_awarded", "?")
        total_max = final.get("total_max", "?")
        ui.score_hero(total_awarded, total_max, subtitle=f"Final Score — {selected}")

        st.subheader("Question-wise Breakdown (Moderator's Final Decision)")
        for q in final.get("questions", []):
            ui.question_card(
                q.get("question_no"),
                q.get("awarded_marks"),
                q.get("max_marks"),
                q.get("breakdown", {}),
                q.get("reasoning", ""),
            )

        with st.expander("🔍 See both independent evaluations (transparency view)"):
            c1, c2 = st.columns(2)
            with c1:
                st.write("**Evaluator A**")
                st.json(record["primary_eval"])
            with c2:
                st.write("**Evaluator B**")
                st.json(record["secondary_eval"])

        st.subheader("📋 Personalized Feedback Report")
        fb = record.get("feedback")
        if fb:
            colA, colB = st.columns(2)
            with colA:
                st.markdown("**✅ Strengths**")
                for s in fb.get("strengths", []):
                    ui.strength_weakness_pill(s, kind="strength")
                st.markdown("**⚠️ Weaknesses**")
                for w in fb.get("weaknesses", []):
                    ui.strength_weakness_pill(w, kind="weakness")
            with colB:
                st.markdown("**🔁 Recurring Mistakes (whole-paper pattern)**")
                for m in fb.get("recurring_mistakes", []):
                    ui.strength_weakness_pill(m, kind="weakness")
                st.markdown("**💡 Recommendations**")
                for r in fb.get("recommendations", []):
                    ui.strength_weakness_pill(r, kind="strength")
        else:
            st.warning("Feedback report unavailable for this evaluation.")

# ---------------------------------------------------------------------------
# APPEAL TAB
# ---------------------------------------------------------------------------
with tab_appeal:
    st.header("Student Appeal")
    if not st.session_state.records:
        st.info("No evaluations yet to appeal.")
    else:
        selected = st.selectbox("Select student", list(st.session_state.records.keys()), key="appeal_student")
        record = st.session_state.records[selected]
        final = record["final_eval"]
        questions = final.get("questions", [])
        q_options = {f"Q{q.get('question_no')}": q for q in questions}

        if q_options:
            q_label = st.selectbox("Which question do you want to appeal?", list(q_options.keys()))
            q_data = q_options[q_label]
            st.write(f"**Current marks:** {q_data.get('awarded_marks')}/{q_data.get('max_marks')}")
            st.write(f"**Original reasoning:** {q_data.get('reasoning')}")

            appeal_reason = st.text_area("Why do you think this mark should be reconsidered?")
            if st.button("📨 Submit Appeal"):
                if not api_key:
                    st.error("Enter your Groq API key in the sidebar first.")
                elif not appeal_reason:
                    st.error("Please explain your reason for appeal.")
                else:
                    with st.spinner("Appeal Agent reviewing your case..."):
                        # find the question text from the original question paper (best effort)
                        result, err = agents.run_appeal(
                            api_key,
                            q_data.get("question_no"),
                            record["question_paper"],
                            record["student_answer"],
                            q_data.get("reasoning"),
                            record["rubric"],
                            appeal_reason,
                        )
                    if err:
                        st.error("Appeal Agent returned an unexpected format.")
                        st.code(err)
                    else:
                        ui.appeal_result_card(
                            result.get("outcome", "Unknown"),
                            result.get("original_marks"),
                            result.get("revised_marks"),
                            result.get("explanation"),
                        )
        else:
            st.warning("No question-wise data found for this student.")

# ---------------------------------------------------------------------------
# DIFFICULTY TAB (teacher role only)
# ---------------------------------------------------------------------------
if tab_difficulty is not None:
    with tab_difficulty:
        st.header("Question Paper Difficulty Analysis")
        qp_for_difficulty = st.text_area("Paste the question paper to analyze", height=200,
                                          key="difficulty_qp")
        if st.button("Analyze Difficulty"):
            if not api_key:
                st.error("Enter your Groq API key in the sidebar first.")
            elif not qp_for_difficulty:
                st.error("Paste a question paper first.")
            else:
                with st.spinner("Difficulty Analysis Agent working..."):
                    result, err = agents.run_difficulty_analysis(api_key, qp_for_difficulty)
                if err:
                    st.error("Unexpected format returned.")
                    st.code(err)
                else:
                    st.session_state.difficulty = result

        if st.session_state.difficulty:
            d = st.session_state.difficulty
            c1, c2 = st.columns(2)
            with c1:
                st.metric("Overall Difficulty", d.get("overall_difficulty", "?"))
            with c2:
                st.metric("Predicted Average Score", f"{d.get('predicted_average_score_percent', '?')}%")
            st.subheader("Question-wise Difficulty")
            for q in d.get("questions", []):
                ui.difficulty_node(q.get("question_no"), q.get("difficulty"), q.get("reason"))
