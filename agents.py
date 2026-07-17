"""
FairGrade AI — Agent logic layer
All LLM calls (the "agents") live here, separate from the UI (app.py).
"""

import requests
import json
import base64
import io
import time
from pypdf import PdfReader
from PIL import Image, ImageEnhance, ImageOps

API_URL = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
MODEL_TEXT = "gemini-2.5-flash"    # Google's free tier: ~250k-1M tokens/minute (vs Groq's ~6-8k)
MODEL_VISION = "gemini-2.5-flash"  # same model handles vision natively, no separate model needed


# ---------------------------------------------------------------------------
# LOW-LEVEL API HELPERS
# ---------------------------------------------------------------------------
def _call_llm(api_key, messages, model=MODEL_TEXT, temperature=0.4,
                max_tokens=1200, json_mode=False, max_retries=4, timeout=90):
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    for attempt in range(max_retries):
        try:
            resp = requests.post(API_URL, headers=headers, json=payload, timeout=timeout)
        except requests.exceptions.Timeout:
            raise RuntimeError(
                "The request timed out — this usually means your internet connection is too slow "
                "right now to upload the image/data in time. Try again on a stronger connection, "
                "or use a smaller/lighter photo."
            )

        if resp.status_code == 429:
            # Rate limited — back off and retry rather than failing immediately
            wait_seconds = 3 * (attempt + 1)
            if attempt < max_retries - 1:
                time.sleep(wait_seconds)
                continue
            raise RuntimeError(
                "Google's free-tier rate limit was hit repeatedly. Wait about a minute "
                "before trying again, or space out your requests."
            )

        if resp.status_code == 401 or resp.status_code == 403:
            raise RuntimeError("Google rejected the API key (401/403 Unauthorized). "
                                "Double-check the key in the sidebar / Secrets — get one free "
                                "at aistudio.google.com/apikey.")

        if resp.status_code == 400 and "json_validate_failed" in resp.text:
            raise RuntimeError(
                "The AI's response got cut off before it finished (usually because the "
                "question paper/answers are long and hit the output length limit). "
                "Try again — if it keeps happening, shorten the rubric/answers a little."
            )

        try:
            resp.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise RuntimeError(f"Google API error ({resp.status_code}): {resp.text[:300]}") from e

        return resp.json()["choices"][0]["message"]["content"]


def _call_llm_json(api_key, messages, model=MODEL_TEXT, temperature=0.3, max_tokens=2500):
    """Calls the model in JSON mode and safely parses the result."""
    raw = _call_llm(api_key, messages, model=model, temperature=temperature,
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
# IMAGE PREPROCESSING (helps handwriting OCR meaningfully)
# ---------------------------------------------------------------------------
def preprocess_image_for_ocr(image_bytes):
    """Cleans up a photo before sending it to the vision model:
    - grayscale (removes color noise/shadows), contrast + sharpness boost
    - resizes to a sensible range (helps accuracy without bloating upload size)
    - saves as compressed JPEG, not PNG — much smaller upload on slow connections
    This improves handwriting recognition without making uploads painfully slow."""
    try:
        img = Image.open(io.BytesIO(image_bytes))
        img = ImageOps.exif_transpose(img)  # fix phone camera rotation
        img = img.convert("L")  # grayscale

        # Keep the image in a sensible size range: upscale only if quite small,
        # and cap the max side so a huge phone photo doesn't balloon upload size.
        max_dim = max(img.size)
        if max_dim < 1200:
            scale = 1200 / max_dim
            img = img.resize((int(img.width * scale), int(img.height * scale)), Image.LANCZOS)
        elif max_dim > 1800:
            scale = 1800 / max_dim
            img = img.resize((int(img.width * scale), int(img.height * scale)), Image.LANCZOS)

        img = ImageOps.autocontrast(img, cutoff=1)
        img = ImageEnhance.Contrast(img).enhance(1.3)
        img = ImageEnhance.Sharpness(img).enhance(1.5)

        out = io.BytesIO()
        img.save(out, format="JPEG", quality=80, optimize=True)
        return out.getvalue()
    except Exception:
        # If preprocessing fails for any reason, fall back to the original image
        # rather than blocking the whole OCR pipeline.
        return image_bytes


# ---------------------------------------------------------------------------
# AGENT 1 — OCR / EXTRACTION AGENT (image -> text)
# ---------------------------------------------------------------------------
def ocr_extract_text(api_key, image_bytes, mime_type="image/png"):
    cleaned_bytes = preprocess_image_for_ocr(image_bytes)
    b64 = base64.b64encode(cleaned_bytes).decode("utf-8")
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": (
                        "You are transcribing a HANDWRITTEN exam answer sheet. Handwriting varies in "
                        "neatness, so read carefully and deliberately, letter by letter where needed, "
                        "rather than guessing from shape alone.\n\n"
                        "Rules:\n"
                        "1. Transcribe every word exactly as written, preserving question numbers/labels.\n"
                        "2. If a word or short phrase is genuinely illegible, write [illegible] in its place "
                        "instead of guessing — never invent content that isn't visibly there.\n"
                        "3. Preserve line breaks between distinct answers/questions where visible.\n"
                        "4. Do not correct the student's spelling, grammar, or technical errors — "
                        "transcribe exactly what is written, mistakes included.\n"
                        "5. Return plain text only — no commentary, no markdown, no summary."
                    ),
                },
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
            ],
        }
    ]
    return _call_llm(api_key, messages, model=MODEL_VISION, temperature=0.0, max_tokens=3000,
                       timeout=60, max_retries=2)


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
      "reasoning": "ONE concise sentence, max ~20 words, on what was missing or correct"
    }
  ],
  "total_awarded": 0,
  "total_max": 0
}
Be specific and rubric-grounded, but keep every "reasoning" field short — one sentence, not a
paragraph. This is a hard length limit, not a suggestion: brevity matters more than completeness here.
Output compact JSON with minimal whitespace (no pretty-printing/indentation) to save space.
Never award marks without a stated reason.
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
    return _call_llm_json(api_key, messages, max_tokens=3800)
# ---------------------------------------------------------------------------
def run_moderator(api_key, question_paper, rubric, primary_eval, secondary_eval):
    system_prompt = (
        "You are the Moderator Agent, the final decision-maker in a dual-evaluator grading system. "
        "You are given two independent evaluations of the same student answer sheet. "
        "Compare them question by question. Where they agree, confirm the mark. "
        "Where they disagree, re-examine against the rubric and decide the fairer mark, "
        "explaining why you sided with one evaluator, split the difference, or overruled both. "
        + EVAL_SCHEMA_INSTRUCTIONS.replace(
            '"reasoning": "ONE concise sentence, max ~20 words, on what was missing or correct"',
            '"reasoning": "ONE concise sentence, max ~20 words — note only if evaluators disagreed and how it was resolved, otherwise just the verdict"'
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
    return _call_llm_json(api_key, messages, max_tokens=3800)


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
    return _call_llm_json(api_key, messages)


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
    return _call_llm_json(api_key, messages)


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
    return _call_llm_json(api_key, messages)
