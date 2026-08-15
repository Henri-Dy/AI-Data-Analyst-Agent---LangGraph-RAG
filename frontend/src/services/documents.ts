import type { DocumentSummary, DocumentUploadResponse } from "../types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export async function listDocuments(): Promise<DocumentSummary[]> {
  const response = await fetch(`${API_BASE_URL}/api/documents`);
  if (!response.ok) throw new Error(`Failed to list documents (status ${response.status})`);
  return response.json();
}

export async function uploadDocument(
  file: File,
  title: string,
  category: string,
): Promise<DocumentUploadResponse> {
  const form = new FormData();
  form.append("file", file);
  form.append("title", title);
  form.append("category", category);

  const response = await fetch(`${API_BASE_URL}/api/documents`, { method: "POST", body: form });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail ?? `Upload failed (status ${response.status})`);
  }
  return response.json();
}

export async function deleteDocument(documentId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/documents/${documentId}`, { method: "DELETE" });
  if (!response.ok) throw new Error(`Failed to delete document (status ${response.status})`);
}
