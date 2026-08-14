export function ConfidenceBadge({ confidence }: { confidence: number }) {
  const pct = Math.round(confidence * 100);
  const tone =
    confidence >= 0.7
      ? "bg-emerald-100 text-emerald-700"
      : confidence >= 0.4
        ? "bg-amber-100 text-amber-700"
        : "bg-rose-100 text-rose-700";

  return <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${tone}`}>{pct}% confidence</span>;
}
