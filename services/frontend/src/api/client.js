const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function handleResponse(response) {
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || "API request failed");
  }
  return response.json();
}

export async function uploadFile(file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/upload`, {
    method: "POST",
    body: formData,
  });

  return handleResponse(response);
}

export async function createJob(fileId, prompt) {
  const response = await fetch(`${API_BASE_URL}/jobs`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      file_id: fileId,
      prompt: prompt,
    }),
  });

  return handleResponse(response);
}

export async function getJob(jobId) {
  const response = await fetch(`${API_BASE_URL}/jobs/${jobId}`);
  return handleResponse(response);
}

export function downloadResult(jobId) {
  window.location.href = `${API_BASE_URL}/download/result/${jobId}`;
}
