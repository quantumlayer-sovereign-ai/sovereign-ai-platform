"""
Semantic Router and Triple Hybrid Model
=======================================
Production-grade semantic routing across three model tiers:
- Local (Qwen 14B): Simple utilities, scripts, formatting
- Azure (GPT-4.1): Production APIs, databases, enterprise
- Claude (Claude 3 Sonnet): Complex reasoning, architecture, security

Features:
- Embedding-based semantic routing
- Pre-computed reference examples
- Configurable thresholds
- Fallback chain
- Routing history tracking
"""

import json
import os
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import numpy as np
import structlog

from core.rag.embeddings import EmbeddingModel

from .azure_openai import AzureOpenAIModel
from .claude import ClaudeModel
from .interface import GenerationConfig, ModelInterface
from .qwen import QwenModel

logger = structlog.get_logger()


class RouteTarget(Enum):
    """Target model tier for routing."""
    LOCAL = "local"
    AZURE = "azure"
    CLAUDE = "claude"


class RoutingMode(Enum):
    """Routing decision mode."""
    SEMANTIC = "semantic"  # Embedding similarity (default)
    KEYWORD = "keyword"    # Fallback keyword matching
    MANUAL = "manual"      # Always use configured default


@dataclass
class RouteDecision:
    """Result of a routing decision."""
    target: RouteTarget
    confidence: float
    mode: RoutingMode
    matched_example: str | None = None
    reason: str = ""
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class RoutingExample:
    """Reference example for routing."""
    text: str
    target: RouteTarget
    embedding: list[float] | None = None


