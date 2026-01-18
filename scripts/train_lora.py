#!/usr/bin/env python3
"""
LoRA Training CLI for Sovereign AI Platform

Train specialized LoRA adapters for FinTech agent roles.

Usage:
    # Generate training data first
    python -m core.training.data_pipeline --role fintech_coder

    # Train single role
    python scripts/train_lora.py --role fintech_coder --epochs 3

    # Train all roles
    python scripts/train_lora.py --role all

    # Train with custom settings
    python scripts/train_lora.py --role fintech_coder --lora-rank 32 --epochs 5
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import structlog

from core.training.config import ROLE_CONFIGS, LoRAConfig, TrainingConfig
from core.training.trainer import RoleLoRATrainer, train_all_roles
from core.training.adapter_manager import AdapterManager
from core.training.data_pipeline import DataPipeline

logger = structlog.get_logger()


def setup_logging(verbose: bool = False):
    """Configure structured logging"""
    processors = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if verbose:
        processors.append(structlog.dev.ConsoleRenderer(colors=True))
    else:
        processors.append(structlog.processors.JSONRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def generate_data(args) -> bool:
    """Generate training data for roles"""
    print(f"\n{'='*60}")
    print("Generating Training Data")
    print(f"{'='*60}\n")

    pipeline = DataPipeline(
        knowledge_dir=Path(args.knowledge_dir),
        output_dir=Path(args.training_data_dir)
    )

    if args.role == "all":
        all_samples = pipeline.generate_all(augment=not args.no_augment)
        for role, samples in all_samples.items():
            stats = pipeline.get_statistics(samples)
            print(f"\n{role}:")
            print(f"  Samples: {stats['total_samples']}")
            print(f"  Estimated tokens: {stats['estimated_tokens']:,}")
    else:
        samples = pipeline.generate_for_role(args.role, augment=not args.no_augment)
        pipeline.save_dataset(samples, args.role)
        pipeline.save_chat_format(samples, args.role)

        stats = pipeline.get_statistics(samples)
        print(f"\n{args.role}:")
        print(f"  Samples: {stats['total_samples']}")
        print(f"  Estimated tokens: {stats['estimated_tokens']:,}")
        print(f"  Categories: {stats['categories']}")

    return True


def train_role(args) -> dict:
    """Train a single role adapter"""
    print(f"\n{'='*60}")
    print(f"Training LoRA Adapter: {args.role}")
    print(f"{'='*60}\n")

    # Check training data exists
    data_path = Path(args.training_data_dir) / args.role / "train_chat.jsonl"
    if not data_path.exists():
        print(f"Error: Training data not found at {data_path}")
        print("Run with --generate-data first, or use: python -m core.training.data_pipeline")
        return {"error": "Training data not found"}

    # Get role-specific config or use custom
    role_cfg = ROLE_CONFIGS.get(args.role, {})

    # Override with CLI args
    lora_config = role_cfg.get("lora", LoRAConfig())
    if args.lora_rank:
        lora_config = LoRAConfig(
            r=args.lora_rank,
            lora_alpha=args.lora_rank * 2
        )

    training_config = role_cfg.get("training", TrainingConfig())
    if args.epochs:
        training_config.epochs = args.epochs
    if args.batch_size:
        training_config.batch_size = args.batch_size
    if args.learning_rate:
        training_config.learning_rate = args.learning_rate
    if args.max_seq_length:
        training_config.max_seq_length = args.max_seq_length

    print(f"Configuration:")
    print(f"  LoRA Rank: {lora_config.r}")
    print(f"  LoRA Alpha: {lora_config.lora_alpha}")
    print(f"  Epochs: {training_config.epochs}")
    print(f"  Batch Size: {training_config.batch_size}")
    print(f"  Learning Rate: {training_config.learning_rate}")
    print(f"  Max Seq Length: {training_config.max_seq_length}")
    print(f"  Model: {args.model}")
    print()

    if args.dry_run:
        print("Dry run - skipping actual training")
        return {"dry_run": True}

    # Train
    trainer = RoleLoRATrainer(
        model_name=args.model,
        quantize=not args.no_quantize
    )

    try:
        metrics = trainer.train(
            role_name=args.role,
            data_path=data_path,
            output_dir=Path(args.output_dir) / args.role,
            training_config=training_config,
            lora_config=lora_config
        )

        print(f"\nTraining Complete!")
        print(f"  Final Loss: {metrics.get('train_loss', 'N/A')}")
        print(f"  Eval Loss: {metrics.get('eval_loss', 'N/A')}")

        return metrics

    finally:
        trainer.cleanup()


def train_all(args) -> dict:
    """Train all role adapters"""
    print(f"\n{'='*60}")
    print("Training All Role Adapters")
    print(f"{'='*60}\n")

    if args.dry_run:
        print("Dry run - skipping actual training")
        return {"dry_run": True}

    metrics = train_all_roles(
        training_data_dir=Path(args.training_data_dir),
        output_dir=Path(args.output_dir),
        model_name=args.model
    )

    print("\nTraining Summary:")
    for role, role_metrics in metrics.items():
        if "error" in role_metrics:
            print(f"  {role}: FAILED - {role_metrics['error']}")
        else:
            print(f"  {role}: train_loss={role_metrics.get('train_loss', 'N/A'):.4f}")

    return metrics


def list_adapters(args):
    """List all trained adapters"""
    manager = AdapterManager(Path(args.output_dir))

    print(f"\n{'='*60}")
    print("Trained Adapters")
    print(f"{'='*60}\n")

    for role in manager.list_roles():
        versions = manager.list_versions(role)
        print(f"\n{role}:")

        for v in versions:
            latest = " (latest)" if v.is_latest else ""
            loss = v.metrics.get("train_loss", "N/A")
            print(f"  - {v.version}{latest}")
            print(f"    Created: {v.created_at.strftime('%Y-%m-%d %H:%M')}")
            print(f"    Train Loss: {loss}")


def cleanup_adapters(args):
    """Cleanup old adapter versions"""
    manager = AdapterManager(Path(args.output_dir))

    print(f"\n{'='*60}")
    print(f"Cleaning up old versions (keeping {args.keep} per role)")
    print(f"{'='*60}\n")

    for role in manager.list_roles():
        deleted = manager.cleanup_old_versions(role, keep_count=args.keep)
        if deleted:
            print(f"{role}: Deleted {len(deleted)} versions")
        else:
            print(f"{role}: Nothing to clean up")


def main():
    parser = argparse.ArgumentParser(
        description="Train LoRA adapters for FinTech agent roles",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate training data
  python scripts/train_lora.py --role fintech_coder --generate-data

  # Train single role
  python scripts/train_lora.py --role fintech_coder

  # Train all roles
  python scripts/train_lora.py --role all

  # Custom configuration
  python scripts/train_lora.py --role fintech_coder --lora-rank 32 --epochs 5

  # List adapters
  python scripts/train_lora.py --list

  # Cleanup old versions
  python scripts/train_lora.py --cleanup --keep 3
"""
    )

    # Role selection
    parser.add_argument(
        "--role",
        type=str,
        default="all",
        choices=list(ROLE_CONFIGS.keys()) + ["all"],
        help="Role to train (or 'all')"
    )

    # Actions
    parser.add_argument(
        "--generate-data",
        action="store_true",
        help="Generate training data before training"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all trained adapters"
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Clean up old adapter versions"
    )

    # Model settings
    parser.add_argument(
        "--model",
        type=str,
        default="Qwen/Qwen2.5-Coder-7B-Instruct",
        help="Base model to use"
    )
    parser.add_argument(
        "--no-quantize",
        action="store_true",
        help="Disable 4-bit quantization"
    )

    # LoRA settings
    parser.add_argument(
        "--lora-rank",
        type=int,
        help="LoRA rank (default: role-specific)"
    )

    # Training settings
    parser.add_argument(
        "--epochs",
        type=int,
        help="Number of training epochs"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        help="Training batch size"
    )
    parser.add_argument(
        "--learning-rate",
        type=float,
        help="Learning rate"
    )
    parser.add_argument(
        "--max-seq-length",
        type=int,
        help="Maximum sequence length"
    )

    # Paths
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/adapters",
        help="Output directory for adapters"
    )
    parser.add_argument(
        "--training-data-dir",
        type=str,
        default="data/training",
        help="Training data directory"
    )
    parser.add_argument(
        "--knowledge-dir",
        type=str,
        default="data/knowledge",
        help="Knowledge documents directory"
    )

    # Data generation
    parser.add_argument(
        "--no-augment",
        action="store_true",
        help="Disable synthetic sample generation"
    )

    # Cleanup
    parser.add_argument(
        "--keep",
        type=int,
        default=3,
        help="Number of versions to keep during cleanup"
    )

    # Other
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show configuration but don't train"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output"
    )

    args = parser.parse_args()
    setup_logging(args.verbose)

    # Handle actions
    if args.list:
        list_adapters(args)
        return

    if args.cleanup:
        cleanup_adapters(args)
        return

    # Generate data if requested
    if args.generate_data:
        generate_data(args)
        if args.dry_run:
            return

    # Train
    if args.role == "all":
        train_all(args)
    else:
        train_role(args)


if __name__ == "__main__":
    main()
