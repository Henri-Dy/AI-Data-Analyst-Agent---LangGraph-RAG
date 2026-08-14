import { lazy, Suspense } from "react";
import type { FinalReport } from "../types";
import { ConfidenceBadge } from "./ConfidenceBadge";

// plotly.js is a multi-MB dependency; load it only once a report actually
// has a chart to render, instead of in the app's initial bundle.
const ChartView = lazy(() => import("./ChartView").then((m) => ({ default: m.ChartView })));

export function AnswerReport({ report }: { report: FinalReport }) {
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <ConfidenceBadge confidence={report.confidence} />
        {report.human_reviewed && (
          <span className="rounded-full bg-sky-100 px-2 py-0.5 text-xs font-medium text-sky-700">
            Human-reviewed
          </span>
        )}
      </div>

      <p className="text-sm leading-relaxed text-slate-800">{report.answer}</p>

      {report.errors.length > 0 && (
        <ul className="space-y-1 rounded-lg border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700">
          {report.errors.map((err) => (
            <li key={err}>{err}</li>
          ))}
        </ul>
      )}

      {report.chart && (
        <Suspense fallback={<div className="h-80 animate-pulse rounded-lg bg-slate-100" />}>
          <ChartView chart={report.chart} />
        </Suspense>
      )}

      {report.sql && (
        <details className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-xs">
          <summary className="cursor-pointer font-medium text-slate-600">
            SQL{report.sql_row_count !== null ? ` (${report.sql_row_count} row${report.sql_row_count === 1 ? "" : "s"})` : ""}
          </summary>
          <pre className="mt-2 overflow-x-auto whitespace-pre-wrap text-slate-700">{report.sql}</pre>
        </details>
      )}

      {report.sources.length > 0 && (
        <details className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-xs">
          <summary className="cursor-pointer font-medium text-slate-600">Sources ({report.sources.length})</summary>
          <ul className="mt-2 space-y-1 text-slate-700">
            {report.sources.map((source) => (
              <li key={source.title}>
                <span className="font-medium">{source.title}</span>{" "}
                <span className="text-slate-400">— {source.category}</span>
              </li>
            ))}
          </ul>
        </details>
      )}

      {report.fact_check_notes.length > 0 && (
        <details className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-xs">
          <summary className="cursor-pointer font-medium text-slate-600">Fact-check notes</summary>
          <ul className="mt-2 space-y-1 text-slate-700">
            {report.fact_check_notes.map((note) => (
              <li key={note}>{note}</li>
            ))}
          </ul>
        </details>
      )}
    </div>
  );
}
