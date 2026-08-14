export interface HealthResponse {
  status: string;
  app: string;
  environment: string;
  llm_provider: string;
}

export interface ChartSpec {
  chart_type: string;
  figure: {
    data: Record<string, unknown>[];
    layout: Record<string, unknown>;
  };
}

export interface ReportSource {
  title: string;
  category: string;
  source_path: string;
}

export interface FinalReport {
  answer: string;
  confidence: number;
  sql: string | null;
  sql_row_count: number | null;
  chart: ChartSpec | null;
  fact_check_notes: string[];
  human_reviewed: boolean;
  sources: ReportSource[];
  errors: string[];
}

export interface ChatUpdateEvent {
  thread_id: string;
  node: string;
  output: Record<string, unknown>;
}

export interface ChatInterruptEvent {
  thread_id: string;
  reason: string;
  confidence: number;
  narrative: string;
  fact_check_notes: string[];
}

export interface ChatDoneEvent {
  thread_id: string;
  report: FinalReport;
}

export interface ChatErrorEvent {
  thread_id: string;
  message: string;
}

export type ChatEvent =
  | { event: "update"; data: ChatUpdateEvent }
  | { event: "interrupt"; data: ChatInterruptEvent }
  | { event: "done"; data: ChatDoneEvent }
  | { event: "error"; data: ChatErrorEvent };

export interface ReviewDecision {
  approved: boolean;
  reviewer_notes: string | null;
  edited_narrative: string | null;
}
