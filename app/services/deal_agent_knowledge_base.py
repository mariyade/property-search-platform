from pathlib import Path

DOCS_DIR = Path("docs")
PERSIST_DIR = Path("chroma_db/deal_agent_docs_v1")
RETRIEVAL_K = 4

_retriever = None


def _section_documents(content: str, filename: str):
    from langchain_core.documents import Document

    chunks = []
    current = []
    for line in content.splitlines():
        if (line.startswith("## ") or line.startswith("### ")) and current:
            chunks.append("\n".join(current).strip())
            current = []
        current.append(line)
    if current:
        chunks.append("\n".join(current).strip())

    return [
        Document(
            page_content=chunk,
            metadata={"source": filename, "section": chunk.splitlines()[0]},
        )
        for chunk in chunks
        if chunk
    ]


def _load_documents():
    documents = []
    for path in sorted(DOCS_DIR.glob("*.md")):
        documents.extend(_section_documents(path.read_text(encoding="utf-8"), path.name))
    return documents


def _build_retriever(k: int = RETRIEVAL_K):
    from langchain_community.vectorstores import Chroma
    from langchain_openai import OpenAIEmbeddings

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    if PERSIST_DIR.exists():
        vectorstore = Chroma(persist_directory=str(PERSIST_DIR), embedding_function=embeddings)
        if vectorstore._collection.count() > 0:
            return vectorstore.as_retriever(search_kwargs={"k": k})

    documents = _load_documents()
    vectorstore = Chroma.from_documents(
        documents,
        embeddings,
        persist_directory=str(PERSIST_DIR),
    )
    return vectorstore.as_retriever(search_kwargs={"k": k})


def get_retriever(k: int = RETRIEVAL_K):
    global _retriever
    if _retriever is None:
        _retriever = _build_retriever(k=k)
    return _retriever


def retrieve(query: str, k: int = RETRIEVAL_K) -> list[str]:
    docs = get_retriever(k=k).invoke(query)
    return [doc.page_content for doc in docs]
