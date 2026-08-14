"""SQL Fixer agent: repairs SQL that failed validation, given the specific errors."""
from langchain_core.prompts import ChatPromptTemplate

from app.agents.sql_generator import SQLGeneration, StructuredSQLGenerator
from app.core.llm import get_chat_model

SYSTEM_PROMPT = """You are the SQL Fixer for an AI data analyst platform. A \
previously generated PostgreSQL query failed validation. Given the original \
question, the live schema, the invalid SQL, and the specific validation \
errors, produce a corrected single read-only SELECT statement.

Rules:
- Only SELECT statements. Never write DROP, DELETE, UPDATE, INSERT, ALTER, \
TRUNCATE, or CREATE.
- Only reference tables and columns that literally appear in the schema below.
- Write exactly one SQL statement (no semicolon-separated statements).
- Fix every listed error; do not reintroduce them.

Schema:
{schema}

Invalid SQL:
{sql}

Validation errors:
{errors}"""

_PROMPT = ChatPromptTemplate.from_messages([("system", SYSTEM_PROMPT), ("human", "{question}")])


def get_sql_fixer_llm() -> StructuredSQLGenerator:
    """Production factory: a real chat model constrained to SQLGeneration output."""
    return _PROMPT | get_chat_model().with_structured_output(SQLGeneration)


def fix_sql(
    question: str,
    schema: str,
    sql: str,
    errors: str,
    fixer: StructuredSQLGenerator,
) -> SQLGeneration:
    """Runs the SQL Fixer. `fixer` is injected so tests can supply a fake
    implementation without calling a real LLM provider."""
    return fixer.invoke({"question": question, "schema": schema, "sql": sql, "errors": errors})
