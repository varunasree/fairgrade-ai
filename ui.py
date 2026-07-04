"""
FairGrade AI — visual theme layer.
Pure CSS injected into Streamlit (no React/Framer Motion needed) so the app
keeps its working architecture while adopting the indigo/navy + amber
"quest log" visual language from the design doc.
"""

import streamlit as st

BASE_CSS = """
<style>
:root {
    --fg-navy: #1b2140;
    --fg-navy-light: #262d52;
    --fg-indigo: #4c4fe0;
    --fg-amber: #f5a524;
    --fg-amber-soft: #fdebc8;
    --fg-green: #2fbf71;
    --fg-green-soft: #e3f9ee;
    --fg-red: #e5484d;
    --fg-red-soft: #fde4e4;
    --fg-cream: #fbf8f2;
}

/* ---- App background & typography ---- */
.stApp {
    background: linear-gradient(180deg, var(--fg-cream) 0%, #f3f0ea 100%);
    font-family: 'Inter', 'Poppins', -apple-system, sans-serif;
}
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, var(--fg-navy) 0%, var(--fg-navy-light) 100%);
}
section[data-testid="stSidebar"] * {
    color: #f1f1fa !important;
}

/* ---- Headings ---- */
h1, h2, h3 {
    color: var(--fg-navy);
    font-weight: 700;
}

/* ---- Buttons: hover glow + click pulse ---- */
.stButton > button {
    border-radius: 10px;
    border: 1px solid var(--fg-indigo);
    background: white;
    color: var(--fg-navy);
    font-weight: 600;
    transition: box-shadow 0.2s ease, transform 0.15s ease;
}
.stButton > button:hover {
    box-shadow: 0 0 0 4px rgba(76, 79, 224, 0.18), 0 4px 14px rgba(76, 79, 224, 0.25);
    transform: translateY(-1px);
    border-color: var(--fg-indigo);
}
.stButton > button:active {
    animation: fg-pulse 0.15s ease;
}
button[kind="primary"] {
    background: linear-gradient(135deg, var(--fg-indigo), #6a6df0) !important;
    color: white !important;
    border: none !important;
}
button[kind="primary"]:hover {
    box-shadow: 0 0 0 5px rgba(76, 79, 224, 0.25), 0 6px 18px rgba(76, 79, 224, 0.35) !important;
}
@keyframes fg-pulse {
    0% { transform: scale(1); }
    50% { transform: scale(0.97); }
    100% { transform: scale(1); }
}

/* ---- Tabs styled like a top nav ---- */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    border-bottom: 2px solid #e8e4da;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 10px 10px 0 0;
    padding: 10px 18px;
    font-weight: 600;
    color: var(--fg-navy);
}
.stTabs [aria-selected="true"] {
    background: var(--fg-navy) !important;
    color: white !important;
}

/* ---- Quest card ---- */
.fg-card {
    background: white;
    border-radius: 14px;
    padding: 18px 20px;
    margin-bottom: 14px;
    box-shadow: 0 2px 10px rgba(27, 33, 64, 0.08);
    border-left: 5px solid var(--fg-indigo);
    transition: box-shadow 0.2s ease, transform 0.15s ease;
}
.fg-card:hover {
    box-shadow: 0 4px 20px rgba(27, 33, 64, 0.14);
    transform: translateY(-1px);
}

/* ---- Badges ---- */
.fg-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.02em;
    text-transform: uppercase;
}
.fg-badge-full   { background: var(--fg-green-soft); color: #1a7a4c; }
.fg-badge-partial{ background: var(--fg-amber-soft); color: #92600a; }
.fg-badge-missed { background: var(--fg-red-soft);   color: #b53034; }
.fg-badge-neutral{ background: #e9e8fb; color: var(--fg-indigo); }

/* ---- Appeal outcome card (card-flip flavor via a reveal border) ---- */
.fg-appeal-card {
    border-radius: 14px;
    padding: 20px;
    margin-top: 10px;
    animation: fg-reveal 0.35s ease;
}
.fg-appeal-accepted { background: var(--fg-green-soft); border: 2px solid var(--fg-green); }
.fg-appeal-rejected { background: var(--fg-red-soft); border: 2px solid var(--fg-red); }
.fg-appeal-partial  { background: var(--fg-amber-soft); border: 2px solid var(--fg-amber); }
@keyframes fg-reveal {
    from { opacity: 0; transform: rotateX(-8deg) scale(0.98); }
    to { opacity: 1; transform: rotateX(0) scale(1); }
}

/* ---- Difficulty path nodes ---- */
.fg-node {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 8px 16px;
    border-radius: 999px;
    margin: 4px 6px 4px 0;
    font-weight: 600;
    font-size: 0.85rem;
}
.fg-node-easy   { background: var(--fg-green-soft); color: #1a7a4c; }
.fg-node-medium { background: var(--fg-amber-soft); color: #92600a; }
.fg-node-hard   { background: var(--fg-red-soft); color: #b53034; }

/* ---- Score hero ---- */
.fg-score-hero {
    background: linear-gradient(135deg, var(--fg-navy), var(--fg-indigo));
    color: white;
    border-radius: 18px;
    padding: 26px 30px;
    margin-bottom: 20px;
    box-shadow: 0 8px 24px rgba(27, 33, 64, 0.25);
}
.fg-score-hero .fg-score-num {
    font-size: 2.4rem;
    font-weight: 800;
}
.fg-score-hero .fg-score-label {
    opacity: 0.8;
    font-size: 0.9rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* ---- Login hero banner ---- */
.fg-login-hero {
    text-align: center;
    padding: 30px 10px 10px 10px;
}
.fg-login-hero .fg-emoji {
    font-size: 2.6rem;
    animation: fg-breathe 3s ease-in-out infinite;
    display: inline-block;
}
@keyframes fg-breathe {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.08); }
}
.fg-login-hero h1 {
    background: linear-gradient(135deg, var(--fg-navy), var(--fg-indigo));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2.1rem;
    margin-bottom: 0;
}
.fg-login-hero p {
    color: #6b6f8a;
    margin-top: 4px;
}
</style>
"""

