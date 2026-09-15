import { useEffect, useRef, useState } from "react";
import { api } from "../api";

export default function GesturePractice() {
  const videoRef = useRef(null);
  const canvasRef = useRef(null); // hidden capture canvas
  const overlayRef = useRef(null); // visible landmark-overlay canvas

  const [library, setLibrary] = useState([]);
  const [connections, setConnections] = useState([]);
  const [targetLabel, setTargetLabel] = useState("");
  const [cameraError, setCameraError] = useState("");
  const [busy, setBusy] = useState(false);
  const [mode, setMode] = useState("assess"); // "assess" | "detect"

  const [assessResult, setAssessResult] = useState(null);
  const [detectResult, setDetectResult] = useState(null);

  const [history, setHistory] = useState([]);
  const [stats, setStats] = useState(null);

  // --- Setup: library, connections, webcam, history/stats ------------------
  useEffect(() => {
    api.getGestureLibrary().then((lib) => {
      setLibrary(lib);
      if (lib.length > 0) setTargetLabel(lib[0].key);
    });
    api.getHandConnections().then(setConnections);
    loadHistoryAndStats();

    let stream;
    navigator.mediaDevices
      ?.getUserMedia({ video: { width: 480, height: 360 } })
      .then((s) => {
        stream = s;
        if (videoRef.current) {
          videoRef.current.srcObject = s;
        }
      })
      .catch((err) => setCameraError(`Could not access webcam: ${err.message}`));

    return () => {
      if (stream) stream.getTracks().forEach((t) => t.stop());
    };
  }, []);

  function loadHistoryAndStats() {
    api.getGestureHistory(10).then(setHistory);
    api.getGestureStats().then(setStats);
  }

  // --- Draw landmarks + skeleton over the video preview ---------------------
  function drawLandmarks(landmarks) {
    const canvas = overlayRef.current;
    const video = videoRef.current;
    if (!canvas || !video) return;
    const ctx = canvas.getContext("2d");
    canvas.width = video.videoWidth || 480;
    canvas.height = video.videoHeight || 360;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (!landmarks) return;

    const pts = landmarks.map((lm) => ({ x: lm.x * canvas.width, y: lm.y * canvas.height }));

    ctx.strokeStyle = "#6d28d9";
    ctx.lineWidth = 2;
    connections.forEach(([a, b]) => {
      ctx.beginPath();
      ctx.moveTo(pts[a].x, pts[a].y);
      ctx.lineTo(pts[b].x, pts[b].y);
      ctx.stroke();
    });

    ctx.fillStyle = "#ec4899";
    pts.forEach((p) => {
      ctx.beginPath();
      ctx.arc(p.x, p.y, 4, 0, Math.PI * 2);
      ctx.fill();
    });
  }

  function captureBlob() {
    return new Promise((resolve) => {
      const video = videoRef.current;
      const canvas = canvasRef.current;
      if (!video || !canvas) return resolve(null);
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      const ctx = canvas.getContext("2d");
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      canvas.toBlob((blob) => resolve(blob), "image/jpeg", 0.9);
    });
  }

  async function handleDetect() {
    setBusy(true);
    setDetectResult(null);
    try {
      const blob = await captureBlob();
      if (!blob) return;
      const result = await api.detectGesture(blob);
      setDetectResult(result);
      drawLandmarks(result.landmarks);
    } catch (err) {
      setDetectResult({ error: err.message });
    } finally {
      setBusy(false);
    }
  }

  async function handleAssess() {
    setBusy(true);
    setAssessResult(null);
    try {
      const blob = await captureBlob();
      if (!blob) return;
      const result = await api.assessGesture(blob, targetLabel);
      setAssessResult(result);
      drawLandmarks(result.landmarks);
      loadHistoryAndStats();
    } catch (err) {
      setAssessResult({ error: err.message });
    } finally {
      setBusy(false);
    }
  }

  const selectedGestureInfo = library.find((g) => g.key === targetLabel);

  return (
    <div className="page">
      <h1>🖐️ Gesture Practice</h1>
      <p className="muted">
        Milestone 2 — Gesture Recognition Engine, Hand Tracking & Sign Accuracy Assessment.
      </p>

      {stats && (
        <div className="kpi-row">
          <div className="kpi-card">
            <div className="kpi-value">{stats.total_attempts}</div>
            <div className="kpi-label">Total Attempts</div>
          </div>
          <div className="kpi-card">
            <div className="kpi-value">{stats.avg_accuracy}%</div>
            <div className="kpi-label">Avg Accuracy</div>
          </div>
          <div className="kpi-card">
            <div className="kpi-value">{stats.best_accuracy}%</div>
            <div className="kpi-label">Best Accuracy</div>
          </div>
          <div className="kpi-card">
            <div className="kpi-value">{stats.matched_count}</div>
            <div className="kpi-label">Matched Signs</div>
          </div>
        </div>
      )}

      <div className="grid-2">
        <div className="card">
          <h3>📷 Camera</h3>
          {cameraError && <div className="alert alert-error">{cameraError}</div>}
          <div className="camera-wrap">
            <video ref={videoRef} autoPlay playsInline muted className="camera-video" />
            <canvas ref={overlayRef} className="camera-overlay" />
          </div>
          <canvas ref={canvasRef} style={{ display: "none" }} />

          <div className="tabs" style={{ marginTop: 12 }}>
            <button className={mode === "assess" ? "tab active" : "tab"} onClick={() => setMode("assess")}>
              🎯 Assess Against Target
            </button>
            <button className={mode === "detect" ? "tab active" : "tab"} onClick={() => setMode("detect")}>
              🔍 Free Detect
            </button>
          </div>

          {mode === "assess" && (
            <>
              <label>
                Target sign
                <select value={targetLabel} onChange={(e) => setTargetLabel(e.target.value)}>
                  {library.map((g) => (
                    <option key={g.key} value={g.key}>
                      {g.display_name} ({g.related_sign})
                    </option>
                  ))}
                </select>
              </label>
              {selectedGestureInfo && <p className="muted small">{selectedGestureInfo.description}</p>}
              <button className="btn-primary" onClick={handleAssess} disabled={busy}>
                {busy ? "Analyzing..." : "📸 Capture & Assess"}
              </button>
            </>
          )}

          {mode === "detect" && (
            <>
              <p className="muted small">
                Make any hand shape from the library and see what the engine recognizes.
              </p>
              <button className="btn-primary" onClick={handleDetect} disabled={busy}>
                {busy ? "Analyzing..." : "📸 Capture & Detect"}
              </button>
            </>
          )}
        </div>

        <div className="card">
          <h3>📊 Result</h3>

          {mode === "assess" && assessResult && <AssessResultView result={assessResult} />}
          {mode === "assess" && !assessResult && <p className="muted">Capture a frame to see your score.</p>}

          {mode === "detect" && detectResult && <DetectResultView result={detectResult} />}
          {mode === "detect" && !detectResult && (
            <p className="muted">Capture a frame to see the recognized gesture.</p>
          )}
        </div>
      </div>

      <div className="card">
        <h3>📚 Gesture Library</h3>
        <table className="table">
          <thead>
            <tr>
              <th>Gesture</th>
              <th>Related Sign</th>
              <th>Description</th>
            </tr>
          </thead>
          <tbody>
            {library.map((g) => (
              <tr key={g.key}>
                <td>{g.display_name}</td>
                <td>{g.related_sign}</td>
                <td>{g.description}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="card">
        <h3>🕘 Recent Practice Attempts</h3>
        {history.length > 0 ? (
          <table className="table">
            <thead>
              <tr>
                <th>Target</th>
                <th>Detected</th>
                <th>Overall</th>
                <th>Matched</th>
                <th>When</th>
              </tr>
            </thead>
            <tbody>
              {history.map((h) => (
                <tr key={h.id}>
                  <td>{h.target_display_name}</td>
                  <td>{h.detected_label || "—"}</td>
                  <td>{h.overall_accuracy}%</td>
                  <td>{h.matched ? "✅" : "❌"}</td>
                  <td>{h.created_at}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="muted">No practice attempts yet — try assessing a gesture above.</p>
        )}
      </div>
    </div>
  );
}

function AssessResultView({ result }) {
  if (result.error) return <div className="alert alert-error">{result.error}</div>;
  if (!result.hand_detected) {
    return (
      <div className="alert alert-error">
        {result.feedback?.[0] || "No hand detected. Try again with better lighting/framing."}
      </div>
    );
  }
  return (
    <div>
      <div className={result.matched ? "alert alert-success" : "alert alert-info"}>
        <strong>{result.overall_accuracy}% overall accuracy</strong> for "{result.target_display_name}"
        {result.matched ? " — matched! 🎉" : ""}
      </div>

      <div className="grid-2">
        <div className="kpi-card">
          <div className="kpi-value">{result.hand_shape_accuracy}%</div>
          <div className="kpi-label">Hand Shape Accuracy</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-value">{result.position_accuracy}%</div>
          <div className="kpi-label">Position Accuracy</div>
        </div>
      </div>

      <h4>Finger-by-finger breakdown</h4>
      <table className="table">
        <thead>
          <tr>
            <th>Finger</th>
            <th>Expected</th>
            <th>Actual</th>
            <th>Correct</th>
          </tr>
        </thead>
        <tbody>
          {result.finger_breakdown.map((f) => (
            <tr key={f.finger}>
              <td>{f.finger}</td>
              <td>{f.expected ? "Extended" : "Curled"}</td>
              <td>{f.actual ? "Extended" : "Curled"}</td>
              <td>{f.correct ? "✅" : "❌"}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h4>Feedback</h4>
      <ul>
        {result.feedback.map((f, i) => (
          <li key={i}>{f}</li>
        ))}
      </ul>
    </div>
  );
}

function DetectResultView({ result }) {
  if (result.error) return <div className="alert alert-error">{result.error}</div>;
  if (!result.hand_detected) {
    return <div className="alert alert-error">No hand detected. Try again with better lighting/framing.</div>;
  }
  return (
    <div>
      <div className="alert alert-success">
        Recognized as <strong>{result.predicted_display_name || "Unrecognized shape"}</strong>
        {result.confidence != null && ` (${Math.round(result.confidence * 100)}% match)`}
      </div>
      <p>
        <strong>Handedness:</strong> {result.handedness} (
        {Math.round((result.handedness_confidence || 0) * 100)}% confidence)
      </p>
    </div>
  );
}
