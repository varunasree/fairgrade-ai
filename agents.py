"""
FairGrade AI — Agent logic layer
All LLM calls (the "agents") live here, separate from the UI (app.py).
"""

import requests
import json
import base64
import io
from pypdf import PdfReader

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL_TEXT = "openai/gpt-oss-120b"      # current Groq free-tier text model (2026)
MODEL_VISION = "qwen/qwen3.6-27b"        # current Groq free-tier vision-capable model (2026)


# ---------------------------------------------------------------------------
# LOW-LEVEL API HELPERS
# ---------------------------------------------------------------------------
def _call_groq(api_key, messages, model=MODEL_TEXT, temperature=0.4,
                max_tokens=1200, json_mode=False):
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    resp = requests.post(GROQ_URL, headers=headers, json=payload, timeout=90)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def _call_groq_json(api_key, messages, model=MODEL_TEXT, temperature=0.3, max_tokens=1500):
    """Calls the model in JSON mode and safely parses the result."""
    raw = _call_groq(api_key, messages, model=model, temperature=temperature,
                      max_tokens=max_tokens, json_mode=True)
    try:
        return json.loads(raw), None
    except json.JSONDecodeError:
        # fallback: try to salvage JSON substring
        try:
            start = raw.index("{")
            end = raw.rindex("}") + 1
            return json.loads(raw[start:end]), None
        except Exception:
            return None, raw  # return raw text as error payload


# ---------------------------------------------------------------------------
# AGENT 1 — OCR / EXTRACTION AGENT (image -> text)
# ---------------------------------------------------------------------------
def ocr_extract_text(api_key, image_bytes, mime_type="image/png"):
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": (
                        "Extract ALL text from this exam answer sheet exactly as written. "
                        "Preserve question numbers if visible. Return plain text only, "
                        "no commentary, no markdown formatting."
                    ),
                },
                {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{b64}"}},
            ],
        }
    ]
    return _call_groq(api_key, messages, model=MODEL_VISION, temperature=0.1, max_tokens=1500)


# ---------------------------------------------------------------------------
# PDF TEXT EXTRACTION (deterministic — not an LLM call)
# Most PDFs (Word exports, typed documents) already contain real selectable
# text, so this is fast, free, and more reliable than OCR for that case.
# ---------------------------------------------------------------------------
def extract_text_from_pdf(pdf_bytes):
    reader = PdfReader(io.BytesIO(pdf_bytes))
    pages_text = []
    for page in reader.pages:
        pages_text.append(page.extract_text() or "")
    text = "\n".join(pages_text).strip()
    return text


def pdf_has_extractable_text(pdf_bytes):
    """Returns False for scanned/image-only PDFs where extract_text() finds nothing."""
    text = extract_text_from_pdf(pdf_bytes)
    return len(text.strip()) > 20


def extract_text_from_scanned_pdf(api_key, pdf_bytes):
    """Fallback for scanned/photographed PDFs with no real text layer:
    renders each page as an image and runs the OCR Agent on it."""
    import fitz  # PyMuPDF
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    all_text = []
    for page_num in range(len(doc)):
        pix = doc[page_num].get_pixmap(dpi=200)
        img_bytes = pix.tobytes("png")
        page_text = ocr_extract_text(api_key, img_bytes, mime_type="image/png")
        all_text.append(page_text)
    return "\n\n".join(all_text)


def smart_extract_document(api_key, uploaded_file):
    """
    Given a Streamlit UploadedFile (image or PDF), returns extracted text
    using the right method automatically:
      - image -> OCR Agent (vision model)
      - PDF with real text layer -> direct extraction (fast, free, no AI needed)
      - PDF with no text layer (scanned) -> render pages + OCR Agent
    """
    filename = uploaded_file.name.lower()
    file_bytes = uploaded_file.getvalue()

    if filename.endswith(".pdf"):
        if pdf_has_extractable_text(file_bytes):
            return extract_text_from_pdf(file_bytes), "pdf_text"
        else:
            return extract_text_from_scanned_pdf(api_key, file_bytes), "pdf_ocr"
    else:
        return ocr_extract_text(api_key, file_bytes, mime_type=uploaded_file.type), "image_ocr"


# ---------------------------------------------------------------------------
# AGENT 2 & 3 — PRIMARY / SECONDARY EVALUATOR AGENTS
# ---------------------------------------------------------------------------
EVAL_SCHEMA_INSTRUCTIONS = """
Respond ONLY with valid JSON in this exact shape (no markdown, no extra text):
{
  "questions": [
    {
      "question_no": "1",
      "max_marks": 10,
      "awarded_marks": 7,
      "breakdown": {"section_name": "marks awarded / marks possible as a string"},
      "reasoning": "specific explanation referencing the rubric and what was missing or correct"
    }
  ],
  "total_awarded": 0,
  "total_max": 0
}
Be specific and rubric-grounded. Never award marks without a stated reason.
"""

