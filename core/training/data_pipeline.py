"""
Data Pipeline for LoRA Training

Orchestrates knowledge document conversion to instruction-tuning datasets.

Usage:
    python -m core.training.data_pipeline --role fintech_coder --output data/training/
"""

import argparse
import json
from pathlib import Path
from typing import Iterator

import structlog

from .config import ROLE_CONFIGS, DEFAULT_KNOWLEDGE_DIR, DEFAULT_TRAINING_DATA_DIR
from .generators import get_generator, TrainingSample

logger = structlog.get_logger()


class DataPipeline:
    """
    Pipeline for generating training data from knowledge documents

    Converts markdown knowledge files into Alpaca-style instruction tuning datasets
    optimized for each FinTech role.
    """

    def __init__(
        self,
        knowledge_dir: Path = DEFAULT_KNOWLEDGE_DIR,
        output_dir: Path = DEFAULT_TRAINING_DATA_DIR
    ):
        self.knowledge_dir = Path(knowledge_dir)
        self.output_dir = Path(output_dir)

    def generate_for_role(
        self,
        role_name: str,
        augment: bool = True
    ) -> list[TrainingSample]:
        """
        Generate training data for a specific role

        Args:
            role_name: Name of the role to generate data for
            augment: Whether to include synthetic samples

        Returns:
            List of training samples
        """
        if role_name not in ROLE_CONFIGS:
            raise ValueError(f"Unknown role: {role_name}")

        logger.info("generating_training_data", role=role_name)

        generator = get_generator(role_name)
        samples = []

        # Process knowledge documents
        knowledge_path = self.knowledge_dir / "fintech"
        if knowledge_path.exists():
            for sample in generator.generate_from_directory(knowledge_path):
                samples.append(sample)

        logger.info("samples_from_documents", role=role_name, count=len(samples))

        # Add augmented/synthetic samples if enabled
        if augment:
            augmented = self._generate_augmented_samples(generator, role_name)
            samples.extend(augmented)
            logger.info("augmented_samples_added", role=role_name, count=len(augmented))

        # Deduplicate by instruction
        samples = self._deduplicate_samples(samples)

        logger.info("total_samples", role=role_name, count=len(samples))

        return samples

    def _generate_augmented_samples(
        self,
        generator,
        role_name: str
    ) -> list[TrainingSample]:
        """Generate role-specific augmented samples"""
        augmented = []

        # Call role-specific synthetic generators
        if hasattr(generator, 'generate_payment_api_samples'):
            augmented.extend(generator.generate_payment_api_samples())

        if hasattr(generator, 'generate_vulnerability_samples'):
            augmented.extend(generator.generate_vulnerability_samples())

        if hasattr(generator, 'generate_rbi_samples'):
            augmented.extend(generator.generate_rbi_samples())

        if hasattr(generator, 'generate_dpdp_samples'):
            augmented.extend(generator.generate_dpdp_samples())

        if hasattr(generator, 'generate_payment_architecture_samples'):
            augmented.extend(generator.generate_payment_architecture_samples())

        if hasattr(generator, 'generate_payment_test_samples'):
            augmented.extend(generator.generate_payment_test_samples())

        return augmented

    def _deduplicate_samples(
        self,
        samples: list[TrainingSample]
    ) -> list[TrainingSample]:
        """Remove duplicate samples based on instruction"""
        seen = set()
        unique = []

        for sample in samples:
            # Create a key from instruction (normalized)
            key = sample.instruction.lower().strip()[:100]
            if key not in seen:
                seen.add(key)
                unique.append(sample)

        if len(samples) != len(unique):
            logger.info("duplicates_removed", original=len(samples), unique=len(unique))

        return unique

    def save_dataset(
        self,
        samples: list[TrainingSample],
        role_name: str,
        format: str = "jsonl"
    ) -> Path:
        """
        Save training dataset to file

        Args:
            samples: List of training samples
            role_name: Role name for output filename
            format: Output format (jsonl or json)

        Returns:
            Path to saved file
        """
        output_path = self.output_dir / role_name
        output_path.mkdir(parents=True, exist_ok=True)

        if format == "jsonl":
            file_path = output_path / "train.jsonl"
            with open(file_path, "w", encoding="utf-8") as f:
                for sample in samples:
                    f.write(json.dumps(sample.to_dict(), ensure_ascii=False) + "\n")
        else:
            file_path = output_path / "train.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump([s.to_dict() for s in samples], f, indent=2, ensure_ascii=False)

        logger.info("dataset_saved", path=str(file_path), samples=len(samples))
        return file_path

    def save_chat_format(
        self,
        samples: list[TrainingSample],
        role_name: str
    ) -> Path:
        """
        Save dataset in chat format for training

        Args:
            samples: List of training samples
            role_name: Role name for output filename

        Returns:
            Path to saved file
        """
        output_path = self.output_dir / role_name
        output_path.mkdir(parents=True, exist_ok=True)

        file_path = output_path / "train_chat.jsonl"
        with open(file_path, "w", encoding="utf-8") as f:
            for sample in samples:
                chat_data = {
                    "messages": sample.to_chat_format(),
                    "role": sample.role,
                }
                if sample.compliance_tags:
                    chat_data["compliance_tags"] = sample.compliance_tags
                f.write(json.dumps(chat_data, ensure_ascii=False) + "\n")

        logger.info("chat_dataset_saved", path=str(file_path), samples=len(samples))
        return file_path

    def generate_all(
        self,
        augment: bool = True
    ) -> dict[str, list[TrainingSample]]:
        """
        Generate training data for all roles

        Args:
            augment: Whether to include synthetic samples

        Returns:
            Dictionary of role -> samples
        """
        all_samples = {}

        for role_name in ROLE_CONFIGS:
            samples = self.generate_for_role(role_name, augment=augment)
            all_samples[role_name] = samples

            # Save to disk
            self.save_dataset(samples, role_name)
            self.save_chat_format(samples, role_name)

        return all_samples

    def get_statistics(
        self,
        samples: list[TrainingSample]
    ) -> dict:
        """Get statistics about the dataset"""
        categories = {}
        compliance_tags = {}
        total_tokens_estimate = 0

        for sample in samples:
            # Category distribution
            cat = sample.category or "unknown"
            categories[cat] = categories.get(cat, 0) + 1

            # Compliance tag distribution
            for tag in (sample.compliance_tags or []):
                compliance_tags[tag] = compliance_tags.get(tag, 0) + 1

            # Rough token estimate (4 chars per token)
            text = sample.instruction + sample.input + sample.output
            total_tokens_estimate += len(text) // 4

        return {
            "total_samples": len(samples),
            "categories": categories,
            "compliance_tags": compliance_tags,
            "estimated_tokens": total_tokens_estimate,
            "avg_tokens_per_sample": total_tokens_estimate // len(samples) if samples else 0
        }


