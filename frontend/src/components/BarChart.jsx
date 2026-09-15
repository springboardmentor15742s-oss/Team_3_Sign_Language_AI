export default function BarChart({ data, labelKey = "label", valueKey = "count", height = 180 }) {
  if (!data || data.length === 0) {
    return <p className="muted">No data to display.</p>;
  }
  const max = Math.max(...data.map((d) => d[valueKey]), 1);

  return (
    <div className="barchart" style={{ height }}>
      {data.map((d, i) => {
        const pct = Math.max((d[valueKey] / max) * 100, 2);
        return (
          <div className="barchart-col" key={i}>
            <div className="barchart-bar-wrap">
              <div className="barchart-bar" style={{ height: `${pct}%` }} title={`${d[labelKey]}: ${d[valueKey]}`}>
                <span className="barchart-value">{d[valueKey]}</span>
              </div>
            </div>
            <div className="barchart-label">{d[labelKey]}</div>
          </div>
        );
      })}
    </div>
  );
}