TEACHER_ACCENT_CSS = """
<style>
.fg-score-hero { background: linear-gradient(135deg, #1b2140, #2d3568); }
</style>
"""

STUDENT_ACCENT_CSS = """
<style>
.fg-score-hero { background: linear-gradient(135deg, #b5720f, #f5a524); }
.stTabs [aria-selected="true"] { background: #f5a524 !important; color: #241a03 !important; }
</style>
"""


def inject_theme(role=None):
    st.markdown(BASE_CSS, unsafe_allow_html=True)
    if role == "teacher":
        st.markdown(TEACHER_ACCENT_CSS, unsafe_allow_html=True)
    elif role == "student":
        st.markdown(STUDENT_ACCENT_CSS, unsafe_allow_html=True)


def login_hero():
    st.markdown(
        """
        <div class="fg-login-hero">
            <span class="fg-emoji">📖</span>
            <h1>FairGrade AI</h1>
            <p>Multi-Agent Examination Evaluation, Feedback &amp; Appeal System</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def score_hero(awarded, total, subtitle="Final Score"):
    st.markdown(
        f"""
        <div class="fg-score-hero">
            <div class="fg-score-label">{subtitle}</div>
            <div class="fg-score-num">{awarded} / {total}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def badge(text, kind="neutral"):
    """kind: full | partial | missed | neutral"""
    return f'<span class="fg-badge fg-badge-{kind}">{text}</span>'


def mark_kind(awarded, maximum):
    try:
        awarded = float(awarded)
        maximum = float(maximum)
        if maximum <= 0:
            return "neutral"
        ratio = awarded / maximum
        if ratio >= 0.95:
            return "full"
        elif ratio > 0:
            return "partial"
        else:
            return "missed"
    except (TypeError, ValueError):
        return "neutral"


def question_card(question_no, awarded, maximum, breakdown, reasoning):
    kind = mark_kind(awarded, maximum)
    label = {"full": "Full Marks", "partial": "Partial", "missed": "Missed", "neutral": "—"}[kind]
    breakdown_html = ""
    if breakdown:
        rows = "".join(f"<li>{section}: {marks}</li>" for section, marks in breakdown.items())
        breakdown_html = f"<ul style='margin:8px 0 8px 18px; padding:0; color:#444;'>{rows}</ul>"
    st.markdown(
        f"""
        <div class="fg-card">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <strong style="font-size:1.05rem; color:var(--fg-navy);">Question {question_no}</strong>
                {badge(label, kind)}
            </div>
            <div style="margin-top:6px; color:#333;">
                <strong>{awarded} / {maximum} marks</strong>
            </div>
            {breakdown_html}
            <div style="margin-top:8px; color:#555; font-size:0.92rem;">{reasoning}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def appeal_result_card(outcome, original_marks, revised_marks, explanation):
    kind_map = {
        "Accepted": ("fg-appeal-accepted", "✅"),
        "Rejected": ("fg-appeal-rejected", "❌"),
        "Partially Accepted": ("fg-appeal-partial", "🟡"),
    }
    css_class, icon = kind_map.get(outcome, ("fg-appeal-partial", "ℹ️"))
    st.markdown(
        f"""
        <div class="fg-appeal-card {css_class}">
            <h3 style="margin-top:0;">{icon} Appeal {outcome}</h3>
            <p><strong>Original marks:</strong> {original_marks} &nbsp;→&nbsp;
               <strong>Revised marks:</strong> {revised_marks}</p>
            <p>{explanation}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def difficulty_node(question_no, difficulty, reason):
    level = (difficulty or "").strip().lower()
    css_class = {"easy": "fg-node-easy", "medium": "fg-node-medium", "hard": "fg-node-hard"}.get(
        level, "fg-node-medium"
    )
    icon = {"easy": "🟢", "medium": "🟠", "hard": "🔴"}.get(level, "🔵")
    st.markdown(
        f"""
        <div class="fg-node {css_class}">
            {icon} <strong>Q{question_no}</strong> · {difficulty} — <span style="font-weight:400;">{reason}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def strength_weakness_pill(text, kind="strength"):
    icon = "🌿" if kind == "strength" else "⚠️"
    css_class = "fg-badge-full" if kind == "strength" else "fg-badge-partial"
    st.markdown(
        f"""
        <div class="fg-card" style="border-left-color:{'var(--fg-green)' if kind=='strength' else 'var(--fg-amber)'}; padding:12px 16px; margin-bottom:8px;">
            {icon} {text}
        </div>
        """,
        unsafe_allow_html=True,
    )
