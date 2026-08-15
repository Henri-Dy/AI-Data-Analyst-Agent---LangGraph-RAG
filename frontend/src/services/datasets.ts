import type { DatasetSummary, DatasetUploadResponse } from "../types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export async function listDatasets(): Promise<DatasetSummary[]> {
  const response = await fetch(`${API_BASE_URL}/api/datasets`);
  if (!response.ok) throw new Error(`Failed to list datasets (status ${response.status})`);
  return response.json();
}

export async function uploadDataset(file: File, tableName?: string): Promise<DatasetUploadResponse> {
  const form = new FormData();
  form.append("file", file);
  if (tableName) form.append("table_name", tableName);

  const response = await fetch(`${API_BASE_URL}/api/datasets`, { method: "POST", body: form });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail ?? `Upload failed (status ${response.status})`);
  }
  return response.json();
}

export async function deleteDataset(tableName: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/datasets/${tableName}`, { method: "DELETE" });
  if (!response.ok) throw new Error(`Failed to delete dataset (status ${response.status})`);
}
