"""
Training Configuration for LoRA Fine-tuning

Defines LoRA configurations and training arguments for each FinTech role.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar


@dataclass
class LoRAConfig:
    """LoRA adapter configuration"""

    r: int = 16  # LoRA rank
    lora_alpha: int = 32  # Scaling factor
    target_modules: list[str] = field(default_factory=lambda: [
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj"
    ])
    lora_dropout: float = 0.05
    bias: str = "none"
    task_type: str = "CAUSAL_LM"

    def to_peft_config(self):
        """Convert to PEFT LoraConfig"""
        from peft import LoraConfig as PeftLoraConfig, TaskType

        return PeftLoraConfig(
            r=self.r,
            lora_alpha=self.lora_alpha,
            target_modules=self.target_modules,
            lora_dropout=self.lora_dropout,
            bias=self.bias,
            task_type=TaskType.CAUSAL_LM,
        )


@dataclass
class TrainingConfig:
    """Training configuration"""

    # Training parameters
    epochs: int = 3
    batch_size: int = 4
    gradient_accumulation_steps: int = 4  # Effective batch = 16
    learning_rate: float = 2e-4
    weight_decay: float = 0.01
    warmup_ratio: float = 0.03
    max_grad_norm: float = 0.3

    # Optimizer settings
    optimizer: str = "adamw_torch"  # Use standard AdamW for CPU/GPU compatibility
    lr_scheduler_type: str = "cosine"

    # Sequence settings
    max_seq_length: int = 2048

    # Logging and saving
    logging_steps: int = 10
    save_steps: int = 100
    save_total_limit: int = 3

    # Evaluation
    eval_steps: int = 50
    eval_strategy: str = "steps"

    # Mixed precision (bf16 for modern GPUs like RTX 30xx/40xx, fp16 fallback)
    fp16: bool = False
    bf16: bool = True

    # Memory optimization
    gradient_checkpointing: bool = True
    optim_bits: int = 8

    # Paths
    output_dir: str = "data/adapters"
    logging_dir: str = "logs/tensorboard"

    def to_training_arguments(self, role_name: str):
        """Convert to HuggingFace TrainingArguments"""
        from transformers import TrainingArguments

        output_path = Path(self.output_dir) / role_name
        log_path = Path(self.logging_dir) / role_name

        return TrainingArguments(
            output_dir=str(output_path),
            num_train_epochs=self.epochs,
            per_device_train_batch_size=self.batch_size,
            gradient_accumulation_steps=self.gradient_accumulation_steps,
            learning_rate=self.learning_rate,
            weight_decay=self.weight_decay,
            warmup_ratio=self.warmup_ratio,
            max_grad_norm=self.max_grad_norm,
            optim=self.optimizer,
            lr_scheduler_type=self.lr_scheduler_type,
            logging_steps=self.logging_steps,
            save_steps=self.save_steps,
            save_total_limit=self.save_total_limit,
            eval_strategy=self.eval_strategy,
            eval_steps=self.eval_steps,
            fp16=self.fp16,
            bf16=self.bf16,
            gradient_checkpointing=self.gradient_checkpointing,
            logging_dir=str(log_path),
            report_to=["tensorboard"],
            remove_unused_columns=False,
            push_to_hub=False,
            load_best_model_at_end=True,
            metric_for_best_model="eval_loss",
            greater_is_better=False,
        )


# Role-specific LoRA configurations
ROLE_CONFIGS: dict[str, dict] = {
    "fintech_coder": {
        "lora": LoRAConfig(r=32, lora_alpha=64),  # Higher rank for complex code
        "training": TrainingConfig(
            epochs=3,
            learning_rate=2e-4,
            max_seq_length=4096,  # Longer for code
        ),
        "focus": ["code_generation", "api_patterns", "secure_coding"],
        "target_samples": 1500,
        "priority": "high",
    },
    "fintech_security": {
        "lora": LoRAConfig(r=16, lora_alpha=32),
        "training": TrainingConfig(
            epochs=3,
            learning_rate=2e-4,
        ),
        "focus": ["vulnerability_detection", "pci_dss", "security_patterns"],
        "target_samples": 1000,
        "priority": "high",
    },
    "fintech_compliance": {
        "lora": LoRAConfig(r=8, lora_alpha=16),  # Lower rank for regulatory Q&A
        "training": TrainingConfig(
            epochs=3,
            learning_rate=2e-4,
        ),
        "focus": ["rbi_guidelines", "sebi_regulations", "dpdp_act", "pci_dss"],
        "target_samples": 800,
        "priority": "medium",
    },
    "fintech_architect": {
        "lora": LoRAConfig(r=16, lora_alpha=32),
        "training": TrainingConfig(
            epochs=3,
            learning_rate=2e-4,
        ),
        "focus": ["system_design", "payment_architecture", "security_architecture"],
        "target_samples": 800,
        "priority": "medium",
    },
    "fintech_tester": {
        "lora": LoRAConfig(r=16, lora_alpha=32),
        "training": TrainingConfig(
            epochs=3,
            learning_rate=2e-4,
        ),
        "focus": ["test_generation", "payment_testing", "security_testing"],
        "target_samples": 600,
        "priority": "low",
    },

    # EU FinTech Roles
    "eu_fintech_coder": {
        "lora": LoRAConfig(r=32, lora_alpha=64),
        "training": TrainingConfig(
            epochs=3,
            learning_rate=2e-4,
            max_seq_length=4096,
        ),
        "focus": ["sepa_integration", "psd2_sca", "gdpr_code", "open_banking_eu"],
        "target_samples": 1500,
        "priority": "high",
        "region": "eu",
    },
    "eu_fintech_security": {
        "lora": LoRAConfig(r=16, lora_alpha=32),
        "training": TrainingConfig(
            epochs=3,
            learning_rate=2e-4,
        ),
        "focus": ["gdpr_security", "psd2_security", "dora_compliance"],
        "target_samples": 1000,
        "priority": "high",
        "region": "eu",
    },
    "eu_fintech_compliance": {
        "lora": LoRAConfig(r=8, lora_alpha=16),
        "training": TrainingConfig(
            epochs=3,
            learning_rate=2e-4,
        ),
        "focus": ["gdpr_articles", "psd2_requirements", "dora_framework", "eidas"],
        "target_samples": 800,
        "priority": "medium",
        "region": "eu",
    },
    "eu_fintech_architect": {
        "lora": LoRAConfig(r=16, lora_alpha=32),
        "training": TrainingConfig(
            epochs=3,
            learning_rate=2e-4,
        ),
        "focus": ["sepa_architecture", "open_banking_design", "gdpr_by_design"],
        "target_samples": 800,
        "priority": "medium",
        "region": "eu",
    },
    "eu_fintech_tester": {
        "lora": LoRAConfig(r=16, lora_alpha=32),
        "training": TrainingConfig(
            epochs=3,
            learning_rate=2e-4,
        ),
        "focus": ["sepa_testing", "psd2_testing", "gdpr_testing"],
        "target_samples": 600,
        "priority": "low",
        "region": "eu",
    },

    # UK FinTech Roles
    "uk_fintech_coder": {
        "lora": LoRAConfig(r=32, lora_alpha=64),
        "training": TrainingConfig(
            epochs=3,
            learning_rate=2e-4,
            max_seq_length=4096,
        ),
        "focus": ["fps_integration", "open_banking_uk", "fca_code", "cop_implementation"],
        "target_samples": 1500,
        "priority": "high",
        "region": "uk",
    },
    "uk_fintech_security": {
        "lora": LoRAConfig(r=16, lora_alpha=32),
        "training": TrainingConfig(
            epochs=3,
            learning_rate=2e-4,
        ),
        "focus": ["fca_security", "uk_gdpr_security", "psr_fraud_prevention"],
        "target_samples": 1000,
        "priority": "high",
        "region": "uk",
    },
    "uk_fintech_compliance": {
        "lora": LoRAConfig(r=8, lora_alpha=16),
        "training": TrainingConfig(
            epochs=3,
            learning_rate=2e-4,
        ),
        "focus": ["fca_handbook", "consumer_duty", "uk_gdpr", "psr_requirements"],
        "target_samples": 800,
        "priority": "medium",
        "region": "uk",
    },
    "uk_fintech_architect": {
        "lora": LoRAConfig(r=16, lora_alpha=32),
        "training": TrainingConfig(
            epochs=3,
            learning_rate=2e-4,
        ),
        "focus": ["fps_architecture", "open_banking_uk_design", "fca_architecture"],
        "target_samples": 800,
        "priority": "medium",
        "region": "uk",
    },
    "uk_fintech_tester": {
        "lora": LoRAConfig(r=16, lora_alpha=32),
        "training": TrainingConfig(
            epochs=3,
            learning_rate=2e-4,
        ),
        "focus": ["fps_testing", "cop_testing", "psr_testing"],
        "target_samples": 600,
        "priority": "low",
        "region": "uk",
    },
}


def get_role_lora_config(role_name: str) -> dict:
    """Get LoRA configuration for a specific role"""
    if role_name not in ROLE_CONFIGS:
        raise ValueError(f"Unknown role: {role_name}. Available: {list(ROLE_CONFIGS.keys())}")
    return ROLE_CONFIGS[role_name]


def get_all_roles() -> list[str]:
    """Get all available role names"""
    return list(ROLE_CONFIGS.keys())


# Default paths
DEFAULT_ADAPTERS_DIR = Path("data/adapters")
DEFAULT_TRAINING_DATA_DIR = Path("data/training")
DEFAULT_KNOWLEDGE_DIR = Path("data/knowledge")
