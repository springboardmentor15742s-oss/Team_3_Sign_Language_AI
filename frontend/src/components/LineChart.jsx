export default function LineChart({
  points,
  xKey = "index",
  yKey = "overall_accuracy",
  height = 160,
  yMin = 0,
  yMax = 100,
}) {
  if (!points || points.length === 0) {
    return <p className="muted">No data to display.</p>;
  }

  const width = 600;
  const padding = 24;
  const xs = points.map((p) => p[xKey]);
  const xMin = Math.min(...xs);
  const xMaxVal = Math.max(...xs);
  const xRange = xMaxVal - xMin || 1;
  const yRange = yMax - yMin || 1;

  const toX = (x) => padding + ((x - xMin) / xRange) * (width - 2 * padding);
  const toY = (y) => height - padding - ((y - yMin) / yRange) * (height - 2 * padding);

  const pathD = points
    .map((p, i) => `${i === 0 ? "M" : "L"} ${toX(p[xKey]).toFixed(1)} ${toY(p[yKey]).toFixed(1)}`)
    .join(" ");

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="linechart" preserveAspectRatio="none">
      {/* gridlines at 0/50/100 */}
      {[0, 50, 100].map((v) => (
        <line
          key={v}
          x1={padding}
          x2={width - padding}
          y1={toY(v)}
          y2={toY(v)}
          className="linechart-grid"
        />
      ))}
      <path d={pathD} className="linechart-path" fill="none" />
      {points.map((p, i) => (
        <circle
          key={i}
          cx={toX(p[xKey])}
          cy={toY(p[yKey])}
          r={3}
          className="linechart-dot"
        >
          <title>{`#${p[xKey]} — ${p[yKey]}%`}</title>
        </circle>
      ))}
    </svg>
  );
}
