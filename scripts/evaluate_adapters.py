#!/usr/bin/env python3
"""
Adapter Evaluation CLI for Sovereign AI Platform

Evaluate trained LoRA adapters against compliance benchmarks.

Usage:
    # Evaluate single role
    python scripts/evaluate_adapters.py --role fintech_coder

    # Evaluate all roles
    python scripts/evaluate_adapters.py --role all

    # Compare adapters
    python scripts/evaluate_adapters.py --role fintech_coder --compare v1 v2
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import structlog

from core.training.config import ROLE_CONFIGS
from core.training.evaluator import AdapterEvaluator, EvaluationResult
from core.training.adapter_manager import AdapterManager

logger = structlog.get_logger()


def setup_logging(verbose: bool = False):
    """Configure logging"""
    processors = [
        structlog.dev.ConsoleRenderer(colors=True)
    ]
    structlog.configure(processors=processors)


async def evaluate_role(
    role: str,
    adapter_path: Path | None,
    model_interface=None,
    output_dir: Path | None = None
) -> EvaluationResult:
    """Evaluate a single role"""
    print(f"\n{'='*60}")
    print(f"Evaluating: {role}")
    print(f"{'='*60}\n")

    evaluator = AdapterEvaluator(model_interface)

    result = await evaluator.evaluate_adapter(role, adapter_path)

    # Print results
    print(f"Overall Score: {result.overall_score:.2%}")
    print(f"Passed: {'✓' if result.passed else '✗'}")
    print()

    print("Category Scores:")
    for category, score in result.metrics.items():
        if category != "overall":
            status = "✓" if score >= 0.6 else "✗"
            print(f"  {category}: {score:.2%} {status}")
    print()

    print("Detailed Results:")
    for test in result.detailed_results:
        status = "✓" if test["passed"] else "✗"
        print(f"  [{status}] {test['test_id']}: {test['score']:.2%}")
        print(f"      Expected: {test['expected_matches']}/{test['expected_total']}")
        if test["forbidden_matches"] > 0:
            print(f"      Forbidden matches: {test['forbidden_matches']}")

    # Save results
    if output_dir:
        output_path = output_dir / f"{role}_eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        evaluator.save_results(result, output_path)
        print(f"\nResults saved to: {output_path}")

    return result


async def evaluate_all(args, model_interface=None) -> dict[str, EvaluationResult]:
    """Evaluate all roles"""
    results = {}
    manager = AdapterManager(Path(args.adapter_dir))

    roles = args.roles if args.roles else list(ROLE_CONFIGS.keys())

    for role in roles:
        adapter_path = manager.get_adapter_path(role)
        result = await evaluate_role(
            role,
            adapter_path,
            model_interface,
            Path(args.output_dir) if args.output_dir else None
        )
        results[role] = result

    # Print summary
    print(f"\n{'='*60}")
    print("Evaluation Summary")
    print(f"{'='*60}\n")

    for role, result in results.items():
        status = "✓ PASSED" if result.passed else "✗ FAILED"
        print(f"{role}: {result.overall_score:.2%} {status}")

    passed = sum(1 for r in results.values() if r.passed)
    print(f"\nTotal: {passed}/{len(results)} passed")

    return results


async def compare_versions(args):
    """Compare two adapter versions"""
    manager = AdapterManager(Path(args.adapter_dir))

    version1, version2 = args.compare

    print(f"\n{'='*60}")
    print(f"Comparing Adapters: {args.role}")
    print(f"  Version 1: {version1}")
    print(f"  Version 2: {version2}")
    print(f"{'='*60}\n")

    evaluator = AdapterEvaluator()

    # Evaluate version 1
    path1 = manager.get_adapter_path(args.role, version1)
    result1 = await evaluator.evaluate_adapter(args.role, path1)

    # Evaluate version 2
    path2 = manager.get_adapter_path(args.role, version2)
    result2 = await evaluator.evaluate_adapter(args.role, path2)

    # Compare
    comparison = evaluator.compare_adapters(result1, result2)

    print(f"Version 1 ({version1}): {result1.overall_score:.2%}")
    print(f"Version 2 ({version2}): {result2.overall_score:.2%}")
    print()

    improvement = comparison["improvement"]
    if improvement > 0:
        print(f"Improvement: +{improvement:.2%} ⬆")
    elif improvement < 0:
        print(f"Regression: {improvement:.2%} ⬇")
    else:
        print("No change")

    print("\nCategory Comparison:")
    for category, diff in comparison["category_comparison"].items():
        if category == "overall":
            continue
        arrow = "⬆" if diff > 0 else "⬇" if diff < 0 else "="
        print(f"  {category}: {diff:+.2%} {arrow}")


def generate_report(results: dict[str, EvaluationResult], output_path: Path):
    """Generate HTML evaluation report"""
    html = """<!DOCTYPE html>
