import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import type { DatasetSummary } from "../types";
import { deleteDataset, listDatasets, uploadDataset } from "../services/datasets";

export function DatasetManager() {
  const [datasets, setDatasets] = useState<DatasetSummary[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [tableName, setTableName] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function refresh() {
    listDatasets()
      .then(setDatasets)
      .catch((e: Error) => setError(e.message));
  }

  useEffect(refresh, []);

  async function handleUpload(e: FormEvent) {
    e.preventDefault();
    if (!file) return;
    setBusy(true);
    setError(null);
    try {
      await uploadDataset(file, tableName.trim() || undefined);
      setFile(null);
      setTableName("");
      refresh();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function handleDelete(name: string) {
    setError(null);
    try {
      await deleteDataset(name);
      refresh();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  return (
    <div className="space-y-4 rounded-lg border border-slate-200 bg-white p-4">
      <h2 className="text-sm font-semibold text-slate-900">Tabular datasets (SQL)</h2>

      <form onSubmit={handleUpload} className="space-y-2">
        <input
          type="file"
          accept=".csv"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          className="block w-full text-sm"
        />
        <input
          type="text"
          value={tableName}
          onChange={(e) => setTableName(e.target.value)}
          placeholder="Table name (optional, defaults to the filename)"
          className="w-full rounded-md border border-slate-300 px-3 py-1.5 text-sm outline-none focus:border-slate-500"
        />
        <button
          type="submit"
          disabled={busy || !file}
          className="rounded-md bg-slate-900 px-3 py-1.5 text-sm font-medium text-white disabled:bg-slate-300"
        >
          Upload
        </button>
      </form>

      {error && <p className="text-xs text-red-600">{error}</p>}

      <ul className="space-y-1">
        {datasets.map((ds) => (
          <li
            key={ds.table_name}
            className="flex items-center justify-between rounded-md border border-slate-200 px-3 py-1.5 text-sm"
          >
            <span>
              <span className="font-medium">{ds.table_name}</span>{" "}
              <span className="text-slate-400">
                ({ds.row_count} rows, {ds.columns.length} columns)
              </span>
            </span>
            <button
              type="button"
              onClick={() => handleDelete(ds.table_name)}
              className="text-xs font-medium text-red-600 hover:text-red-700"
            >
              Delete
            </button>
          </li>
        ))}
        {datasets.length === 0 && <li className="text-xs text-slate-400">No datasets uploaded yet.</li>}
      </ul>
    </div>
  );
}
