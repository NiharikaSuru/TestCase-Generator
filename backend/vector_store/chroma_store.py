import os
import uuid
from typing import List, Dict, Any


class ChromaMemoryStore:
    """Optional Chroma-backed memory store with graceful fallback."""

    def __init__(self) -> None:
        self.enabled = os.getenv("ENABLE_VECTOR_DB", "true").strip().lower() == "true"
        self._collection = None

        if not self.enabled:
            return

        try:
            import chromadb

            persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
            collection_name = os.getenv("CHROMA_COLLECTION", "unit_test_creator_memory")
            client = chromadb.PersistentClient(path=persist_dir)
            self._collection = client.get_or_create_collection(name=collection_name)
        except Exception:
            # Do not break existing functionality if Chroma setup fails.
            self.enabled = False
            self._collection = None

    def is_ready(self) -> bool:
        return self.enabled and self._collection is not None

    def store_run(
        self,
        code: str,
        language: str,
        analysis: str,
        final_tests: str,
    ) -> None:
        """Persist a generation run into Chroma for future retrieval."""
        if not self.is_ready():
            return

        try:
            doc = (
                f"Language: {language}\n"
                f"Code:\n{code}\n\n"
                f"Analysis:\n{analysis}\n\n"
                f"FinalTests:\n{final_tests}"
            )
            self._collection.add(
                ids=[str(uuid.uuid4())],
                documents=[doc],
                metadatas=[{"language": language}],
            )
        except Exception:
            # Keep app behavior unchanged if memory write fails.
            return

    def search_similar(self, code: str, language: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Retrieve similar historical runs by semantic similarity."""
        if not self.is_ready():
            return []

        try:
            results = self._collection.query(
                query_texts=[f"Language: {language}\nCode:\n{code}"],
                n_results=top_k,
                include=["documents", "metadatas", "distances"],
                where={"language": language},
            )
        except Exception:
            return []

        docs = (results.get("documents") or [[]])[0]
        metas = (results.get("metadatas") or [[]])[0]
        dists = (results.get("distances") or [[]])[0]

        matches: List[Dict[str, Any]] = []
        for idx, document in enumerate(docs):
            matches.append(
                {
                    "document": document,
                    "metadata": metas[idx] if idx < len(metas) else {},
                    "distance": dists[idx] if idx < len(dists) else None,
                }
            )
        return matches


def format_memory_context(matches: List[Dict[str, Any]], max_chars: int = 3000) -> str:
    """Compactly formats retrieved memory examples for prompt injection."""
    if not matches:
        return ""

    chunks: List[str] = []
    for i, item in enumerate(matches, start=1):
        doc = item.get("document", "")
        distance = item.get("distance")
        header = f"Example {i} (distance={distance}):"
        chunks.append(f"{header}\n{doc}")

    text = "\n\n".join(chunks)
    if len(text) > max_chars:
        return text[:max_chars]
    return text
