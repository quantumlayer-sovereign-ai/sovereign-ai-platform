"""
Azure OpenAI Model Implementation
=================================
High-quality code generation using Azure OpenAI GPT-4/GPT-5 models.

Features:
- GPT-4, GPT-4.1, GPT-5 support
- Streaming generation
- Automatic retry with exponential backoff
- Token usage tracking
"""

import os
from collections.abc import AsyncGenerator
from typing import Any

import structlog
from openai import AsyncAzureOpenAI

from .interface import GenerationConfig, ModelInterface

logger = structlog.get_logger()


class AzureOpenAIModel(ModelInterface):
    """
    Azure OpenAI Model Implementation

    Supports GPT-4, GPT-4.1, GPT-5, and other Azure OpenAI deployments.
    """

    # Available deployments (can be configured)
    DEFAULT_DEPLOYMENTS = {
        "gpt-4": "gpt-4",
        "gpt-4.1": "gpt-4.1",
        "gpt-4.1-mini": "gpt-4.1-mini",
        "gpt-5": "gpt-5",
        "o4-mini": "o4-mini",
    }

    def __init__(
        self,
        endpoint: str | None = None,
        api_key: str | None = None,
        deployment: str = "gpt-4.1",
        api_version: str = "2024-08-01-preview",
    ):
        """
        Initialize Azure OpenAI model.

        Args:
            endpoint: Azure OpenAI endpoint URL
            api_key: Azure OpenAI API key
            deployment: Deployment name to use
            api_version: API version
        """
        self.endpoint = endpoint or os.environ.get("AZURE_OPENAI_ENDPOINT")
        self.api_key = api_key or os.environ.get("AZURE_OPENAI_API_KEY")
        self.deployment = deployment
        self.api_version = api_version

        if not self.endpoint or not self.api_key:
            raise ValueError(
                "Azure OpenAI endpoint and API key required. "
                "Set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY environment variables."
            )

        self.client: AsyncAzureOpenAI | None = None
        self._loaded = False
        self._total_tokens_used = 0

    def load(self) -> None:
        """Initialize the Azure OpenAI client."""
        if self._loaded:
            logger.warning("azure_openai_already_loaded")
            return

        self.client = AsyncAzureOpenAI(
            azure_endpoint=self.endpoint,
            api_key=self.api_key,
            api_version=self.api_version,
        )

        self._loaded = True
        logger.info(
            "azure_openai_loaded",
            endpoint=self.endpoint,
            deployment=self.deployment,
        )

    def unload(self) -> None:
        """Close the Azure OpenAI client."""
        if self.client:
            self.client = None
        self._loaded = False
        logger.info("azure_openai_unloaded")

    async def generate(
        self,
        messages: list[dict[str, str]],
        config: GenerationConfig | None = None,
    ) -> str:
        """Generate a response using Azure OpenAI."""
        if not self._loaded or not self.client:
            raise RuntimeError("Model not loaded. Call load() first.")

        config = config or GenerationConfig()

        try:
            response = await self.client.chat.completions.create(
                model=self.deployment,
                messages=messages,
                max_tokens=config.max_new_tokens,
                temperature=config.temperature,
                top_p=config.top_p,
            )

            # Track token usage
            if response.usage:
                self._total_tokens_used += response.usage.total_tokens
                logger.debug(
                    "azure_openai_tokens",
                    prompt=response.usage.prompt_tokens,
                    completion=response.usage.completion_tokens,
                    total=response.usage.total_tokens,
                )

            return response.choices[0].message.content or ""

        except Exception as e:
            logger.error("azure_openai_error", error=str(e))
            raise

    async def generate_stream(
        self,
        messages: list[dict[str, str]],
        config: GenerationConfig | None = None,
    ) -> AsyncGenerator[str, None]:
        """Stream generated tokens from Azure OpenAI."""
        if not self._loaded or not self.client:
            raise RuntimeError("Model not loaded. Call load() first.")

        config = config or GenerationConfig()

        try:
            stream = await self.client.chat.completions.create(
                model=self.deployment,
                messages=messages,
                max_tokens=config.max_new_tokens,
                temperature=config.temperature,
                top_p=config.top_p,
                stream=True,
            )

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error("azure_openai_stream_error", error=str(e))
            raise

    def load_lora(self, adapter_path: str, adapter_name: str = "default") -> None:
        """LoRA not supported for Azure OpenAI."""
        logger.warning("lora_not_supported", provider="azure_openai")

    def unload_lora(self, adapter_name: str = "default") -> None:
        """LoRA not supported for Azure OpenAI."""
        pass

    def set_active_lora(self, adapter_name: str) -> None:
        """LoRA not supported for Azure OpenAI."""
        pass

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def model_info(self) -> dict[str, Any]:
        return {
            "provider": "azure_openai",
            "endpoint": self.endpoint,
            "deployment": self.deployment,
            "api_version": self.api_version,
            "loaded": self._loaded,
            "total_tokens_used": self._total_tokens_used,
        }


