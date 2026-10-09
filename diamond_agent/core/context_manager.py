"""
Context Management, Token Budgeting, and Long-Context Compactor.
"""

from typing import Any, Dict, List
import logging

logger = logging.getLogger("diamond_agent.context")


class ContextCompactor:
    """Manages context windows, token limits, and compaction for Claude 3.5 Sonnet (200k context)."""

    def __init__(self, max_token_budget: int = 180000, summary_threshold: int = 50000):
        self.max_token_budget = max_token_budget
        self.summary_threshold = summary_threshold
        self.memory_store: List[Dict[str, Any]] = []

    def estimate_tokens(self, text: str) -> int:
        """Rough token estimation (approx 4 chars per token)."""
        return len(text) // 4

    def add_memory(self, role: str, content: str, tags: List[str] = None):
        """Append message to working memory."""
        self.memory_store.append({
            "role": role,
            "content": content,
            "tokens": self.estimate_tokens(content),
            "tags": tags or [],
        })

    def get_token_usage(self) -> int:
        return sum(item["tokens"] for item in self.memory_store)

    def compact_history(self) -> List[Dict[str, str]]:
        """Compact memory if exceeding threshold, preserving recent context and system anchors."""
        current_tokens = self.get_token_usage()
        if current_tokens < self.summary_threshold or len(self.memory_store) <= 4:
            return [{"role": m["role"], "content": m["content"]} for m in self.memory_store]

        logger.info(f"Compacting context: current tokens {current_tokens} > threshold {self.summary_threshold}")
        # Keep first 2 (system anchors) and last 4 (recent turns)
        anchors = self.memory_store[:2]
        recent = self.memory_store[-4:]
        middle = self.memory_store[2:-4]

        summary_content = f"[Compacted Summary of {len(middle)} intermediate agent interactions to conserve token budget]"
        compacted = [
            {"role": m["role"], "content": m["content"]} for m in anchors
        ] + [
            {"role": "assistant", "content": summary_content}
        ] + [
            {"role": m["role"], "content": m["content"]} for m in recent
        ]
        return compacted
