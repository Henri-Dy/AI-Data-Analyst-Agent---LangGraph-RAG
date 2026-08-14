from app.rag.chunking import chunk_documents
from app.rag.loader import load_documents


def test_chunking_respects_size_bound():
    documents = load_documents()
    chunks = chunk_documents(documents, chunk_size=800, chunk_overlap=100)

    assert len(chunks) >= len(documents)
    # A little slack over chunk_size is expected since the splitter avoids
    # cutting mid-sentence when possible.
    assert all(len(chunk.content) <= 900 for chunk in chunks)


def test_chunking_preserves_source_metadata():
    documents = load_documents()
    chunks = chunk_documents(documents)

    titles = {doc.title for doc in documents}
    chunk_titles = {chunk.title for chunk in chunks}
    assert chunk_titles == titles
    assert all(chunk.source_path for chunk in chunks)
