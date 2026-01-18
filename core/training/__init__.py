"""
LoRA Training Module for Sovereign AI Platform

Provides QLoRA fine-tuning infrastructure for specialized FinTech agent roles.

Components:
- config: Training and LoRA configurations
- data_pipeline: Knowledge-to-instruction conversion
- generators: Domain-specific training data generators
- trainer: QLoRA training logic
- adapter_manager: Adapter versioning and storage
- evaluator: Compliance benchmarks and evaluation

Usage:
    # Generate training data
    python -m core.training.data_pipeline --role fintech_coder

    # Train adapter
    python scripts/train_lora.py --role fintech_coder

    # Evaluate adapter
    python scripts/evaluate_adapters.py --role fintech_coder
"""

from .config import (
    LoRAConfig,
    TrainingConfig,
    get_role_lora_config,
    get_all_roles,
    ROLE_CONFIGS,
    DEFAULT_ADAPTERS_DIR,
    DEFAULT_TRAINING_DATA_DIR,
    DEFAULT_KNOWLEDGE_DIR,
)
from .data_pipeline import DataPipeline, create_train_test_split
from .trainer import RoleLoRATrainer, train_all_roles
from .adapter_manager import AdapterManager, AdapterInfo, get_manager
from .evaluator import AdapterEvaluator, EvaluationResult, ComplianceAuditor

__all__ = [
    # Config
    "LoRAConfig",
    "TrainingConfig",
    "get_role_lora_config",
    "get_all_roles",
    "ROLE_CONFIGS",
    "DEFAULT_ADAPTERS_DIR",
    "DEFAULT_TRAINING_DATA_DIR",
    "DEFAULT_KNOWLEDGE_DIR",
    # Data Pipeline
    "DataPipeline",
    "create_train_test_split",
    # Trainer
    "RoleLoRATrainer",
    "train_all_roles",
    # Adapter Manager
    "AdapterManager",
    "AdapterInfo",
    "get_manager",
    # Evaluator
    "AdapterEvaluator",
    "EvaluationResult",
    "ComplianceAuditor",
]
