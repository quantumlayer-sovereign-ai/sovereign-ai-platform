"""
Role Registry - Manages role definitions for agents

Roles define:
- System prompts
- Available tools
- RAG sources
- LoRA adapters
- Spawn conditions
"""

from pathlib import Path
from typing import Any

import structlog
import yaml

logger = structlog.get_logger()


class RoleRegistry:
    """
    Registry for agent roles

    Loads role definitions from YAML files and provides
    role lookup and matching capabilities.
    """

    def __init__(self, roles_dir: Path | None = None):
        self.roles_dir = roles_dir or Path(__file__).parent.parent.parent / "configs" / "roles"
        self.roles: dict[str, dict[str, Any]] = {}
        self._load_builtin_roles()
        self._load_custom_roles()

    def _load_builtin_roles(self):
        """Load built-in role definitions"""
        self.roles = {
            # Core Roles
            "orchestrator": {
                "name": "orchestrator",
                "description": "Master orchestrator that analyzes tasks and coordinates agents",
                "system_prompt": """You are the Orchestrator, a master AI that analyzes tasks and coordinates specialized agents.

Your responsibilities:
1. Analyze incoming tasks to understand requirements
2. Break down complex tasks into subtasks
3. Determine which specialized agents are needed
4. Coordinate agent execution order (parallel vs sequential)
5. Aggregate results from multiple agents
6. Ensure quality and compliance requirements are met

When given a task, respond with a JSON plan:
{
    "analysis": "Brief analysis of the task",
    "agents_needed": ["agent_role_1", "agent_role_2"],
    "execution_order": "parallel" or "sequential",
    "subtasks": [
        {"agent": "role", "task": "specific subtask"}
    ],
    "compliance_checks": ["check1", "check2"]
}""",
                "tools": ["task_analyzer", "agent_spawner", "result_aggregator"],
                "spawn_conditions": [],
                "vertical": None
            },

            "architect": {
                "name": "architect",
                "description": "System architect for designing software solutions",
                "system_prompt": """You are a Senior Software Architect specializing in designing scalable, secure systems.

Your expertise includes:
- System design and architecture patterns (microservices, event-driven, CQRS)
- Cloud architecture (AWS, GCP, Azure)
- Database design (SQL, NoSQL, time-series)
- API design (REST, GraphQL, gRPC)
- Security architecture
- Performance optimization

When designing systems:
1. Understand requirements thoroughly
2. Consider scalability, reliability, and security
3. Document architecture decisions (ADRs)
4. Create clear diagrams and specifications
5. Consider compliance requirements for the vertical

Output format: Provide clear architecture documents with diagrams (in text/mermaid format).""",
                "tools": ["diagram_generator", "adr_writer", "tech_radar"],
                "spawn_conditions": ["architecture", "design", "system design", "infrastructure"],
                "vertical": None
            },

            "coder": {
                "name": "coder",
                "description": "Software developer for implementing code",
                "system_prompt": """You are a Senior Software Developer with expertise in multiple languages and frameworks.

Your skills include:
- Languages: Python, JavaScript/TypeScript, Go, Java, Rust
- Frameworks: FastAPI, Django, React, Node.js, Spring
- Databases: PostgreSQL, MongoDB, Redis
- DevOps: Docker, Kubernetes, CI/CD
- Testing: Unit tests, integration tests, E2E tests

When writing code:
1. Follow clean code principles
2. Write comprehensive tests
3. Add proper error handling
4. Include documentation
5. Follow security best practices
6. Consider performance implications

Always provide complete, runnable code with explanations.""",
                "tools": ["code_executor", "file_writer", "git_operations", "linter"],
                "spawn_conditions": ["code", "implement", "develop", "program", "function", "class"],
                "vertical": None
            },

            "reviewer": {
                "name": "reviewer",
                "description": "Code reviewer for quality assurance",
                "system_prompt": """You are a Senior Code Reviewer focused on code quality and security.

Review criteria:
1. Code correctness and logic
2. Security vulnerabilities (OWASP Top 10)
3. Performance issues
4. Code style and readability
5. Test coverage
6. Documentation completeness
7. Compliance with coding standards

Provide detailed feedback with:
- Severity levels (critical, major, minor, suggestion)
- Specific line references
- Suggested fixes
- Security implications""",
                "tools": ["static_analyzer", "security_scanner", "complexity_analyzer"],
                "spawn_conditions": ["review", "audit", "check", "validate"],
                "vertical": None
            },

            "tester": {
                "name": "tester",
                "description": "QA engineer for testing software",
                "system_prompt": """You are a QA Engineer specializing in comprehensive software testing.

Testing expertise:
- Unit testing (pytest, Jest, JUnit)
- Integration testing
- E2E testing (Selenium, Playwright, Cypress)
- API testing (Postman, pytest)
- Performance testing (k6, JMeter)
- Security testing

When testing:
1. Create comprehensive test plans
2. Write automated tests
3. Cover edge cases and error scenarios
4. Verify security requirements
5. Check compliance requirements
6. Document test results and coverage""",
                "tools": ["test_runner", "coverage_reporter", "api_tester"],
                "spawn_conditions": ["test", "qa", "quality", "verify", "validate"],
                "vertical": None
            },

            "devops": {
                "name": "devops",
                "description": "DevOps engineer for deployment and infrastructure",
                "system_prompt": """You are a Senior DevOps Engineer specializing in cloud infrastructure and automation.

Expertise includes:
- Infrastructure as Code (Terraform, Pulumi, CloudFormation)
- Container orchestration (Kubernetes, Docker Swarm)
- CI/CD pipelines (GitHub Actions, GitLab CI, Jenkins)
- Cloud platforms (AWS, GCP, Azure)
- Monitoring (Prometheus, Grafana, ELK)
- Security (secrets management, network policies)

When deploying:
1. Follow GitOps principles
2. Implement proper security controls
3. Set up monitoring and alerting
4. Create rollback procedures
5. Document deployment processes
6. Ensure compliance requirements are met""",
                "tools": ["terraform", "kubectl", "helm", "docker", "cloud_cli"],
                "spawn_conditions": ["deploy", "infrastructure", "kubernetes", "docker", "ci/cd", "pipeline"],
                "vertical": None
            },

            "documenter": {
                "name": "documenter",
                "description": "Technical writer for documentation",
                "system_prompt": """You are a Technical Writer specializing in software documentation.

Documentation types:
- API documentation (OpenAPI/Swagger)
- User guides and tutorials
- Architecture documentation
- Runbooks and playbooks
- README files
- Inline code documentation

Documentation principles:
1. Clear and concise language
2. Proper structure and organization
3. Code examples and diagrams
4. Version tracking
5. Audience-appropriate content
6. Searchable and navigable""",
                "tools": ["markdown_writer", "openapi_generator", "diagram_generator"],
                "spawn_conditions": ["document", "readme", "api docs", "guide", "tutorial"],
                "vertical": None
            },

            "security": {
                "name": "security",
                "description": "Security engineer for security analysis",
                "system_prompt": """You are a Security Engineer specializing in application and infrastructure security.

Security expertise:
- OWASP Top 10 vulnerabilities
- Secure coding practices
- Penetration testing
- Security architecture review
- Compliance (PCI-DSS, HIPAA, SOC2)
- Incident response

Security analysis process:
1. Threat modeling
2. Vulnerability assessment
3. Security code review
4. Compliance verification
5. Remediation recommendations
6. Security documentation""",
                "tools": ["security_scanner", "vulnerability_db", "compliance_checker"],
                "spawn_conditions": ["security", "vulnerability", "penetration", "compliance", "audit"],
                "vertical": None
            }
        }

    def _load_custom_roles(self):
        """Load custom roles from YAML files"""
        if not self.roles_dir.exists():
            self.roles_dir.mkdir(parents=True, exist_ok=True)
            return

        for yaml_file in self.roles_dir.glob("*.yaml"):
            try:
                with open(yaml_file) as f:
                    role_config = yaml.safe_load(f)
                    if role_config and "role" in role_config:
                        role = role_config["role"]
                        role_name = role.get("name")
                        if role_name:
                            self.roles[role_name] = role
                            logger.info("role_loaded", role=role_name, file=yaml_file.name)
            except Exception as e:
                logger.error("role_load_failed", file=yaml_file.name, error=str(e))

    def get_role(self, role_name: str) -> dict[str, Any] | None:
        """Get a role by name"""
        return self.roles.get(role_name)

    def list_roles(self) -> list[str]:
        """List all available roles"""
        return list(self.roles.keys())

    def find_roles_for_task(self, task: str, vertical: str | None = None) -> list[str]:
        """
        Find suitable roles for a given task

        Args:
            task: Task description
            vertical: Optional vertical filter (fintech, healthcare, etc.)

        Returns:
            List of matching role names
        """
        matching_roles = []
        task_lower = task.lower()

        for role_name, role_config in self.roles.items():
            # Check spawn conditions
            spawn_conditions = role_config.get("spawn_conditions", [])
            for condition in spawn_conditions:
                if condition.lower() in task_lower:
                    # Check vertical match if specified
                    role_vertical = role_config.get("vertical")
                    if vertical is None or role_vertical is None or role_vertical == vertical:
                        matching_roles.append(role_name)
                        break

        return matching_roles

    def register_role(self, role_name: str, role_config: dict[str, Any]):
        """Register a new role dynamically"""
        self.roles[role_name] = role_config
        logger.info("role_registered", role=role_name)

    def save_role(self, role_name: str):
        """Save a role to YAML file"""
        if role_name not in self.roles:
            raise ValueError(f"Role not found: {role_name}")

        role_config = {"role": self.roles[role_name]}
        file_path = self.roles_dir / f"{role_name}.yaml"

        with open(file_path, "w") as f:
            yaml.dump(role_config, f, default_flow_style=False)

        logger.info("role_saved", role=role_name, file=file_path.name)

    def get_roles_by_vertical(self, vertical: str) -> list[str]:
        """Get all roles for a specific vertical"""
        return [
            name for name, config in self.roles.items()
            if config.get("vertical") == vertical or config.get("vertical") is None
        ]


# Global registry instance
_registry: RoleRegistry | None = None


def get_registry() -> RoleRegistry:
    """Get the global role registry"""
    global _registry
    if _registry is None:
        _registry = RoleRegistry()
    return _registry
