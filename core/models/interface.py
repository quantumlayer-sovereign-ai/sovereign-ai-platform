"""
Model Interface - Abstract interface for LLM models

Supports:
- Multiple model backends (Qwen, Llama, etc.)
- LoRA adapter hot-swapping
- Streaming generation
- Async generation
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import Any


@dataclass
class GenerationConfig:
    """Configuration for text generation"""
    max_new_tokens: int = 2048
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 50
    do_sample: bool = True
    repetition_penalty: float = 1.1
    stop_sequences: list[str] = None

    def __post_init__(self):
        if self.stop_sequences is None:
            self.stop_sequences = []


class ModelInterface(ABC):
    """Abstract interface for LLM models"""

    @abstractmethod
    def load(self) -> None:
        """Load the model into memory"""
        pass

    @abstractmethod
    def unload(self) -> None:
        """Unload the model from memory"""
        pass

    @abstractmethod
    async def generate(
        self,
        messages: list[dict[str, str]],
        config: GenerationConfig | None = None
    ) -> str:
        """
        Generate a response from messages

        Args:
            messages: List of message dicts with 'role' and 'content'
            config: Generation configuration

        Returns:
            Generated text response
        """
        pass

    @abstractmethod
    async def generate_stream(
        self,
        messages: list[dict[str, str]],
        config: GenerationConfig | None = None
    ) -> AsyncGenerator[str, None]:
        """
        Stream generated tokens

        Args:
            messages: List of message dicts
            config: Generation configuration

        Yields:
            Generated tokens one at a time
        """
        pass

    @abstractmethod
    def load_lora(self, adapter_path: str, adapter_name: str = "default") -> None:
        """
        Load a LoRA adapter

        Args:
            adapter_path: Path to LoRA adapter
            adapter_name: Name for the adapter
        """
        pass

    @abstractmethod
    def unload_lora(self, adapter_name: str = "default") -> None:
        """Unload a LoRA adapter"""
        pass

    @abstractmethod
    def set_active_lora(self, adapter_name: str) -> None:
        """Set the active LoRA adapter"""
        pass

    @property
    @abstractmethod
    def is_loaded(self) -> bool:
        """Check if model is loaded"""
        pass

    @property
    @abstractmethod
    def model_info(self) -> dict[str, Any]:
        """Get model information"""
        pass