class SemanticRouter:
    """
    Semantic router using embedding similarity.

    Routes tasks to appropriate model tier based on similarity
    to pre-defined reference examples.
    """

    def __init__(
        self,
        embedding_model: EmbeddingModel | None = None,
        examples_path: str | None = None,
        local_threshold: float = 0.75,
        azure_threshold: float = 0.70,
        claude_threshold: float = 0.70,
        default_target: RouteTarget = RouteTarget.LOCAL,
        mode: RoutingMode = RoutingMode.SEMANTIC,
    ):
        """
        Initialize semantic router.

        Args:
            embedding_model: Embedding model for semantic similarity
            examples_path: Path to routing examples JSON
            local_threshold: Similarity threshold for local routing
            azure_threshold: Similarity threshold for Azure routing
            claude_threshold: Similarity threshold for Claude routing
            default_target: Default target when no threshold met
            mode: Routing mode (semantic, keyword, manual)
        """
        self.embedding_model = embedding_model or EmbeddingModel()
        self.local_threshold = local_threshold
        self.azure_threshold = azure_threshold
        self.claude_threshold = claude_threshold
        self.default_target = default_target
        self.mode = mode

        # Load examples
        self.examples: dict[RouteTarget, list[RoutingExample]] = {
            RouteTarget.LOCAL: [],
            RouteTarget.AZURE: [],
            RouteTarget.CLAUDE: [],
        }

        # Keyword fallbacks
        self.keywords: dict[RouteTarget, list[str]] = {
            RouteTarget.LOCAL: [
                "simple", "utility", "format", "parse", "convert", "basic",
                "script", "helper", "validator", "mask", "csv", "json",
            ],
            RouteTarget.AZURE: [
                "production", "enterprise", "database", "api", "rest",
                "authentication", "jwt", "oauth", "microservice", "pci",
                "compliance", "transaction", "payment", "reconciliation",
            ],
            RouteTarget.CLAUDE: [
                "architecture", "design", "security", "fraud", "ml",
                "machine learning", "complex", "analysis", "review",
                "multi-tenant", "disaster recovery", "trade-off",
            ],
        }

        # Load examples if path provided
        if examples_path:
            self._load_examples(examples_path)
        else:
            # Try default path
            default_path = Path(__file__).parent / "routing_examples.json"
            if default_path.exists():
                self._load_examples(str(default_path))

        self._embeddings_computed = False

    def _load_examples(self, path: str) -> None:
        """Load routing examples from JSON file."""
        try:
            with open(path) as f:
                data = json.load(f)

            for target_name, examples in data.items():
                target = RouteTarget(target_name)
                for text in examples:
                    self.examples[target].append(
                        RoutingExample(text=text, target=target)
                    )

            logger.info(
                "routing_examples_loaded",
                path=path,
                local=len(self.examples[RouteTarget.LOCAL]),
                azure=len(self.examples[RouteTarget.AZURE]),
                claude=len(self.examples[RouteTarget.CLAUDE]),
            )
        except Exception as e:
            logger.warning("routing_examples_load_failed", error=str(e))

    def _compute_embeddings(self) -> None:
        """Pre-compute embeddings for all examples."""
        if self._embeddings_computed:
            return

        if not self.embedding_model.is_loaded:
            self.embedding_model.load()

        for target, examples in self.examples.items():
            texts = [ex.text for ex in examples]
            if texts:
                embeddings = self.embedding_model.embed(texts)
                for ex, emb in zip(examples, embeddings):
                    ex.embedding = emb

        self._embeddings_computed = True
        logger.info("routing_embeddings_computed")

    def _keyword_route(self, task: str) -> RouteDecision:
        """Route using keyword matching."""
        task_lower = task.lower()

        # Check Claude keywords first (highest priority)
        for kw in self.keywords[RouteTarget.CLAUDE]:
            if kw in task_lower:
                return RouteDecision(
                    target=RouteTarget.CLAUDE,
                    confidence=0.6,
                    mode=RoutingMode.KEYWORD,
                    reason=f"Matched keyword: {kw}",
                )

        # Check Azure keywords
        for kw in self.keywords[RouteTarget.AZURE]:
            if kw in task_lower:
                return RouteDecision(
                    target=RouteTarget.AZURE,
                    confidence=0.6,
                    mode=RoutingMode.KEYWORD,
                    reason=f"Matched keyword: {kw}",
                )

        # Check Local keywords
        for kw in self.keywords[RouteTarget.LOCAL]:
            if kw in task_lower:
                return RouteDecision(
                    target=RouteTarget.LOCAL,
                    confidence=0.6,
                    mode=RoutingMode.KEYWORD,
                    reason=f"Matched keyword: {kw}",
                )

        # Default
        return RouteDecision(
            target=self.default_target,
            confidence=0.5,
            mode=RoutingMode.KEYWORD,
            reason="No keyword match, using default",
        )

    def _semantic_route(self, task: str) -> RouteDecision:
        """Route using semantic similarity."""
        self._compute_embeddings()

        if not self.embedding_model.is_loaded:
            self.embedding_model.load()

        task_embedding = self.embedding_model.embed_query(task)

        best_match: RouteDecision | None = None
        best_similarity = -1.0

        thresholds = {
            RouteTarget.LOCAL: self.local_threshold,
            RouteTarget.AZURE: self.azure_threshold,
            RouteTarget.CLAUDE: self.claude_threshold,
        }

        for target, examples in self.examples.items():
            for example in examples:
                if example.embedding is None:
                    continue

                similarity = self._cosine_similarity(task_embedding, example.embedding)

                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = RouteDecision(
                        target=target,
                        confidence=similarity,
                        mode=RoutingMode.SEMANTIC,
                        matched_example=example.text,
                        reason=f"Best semantic match (similarity: {similarity:.3f})",
                    )

        # Check if best match meets threshold
        if best_match and best_similarity >= thresholds.get(best_match.target, 0.7):
            return best_match

        # Fallback to keyword routing
        logger.debug(
            "semantic_below_threshold",
            best_similarity=best_similarity,
            falling_back_to="keyword",
        )
        return self._keyword_route(task)

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        a_arr = np.array(a)
        b_arr = np.array(b)
        return float(np.dot(a_arr, b_arr) / (np.linalg.norm(a_arr) * np.linalg.norm(b_arr)))

    def route(self, task: str) -> RouteDecision:
        """
        Route a task to the appropriate model tier.

        Args:
            task: Task description

        Returns:
            RouteDecision with target and confidence
        """
        if self.mode == RoutingMode.MANUAL:
            return RouteDecision(
                target=self.default_target,
                confidence=1.0,
                mode=RoutingMode.MANUAL,
                reason="Manual routing mode",
            )

        if self.mode == RoutingMode.KEYWORD:
            return self._keyword_route(task)

        # Semantic routing (default)
        return self._semantic_route(task)

    def add_example(self, text: str, target: RouteTarget) -> None:
        """Add a new routing example."""
        example = RoutingExample(text=text, target=target)

        # Compute embedding if model is ready
        if self._embeddings_computed and self.embedding_model.is_loaded:
            example.embedding = self.embedding_model.embed_query(text)

        self.examples[target].append(example)

    def get_stats(self) -> dict[str, Any]:
        """Get router statistics."""
        return {
            "mode": self.mode.value,
            "thresholds": {
                "local": self.local_threshold,
                "azure": self.azure_threshold,
                "claude": self.claude_threshold,
            },
            "examples": {
                "local": len(self.examples[RouteTarget.LOCAL]),
                "azure": len(self.examples[RouteTarget.AZURE]),
                "claude": len(self.examples[RouteTarget.CLAUDE]),
            },
            "embeddings_computed": self._embeddings_computed,
            "default_target": self.default_target.value,
        }


