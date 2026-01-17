# Sovereign AI Platform

**Enterprise AI Agents for Regulated Industries**

An on-premise, air-gapped capable AI platform with dynamic agent spawning and role-based specialization for FinTech, Healthcare, Government, and Legal verticals.

## Key Features

- **Dynamic Agent Spawning** - Agents created on-demand based on task requirements
- **Role-Based Specialization** - Agents assume roles with specific prompts, tools, and knowledge
- **Hot-Swappable LoRA** - Specialize models on-the-fly
- **Vertical Modules** - Pre-built compliance for FinTech, Healthcare, Government, Legal
- **On-Premise/Air-Gapped** - Runs entirely within your infrastructure
- **Audit Logging** - Complete traceability for compliance

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      ORCHESTRATOR                            │
│            (Task analysis, agent coordination)               │
└─────────────────────────┬───────────────────────────────────┘
                          │
                ┌─────────▼─────────┐
                │   AGENT FACTORY   │
                │  (Spawns agents)  │
                └─────────┬─────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
   ┌─────────┐       ┌─────────┐       ┌─────────┐
   │ Agent 1 │       │ Agent 2 │       │ Agent N │
   │ (Role A)│       │ (Role B)│       │ (Role C)│
   └─────────┘       └─────────┘       └─────────┘
        │                 │                 │
        └─────────────────┼─────────────────┘
                          ▼
              ┌───────────────────────┐
              │     ROLE REGISTRY     │
              │  ┌─────┐ ┌─────┐     │
              │  │Arch │ │Coder│ ... │
              │  └─────┘ └─────┘     │
              └───────────────────────┘
                          │
              ┌───────────▼───────────┐
              │    BASE MODEL         │
              │   Qwen2.5-Coder       │
              │  + LoRA Adapters      │
              └───────────────────────┘
```

## Quick Start

```bash
# Activate environment
source ~/pytorch-env/bin/activate

# Install dependencies
pip install -r requirements.txt

# Test base model
python scripts/test_model.py

# Run the platform
python -m api.main
```

## Project Structure

```
sovereign-ai/
├── core/
│   ├── agents/          # Agent base classes and spawning
│   ├── models/          # Model loading and LoRA management
│   ├── rag/             # RAG pipeline
│   ├── tools/           # Tool definitions
│   └── orchestrator/    # Task orchestration
├── verticals/
│   ├── fintech/         # PCI-DSS, RBI/SEBI compliance
│   ├── healthcare/      # HIPAA, HL7/FHIR
│   ├── government/      # FedRAMP, security
│   └── legal/           # Contract analysis
├── deployment/
│   ├── docker/          # Docker configs
│   ├── kubernetes/      # K8s manifests
│   └── airgapped/       # Air-gapped deployment
├── configs/
│   └── roles/           # Role definitions (YAML)
├── api/                 # REST API
├── data/
│   ├── training/        # Training datasets
│   └── knowledge/       # RAG knowledge bases
└── tests/               # Test suite
```

## Supported Verticals

| Vertical | Compliance | Specializations |
|----------|------------|-----------------|
| FinTech | PCI-DSS, RBI, SEBI | Payments, Banking APIs, UPI |
| Healthcare | HIPAA, HL7, FHIR | Medical records, Clinical |
| Government | FedRAMP, Security | Procurement, Public services |
| Legal | Contract law | Document analysis, Compliance |

## License

Apache 2.0 - Commercial use allowed

---

Built with Qwen2.5-Coder (Apache 2.0)
