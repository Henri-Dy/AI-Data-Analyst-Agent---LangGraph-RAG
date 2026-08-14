"""Insight Agent: turns computed results into a grounded narrative answer.

Every specific number the narrative asserts must also be listed as a
`claim`, so the (deterministic, LLM-free) Fact Checker can verify each one
against the actual SQL/statistical results before the answer ships.
"""
from typing import Protocol

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from app.core.llm import get_chat_model


class InsightClaim(BaseModel):
    text: str = Field(description="A single factual sentence from the narrative, e.g. 'Revenue grew 12% in July.'")
    value: float = Field(description="The specific number asserted by this claim, e.g. 12.0 for '12%'.")


class InsightGeneration(BaseModel):
    narrative: str = Field(
        description="A 2-5 sentence narrative answer to the user's question, citing only numbers "
        "that literally appear in the provided data."
    )
    claims: list[InsightClaim] = Field(
        default_factory=list,
        description="Every specific number or percentage stated in the narrative, extracted so each "
        "can be independently checked against the source data.",
    )


class StructuredInsightAgent(Protocol):
    def invoke(self, prompt_input: dict) -> InsightGeneration: ...


SYSTEM_PROMPT = """You are the Insight Agent for an AI data analyst platform. \
Given a user's question and the actual computed results (SQL data, \
statistical analysis, and/or retrieved business context), write a short \
narrative answer.

Rules:
- State only numbers, percentages, and facts that literally appear in the \
computed data below. Never invent, round loosely, or estimate a figure.
- If the data doesn't answer the question, say so plainly instead of guessing.
- List every specific number or percentage you state as a separate claim, \
so it can be checked against the source data.

Question intent:
{analysis}

Business context (may be empty):
{rag_context}

Computed data:
{data_context}"""

_PROMPT = ChatPromptTemplate.from_messages([("system", SYSTEM_PROMPT), ("human", "{question}")])


def get_insight_agent_llm() -> StructuredInsightAgent:
    """Production factory: a real chat model constrained to InsightGeneration output."""
    return _PROMPT | get_chat_model().with_structured_output(InsightGeneration)


def generate_insight(
    question: str,
    analysis: str,
    rag_context: str,
    data_context: str,
    agent: StructuredInsightAgent,
) -> InsightGeneration:
    """Runs the Insight Agent. `agent` is injected so tests can supply a
    fake implementation without calling a real LLM provider."""
    return agent.invoke(
        {"question": question, "analysis": analysis, "rag_context": rag_context, "data_context": data_context}
    )
