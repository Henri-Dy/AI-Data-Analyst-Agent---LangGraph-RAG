from app.rag.loader import load_documents

EXPECTED_CATEGORIES = {
    "glossary", "kpi", "product", "financial", "sales", "regional", "policies"
}


def test_load_documents_covers_all_categories():
    documents = load_documents()
    assert len(documents) >= 14
    assert {doc.category for doc in documents} == EXPECTED_CATEGORIES


def test_load_documents_have_titles_and_content():
    documents = load_documents()
    for doc in documents:
        assert doc.title
        assert len(doc.content) > 50
        assert doc.source_path.startswith("data/business_docs/")
