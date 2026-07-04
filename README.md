FairGrade AI

Overview

FairGrade AI is a multi-agent examination evaluation system designed to make grading more transparent, consistent, and informative. Instead of simply assigning marks, the platform explains why marks were awarded or deducted, identifies recurring mistakes across the entire paper, provides personalized feedback, and supports re-evaluation through an appeal mechanism.

Features

- Dual independent evaluation agents for fair grading
- Moderator agent for final score reconciliation
- Question-wise mark justification
- Detailed explanation for awarded and deducted marks
- Whole-paper mistake analysis
- Common error detection
- Personalized feedback and improvement suggestions
- Difficulty estimation for question papers
- Student appeal and re-evaluation system
- Separate Teacher and Student portals

System Architecture

Teacher Uploads:
- Question Paper
- Answer Key
- Rubric
- Student Answer Sheet
          │
          ▼
OCR / Document Processing Agent
          │
          ▼
Answer Extraction & Structuring
          │
          ▼
 ┌─────────────────────┐
 │ Evaluator Agent A   │
 └─────────────────────┘
          │
          ├──────────────┐
          │              │
          ▼              ▼
 ┌─────────────────────┐
 │ Evaluator Agent B   │
 └─────────────────────┘
          │
          └──────────────┘
                 │
                 ▼
      ┌───────────────────┐
      │ Moderator Agent   │
      └───────────────────┘
                 │
                 ▼
        Final Mark Allocation
                 │
                 ▼
 ┌─────────────────────────────────────┐
 │ Explanation Agent                   │
 │ • Why marks were awarded            │
 │ • Why marks were deducted           │
 │ • Question-wise justification       │
 └─────────────────────────────────────┘
                 │
                 ▼
 ┌─────────────────────────────────────┐
 │ Feedback Agent                      │
 │ • Overall paper mistakes            │
 │ • Common recurring errors           │
 │ • Strengths identified              │
 │ • Improvement suggestions           │
 └─────────────────────────────────────┘
                 │
                 ▼
 ┌─────────────────────────────────────┐
 │ Appeal / Re-evaluation Agent        │
 │ • Student challenge request         │
 │ • Recheck disputed questions        │
 └─────────────────────────────────────┘
                 │
                 ▼
          Student Report

Parallel Process:

Question Paper
      │
      ▼
Difficulty Analysis Agent
      │
      ▼
Difficulty Score + Exam Insights

How It Works

1. Teachers upload the question paper, answer key, marking rubric, and student answer sheet.
2. The OCR and Document Processing Agent extracts and structures the student's answers.
3. Two independent evaluator agents assess the answers separately.
4. A Moderator Agent compares both evaluations and determines the final score.
5. The Explanation Agent generates question-wise reasoning for awarded and deducted marks.
6. The Feedback Agent analyzes the entire paper and identifies common mistakes, strengths, and areas for improvement.
7. The Difficulty Analysis Agent evaluates the complexity of the question paper and generates exam insights.
8. Students can request re-evaluation through the Appeal Agent if they believe marks were unfairly deducted.

Tech Stack

- Python
- Streamlit
- Groq API
- OCR / Vision Processing
- Multi-Agent AI Architecture

Key Outputs

For Students

- Final score
- Question-wise marks
- Explanation for awarded marks
- Explanation for deducted marks
- Overall paper feedback
- Common mistakes summary
- Improvement recommendations
- Appeal option

For Teachers

- Automated evaluation
- Consistent grading
- Difficulty analysis
- Performance insights
- Faster assessment workflow

Future Improvements

- Real user authentication
- Database integration
- Batch evaluation for entire classes
- Advanced analytics dashboard
- Handwriting-specific evaluation models
- Institution-wide deployment
- Performance tracking across exams

Author

Developed as an AI-powered educational assessment system focused on fairness, transparency, consistency, and meaningful student feedback.
