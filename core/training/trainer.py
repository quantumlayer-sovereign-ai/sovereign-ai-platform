"""
QLoRA Trainer for FinTech Role Adapters

Provides QLoRA fine-tuning infrastructure for specialized agent roles.
Optimized for 16GB VRAM with 4-bit quantization.

Features:
- Role-specific LoRA configurations
- Training metrics logging
- Checkpoint management
- TensorBoard integration
"""

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

import structlog
import torch

from .config import ROLE_CONFIGS, TrainingConfig, LoRAConfig

logger = structlog.get_logger()


class RoleLoRATrainer:
    """
    QLoRA trainer for specialized FinTech roles

    Handles model loading, dataset preparation, training loop,
    and adapter saving with proper versioning.
    """

    def __init__(
        self,
        model_name: str = "Qwen/Qwen2.5-Coder-7B-Instruct",
        device: str = "cuda",
        quantize: bool = True
    ):
        self.model_name = model_name
        self.device = device
        self.quantize = quantize

        self.model = None
        self.tokenizer = None
        self.peft_model = None

    def load_model(self):
        """Load base model with quantization"""
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

        logger.info("loading_base_model", model=self.model_name)

        # Determine device map - use CUDA explicitly if available
        if torch.cuda.is_available() and self.device == "cuda":
            device_map = "cuda:0"
            # Use bfloat16 for modern GPUs (RTX 30xx/40xx), consistent with training config
            compute_dtype = torch.bfloat16
        else:
            device_map = "cpu"
            compute_dtype = torch.float32

        # 4-bit quantization config (only works on CUDA)
        bnb_config = None
        if self.quantize and torch.cuda.is_available():
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=compute_dtype,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_use_double_quant=True,
            )

        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_name,
            trust_remote_code=True,
            padding_side="right"
        )

        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        # Load model
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            quantization_config=bnb_config,
            device_map=device_map,
            trust_remote_code=True,
            torch_dtype=compute_dtype,
        )

        # Enable gradient checkpointing
        self.model.gradient_checkpointing_enable()

        vram = torch.cuda.memory_allocated() / 1024**3 if torch.cuda.is_available() else 0
        logger.info("model_loaded", vram_gb=f"{vram:.2f}")

    def prepare_model_for_training(self, lora_config: LoRAConfig):
        """Apply LoRA configuration to model"""
        from peft import get_peft_model, prepare_model_for_kbit_training

        logger.info("preparing_peft_model", rank=lora_config.r)

        # Prepare for k-bit training
        self.model = prepare_model_for_kbit_training(self.model)

        # Apply LoRA
        peft_config = lora_config.to_peft_config()
        self.peft_model = get_peft_model(self.model, peft_config)

        # Log trainable parameters
        trainable, total = self._count_parameters()
        logger.info(
            "peft_model_ready",
            trainable_params=trainable,
            total_params=total,
            trainable_pct=f"{100 * trainable / total:.2f}%"
        )

    def _count_parameters(self) -> tuple[int, int]:
        """Count trainable and total parameters"""
        trainable = sum(p.numel() for p in self.peft_model.parameters() if p.requires_grad)
        total = sum(p.numel() for p in self.peft_model.parameters())
        return trainable, total

    def load_dataset(
        self,
        data_path: Path,
        max_seq_length: int = 2048,
        test_size: float = 0.1
    ):
        """Load and prepare dataset for training"""
        from datasets import Dataset

        logger.info("loading_dataset", path=str(data_path))

        # Load JSONL data
        samples = []
        with open(data_path, encoding="utf-8") as f:
            for line in f:
                samples.append(json.loads(line))

        # Convert to chat format
        def format_sample(sample):
            messages = sample.get("messages", [])
            if not messages:
                # Convert from instruction format
                if sample.get("input"):
                    content = f"{sample['instruction']}\n\nContext:\n{sample['input']}"
                else:
                    content = sample["instruction"]

                messages = [
                    {"role": "user", "content": content},
                    {"role": "assistant", "content": sample["output"]}
                ]

            text = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=False
            )
            return {"text": text}

        # Create dataset
        formatted_samples = [format_sample(s) for s in samples]
        dataset = Dataset.from_list(formatted_samples)

        # Split into train/test
        split = dataset.train_test_split(test_size=test_size, seed=42)

        logger.info(
            "dataset_loaded",
            train_samples=len(split["train"]),
            test_samples=len(split["test"])
        )

        return split

    def train(
        self,
        role_name: str,
        data_path: Path,
        output_dir: Path | None = None,
        training_config: TrainingConfig | None = None,
        lora_config: LoRAConfig | None = None
    ) -> dict:
        """
        Train LoRA adapter for a specific role

        Args:
            role_name: Name of the role
            data_path: Path to training data (JSONL)
            output_dir: Directory to save adapter
            training_config: Training configuration
            lora_config: LoRA configuration

        Returns:
            Training metrics
        """
        from trl import SFTTrainer

        # Get role-specific configs if not provided
        role_cfg = ROLE_CONFIGS.get(role_name, {})
        if training_config is None:
            training_config = role_cfg.get("training", TrainingConfig())
        if lora_config is None:
            lora_config = role_cfg.get("lora", LoRAConfig())

        if output_dir is None:
            output_dir = Path("data/adapters") / role_name

        logger.info(
            "starting_training",
            role=role_name,
            lora_rank=lora_config.r,
            epochs=training_config.epochs
        )

        # Load model if not already loaded
        if self.model is None:
            self.load_model()

        # Prepare for training
        self.prepare_model_for_training(lora_config)

        # Load dataset
        dataset = self.load_dataset(
            data_path,
            max_seq_length=training_config.max_seq_length
        )

        # Create training arguments
        training_args = training_config.to_training_arguments(role_name)

        # Create trainer
        trainer = SFTTrainer(
            model=self.peft_model,
            processing_class=self.tokenizer,
            train_dataset=dataset["train"],
            eval_dataset=dataset["test"],
            args=training_args,
        )

        # Train
        train_result = trainer.train()

        # Save adapter
        self._save_adapter(
            role_name=role_name,
            output_dir=output_dir,
            trainer=trainer,
            training_config=training_config,
            lora_config=lora_config,
            metrics=train_result.metrics
        )

        return train_result.metrics

    def _save_adapter(
        self,
        role_name: str,
        output_dir: Path,
        trainer,
        training_config: TrainingConfig,
        lora_config: LoRAConfig,
        metrics: dict
    ):
        """Save trained adapter with metadata"""
        output_dir = Path(output_dir)

        # Create versioned directory
        version = datetime.now().strftime("v%Y%m%d_%H%M%S")
        version_dir = output_dir / version
        version_dir.mkdir(parents=True, exist_ok=True)

        # Save adapter
        trainer.save_model(str(version_dir))

        # Save training metadata
        metadata = {
            "role": role_name,
            "version": version,
            "base_model": self.model_name,
            "created_at": datetime.now().isoformat(),
            "training_config": asdict(training_config),
            "lora_config": {
                "r": lora_config.r,
                "lora_alpha": lora_config.lora_alpha,
                "target_modules": lora_config.target_modules,
                "lora_dropout": lora_config.lora_dropout,
            },
            "metrics": metrics
        }

        with open(version_dir / "training_metadata.json", "w") as f:
            json.dump(metadata, f, indent=2, default=str)

        # Update latest symlink
        latest_link = output_dir / "latest"
        if latest_link.exists() or latest_link.is_symlink():
            latest_link.unlink()
        latest_link.symlink_to(version)

        logger.info(
            "adapter_saved",
            role=role_name,
            version=version,
            path=str(version_dir)
        )

    def evaluate(
        self,
        test_data_path: Path,
        adapter_path: Path | None = None
    ) -> dict:
        """
        Evaluate adapter on test data

        Args:
            test_data_path: Path to test data
            adapter_path: Path to adapter (uses loaded model if None)

        Returns:
            Evaluation metrics
        """
        from trl import SFTTrainer
        from transformers import TrainingArguments

        # Load adapter if path provided
        if adapter_path and self.peft_model is None:
            from peft import PeftModel

            if self.model is None:
                self.load_model()

            self.peft_model = PeftModel.from_pretrained(
                self.model,
                str(adapter_path)
            )

        # Load test dataset
        dataset = self.load_dataset(test_data_path, test_size=0.0)

        # Create minimal training args for evaluation
        eval_args = TrainingArguments(
            output_dir="./eval_output",
            per_device_eval_batch_size=4,
            do_train=False,
            do_eval=True,
        )

        trainer = SFTTrainer(
            model=self.peft_model,
            tokenizer=self.tokenizer,
            eval_dataset=dataset["train"],  # Using all data for eval
            args=eval_args,
            dataset_text_field="text",
        )

        metrics = trainer.evaluate()
        logger.info("evaluation_complete", metrics=metrics)

        return metrics

    def cleanup(self):
        """Release GPU memory"""
        if self.peft_model is not None:
            del self.peft_model
            self.peft_model = None

        if self.model is not None:
            del self.model
            self.model = None

        if self.tokenizer is not None:
            del self.tokenizer
            self.tokenizer = None

        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        logger.info("resources_released")


