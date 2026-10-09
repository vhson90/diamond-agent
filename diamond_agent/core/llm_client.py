"""
Anthropic Claude API client with Prompt Caching, streaming, and token analytics.
"""

from typing import Any, AsyncGenerator, Dict, List, Optional
import os
import time
import logging

try:
    import anthropic
    from anthropic import AsyncAnthropic
except ImportError:
    anthropic = None
    AsyncAnthropic = None

logger = logging.getLogger("diamond_agent.llm")


class ClaudeClient:
    """Enterprise client for Anthropic Claude models with built-in prompt caching."""

    DEFAULT_MODEL = "claude-3-5-sonnet-20241022"
    FAST_MODEL = "claude-3-5-haiku-20241022"
    OPUS_MODEL = "claude-3-opus-20240229"

    def __init__(
        self,
        api_key: Optional[str] = None,
        default_model: str = DEFAULT_MODEL,
        max_retries: int = 3,
    ):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.default_model = default_model
        self.max_retries = max_retries

        if AsyncAnthropic and self.api_key:
            self._client = AsyncAnthropic(api_key=self.api_key, max_retries=self.max_retries)
        else:
            self._client = None
            logger.warning("Anthropic API key not provided or SDK not installed. Running in simulation mode.")

        self.usage_stats = {
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "cache_read_input_tokens": 0,
            "cache_creation_input_tokens": 0,
        }

    async def generate_response(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 4096,
        tools: Optional[List[Dict[str, Any]]] = None,
        enable_caching: bool = True,
    ) -> Dict[str, Any]:
        """Generate response with optional prompt caching and tool calling."""
        selected_model = model or self.default_model

        if not self._client:
            # Fallback mock for local development and testing
            return {
                "content": f"[Simulated Claude Response for {len(messages)} messages]",
                "role": "assistant",
                "model": selected_model,
                "usage": {"input_tokens": 120, "output_tokens": 80, "cached_tokens": 0},
                "tool_calls": [],
            }

        kwargs: Dict[str, Any] = {
            "model": selected_model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
        }

        if system_prompt:
            if enable_caching:
                # Add Anthropic prompt caching control block
                kwargs["system"] = [
                    {
                        "type": "text",
                        "text": system_prompt,
                        "cache_control": {"type": "ephemeral"},
                    }
                ]
            else:
                kwargs["system"] = system_prompt

        if tools:
            kwargs["tools"] = tools

        start_time = time.time()
        response = await self._client.messages.create(**kwargs)
        duration = time.time() - start_time

        # Update stats
        if hasattr(response, "usage") and response.usage:
            u = response.usage
            self.usage_stats["total_input_tokens"] += getattr(u, "input_tokens", 0)
            self.usage_stats["total_output_tokens"] += getattr(u, "output_tokens", 0)
            self.usage_stats["cache_read_input_tokens"] += getattr(u, "cache_read_input_tokens", 0)
            self.usage_stats["cache_creation_input_tokens"] += getattr(u, "cache_creation_input_tokens", 0)

        # Parse text content and tool use blocks
        text_parts = []
        tool_calls = []

        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                tool_calls.append({
                    "id": block.id,
                    "name": block.name,
                    "input": block.input,
                })

        return {
            "content": "\n".join(text_parts),
            "role": "assistant",
            "model": selected_model,
            "duration_sec": round(duration, 3),
            "usage": {
                "input_tokens": getattr(response.usage, "input_tokens", 0),
                "output_tokens": getattr(response.usage, "output_tokens", 0),
                "cache_read_input_tokens": getattr(response.usage, "cache_read_input_tokens", 0),
            },
            "tool_calls": tool_calls,
            "stop_reason": response.stop_reason,
        }

    async def stream_response(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """Stream response chunk by chunk."""
        if not self._client:
            yield "DiamondAgent simulated stream: Connecting to Claude 3.5 Sonnet..."
            yield " Complete."
            return

        selected_model = model or self.default_model
        async with self._client.messages.stream(
            model=selected_model,
            max_tokens=4096,
            system=system_prompt or "You are DiamondAgent, an advanced AI system.",
            messages=messages,
        ) as stream:
            async for text in stream.text_stream:
                yield text
