const PALETTE = ["#6d28d9", "#0891b2", "#d97706", "#dc2626", "#16a34a", "#db2777", "#4338ca"];

function colorFor(seed) {
  let hash = 0;
  for (let i = 0; i < seed.length; i++) hash = seed.charCodeAt(i) + ((hash << 5) - hash);
  return PALETTE[Math.abs(hash) % PALETTE.length];
}

function initialsFor(name) {
  if (!name) return "?";
  const parts = name.trim().split(/\s+/);
  const first = parts[0]?.[0] || "";
  const second = parts.length > 1 ? parts[parts.length - 1][0] : "";
  return (first + second).toUpperCase();
}

export default function Avatar({ name, photo, size = 40 }) {
  const style = { width: size, height: size, fontSize: size * 0.4 };

  if (photo) {
    return (
      <img
        src={photo}
        alt={name || "avatar"}
        className="avatar-img"
        style={style}
      />
    );
  }

  return (
    <div className="avatar-fallback" style={{ ...style, background: colorFor(name || "?") }}>
      {initialsFor(name)}
    </div>
  );
}
