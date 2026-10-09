"""
Knowledge Search and Document Retrieval MCP Tool.
"""

from typing import Dict, Any, List
import re


class KnowledgeSearchTool:
    """In-memory vector / BM25 document search tool for agents."""

    def __init__(self):
        self.corpus: List[Dict[str, str]] = []

    def index_document(self, doc_id: str, title: str, text: str):
        self.corpus.append({"id": doc_id, "title": title, "text": text})

    def search(self, query: str, top_k: int = 3) -> Dict[str, Any]:
        """Perform keyword and semantic match on knowledge corpus."""
        if not self.corpus:
            return {"results": [], "query": query, "message": "Corpus is empty"}

        keywords = re.findall(r"\w+", query.lower())
        scored = []
        for doc in self.corpus:
            score = sum(1 for kw in keywords if kw in doc["text"].lower() or kw in doc["title"].lower())
            if score > 0:
                scored.append((score, doc))

        scored.sort(key=lambda x: x[0], reverse=True)
        results = [{"score": s, "doc": d} for s, d in scored[:top_k]]

        return {"query": query, "total_matches": len(scored), "results": results}