<html>
<head>
    <title>Adapter Evaluation Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        h1 { color: #333; }
        .summary { background: #f5f5f5; padding: 20px; border-radius: 8px; }
        .passed { color: #22c55e; }
        .failed { color: #ef4444; }
        table { border-collapse: collapse; width: 100%; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
        th { background: #f0f0f0; }
        .score { font-weight: bold; }
    </style>
</head>
<body>
    <h1>LoRA Adapter Evaluation Report</h1>
    <p>Generated: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>

    <div class="summary">
        <h2>Summary</h2>
        <table>
            <tr>
                <th>Role</th>
                <th>Score</th>
                <th>Status</th>
            </tr>
"""

    for role, result in results.items():
        status_class = "passed" if result.passed else "failed"
        status_text = "PASSED" if result.passed else "FAILED"
        html += f"""
            <tr>
                <td>{role}</td>
                <td class="score">{result.overall_score:.1%}</td>
                <td class="{status_class}">{status_text}</td>
            </tr>
"""

    html += """
        </table>
    </div>
"""

    for role, result in results.items():
        html += f"""
    <h2>{role}</h2>
    <p>Adapter: {result.adapter_version}</p>
    <p>Evaluated: {result.timestamp.strftime("%Y-%m-%d %H:%M")}</p>

    <h3>Category Scores</h3>
    <table>
        <tr>
            <th>Category</th>
            <th>Score</th>
        </tr>
"""
        for category, score in result.metrics.items():
            if category != "overall":
                html += f"""
        <tr>
            <td>{category}</td>
            <td>{score:.1%}</td>
        </tr>
"""
        html += """
    </table>

    <h3>Test Details</h3>
    <table>
        <tr>
            <th>Test ID</th>
            <th>Category</th>
            <th>Score</th>
            <th>Status</th>
        </tr>
"""
        for test in result.detailed_results:
            status = "PASS" if test["passed"] else "FAIL"
            status_class = "passed" if test["passed"] else "failed"
            html += f"""
        <tr>
            <td>{test['test_id']}</td>
            <td>{test['category']}</td>
            <td>{test['score']:.1%}</td>
            <td class="{status_class}">{status}</td>
        </tr>
"""
        html += """
    </table>
"""

    html += """
</body>
</html>
"""

    output_path.write_text(html)
    print(f"\nHTML report saved to: {output_path}")


async def main():
    parser = argparse.ArgumentParser(
        description="Evaluate LoRA adapters against compliance benchmarks"
    )

    parser.add_argument(
        "--role",
        type=str,
        default="all",
        choices=list(ROLE_CONFIGS.keys()) + ["all"],
        help="Role to evaluate"
    )
    parser.add_argument(
        "--roles",
        nargs="+",
        help="Specific roles to evaluate"
    )
    parser.add_argument(
        "--adapter-dir",
        type=str,
        default="data/adapters",
        help="Adapter directory"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        help="Output directory for results"
    )
    parser.add_argument(
        "--compare",
        nargs=2,
        metavar=("V1", "V2"),
        help="Compare two adapter versions"
    )
    parser.add_argument(
        "--html-report",
        type=str,
        help="Generate HTML report at path"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output"
    )

    args = parser.parse_args()
    setup_logging(args.verbose)

    if args.compare:
        if args.role == "all":
            print("Error: --compare requires a specific role")
            return
        await compare_versions(args)
        return

    # Evaluate
    if args.role == "all" or args.roles:
        results = await evaluate_all(args)
    else:
        manager = AdapterManager(Path(args.adapter_dir))
        adapter_path = manager.get_adapter_path(args.role)
        result = await evaluate_role(
            args.role,
            adapter_path,
            output_dir=Path(args.output_dir) if args.output_dir else None
        )
        results = {args.role: result}

    # Generate HTML report if requested
    if args.html_report:
        generate_report(results, Path(args.html_report))


if __name__ == "__main__":
    asyncio.run(main())
