"""Splits business documents into overlapping chunks for embedding."""
from dataclasses import dataclass

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.rag.loader import BusinessDocument


@dataclass
class DocumentChunk:
    title: str
    category: str
    content: str
    source_path: str
    chunk_index: int


def chunk_documents(
    documents: list[BusinessDocument], chunk_size: int = 800, chunk_overlap: int = 100
) -> list[DocumentChunk]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap, separators=["\n\n", "\n", ". ", " "]
    )

    chunks: list[DocumentChunk] = []
    for doc in documents:
        for i, text in enumerate(splitter.split_text(doc.content)):
            chunks.append(
                DocumentChunk(
                    title=doc.title,
                    category=doc.category,
                    content=text,
                    source_path=doc.source_path,
                    chunk_index=i,
                )
            )
    return chunks
