import React, { useState } from "react";

export default function App() {
  const [file, setFile] = useState(null);
  const [resp, setResp] = useState(null);
  const [loading, setLoading] = useState(false);

  const upload = async () => {
    if (!file) return alert("Choose a file first");
    setLoading(true);
    const form = new FormData();
    form.append("file", file);

    try {
      const res = await fetch("http://localhost:8000/upload", {
        method: "POST",
        body: form,
      });
      const data = await res.json();
      setResp({ ok: res.ok, data });
    } catch (err) {
      setResp({ ok: false, error: err.message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: 24, fontFamily: "Arial, sans-serif" }}>
      <h1>ChangeAnyFile.ai — Dev Upload</h1>
      <p>Choose a file (png/jpg/pdf/docx). No auth required (dev).</p>

      <input
        type="file"
        onChange={(e) => setFile(e.target.files && e.target.files[0])}
      />
      <br />
      <button onClick={upload} disabled={loading} style={{ marginTop: 12 }}>
        {loading ? "Uploading..." : "Upload & Get FileId"}
      </button>

      <div style={{ marginTop: 18 }}>
        <h3>Response</h3>
        <pre style={{ whiteSpace: "pre-wrap" }}>
          {resp ? JSON.stringify(resp, null, 2) : "No response yet"}
        </pre>
      </div>
    </div>
  );
}
