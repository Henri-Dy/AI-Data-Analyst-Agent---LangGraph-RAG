import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import type { DocumentSummary } from "../types";
import { deleteDocument, listDocuments, uploadDocument } from "../services/documents";

const CATEGORIES = [
  "glossary",
  "kpi_definitions",
  "product_docs",
  "financial_definitions",
  "sales_docs",
  "regional_info",
  "policies",
];

export function DocumentManager() {
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [category, setCategory] = useState(CATEGORIES[0]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function refresh() {
    listDocuments()
      .then(setDocuments)
      .catch((e: Error) => setError(e.message));
  }

  useEffect(refresh, []);

  async function handleUpload(e: FormEvent) {
    e.preventDefault();
    if (!file || !title.trim()) return;
    setBusy(true);
    setError(null);
    try {
      await uploadDocument(file, title.trim(), category);
      setFile(null);
      setTitle("");
      refresh();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function handleDelete(documentId: string) {
    setError(null);
    try {
      await deleteDocument(documentId);
      refresh();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  return (
    <div className="space-y-4 rounded-lg border border-slate-200 bg-white p-4">
      <h2 className="text-sm font-semibold text-slate-900">Business documents (RAG)</h2>

      <form onSubmit={handleUpload} className="space-y-2">
        <input
          type="file"
          accept=".md,.txt"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          className="block w-full text-sm"
        />
        <div className="flex gap-2">
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Title"
            className="w-full rounded-md border border-slate-300 px-3 py-1.5 text-sm outline-none focus:border-slate-500"
          />
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="rounded-md border border-slate-300 px-2 py-1.5 text-sm outline-none focus:border-slate-500"
          >
            {CATEGORIES.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </div>
        <button
          type="submit"
          disabled={busy || !file || !title.trim()}
          className="rounded-md bg-slate-900 px-3 py-1.5 text-sm font-medium text-white disabled:bg-slate-300"
        >
          Upload
        </button>
      </form>

      {error && <p className="text-xs text-red-600">{error}</p>}

      <ul className="space-y-1">
        {documents.map((doc) => (
          <li
            key={doc.document_id}
            className="flex items-center justify-between rounded-md border border-slate-200 px-3 py-1.5 text-sm"
          >
            <span>
              <span className="font-medium">{doc.title}</span>{" "}
              <span className="text-slate-400">
                ({doc.category}, {doc.chunk_count} chunk{doc.chunk_count === 1 ? "" : "s"})
              </span>
            </span>
            <button
              type="button"
              onClick={() => handleDelete(doc.document_id)}
              className="text-xs font-medium text-red-600 hover:text-red-700"
            >
              Delete
            </button>
          </li>
        ))}
        {documents.length === 0 && <li className="text-xs text-slate-400">No documents uploaded yet.</li>}
      </ul>
    </div>
  );
}
