import { useEffect, useState } from "react";
import { uploadFile, createJob, getJob, downloadResult } from "../api/client";

function UploadForm() {
  const [file, setFile] = useState(null);
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);

  const [jobId, setJobId] = useState(null);
  const [job, setJob] = useState(null);

  const resetFlow = () => {
    setFile(null);
    setPrompt("");
    setJob(null);
    setJobId(null);
    setLoading(false);
  };

  // Poll job status
  useEffect(() => {
    if (!jobId) return;

    const interval = setInterval(async () => {
      try {
        const data = await getJob(jobId);
        setJob(data);

        if (data.status === "completed" || data.status === "failed") {
          clearInterval(interval);
        }
      } catch (err) {
        console.error("Failed to fetch job status", err);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [jobId]);

  const handleSubmit = async () => {
    if (!file) {
      alert("Please select a file");
      return;
    }

    try {
      setLoading(true);
      setJob(null);
      setJobId(null);

      const uploadRes = await uploadFile(file);
      const jobRes = await createJob(uploadRes.file_id, prompt);

      setJobId(jobRes.job_id);
    } catch (err) {
      console.error(err);
      alert("Something went wrong. Check console.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Upload form */}
      {!jobId && (
        <>
          <div>
            <label className="block text-sm font-medium mb-1">
              Upload file
            </label>
            <input
              type="file"
              onChange={(e) => setFile(e.target.files[0])}
              className="block w-full text-sm
                file:mr-4 file:py-2 file:px-4
                file:rounded-md file:border-0
                file:text-sm file:font-medium
                file:bg-slate-100 file:text-slate-700
                hover:file:bg-slate-200"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">
              What do you want to do?
            </label>
            <textarea
              rows={3}
              placeholder="e.g. convert to webp passport size very small"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              className="w-full rounded-md border border-slate-300 p-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <button
            onClick={handleSubmit}
            disabled={loading}
            className="w-full rounded-md bg-blue-600 text-white py-2 font-medium hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? "Starting..." : "Convert"}
          </button>
        </>
      )}

      {/* Job status */}
      {job && (
        <div className="rounded-lg border border-slate-200 p-4 bg-slate-50 space-y-4">
          <p className="text-sm font-medium">
            Status:{" "}
            <span className="capitalize font-semibold">
              {job.status}
            </span>
          </p>

          {job.logs && job.logs.length > 0 && (
            <div className="text-xs text-slate-600 bg-white rounded-md border p-3 max-h-40 overflow-auto">
              {job.logs.map((log, idx) => (
                <div key={idx}>• {log}</div>
              ))}
            </div>
          )}

          {job.status === "completed" && (
            <>
              <button
                onClick={() => downloadResult(job.job_id)}
                className="w-full rounded-md bg-green-600 text-white py-2 font-medium hover:bg-green-700"
              >
                Download Result
              </button>

              <div className="flex gap-3">
                <button
                  onClick={resetFlow}
                  className="flex-1 rounded-md border border-slate-300 py-2 text-sm hover:bg-slate-100"
                >
                  Convert Another File
                </button>

                <button
                  onClick={resetFlow}
                  className="flex-1 rounded-md border border-slate-300 py-2 text-sm hover:bg-slate-100"
                >
                  Back to Home
                </button>
              </div>
            </>
          )}

          {job.status === "failed" && (
            <>
              <p className="text-sm text-red-600">
                Job failed. Please try again.
              </p>

              <button
                onClick={resetFlow}
                className="w-full rounded-md border border-slate-300 py-2 text-sm hover:bg-slate-100"
              >
                Try Again
              </button>
            </>
          )}
        </div>
      )}
    </div>
  );
}

export default UploadForm;