def _evaluator_prompt(evaluator_label):
    return (
        f"You are {evaluator_label}, an independent, strict but fair exam evaluator. "
        "You will be given a question paper, an answer key / model answers, a grading rubric, "
        "and a student's submitted answers. Grade the student's answers question by question. "
        "Evaluate independently and rigorously — do not be lenient. "
        + EVAL_SCHEMA_INSTRUCTIONS
    )


def run_evaluator(api_key, evaluator_label, question_paper, answer_key, rubric, student_answer):
    system_prompt = _evaluator_prompt(evaluator_label)
    user_content = (
        f"QUESTION PAPER:\n{question_paper}\n\n"
        f"ANSWER KEY / MODEL ANSWERS:\n{answer_key}\n\n"
        f"GRADING RUBRIC / INSTRUCTIONS:\n{rubric}\n\n"
        f"STUDENT ANSWERS:\n{student_answer}"
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ]
    return _call_groq_json(api_key, messages)


# ---------------------------------------------------------------------------
# AGENT 4 — MODERATOR AGENT
# ---------------------------------------------------------------------------
def run_moderator(api_key, question_paper, rubric, primary_eval, secondary_eval):
    system_prompt = (
        "You are the Moderator Agent, the final decision-maker in a dual-evaluator grading system. "
        "You are given two independent evaluations of the same student answer sheet. "
        "Compare them question by question. Where they agree, confirm the mark. "
        "Where they disagree, re-examine against the rubric and decide the fairer mark, "
        "explaining why you sided with one evaluator, split the difference, or overruled both. "
        + EVAL_SCHEMA_INSTRUCTIONS.replace(
            '"reasoning": "specific explanation referencing the rubric and what was missing or correct"',
            '"reasoning": "final reasoning, explicitly noting if/how the two evaluators disagreed and how it was resolved"'
        )
    )
    user_content = (
        f"RUBRIC:\n{rubric}\n\n"
        f"EVALUATOR A RESULT:\n{json.dumps(primary_eval)}\n\n"
        f"EVALUATOR B RESULT:\n{json.dumps(secondary_eval)}"
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ]
    return _call_groq_json(api_key, messages)


# ---------------------------------------------------------------------------
# AGENT 5 — FEEDBACK AGENT
# ---------------------------------------------------------------------------
def run_feedback(api_key, final_eval, student_answer):
    system_prompt = """You are the Feedback Agent, focused on the student's learning and growth.
Given the final grading result and the student's full answer sheet, respond ONLY with valid JSON:
{
  "strengths": ["..."],
  "weaknesses": ["..."],
  "recurring_mistakes": ["patterns seen across multiple questions, not one-off errors"],
  "recommendations": ["specific, actionable study or writing suggestions"]
}
Be constructive and specific — reference actual patterns from the answers, not generic advice."""
    user_content = (
        f"FINAL GRADING RESULT:\n{json.dumps(final_eval)}\n\n"
        f"STUDENT'S FULL ANSWER SHEET:\n{student_answer}"
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ]
    return _call_groq_json(api_key, messages)


# ---------------------------------------------------------------------------
# AGENT 6 — DIFFICULTY ANALYSIS AGENT
# ---------------------------------------------------------------------------
def run_difficulty_analysis(api_key, question_paper):
    system_prompt = """You are the Difficulty Analysis Agent. Analyze a question paper's complexity.
Respond ONLY with valid JSON:
{
  "questions": [{"question_no": "1", "difficulty": "Easy|Medium|Hard", "reason": "short reason"}],
  "overall_difficulty": "Easy|Medium|Hard",
  "predicted_average_score_percent": 65
}"""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"QUESTION PAPER:\n{question_paper}"},
    ]
    return _call_groq_json(api_key, messages)


# ---------------------------------------------------------------------------
# AGENT 7 — APPEAL AGENT
# ---------------------------------------------------------------------------
def run_appeal(api_key, question_no, question_text, student_answer_excerpt,
                original_reasoning, rubric, appeal_reason):
    system_prompt = """You are the Appeal Agent, handling a student's request for re-evaluation.
Re-examine the specific answer strictly against the rubric. Be fair to both the student and the
original grading — only change the mark if the appeal reveals a genuine grading error or overlooked
content. Respond ONLY with valid JSON:
{
  "outcome": "Accepted" | "Rejected" | "Partially Accepted",
  "original_marks": 0,
  "revised_marks": 0,
  "explanation": "clear reasoning for the decision"
}"""
    user_content = (
        f"QUESTION {question_no}: {question_text}\n\n"
        f"RUBRIC:\n{rubric}\n\n"
        f"STUDENT'S ANSWER TO THIS QUESTION:\n{student_answer_excerpt}\n\n"
        f"ORIGINAL GRADING REASONING:\n{original_reasoning}\n\n"
        f"STUDENT'S APPEAL:\n{appeal_reason}"
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ]
    return _call_groq_json(api_key, messages)
