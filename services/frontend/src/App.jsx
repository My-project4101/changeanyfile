import React, { useState, useEffect, useRef } from "react";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export default function App() {
  const [file, setFile] = useState(null);
  const [uploadResp, setUploadResp] = useState(null);
  const [job, setJob] = useState(null);
  const [prompt, setPrompt] = useState("");
  const [loadingUpload, setLoadingUpload] = useState(false);
  const [creatingJob, setCreatingJob] = useState(false);
  const [polling, setPolling] = useState(false);

  const pollRef = useRef(null);

  // Upload file to backend
  const upload = async () => {
    if (!file) return alert("Choose a file first");
    setLoadingUpload(true);
    const form = new FormData();
    form.append("file", file);
    try {
      const res = await fetch(`${API_BASE}/upload`, {
        method: "POST",
        body: form,
      });
      const data = await res.json();
      setUploadResp({ ok: res.ok, data });
    } catch (err) {
      setUploadResp({ ok: false, error: err.message });
    } finally {
      setLoadingUpload(false);
    }
  };

  // Create job for the uploaded file
  const createJob = async () => {
    if (!uploadResp || !uploadResp.data || !uploadResp.data.fileId) {
      return alert("Upload a file first");
    }
    setCreatingJob(true);
    try {
      const payload = {
        fileId: uploadResp.data.fileId,
        prompt: prompt || "Process this file (default)",
      };
      const res = await fetch(`${API_BASE}/jobs`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to create job");
      setJob({ jobId: data.jobId, status: data.status, createdAt: data.createdAt });
      startPolling(data.jobId);
    } catch (err) {
      alert("Create job failed: " + err.message);
    } finally {
      setCreatingJob(false);
    }
  };

  // Poll job status every 1.5s
  const startPolling = (jobId) => {
    if (pollRef.current) clearInterval(pollRef.current);
    setPolling(true);
    pollRef.current = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/jobs/${jobId}`);
        const data = await res.json();
        setJob(data);
        if (data.status === "completed" || data.status === "failed") {
          clearInterval(pollRef.current);
          pollRef.current = null;
          setPolling(false);
        }
      } catch (err) {
        console.error("Polling error", err);
      }
    }, 1500);
  };

  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);

  const downloadResult = () => {
    if (!job || !job.jobId) return;
    window.location.href = `${API_BASE}/download/result/${job.jobId}`;
  };

  const statusChip = (status) => {
    if (!status) return null;
    const lowered = status.toLowerCase();
    let label = lowered;
    let cls = "";
    if (lowered === "processing") cls = "processing";
    if (lowered === "completed") cls = "completed";
    if (lowered === "failed") cls = "failed";

    return (
      <span className="chip">
        <span className={`status-dot ${cls}`} />
        {label}
      </span>
    );
  };

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="badge">
          <span className="badge-dot" />
          Sprint Dev Environment · No Docker
        </div>
        <h1 className="app-title">ChangeAnyFile.ai</h1>
        <p className="app-subtitle">
          Upload any file, describe what you want, and let the automation pipeline handle the rest.
          (Sprint build: upload → job → async processing → download)
        </p>
      </header>

      <div className="grid">
        {/* LEFT: Upload + Job creation */}
        <div className="card">
          <h3>1 · Upload a file</h3>
          <small>Supports images, PDF, DOC/DOCX, TXT (50MB max in this dev build).</small>

          <div className="field">
            <label className="label">Select file</label>
            <input
              className="input"
              type="file"
              onChange={(e) => setFile(e.target.files && e.target.files[0])}
            />
          </div>

          <button
            className="button"
            onClick={upload}
            disabled={loadingUpload}
            style={{ marginBottom: 12 }}
          >
            {loadingUpload ? "Uploading..." : "Upload"}
          </button>

          <div className="field">
            <span className="label">Upload response</span>
            <div className="code-block">
              {uploadResp ? JSON.stringify(uploadResp, null, 2) : "// No upload yet"}
            </div>
          </div>

          <hr style={{ margin: "16px 0", border: "none", borderTop: "1px solid #e5e7eb" }} />

          <h3>2 · Create a Job</h3>
          <small>
            This is where AI will eventually parse your instruction into actions. For now, it just
            triggers the background worker.
          </small>

          <div className="field">
            <label className="label">Instruction to the system (prompt)</label>
            <input
              className="text-input"
              type="text"
              placeholder="e.g. Compress to 200KB and convert to webp"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
            />
          </div>

          <button
            className="button"
            onClick={createJob}
            disabled={creatingJob || !uploadResp}
          >
            {creatingJob ? "Creating job..." : "Create Job"}
          </button>
        </div>

        {/* RIGHT: Job status + logs + result */}
        <div className="card">
          <h3>3 · Job status & result</h3>
          <small>Track the background processing and download output when ready.</small>

          <div className="field">
            <span className="label">Current job</span>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
              <div>
                {job?.jobId ? (
                  <>
                    <div style={{ fontSize: "0.8rem", color: "#6b7280" }}>Job ID</div>
                    <div style={{ fontSize: "0.78rem", wordBreak: "break-all" }}>{job.jobId}</div>
                  </>
                ) : (
                  <span style={{ fontSize: "0.85rem", color: "#9ca3af" }}>
                    No job created yet.
                  </span>
                )}
              </div>
              <div>{job?.status && statusChip(job.status)}</div>
            </div>
          </div>

          <div className="field">
            <span className="label">Logs</span>
            <div className="code-block">
              {job?.logs && job.logs.length > 0
                ? job.logs.join("\n")
                : "// No logs yet — create a job first"}
            </div>
          </div>

          <div className="field">
            <span className="label">Result</span>
            {job && job.status === "completed" && job.result ? (
              <>
                <div style={{ marginBottom: 8 }}>
                  <div style={{ fontSize: "0.8rem", color: "#6b7280" }}>Filename</div>
                  <div style={{ fontSize: "0.85rem" }}>{job.result.filename}</div>
                  <div style={{ fontSize: "0.8rem", color: "#6b7280" }}>
                    Size: {job.result.size} bytes
                  </div>
                </div>
                <button className="button" onClick={downloadResult}>
                  Download processed file
                </button>
              </>
            ) : job && job.status === "failed" ? (
              <div style={{ color: "#ef4444", fontSize: "0.85rem" }}>
                Job failed · check logs above.
              </div>
            ) : job && (job.status === "processing" || job.status === "queued") ? (
              <div style={{ fontSize: "0.85rem", color: "#6b7280" }}>
                {polling ? "Processing in background…" : "Waiting for worker…"}
              </div>
            ) : (
              <div style={{ fontSize: "0.85rem", color: "#9ca3af" }}>
                Result will appear here after processing.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
