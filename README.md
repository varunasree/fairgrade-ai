# FairGrade AI — Multi-Agent Examination Evaluation, Feedback & Appeal System

## What's actually built (all real, working agents)
1. **Evaluator Agent A** — grades independently against the answer key + rubric
2. **Evaluator Agent B** — grades independently, without seeing Agent A's result
3. **Moderator Agent** — compares both, resolves disagreements, gives the final transparent score with per-section breakdown and reasoning
4. **Feedback Agent** — strengths, weaknesses, recurring mistake patterns across the whole paper, and personalized recommendations
5. **Difficulty Analysis Agent** — rates each question's difficulty and predicts the class average
6. **Appeal Agent** — re-examines a specific question against the original reasoning and rubric, and accepts/rejects/partially accepts the appeal
7. **OCR Agent (beta)** — extracts text from a photographed answer sheet using a vision model, shown to the teacher for review/correction before grading

This is a real separation of concerns between agents — not one model wearing different hats in a single prompt. Each is an independent call with its own role, and the Moderator genuinely reconciles two separate outputs.

## Visual design
`ui.py` holds the theme layer — a CSS "quest log" skin (indigo/navy + amber palette, glowing badges for Full Marks/Partial/Missed, quest-style cards, a portal tonal shift between Teacher/navy and Student/amber, hover-glow + click-pulse on buttons, and a reveal animation on appeal outcomes). It's pure CSS injected into Streamlit, not a React rebuild — same working architecture, dressed up. The full cinematic version (book-opening intro, page-turn transitions) would need a JS framework and wasn't worth the rebuild risk this close to your deadline; this gets you most of the visual personality for a fraction of the effort.

## Honest scope notes — say these upfront if asked, don't get caught out
- **"Teacher portal" and "Student portal"** are role-gated tabs behind a shared passcode login, not per-user accounts with a database. That's a legitimate MVP scoping choice — say so if asked, and list real accounts as future work.
- **OCR accuracy on messy handwriting is not guaranteed.** For your live demo, use typed/pasted answers or a clearly printed, well-lit scan. Frame OCR as "implemented, with handwriting robustness as a next iteration" rather than pretending it's production-grade.
- **No persistent database** — records live in memory for the session (a demo choice, not a flaw to hide; mention SQLite/Firebase as the natural next step).

---

## Login
The app now has two role-based logins (shared passcode per role — a legitimate demo pattern, not real per-user accounts):
- **Teacher passcode:** `teach123` (change via Streamlit Cloud secrets, see below)
- **Student passcode:** `learn456`

Teachers see Evaluate / Results / Difficulty. Students see Results (view) / Submit Appeal.

---

## Option A — Run entirely from your phone (no laptop needed)

This deploys the app to a real public URL using **GitHub + Streamlit Community Cloud**, both free, both usable from a phone browser. Unlike Colab, this URL stays live permanently — you don't have to keep a tab open.

### 1. Put the code on GitHub (from your phone browser)
- Go to github.com → sign up/log in
- Tap **+** → **New repository** → name it `fairgrade-ai` → Create
- Tap **Add file → Create new file**, name it `app.py`, paste in the full contents of this project's `app.py`, commit
- Repeat for `agents.py`, `ui.py`, and `requirements.txt`

### 2. Deploy on Streamlit Community Cloud
- Go to **share.streamlit.io** → sign in with GitHub
- Tap **New app** → pick your `fairgrade-ai` repo → set main file to `app.py` → Deploy
- Wait ~1-2 minutes — it will give you a permanent URL like `fairgrade-ai.streamlit.app`

### 3. Add your Groq key as a Secret (so you never type it on your phone)
- In Streamlit Cloud, open your app → **Settings → Secrets** → paste:
  ```
  GROQ_API_KEY = "gsk_your_actual_key_here"
  TEACHER_PASSCODE = "your_teacher_passcode"
  STUDENT_PASSCODE = "your_student_passcode"
  ```
- Save — the app auto-restarts with the key loaded

### 4. Use it
Open the `.streamlit.app` URL on any phone, tablet, or laptop, log in with either passcode, and it works exactly like running locally — because it now *is* running in the cloud, not on your device.

This is genuinely the better option even beyond the emergency — you can hand the URL to your evaluator/professor directly.

---

## Option B — Run locally (if you get a working computer back)

### 1. Get a free Groq API key
- https://console.groq.com → sign up → API Keys → Create Key (starts with `gsk_...`)

### 2. Install dependencies
```
pip install -r requirements.txt
```

### 3. Run
```
streamlit run app.py
```
Opens automatically at `http://localhost:8501`. Your laptop only renders a browser page — all AI inference happens on Groq's cloud servers, so hardware doesn't matter.

### 4. Demo flow
1. **Teacher tab** — paste question paper, answer key, rubric, and a student's answers → "Run Full Multi-Agent Evaluation"
2. **Results tab** — show the final score, expand each question to reveal the reasoning, expand "see both independent evaluations" to show the dual-agent transparency, scroll to the feedback report
3. **Appeal tab** — pick a question, write a reason, submit, show the Appeal Agent's verdict
4. **Difficulty tab** — paste the same question paper, show difficulty ratings

A ready-to-paste sample dataset is in `sample_data.md` so you can rehearse right now without hunting for a real exam paper.

---

## For your report / slides

**Problem statement:** Manual grading is inconsistent, time-consuming, and opaque — students rarely know exactly why they lost marks, and bias or fatigue can affect fairness. Appeals are often informal and undocumented.

**Architecture:**
```
                    ┌─────────────────┐
   Answer Sheet --> │   OCR Agent     │ (image -> text, human-reviewed)
   (image/text)     └────────┬────────┘
                              v
                 ┌────────────────────────┐
                 │  Evaluator Agent A      │
                 │  Evaluator Agent B      │  (independent, parallel grading)
                 └───────────┬────────────┘
                              v
                    ┌───────────────────┐
                    │  Moderator Agent   │ (reconciles, final score)
                    └─────────┬─────────┘
                              v
              ┌───────────────┴───────────────┐
              v                                 v
   ┌────────────────────┐          ┌────────────────────┐
   │  Feedback Agent      │          │ Difficulty Agent    │
   └────────────────────┘          └────────────────────┘
              |
              v
      ┌───────────────┐
      │  Appeal Agent  │ (on-demand, per question)
      └───────────────┘
```

**Why dual evaluation matters (say this explicitly):** a single LLM call grading a paper has the same single-point-of-failure problem as a single human grader. Two independent agents plus a moderator that explains *why* it sided with one, split the difference, or overruled both — mirrors how serious human grading (e.g., board exams) already works with multiple examiners, and gives you a genuine multi-agent architecture rather than a single wrapped prompt.

**Future work slide (fair to say even though not built):**
- Real authentication and persistent database for teacher/student accounts
- Handwriting-robust OCR at scale (fine-tuned or ensemble OCR)
- Batch grading for an entire class at once
- Analytics dashboard across all students for a teacher
- 
