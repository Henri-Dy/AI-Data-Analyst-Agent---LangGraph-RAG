"""SQL Generator agent: turns a question + schema + business context into SQL."""
from typing import Protocol

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from app.core.llm import get_chat_model


class SQLGeneration(BaseModel):
    sql: str = Field(description="A single read-only PostgreSQL SELECT statement that answers the question.")
    reasoning: str = Field(description="One or two sentences explaining the query's logic.")


class StructuredSQLGenerator(Protocol):
    def invoke(self, prompt_input: dict) -> SQLGeneration: ...


SYSTEM_PROMPT = """You are the SQL Generator for an AI data analyst platform. \
Given a user's question, its extracted intent, the live PostgreSQL schema, and \
optional business context, write a single read-only PostgreSQL SELECT \
statement that answers the question.

Rules:
- Only SELECT statements. Never write DROP, DELETE, UPDATE, INSERT, ALTER, \
TRUNCATE, or CREATE.
- Only reference tables and columns that literally appear in the schema below.
- Write exactly one SQL statement (no semicolon-separated statements).
- Prefer explicit column lists and JOINs over SELECT *.

Schema:
{schema}

Business context (may be empty):
{rag_context}

Extracted intent:
{analysis}"""

_PROMPT = ChatPromptTemplate.from_messages([("system", SYSTEM_PROMPT), ("human", "{question}")])


def get_sql_generator_llm() -> StructuredSQLGenerator:
    """Production factory: a real chat model constrained to SQLGeneration output."""
    return _PROMPT | get_chat_model().with_structured_output(SQLGeneration)


def generate_sql(
    question: str,
    schema: str,
    analysis: str,
    rag_context: str,
    generator: StructuredSQLGenerator,
) -> SQLGeneration:
    """Runs the SQL Generator. `generator` is injected so tests can supply a
    fake implementation without calling a real LLM provider."""
    return generator.invoke(
        {"question": question, "schema": schema, "analysis": analysis, "rag_context": rag_context}
    )
