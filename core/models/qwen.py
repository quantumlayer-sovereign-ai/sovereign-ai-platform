"""
Qwen Model Implementation - Qwen2.5-Coder integration

Features:
- 4-bit quantization for 16GB VRAM
- LoRA adapter support
- Streaming generation
- Code-optimized generation
"""

import torch
from typing import List, Dict, Any, Optional, AsyncGenerator
import asyncio
import structlog

from .interface import ModelInterface, GenerationConfig

logger = structlog.get_logger()


class QwenModel(ModelInterface):
    """
    Qwen2.5-Coder Model Implementation

    Optimized for coding tasks with 4-bit quantization
    """

    # Available model sizes
    MODELS = {
        "1.5b": "Qwen/Qwen2.5-Coder-1.5B-Instruct",
        "3b": "Qwen/Qwen2.5-Coder-3B-Instruct",
        "7b": "Qwen/Qwen2.5-Coder-7B-Instruct",
        "14b": "Qwen/Qwen2.5-Coder-14B-Instruct",
        "32b": "Qwen/Qwen2.5-Coder-32B-Instruct",
    }

    def __init__(
        self,
        model_size: str = "7b",
        quantize: bool = True,
        device: str = "cuda"
    ):
        """
        Initialize Qwen model

        Args:
            model_size: Model size (1.5b, 3b, 7b, 14b, 32b)
            quantize: Whether to use 4-bit quantization
            device: Device to load model on
        """
        self.model_size = model_size
        self.model_id = self.MODELS.get(model_size)
        if not self.model_id:
            raise ValueError(f"Unknown model size: {model_size}. Available: {list(self.MODELS.keys())}")

        self.quantize = quantize
        self.device = device

        self.model = None
        self.tokenizer = None
        self.lora_adapters: Dict[str, str] = {}
        self.active_lora: Optional[str] = None

        self._loaded = False

    def load(self) -> None:
        """Load the model with optional quantization"""
        if self._loaded:
            logger.warning("model_already_loaded", model=self.model_id)
            return

        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

        logger.info("loading_model", model=self.model_id, quantize=self.quantize)

        # Quantization config for 4-bit
        bnb_config = None
        if self.quantize:
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.bfloat16,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_use_double_quant=True,
            )

        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_id,
            trust_remote_code=True
        )

        # Load model
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_id,
            quantization_config=bnb_config,
            device_map="auto" if self.device == "cuda" else None,
            trust_remote_code=True,
            torch_dtype=torch.bfloat16 if not self.quantize else None,
        )

        self._loaded = True
        vram = torch.cuda.memory_allocated() / 1024**3 if torch.cuda.is_available() else 0
        logger.info("model_loaded", model=self.model_id, vram_gb=f"{vram:.2f}")

    def unload(self) -> None:
        """Unload model from memory"""
        if self.model:
            del self.model
            self.model = None

        if self.tokenizer:
            del self.tokenizer
            self.tokenizer = None

        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        self._loaded = False
        logger.info("model_unloaded", model=self.model_id)

    async def generate(
        self,
        messages: List[Dict[str, str]],
        config: Optional[GenerationConfig] = None
    ) -> str:
        """Generate response from messages"""
        if not self._loaded:
            raise RuntimeError("Model not loaded. Call load() first.")

        config = config or GenerationConfig()

        # Apply chat template
        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )

        # Tokenize
        inputs = self.tokenizer(text, return_tensors="pt").to(self.model.device)

        # Generate
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=config.max_new_tokens,
                temperature=config.temperature,
                top_p=config.top_p,
                top_k=config.top_k,
                do_sample=config.do_sample,
                repetition_penalty=config.repetition_penalty,
                pad_token_id=self.tokenizer.eos_token_id,
            )

        # Decode only the new tokens
        response = self.tokenizer.decode(
            outputs[0][inputs["input_ids"].shape[-1]:],
            skip_special_tokens=True
        )

        return response

    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        config: Optional[GenerationConfig] = None
    ) -> AsyncGenerator[str, None]:
        """Stream generated tokens"""
        if not self._loaded:
            raise RuntimeError("Model not loaded. Call load() first.")

        from transformers import TextIteratorStreamer
        from threading import Thread

        config = config or GenerationConfig()

        # Apply chat template
        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )

        inputs = self.tokenizer(text, return_tensors="pt").to(self.model.device)

        # Set up streamer
        streamer = TextIteratorStreamer(
            self.tokenizer,
            skip_prompt=True,
            skip_special_tokens=True
        )

        # Generate in a thread
        generation_kwargs = dict(
            **inputs,
            streamer=streamer,
            max_new_tokens=config.max_new_tokens,
            temperature=config.temperature,
            top_p=config.top_p,
            do_sample=config.do_sample,
            pad_token_id=self.tokenizer.eos_token_id,
        )

        thread = Thread(target=self.model.generate, kwargs=generation_kwargs)
        thread.start()

        # Yield tokens as they're generated
        for token in streamer:
            yield token
            await asyncio.sleep(0)  # Allow other async tasks to run

        thread.join()

    def load_lora(self, adapter_path: str, adapter_name: str = "default") -> None:
        """Load a LoRA adapter"""
        if not self._loaded:
            raise RuntimeError("Model not loaded. Call load() first.")

        from peft import PeftModel

        logger.info("loading_lora", adapter=adapter_name, path=adapter_path)

        if not hasattr(self, '_base_model'):
            self._base_model = self.model

        self.model = PeftModel.from_pretrained(
            self._base_model,
            adapter_path,
            adapter_name=adapter_name
        )

        self.lora_adapters[adapter_name] = adapter_path
        self.active_lora = adapter_name

        logger.info("lora_loaded", adapter=adapter_name)

    def unload_lora(self, adapter_name: str = "default") -> None:
        """Unload a LoRA adapter"""
        if adapter_name in self.lora_adapters:
            # Merge and unload or just restore base model
            if hasattr(self, '_base_model'):
                self.model = self._base_model

            del self.lora_adapters[adapter_name]
            if self.active_lora == adapter_name:
                self.active_lora = None

            logger.info("lora_unloaded", adapter=adapter_name)

    def set_active_lora(self, adapter_name: str) -> None:
        """Set the active LoRA adapter"""
        if adapter_name not in self.lora_adapters:
            raise ValueError(f"LoRA adapter not found: {adapter_name}")

        if hasattr(self.model, 'set_adapter'):
            self.model.set_adapter(adapter_name)
            self.active_lora = adapter_name
            logger.info("lora_activated", adapter=adapter_name)

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def model_info(self) -> Dict[str, Any]:
        info = {
            "model_id": self.model_id,
            "model_size": self.model_size,
            "quantized": self.quantize,
            "loaded": self._loaded,
            "lora_adapters": list(self.lora_adapters.keys()),
            "active_lora": self.active_lora,
        }

        if self._loaded and torch.cuda.is_available():
            info["vram_gb"] = torch.cuda.memory_allocated() / 1024**3

        return info
