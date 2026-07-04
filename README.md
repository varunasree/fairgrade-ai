# FairGrade AI

## Multi-Agent Examination Evaluation, Feedback & Appeal System

FairGrade AI is an AI-powered multi-agent system that evaluates examination answer sheets fairly and transparently. It provides detailed mark explanations, personalized feedback, difficulty analysis, and an appeal mechanism for students.

## Features

- Dual independent evaluation agents for fair grading
- Moderator agent for final score reconciliation
- Explanation for awarded and deducted marks
- Whole-paper mistake analysis
- Personalized feedback and improvement suggestions
- Difficulty estimation for question papers
- Student appeal and re-evaluation system
- Separate Teacher and Student portals

---

## System Architecture

```text
Teacher Upload
      ↓
OCR Processing
      ↓
Answer Extraction
      ↓
Dual Evaluation Agents
      ↓
Moderator Agent
      ↓
Final Marks
      ↓
Explanation Agent
      ↓
Feedback Agent
      ↓
Appeal System
      ↓
Student Report
```

---

## About the System

Instead of relying on a single model, FairGrade AI uses multiple specialized AI agents, each responsible for a specific task. This approach improves fairness, consistency, transparency, and the quality of feedback provided to students.

---

## Tech Stack

- Python
- Streamlit
- Groq API
- OCR / Vision Processing
- Multi-Agent Architecture

---

## How It Works

1. Teacher uploads the question paper, answer key, rubric, and student answer sheet.
2. OCR extracts and processes text from the answer sheet.
3. Answers are structured and prepared for evaluation.
4. Two independent evaluator agents assess the answers separately.
5. A moderator agent compares both evaluations and determines the final score.
6. An explanation agent generates reasons for awarded and deducted marks.
7. A feedback agent analyzes the entire paper and provides improvement suggestions.
8. Students can raise an appeal if they believe marks were unfairly deducted.
9. A final student report is generated.

---

## For Teachers

- Save time on evaluation
- Consistent and transparent grading
- Better performance insights
- Difficulty analysis of question papers

---

## For Students

- Transparent mark breakdown
- Understand mistakes clearly
- Personalized feedback
- Opportunity to appeal evaluations

---

## Future Improvements

- User authentication and role management
- Database integration
- Batch evaluation for entire classes
- Advanced analytics dashboard
- Improved handwriting recognition
- Institution-wide deployment

---

## Author

Developed as an AI-powered educational assessment system focused on fairness, transparency, consistency, and meaningful student feedback.
