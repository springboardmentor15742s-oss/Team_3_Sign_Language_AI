import { useEffect, useState } from "react";
import { api } from "../api";
import BarChart from "../components/BarChart";

export default function DatasetExplorer() {
  const [recommended, setRecommended] = useState([]);
  const [datasetOptions, setDatasetOptions] = useState([]);
  const [selected, setSelected] = useState("sample");
  const [structure, setStructure] = useState(null);
  const [preview, setPreview] = useState(null);
  const [previewClass, setPreviewClass] = useState("");
  const [formatReport, setFormatReport] = useState(null);
  const [width, setWidth] = useState(128);
  const [height, setHeight] = useState(128);
  const [preprocessResult, setPreprocessResult] = useState(null);
  const [log, setLog] = useState([]);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.getRecommendedDatasets().then(setRecommended);
    api.listDatasets().then(setDatasetOptions);
    loadLog();
    loadPreview("sample");
  }, []);

  function loadLog() {
    api.getDatasetLog().then(setLog);
  }

  async function loadPreview(name) {
    const p = await api.getDatasetPreview(name);
    setPreview(p);
    setPreviewClass(p.classes[0] || "");
  }

  async function handleAnalyze() {
    setBusy(true);
    try {
      const s = await api.getDatasetStructure(selected);
      setStructure(s);
      loadLog();
    } finally {
      setBusy(false);
    }
  }

  async function handleFormatReport() {
    setBusy(true);
    try {
      const r = await api.getFormatReport(selected);
      setFormatReport(r);
    } finally {
      setBusy(false);
    }
  }

  async function handlePreprocess() {
    setBusy(true);
    setPreprocessResult(null);
    try {
      const r = await api.preprocessDataset(selected, width, height);
      setPreprocessResult(r);
      loadLog();
    } finally {
      setBusy(false);
    }
  }

  function handleSelectChange(e) {
    const val = e.target.value;
    setSelected(val);
    setStructure(null);
    setFormatReport(null);
    setPreprocessResult(null);
    loadPreview(val);
  }

  return (
    <div className="page">
      <h1>🗂️ Dataset Explorer</h1>
      <p className="muted">Organize, explore, and preprocess the sign-language datasets used by the platform.</p>

      <div className="card">
        <h3>📚 Recommended Datasets (per project plan)</h3>
        <table className="table">
          <thead>
            <tr>
              <th>Dataset</th>
              <th>Purpose</th>
              <th>Source</th>
            </tr>
          </thead>
          <tbody>
            {recommended.map((d) => (
              <tr key={d.name}>
                <td>{d.name}</td>
                <td>{d.purpose.join(", ")}</td>
                <td className="mono small">{d.source}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="alert alert-info">
        Real datasets are large and hosted on Kaggle / academic mirrors, so they aren't bundled
        here. Use <code>backend/datasets/dataset_downloader.py</code> (run locally with your
        Kaggle API key) to download them into <code>backend/datasets/raw/</code>. Below, this page
        explores whichever dataset you select — defaulting to the bundled{" "}
        <strong>synthetic sample dataset</strong> so you can try it immediately.
      </div>

      <div className="card">
        <h3>🔍 Explore a Dataset Folder</h3>
        <label>
          Choose a dataset to explore
          <select value={selected} onChange={handleSelectChange}>
            {datasetOptions.map((o) => (
              <option key={o.key} value={o.key}>
                {o.label}
              </option>
            ))}
          </select>
        </label>

        <div className="grid-2">
          <div>
            <button className="btn-secondary" onClick={handleAnalyze} disabled={busy}>
              📁 Analyze folder structure & labels
            </button>
            {structure && (
              <>
                {structure.classes.length === 0 ? (
                  <p className="muted">
                    No class-labeled images found. Expected layout:{" "}
                    <code>dataset_dir/&lt;class_label&gt;/&lt;image files&gt;</code>
                  </p>
                ) : (
                  <>
                    <p>
                      <strong>Total classes:</strong> {structure.classes.length} |{" "}
                      <strong>Total images:</strong> {structure.total_images}
                    </p>
                    <BarChart
                      data={structure.classes.map((c) => ({ label: c.label, count: c.count }))}
                    />
                    <table className="table">
                      <thead>
                        <tr>
                          <th>Class Label</th>
                          <th>Image Count</th>
                        </tr>
                      </thead>
                      <tbody>
                        {structure.classes.map((c) => (
                          <tr key={c.label}>
                            <td>{c.label}</td>
                            <td>{c.count}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </>
                )}
              </>
            )}
          </div>

          <div>
            <div className="field-label">🖼️ Sample images preview</div>
            {preview && preview.classes.length > 0 ? (
              <>
                <select value={previewClass} onChange={(e) => setPreviewClass(e.target.value)}>
                  {preview.classes.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
                <div className="image-row">
                  {(preview.samples[previewClass] || []).map((imgPath) => (
                    <img key={imgPath} src={api.datasetImageUrl(imgPath)} alt={previewClass} />
                  ))}
                </div>
              </>
            ) : (
              <p className="muted">No class subfolders found.</p>
            )}
          </div>
        </div>
      </div>

      <div className="card">
        <h3>🧾 Image Format Report (sample)</h3>
        <button className="btn-secondary" onClick={handleFormatReport} disabled={busy}>
          Generate format report
        </button>
        {formatReport && formatReport.length > 0 && (
          <table className="table">
            <thead>
              <tr>
                <th>Class</th>
                <th>File</th>
                <th>Width</th>
                <th>Height</th>
                <th>Mode</th>
                <th>Format</th>
              </tr>
            </thead>
            <tbody>
              {formatReport.map((r, i) => (
                <tr key={i}>
                  <td>{r.class}</td>
                  <td>{r.file}</td>
                  <td>{r.width}</td>
                  <td>{r.height}</td>
                  <td>{r.mode}</td>
                  <td>{r.format}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <div className="card">
        <h3>⚙️ Begin Preprocessing</h3>
        <p>
          Resizes images to a fixed size, normalizes pixel values, and saves them into{" "}
          <code>backend/datasets/processed/&lt;dataset&gt;/&lt;class_label&gt;/</code>, ready for
          Milestone-2 model training (CNN / LSTM / Transformer).
        </p>
        <div className="grid-2">
          <label>
            Target width
            <input
              type="range"
              min={32}
              max={256}
              step={32}
              value={width}
              onChange={(e) => setWidth(Number(e.target.value))}
            />
            {width}px
          </label>
          <label>
            Target height
            <input
              type="range"
              min={32}
              max={256}
              step={32}
              value={height}
              onChange={(e) => setHeight(Number(e.target.value))}
            />
            {height}px
          </label>
        </div>
        <button className="btn-primary" onClick={handlePreprocess} disabled={busy}>
          🚀 Run preprocessing on selected dataset
        </button>
        {preprocessResult && (
          <div className="alert alert-success">
            Processed {preprocessResult.processed} images ({preprocessResult.errors} errors) →
            saved to <code>{preprocessResult.output_dir}</code>
          </div>
        )}
      </div>

      <div className="card">
        <h3>📜 Recent Dataset Actions Log</h3>
        {log.length > 0 ? (
          <table className="table">
            <thead>
              <tr>
                <th>Dataset</th>
                <th>Action</th>
                <th>Details</th>
                <th>When</th>
              </tr>
            </thead>
            <tbody>
              {log.map((l) => (
                <tr key={l.id}>
                  <td>{l.dataset_name}</td>
                  <td>{l.action}</td>
                  <td>{l.details}</td>
                  <td>{l.performed_at}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="muted">No dataset actions logged yet.</p>
        )}
      </div>
    </div>
  );
}