class HybridModel(ModelInterface):
    """
    Hybrid model that uses local model for simple tasks
    and Azure OpenAI for complex tasks.

    Decision criteria:
    - Task complexity (length, requirements)
    - Local model confidence
    - Explicit user preference
    """

    def __init__(
        self,
        local_model: ModelInterface,
        azure_model: AzureOpenAIModel,
        complexity_threshold: int = 500,  # chars in task
    ):
        """
        Initialize hybrid model.

        Args:
            local_model: Local model (e.g., Qwen 14B)
            azure_model: Azure OpenAI model
            complexity_threshold: Task length threshold for using Azure
        """
        self.local = local_model
        self.azure = azure_model
        self.complexity_threshold = complexity_threshold
        self._loaded = False

    def load(self) -> None:
        """Load both models."""
        self.local.load()
        self.azure.load()
        self._loaded = True
        logger.info("hybrid_model_loaded")

    def unload(self) -> None:
        """Unload both models."""
        self.local.unload()
        self.azure.unload()
        self._loaded = False
        logger.info("hybrid_model_unloaded")

    def _should_use_azure(self, messages: list[dict[str, str]]) -> bool:
        """Determine if Azure should be used based on task complexity."""
        # Get the user message (task)
        user_messages = [m for m in messages if m.get("role") == "user"]
        if not user_messages:
            return False

        task = user_messages[-1].get("content", "")

        # Use Azure for complex tasks
        if len(task) > self.complexity_threshold:
            return True

        # Use Azure for specific keywords indicating complexity
        complex_keywords = [
            "production", "enterprise", "complete", "full implementation",
            "database", "authentication", "security", "PCI", "compliance",
            "microservice", "distributed", "scalable",
        ]

        task_lower = task.lower()
        if any(kw in task_lower for kw in complex_keywords):
            return True

        return False

    async def generate(
        self,
        messages: list[dict[str, str]],
        config: GenerationConfig | None = None,
        force_azure: bool = False,
        force_local: bool = False,
    ) -> str:
        """Generate using appropriate model."""
        if not self._loaded:
            raise RuntimeError("Model not loaded. Call load() first.")

        if force_azure or (not force_local and self._should_use_azure(messages)):
            logger.info("using_azure_openai")
            return await self.azure.generate(messages, config)
        else:
            logger.info("using_local_model")
            return await self.local.generate(messages, config)

    async def generate_stream(
        self,
        messages: list[dict[str, str]],
        config: GenerationConfig | None = None,
        force_azure: bool = False,
        force_local: bool = False,
    ) -> AsyncGenerator[str, None]:
        """Stream using appropriate model."""
        if not self._loaded:
            raise RuntimeError("Model not loaded. Call load() first.")

        if force_azure or (not force_local and self._should_use_azure(messages)):
            logger.info("streaming_azure_openai")
            async for token in self.azure.generate_stream(messages, config):
                yield token
        else:
            logger.info("streaming_local_model")
            async for token in self.local.generate_stream(messages, config):
                yield token

    def load_lora(self, adapter_path: str, adapter_name: str = "default") -> None:
        """Load LoRA adapter on local model."""
        self.local.load_lora(adapter_path, adapter_name)

    def unload_lora(self, adapter_name: str = "default") -> None:
        """Unload LoRA adapter from local model."""
        self.local.unload_lora(adapter_name)

    def set_active_lora(self, adapter_name: str) -> None:
        """Set active LoRA adapter on local model."""
        self.local.set_active_lora(adapter_name)

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def model_info(self) -> dict[str, Any]:
        return {
            "type": "hybrid",
            "local": self.local.model_info,
            "azure": self.azure.model_info,
            "complexity_threshold": self.complexity_threshold,
        }
