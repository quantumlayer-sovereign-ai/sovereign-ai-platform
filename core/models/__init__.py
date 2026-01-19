"""Model module - LLM loading and inference"""
from .interface import ModelInterface
from .qwen import QwenModel
from .azure_openai import AzureOpenAIModel, HybridModel
from .claude import ClaudeModel
from .router import SemanticRouter, TripleHybridModel, RouteTarget, RoutingMode, RouteDecision

__all__ = [
    "ModelInterface",
    "QwenModel",
    "AzureOpenAIModel",
    "HybridModel",
    "ClaudeModel",
    "SemanticRouter",
    "TripleHybridModel",
    "RouteTarget",
    "RoutingMode",
    "RouteDecision",
]
