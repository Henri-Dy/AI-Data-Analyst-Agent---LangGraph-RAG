"""Query Analyzer agent: turns a natural-language question into structured intent."""
from typing import Literal, Protocol

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from app.core.llm import get_chat_model

AnalysisType = Literal[
    "descriptive", "comparison", "trend", "ranking", "root_cause", "anomaly_detection", "correlation"
]


class QueryAnalysis(BaseModel):
    """Structured intent extracted from a user question."""

    metric: str = Field(description="The primary business metric being asked about, e.g. 'revenue'.")
    period: str | None = Field(default=None, description="The time period referenced, e.g. 'July', 'last quarter'.")
    analysis_type: AnalysisType = Field(description="The kind of analysis required to answer the question.")
    dimensions: list[str] = Field(
        default_factory=list, description="Dimensions to break the metric down by, e.g. region, product."
    )
    requires_sql: bool = Field(description="Whether answering requires querying the operational database.")
    requires_statistics: bool = Field(
        description="Whether answering requires statistical analysis (trends, correlations, anomalies, ...)."
    )
    requires_rag: bool = Field(
        description="Whether answering requires business/domain context from the knowledge base."
    )


class StructuredQueryAnalyzer(Protocol):
    """Anything that maps a prompt to a QueryAnalysis — a real structured-output
    LLM in production, or a fake stand-in in tests."""

    def invoke(self, prompt_input: dict) -> QueryAnalysis: ...


SYSTEM_PROMPT = """You are the Query Analyzer for an AI data analyst platform. \
Given a user's natural-language business question, extract structured intent: \
the metric, time period, analysis type, relevant dimensions, and which \
downstream capabilities (SQL query, statistical analysis, business-knowledge \
retrieval) are needed to answer it. Do not answer the question itself."""

_PROMPT = ChatPromptTemplate.from_messages(
    [("system", SYSTEM_PROMPT), ("human", "{question}")]
)


def get_query_analyzer_llm() -> StructuredQueryAnalyzer:
    """Production factory: a real chat model constrained to QueryAnalysis output."""
    return _PROMPT | get_chat_model().with_structured_output(QueryAnalysis)


def analyze_query(question: str, analyzer: StructuredQueryAnalyzer) -> QueryAnalysis:
    """Runs the Query Analyzer. `analyzer` is injected so tests can supply a
    fake implementation without calling a real LLM provider."""
    return analyzer.invoke({"question": question})