def train_all_roles(
    training_data_dir: Path,
    output_dir: Path,
    roles: list[str] | None = None,
    model_name: str = "Qwen/Qwen2.5-Coder-7B-Instruct"
) -> dict[str, dict]:
    """
    Train adapters for all roles

    Args:
        training_data_dir: Directory containing role training data
        output_dir: Base directory for saving adapters
        roles: List of roles to train (None = all)
        model_name: Base model name

    Returns:
        Dictionary of role -> training metrics
    """
    all_metrics = {}
    training_data_dir = Path(training_data_dir)
    output_dir = Path(output_dir)

    if roles is None:
        roles = list(ROLE_CONFIGS.keys())

    # Sort by priority
    priority_order = {"high": 0, "medium": 1, "low": 2}
    roles = sorted(
        roles,
        key=lambda r: priority_order.get(ROLE_CONFIGS[r].get("priority", "low"), 2)
    )

    trainer = RoleLoRATrainer(model_name=model_name)

    for role_name in roles:
        data_path = training_data_dir / role_name / "train_chat.jsonl"

        if not data_path.exists():
            logger.warning("training_data_not_found", role=role_name, path=str(data_path))
            continue

        try:
            metrics = trainer.train(
                role_name=role_name,
                data_path=data_path,
                output_dir=output_dir / role_name
            )
            all_metrics[role_name] = metrics
        except Exception as e:
            logger.error("training_failed", role=role_name, error=str(e))
            all_metrics[role_name] = {"error": str(e)}
        finally:
            # Cleanup between roles to free memory
            trainer.cleanup()
            trainer.model = None

    return all_metrics
