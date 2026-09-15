import { useState } from "react";
import { api } from "../api";

const LEVELS = ["Beginner", "Intermediate", "Advanced", "Professional"];

export default function Quiz() {
  const [level, setLevel] = useState("Beginner");
  const [questions, setQuestions] = useState(null);
  const [answers, setAnswers] = useState({}); // question_id -> 'a'|'b'|'c'|'d'
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  async function startQuiz() {
    setLoading(true);
    setError("");
    setResult(null);
    setAnswers({});
    try {
      const qs = await api.getQuizQuestions(level, 5);
      setQuestions(qs);
    } catch (err) {
      setError(err.message);
      setQuestions(null);
    } finally {
      setLoading(false);
    }
  }

  function selectAnswer(questionId, option) {
    if (result) return; // locked after submit
    setAnswers((prev) => ({ ...prev, [questionId]: option }));
  }

  async function handleSubmit() {
    setError("");
    setSubmitting(true);
    try {
      const payload = {
        level,
        answers: Object.entries(answers).map(([question_id, selected_option]) => ({
          question_id: Number(question_id),
          selected_option,
        })),
      };
      const res = await api.submitQuiz(payload);
      setResult(res);
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  const resultByQuestion = {};
  if (result) {
    for (const r of result.results) resultByQuestion[r.question_id] = r;
  }

  return (
    <div className="page">
      <h1>📝 Knowledge-Check Quiz</h1>
      <p className="muted">
        Multiple-choice questions on ASL vocabulary, grammar, and Deaf culture — a knowledge
        check alongside your live gesture-practice assessments.
      </p>

      <div className="card">
        <label>
          Level
          <select value={level} onChange={(e) => setLevel(e.target.value)} disabled={!!questions}>
            {LEVELS.map((l) => (
              <option key={l} value={l}>
                {l}
              </option>
            ))}
          </select>
        </label>
        {!questions ? (
          <button className="btn-primary" onClick={startQuiz} disabled={loading}>
            {loading ? "Loading…" : "Start Quiz"}
          </button>
        ) : (
          <button
            className="btn-secondary"
            onClick={() => {
              setQuestions(null);
              setResult(null);
            }}
          >
            ← Choose a different level
          </button>
        )}
        {error && <div className="alert alert-error">{error}</div>}
      </div>

      {result && (
        <div className="card quiz-score-banner">
          <div className="quiz-score-banner-value">
            {result.score} / {result.total}
          </div>
          <div className="muted">{result.percent}% correct — {result.level} level</div>
        </div>
      )}

      {questions &&
        questions.map((q, i) => {
          const r = resultByQuestion[q.id];
          return (
            <div className="card quiz-question-card" key={q.id}>
              <h3>
                {i + 1}. {q.question_text}
              </h3>
              <div className="quiz-options">
                {["a", "b", "c", "d"].map((opt) => {
                  const text = q[`option_${opt}`];
                  const isSelected = answers[q.id] === opt;
                  let cls = "quiz-option";
                  if (isSelected) cls += " selected";
                  if (r) {
                    if (opt === r.correct_option) cls += " correct";
                    else if (isSelected && !r.correct) cls += " incorrect";
                  }
                  return (
                    <label className={cls} key={opt} onClick={() => selectAnswer(q.id, opt)}>
                      <input type="radio" checked={isSelected} readOnly />
                      {text}
                    </label>
                  );
                })}
              </div>
              {r && <p className="quiz-result-explanation">💡 {r.explanation}</p>}
            </div>
          );
        })}

      {questions && !result && (
        <button
          className="btn-primary btn-large"
          onClick={handleSubmit}
          disabled={submitting || Object.keys(answers).length < questions.length}
        >
          {submitting
            ? "Grading…"
            : `Submit (${Object.keys(answers).length}/${questions.length} answered)`}
        </button>
      )}

      {result && (
        <button className="btn-secondary" onClick={startQuiz}>
          🔄 Try another {level} quiz
        </button>
      )}
    </div>
  );
}