class TripleHybridModel(ModelInterface):
    """
    Triple hybrid model using semantic routing across three tiers.

    - Local (Qwen 14B): Simple utilities, scripts, formatting
    - Azure (GPT-4.1): Production APIs, databases, enterprise
    - Claude (Claude 3 Sonnet): Complex reasoning, architecture, security
    """

    def __init__(
        self,
        local_model: QwenModel,
        azure_model: AzureOpenAIModel | None = None,
        claude_model: ClaudeModel | None = None,
        router: SemanticRouter | None = None,
    ):
        """
        Initialize triple hybrid model.

        Args:
            local_model: Local model (e.g., Qwen 14B)
            azure_model: Azure OpenAI model (optional)
            claude_model: Claude model (optional)
            router: Semantic router (created if not provided)
        """
        self.local = local_model
        self.azure = azure_model
        self.claude = claude_model
        self.router = router or SemanticRouter()
        self._loaded = False

        # Routing history for stats
        self._routing_history: list[dict[str, Any]] = []

    def load(self) -> None:
        """Load all available models."""
        self.local.load()

        if self.azure:
            self.azure.load()

        if self.claude:
            self.claude.load()

        self._loaded = True
        logger.info(
            "triple_hybrid_loaded",
            has_azure=self.azure is not None,
            has_claude=self.claude is not None,
        )

    def unload(self) -> None:
        """Unload all models."""
        self.local.unload()

        if self.azure:
            self.azure.unload()

        if self.claude:
            self.claude.unload()

        self._loaded = False
        logger.info("triple_hybrid_unloaded")

    def _get_task_from_messages(self, messages: list[dict[str, str]]) -> str:
        """Extract task text from messages."""
        user_messages = [m for m in messages if m.get("role") == "user"]
        if user_messages:
            return user_messages[-1].get("content", "")
        return ""

    def _select_model(
        self,
        messages: list[dict[str, str]],
        force_local: bool = False,
        force_azure: bool = False,
        force_claude: bool = False,
    ) -> tuple[ModelInterface, RouteDecision]:
        """Select the appropriate model based on routing."""
        # Handle forced routing
        if force_local:
            decision = RouteDecision(
                target=RouteTarget.LOCAL,
                confidence=1.0,
                mode=RoutingMode.MANUAL,
                reason="Forced local",
            )
            return self.local, decision

        if force_azure and self.azure:
            decision = RouteDecision(
                target=RouteTarget.AZURE,
                confidence=1.0,
                mode=RoutingMode.MANUAL,
                reason="Forced Azure",
            )
            return self.azure, decision

        if force_claude and self.claude:
            decision = RouteDecision(
                target=RouteTarget.CLAUDE,
                confidence=1.0,
                mode=RoutingMode.MANUAL,
                reason="Forced Claude",
            )
            return self.claude, decision

        # Semantic routing
        task = self._get_task_from_messages(messages)
        decision = self.router.route(task)

        # Select model based on decision (with fallbacks)
        if decision.target == RouteTarget.CLAUDE and self.claude:
            return self.claude, decision
        elif decision.target == RouteTarget.AZURE and self.azure:
            return self.azure, decision
        elif decision.target == RouteTarget.CLAUDE and self.azure:
            # Fallback: Claude not available, use Azure
            decision.reason += " (fallback: Claude unavailable)"
            return self.azure, decision
        else:
            # Fallback to local
            if decision.target != RouteTarget.LOCAL:
                decision.reason += f" (fallback: {decision.target.value} unavailable)"
            return self.local, decision

    def _record_routing(self, decision: RouteDecision, task: str) -> None:
        """Record routing decision for stats."""
        self._routing_history.append({
            "timestamp": decision.timestamp.isoformat(),
            "target": decision.target.value,
            "confidence": decision.confidence,
            "mode": decision.mode.value,
            "task_preview": task[:100] + "..." if len(task) > 100 else task,
            "reason": decision.reason,
        })

        # Keep only last 1000 entries
        if len(self._routing_history) > 1000:
            self._routing_history = self._routing_history[-1000:]

    def route(self, task: str) -> RouteDecision:
        """
        Get routing decision for a task without executing.

        Args:
            task: Task description

        Returns:
            RouteDecision with target and confidence
        """
        return self.router.route(task)

    async def generate(
        self,
        messages: list[dict[str, str]],
        config: GenerationConfig | None = None,
        force_local: bool = False,
        force_azure: bool = False,
        force_claude: bool = False,
    ) -> str:
        """Generate using semantically selected model."""
        if not self._loaded:
            raise RuntimeError("Model not loaded. Call load() first.")

        model, decision = self._select_model(
            messages, force_local, force_azure, force_claude
        )

        task = self._get_task_from_messages(messages)
        self._record_routing(decision, task)

        logger.info(
            f"using_{decision.target.value}_model",
            confidence=decision.confidence,
            mode=decision.mode.value,
            reason=decision.reason,
        )

        return await model.generate(messages, config)

    async def generate_stream(
        self,
        messages: list[dict[str, str]],
        config: GenerationConfig | None = None,
        force_local: bool = False,
        force_azure: bool = False,
        force_claude: bool = False,
    ) -> AsyncGenerator[str, None]:
        """Stream using semantically selected model."""
        if not self._loaded:
            raise RuntimeError("Model not loaded. Call load() first.")

        model, decision = self._select_model(
            messages, force_local, force_azure, force_claude
        )

        task = self._get_task_from_messages(messages)
        self._record_routing(decision, task)

        logger.info(
            f"streaming_{decision.target.value}_model",
            confidence=decision.confidence,
            mode=decision.mode.value,
        )

        async for token in model.generate_stream(messages, config):
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
            "type": "triple_hybrid",
            "local": self.local.model_info,
            "azure": self.azure.model_info if self.azure else None,
            "claude": self.claude.model_info if self.claude else None,
            "router": self.router.get_stats(),
        }

    def get_routing_stats(self) -> dict[str, Any]:
        """Get routing statistics."""
        if not self._routing_history:
            return {
                "total_requests": 0,
                "by_target": {},
                "by_mode": {},
            }

        by_target = {}
        by_mode = {}
        total_confidence = 0.0

        for entry in self._routing_history:
            target = entry["target"]
            mode = entry["mode"]

            by_target[target] = by_target.get(target, 0) + 1
            by_mode[mode] = by_mode.get(mode, 0) + 1
            total_confidence += entry["confidence"]

        return {
            "total_requests": len(self._routing_history),
            "by_target": by_target,
            "by_mode": by_mode,
            "average_confidence": total_confidence / len(self._routing_history),
            "recent_routes": self._routing_history[-10:],
        }
