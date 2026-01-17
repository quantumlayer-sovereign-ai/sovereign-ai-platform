#!/usr/bin/env python3
"""
Test script for Sovereign AI Platform

Tests:
1. Qwen2.5-Coder model loading
2. Agent creation and execution
3. Orchestrator coordination
"""

import asyncio
import sys
sys.path.insert(0, '/home/satish/sovereign-ai')

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


async def test_model():
    """Test Qwen2.5-Coder loading and generation"""
    console.print("\n[bold blue]═══ Testing Qwen2.5-Coder ═══[/bold blue]\n")

    from core.models.qwen import QwenModel

    # Test with 7B model (fits in 16GB with 4-bit)
    model = QwenModel(model_size="7b", quantize=True)

    console.print("Loading model (this may take a minute)...")
    model.load()

    console.print(f"[green]✓ Model loaded![/green]")
    console.print(f"  VRAM: {model.model_info.get('vram_gb', 0):.2f} GB")

    # Test generation
    messages = [
        {"role": "system", "content": "You are a helpful coding assistant."},
        {"role": "user", "content": "Write a Python function to check if a number is prime. Keep it short."}
    ]

    console.print("\n[yellow]Generating response...[/yellow]")
    response = await model.generate(messages)

    console.print(Panel(response, title="Model Response", border_style="green"))

    # Cleanup
    model.unload()
    console.print("[green]✓ Model unloaded[/green]")

    return True


async def test_agents():
    """Test agent creation and role assignment"""
    console.print("\n[bold blue]═══ Testing Agent Framework ═══[/bold blue]\n")

    from core.agents.base import Agent, AgentContext
    from core.agents.registry import get_registry
    from core.agents.factory import AgentFactory

    # Test registry
    registry = get_registry()
    roles = registry.list_roles()

    table = Table(title="Available Roles")
    table.add_column("Role", style="cyan")
    table.add_column("Description")

    for role_name in roles:
        role = registry.get_role(role_name)
        table.add_row(role_name, role.get("description", "")[:50] + "...")

    console.print(table)

    # Test agent creation
    console.print("\n[yellow]Creating test agents...[/yellow]")

    factory = AgentFactory(max_agents=5)

    # Spawn a coder agent
    coder = factory.spawn("coder")
    console.print(f"[green]✓ Spawned: {coder}[/green]")

    # Spawn an architect agent
    architect = factory.spawn("architect")
    console.print(f"[green]✓ Spawned: {architect}[/green]")

    # Test role switching
    coder.assume_role(registry.get_role("reviewer"))
    console.print(f"[green]✓ Role switched: {coder}[/green]")

    # Show stats
    console.print(f"\n[cyan]Factory Stats:[/cyan] {factory.stats}")

    # Cleanup
    factory.destroy_all()
    console.print("[green]✓ All agents destroyed[/green]")

    return True


async def test_orchestrator():
    """Test orchestrator task coordination"""
    console.print("\n[bold blue]═══ Testing Orchestrator ═══[/bold blue]\n")

    from core.orchestrator.main import Orchestrator

    # Create orchestrator (without model for quick test)
    orchestrator = Orchestrator(model_interface=None, max_agents=5)

    # Test task analysis
    task = "Create a REST API endpoint for user authentication with JWT tokens"

    console.print(f"[yellow]Task:[/yellow] {task}\n")

    result = await orchestrator.execute(task, vertical="fintech")

    console.print(f"[green]✓ Task completed![/green]")
    console.print(f"  Success: {result.success}")
    console.print(f"  Agents used: {result.agents_used}")
    console.print(f"  Execution time: {result.execution_time_seconds:.2f}s")
    console.print(f"  Compliance checks: {list(result.compliance_status.keys())}")

    # Show orchestrator stats
    console.print(f"\n[cyan]Orchestrator Stats:[/cyan] {orchestrator.stats}")

    return True


async def test_full_pipeline():
    """Test full pipeline with model"""
    console.print("\n[bold blue]═══ Testing Full Pipeline ═══[/bold blue]\n")

    from core.models.qwen import QwenModel
    from core.orchestrator.main import Orchestrator

    # Load model
    console.print("Loading Qwen2.5-Coder 7B...")
    model = QwenModel(model_size="7b", quantize=True)
    model.load()

    # Create orchestrator with model
    orchestrator = Orchestrator(model_interface=model, max_agents=3)

    # Execute a real task
    task = "Write a Python function that validates an email address using regex"

    console.print(f"\n[yellow]Task:[/yellow] {task}\n")

    result = await orchestrator.execute(task, vertical="fintech")

    console.print(Panel(
        result.aggregated_output,
        title=f"Result (Success: {result.success})",
        border_style="green" if result.success else "red"
    ))

    # Cleanup
    model.unload()

    return result.success


async def main():
    console.print(Panel.fit(
        "[bold]Sovereign AI Platform - Test Suite[/bold]",
        border_style="blue"
    ))

    try:
        # Test 1: Agents (no model needed)
        await test_agents()

        # Test 2: Orchestrator (no model needed)
        await test_orchestrator()

        # Test 3: Model loading
        await test_model()

        # Test 4: Full pipeline (requires model)
        # Uncomment to run full test:
        # await test_full_pipeline()

        console.print("\n[bold green]═══ All Tests Passed! ═══[/bold green]\n")

    except Exception as e:
        console.print(f"\n[bold red]Test failed: {e}[/bold red]")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