def create_train_test_split(
    samples: list[TrainingSample],
    test_ratio: float = 0.1
) -> tuple[list[TrainingSample], list[TrainingSample]]:
    """
    Split samples into training and test sets

    Args:
        samples: List of samples to split
        test_ratio: Ratio of samples for test set

    Returns:
        Tuple of (train_samples, test_samples)
    """
    import random
    shuffled = samples.copy()
    random.shuffle(shuffled)

    split_idx = int(len(shuffled) * (1 - test_ratio))
    return shuffled[:split_idx], shuffled[split_idx:]


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Generate training data for LoRA fine-tuning"
    )
    parser.add_argument(
        "--role",
        type=str,
        default="all",
        help="Role to generate data for (or 'all')"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/training",
        help="Output directory"
    )
    parser.add_argument(
        "--knowledge-dir",
        type=str,
        default="data/knowledge",
        help="Knowledge documents directory"
    )
    parser.add_argument(
        "--no-augment",
        action="store_true",
        help="Disable synthetic sample generation"
    )
    parser.add_argument(
        "--format",
        choices=["jsonl", "json"],
        default="jsonl",
        help="Output format"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Print dataset statistics"
    )

    args = parser.parse_args()

    # Configure logging
    structlog.configure(
        processors=[
            structlog.dev.ConsoleRenderer()
        ]
    )

    pipeline = DataPipeline(
        knowledge_dir=Path(args.knowledge_dir),
        output_dir=Path(args.output)
    )

    if args.role == "all":
        all_samples = pipeline.generate_all(augment=not args.no_augment)

        if args.stats:
            print("\n=== Dataset Statistics ===\n")
            for role, samples in all_samples.items():
                stats = pipeline.get_statistics(samples)
                print(f"\n{role}:")
                print(f"  Total samples: {stats['total_samples']}")
                print(f"  Estimated tokens: {stats['estimated_tokens']:,}")
                print(f"  Categories: {stats['categories']}")
    else:
        samples = pipeline.generate_for_role(args.role, augment=not args.no_augment)
        pipeline.save_dataset(samples, args.role, format=args.format)
        pipeline.save_chat_format(samples, args.role)

        if args.stats:
            stats = pipeline.get_statistics(samples)
            print("\n=== Dataset Statistics ===")
            print(f"Total samples: {stats['total_samples']}")
            print(f"Estimated tokens: {stats['estimated_tokens']:,}")
            print(f"Avg tokens/sample: {stats['avg_tokens_per_sample']}")
            print(f"Categories: {json.dumps(stats['categories'], indent=2)}")
            print(f"Compliance tags: {json.dumps(stats['compliance_tags'], indent=2)}")


if __name__ == "__main__":
    main()
