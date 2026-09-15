const LEVEL_CLASS = {
  "Needs Improvement": "level-pill level-weak",
  "Developing": "level-pill level-developing",
  "Good": "level-pill level-good",
};

export default function WeakAreas({ analytics }) {
  if (!analytics?.has_data) {
    return (
      <p className="muted small">
        No gesture attempts logged yet — weak-area detection unlocks after you practice.
      </p>
    );
  }

  const { by_gesture } = analytics;

  return (
    <table className="table">
      <thead>
        <tr>
          <th>Gesture</th>
          <th>Avg Accuracy</th>
          <th>Attempts</th>
          <th>Level</th>
        </tr>
      </thead>
      <tbody>
        {by_gesture.map((g) => (
          <tr key={g.gesture}>
            <td>{g.display_name}</td>
            <td>{g.avg_accuracy}%</td>
            <td>{g.attempts}</td>
            <td>
              <span className={LEVEL_CLASS[g.level] || "level-pill"}>{g.level}</span>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
