import streamlit as st
from rag.retriever import retrieve_context


def render_evidence(query):
    st.markdown("### Evidence Explorer")
    if not query:
        st.info("Enter an evidence question to search the indexed knowledge base.")
        return
    context = retrieve_context(query, 6)
    st.code(context, language="text")
