export default function LearningPlan({ plan }) {
  if (!plan || plan.items.length === 0) {
    return <p className="muted small">{plan?.headline || "No plan yet — practice a few gestures first."}</p>;
  }

  return (
    <>
      <p className="learning-plan-headline">🎯 {plan.headline}</p>
      <ol className="learning-plan-list">
        {plan.items.map((item) => (
          <li key={item.gesture}>
            <strong>{item.display_name}</strong>
            <span className="muted"> — Practice: {item.practice_count} attempts</span>
            <div className="muted small">{item.reason}</div>
          </li>
        ))}
      </ol>
    </>
  );
}
