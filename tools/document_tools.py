from rag.retriever import retrieve_context


def search_company_knowledge(query, k=6):
    return retrieve_context(query, k)
