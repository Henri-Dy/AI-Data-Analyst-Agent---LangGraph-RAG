const NODE_LABELS: Record<string, string> = {
  query_analyzer: "Query Analyzer",
  schema_agent: "Schema Agent",
  rag_search: "RAG Search",
  sql_generator: "SQL Generator",
  sql_validator: "SQL Validator",
  sql_fixer: "SQL Fixer",
  sql_executor: "SQL Executor",
  sql_give_up: "SQL Give Up",
  python_analyst: "Python Analyst",
  visualization_agent: "Visualization Agent",
  join: "Join",
  insight_agent: "Insight Agent",
  fact_checker: "Fact Checker",
  human_review_node: "Human Review",
  report_generator: "Report Generator",
};

function label(node: string): string {
  return NODE_LABELS[node] ?? node;
}

export function ProgressTrail({ nodes, active }: { nodes: string[]; active: boolean }) {
  if (nodes.length === 0 && !active) return null;

  return (
    <ol className="flex flex-wrap gap-1.5 text-xs text-slate-500">
      {nodes.map((node, i) => (
        <li key={`${node}-${i}`} className="rounded-full bg-slate-100 px-2 py-0.5">
          {label(node)}
        </li>
      ))}
      {active && (
        <li className="flex items-center gap-1 rounded-full bg-slate-100 px-2 py-0.5 text-slate-400">
          <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-slate-400" />
          working…
        </li>
      )}
    </ol>
  );
}
