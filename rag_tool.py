from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings


# --------------------------------------------------
# Load embeddings and vector store ONCE at startup
# These stay in memory for the full session.
# --------------------------------------------------

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

vector_store = Chroma(
    persist_directory="chroma_db",
    embedding_function=embeddings
)

# k=3 → retrieve top 3 candidates (we deduplicate below)
retriever = vector_store.as_retriever(
    search_kwargs={"k": 3}
)


# --------------------------------------------------
# get_product_context
#
# Returns the raw product text chunks relevant to
# the customer's question.
#
# Fixes applied:
# - Deduplication: removes identical chunks that
#   ChromaDB sometimes returns twice
# - k=3 then deduplicate → effectively gives 2 unique chunks
#
# We do NOT call the LLM here.
# The agent LLM in agent.py uses these chunks directly
# so only ONE LLM call per turn (faster).
# --------------------------------------------------

def get_product_context(question):
    """Retrieve relevant unique product chunks for a question."""

    documents = retriever.invoke(question)

    # Deduplicate — remove chunks with identical content
    seen = set()
    unique_docs = []
    for doc in documents:
        content = doc.page_content.strip()
        if content not in seen:
            seen.add(content)
            unique_docs.append(doc)

    context = "\n\n".join(
        doc.page_content for doc in unique_docs
    )

    return context