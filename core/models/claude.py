"""
Claude API Model Implementation
===============================
High-quality code generation using Anthropic's Claude models.

Features:
- Claude 3 Opus, Sonnet, Haiku support
- Claude 3.5 Sonnet support
- Streaming generation
- Token usage tracking
"""

import os
from collections.abc import AsyncGenerator
from typing import Any

import structlog

from .interface import GenerationConfig, ModelInterface

logger = structlog.get_logger()


class ClaudeModel(ModelInterface):
    """
    Claude API Model Implementation

    Supports Claude 3 Opus, Sonnet, Haiku, and Claude 3.5 Sonnet models.
    Best for complex reasoning, architecture design, and security analysis.
    """

    # Available models
    AVAILABLE_MODELS = {
        "claude-3-opus": "claude-3-opus-20240229",
        "claude-3-sonnet": "claude-3-sonnet-20240229",
        "claude-3-haiku": "claude-3-haiku-20240307",
        "claude-3.5-sonnet": "claude-3-5-sonnet-20241022",
        "claude-3.5-haiku": "claude-3-5-haiku-20241022",
    }

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "claude-3.5-sonnet",
        max_tokens: int = 4096,
    ):
        """
        Initialize Claude model.

        Args:
            api_key: Anthropic API key
            model: Model to use (claude-3-opus, claude-3-sonnet, claude-3.5-sonnet, etc.)
            max_tokens: Maximum tokens for generation
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.model_name = model
        self.model_id = self.AVAILABLE_MODELS.get(model, model)
        self.max_tokens = max_tokens

        if not self.api_key:
            raise ValueError(
                "Anthropic API key required. "
                "Set ANTHROPIC_API_KEY environment variable."
            )

        self.client = None
        self._loaded = False
        self._total_tokens_used = 0
        self._total_input_tokens = 0
        self._total_output_tokens = 0

    def load(self) -> None:
        """Initialize the Anthropic client."""
        if self._loaded:
            logger.warning("claude_already_loaded")
            return

        try:
            from anthropic import AsyncAnthropic

            self.client = AsyncAnthropic(api_key=self.api_key)
            self._loaded = True
            logger.info(
                "claude_loaded",
                model=self.model_id,
            )
        except ImportError:
            raise ImportError(
                "anthropic package not installed. Run: pip install anthropic>=0.25.0"
            )

    def unload(self) -> None:
        """Close the Anthropic client."""
        if self.client:
            self.client = None
        self._loaded = False
        logger.info("claude_unloaded")

    async def generate(
        self,
        messages: list[dict[str, str]],
        config: GenerationConfig | None = None,
    ) -> str:
        """Generate a response using Claude."""
        if not self._loaded or not self.client:
            raise RuntimeError("Model not loaded. Call load() first.")

        config = config or GenerationConfig()

        # Extract system message if present
        system_message = None
        chat_messages = []

        for msg in messages:
            if msg.get("role") == "system":
                system_message = msg.get("content", "")
            else:
                chat_messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", ""),
                })

        try:
            kwargs = {
                "model": self.model_id,
                "messages": chat_messages,
                "max_tokens": config.max_new_tokens or self.max_tokens,
                "temperature": config.temperature,
                "top_p": config.top_p,
            }

            if system_message:
                kwargs["system"] = system_message

            response = await self.client.messages.create(**kwargs)

            # Track token usage
            if response.usage:
                self._total_input_tokens += response.usage.input_tokens
                self._total_output_tokens += response.usage.output_tokens
                self._total_tokens_used += (
                    response.usage.input_tokens + response.usage.output_tokens
                )
                logger.debug(
                    "claude_tokens",
                    input=response.usage.input_tokens,
                    output=response.usage.output_tokens,
                )

            # Extract text from response
            if response.content and len(response.content) > 0:
                return response.content[0].text
            return ""

        except Exception as e:
            logger.error("claude_error", error=str(e))
            raise

    async def generate_stream(
        self,
        messages: list[dict[str, str]],
        config: GenerationConfig | None = None,
    ) -> AsyncGenerator[str, None]:
        """Stream generated tokens from Claude."""
        if not self._loaded or not self.client:
            raise RuntimeError("Model not loaded. Call load() first.")

        config = config or GenerationConfig()

        # Extract system message if present
        system_message = None
        chat_messages = []

        for msg in messages:
            if msg.get("role") == "system":
                system_message = msg.get("content", "")
            else:
                chat_messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", ""),
                })

        try:
            kwargs = {
                "model": self.model_id,
                "messages": chat_messages,
                "max_tokens": config.max_new_tokens or self.max_tokens,
                "temperature": config.temperature,
                "top_p": config.top_p,
            }

            if system_message:
                kwargs["system"] = system_message

            async with self.client.messages.stream(**kwargs) as stream:
                async for text in stream.text_stream:
                    yield text

                # Track final token usage
                final_message = await stream.get_final_message()
                if final_message.usage:
                    self._total_input_tokens += final_message.usage.input_tokens
                    self._total_output_tokens += final_message.usage.output_tokens
                    self._total_tokens_used += (
                        final_message.usage.input_tokens + final_message.usage.output_tokens
                    )

        except Exception as e:
            logger.error("claude_stream_error", error=str(e))
            raise

    def load_lora(self, adapter_path: str, adapter_name: str = "default") -> None:
        """LoRA not supported for Claude API."""
        logger.warning("lora_not_supported", provider="claude")

    def unload_lora(self, adapter_name: str = "default") -> None:
        """LoRA not supported for Claude API."""
        pass

    def set_active_lora(self, adapter_name: str) -> None:
        """LoRA not supported for Claude API."""
        pass

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def model_info(self) -> dict[str, Any]:
        return {
            "provider": "claude",
            "model": self.model_id,
            "model_name": self.model_name,
            "loaded": self._loaded,
            "total_tokens_used": self._total_tokens_used,
            "total_input_tokens": self._total_input_tokens,
            "total_output_tokens": self._total_output_tokens,
        }
