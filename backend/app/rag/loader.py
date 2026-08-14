"""Loads business documents (Markdown + YAML front-matter) for the RAG pipeline.

Documents live under data/business_docs/<category>/*.md. The category is
taken from the immediate parent directory name, and the title from the
front-matter (falling back to the filename).
"""
from dataclasses import dataclass
from pathlib import Path

import frontmatter

DEFAULT_DOCS_DIR = Path(__file__).resolve().parents[3] / "data" / "business_docs"


@dataclass
class BusinessDocument:
    title: str
    category: str
    content: str
    source_path: str


def load_documents(docs_dir: Path = DEFAULT_DOCS_DIR) -> list[BusinessDocument]:
    if not docs_dir.exists():
        raise FileNotFoundError(f"Business documents directory not found: {docs_dir}")

    documents: list[BusinessDocument] = []
    for md_path in sorted(docs_dir.rglob("*.md")):
        post = frontmatter.load(md_path)
        title = post.metadata.get("title", md_path.stem.replace("_", " ").title())
        category = md_path.parent.name
        documents.append(
            BusinessDocument(
                title=title,
                category=category,
                content=post.content.strip(),
                source_path=str(md_path.relative_to(docs_dir.parent.parent)),
            )
        )
    return documents
