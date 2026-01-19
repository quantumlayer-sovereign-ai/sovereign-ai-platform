"""
Intelligent Task Analyzer
=========================
Analyzes tasks to determine complexity, type, and required agents.

Features:
- Task complexity detection (simple, medium, complex)
- Task type classification (full-stack, API, data, security, etc.)
- Intelligent agent selection based on task patterns
- Semantic matching for enhanced agent selection
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import structlog

logger = structlog.get_logger()


class TaskComplexity(Enum):
    """Task complexity levels."""
    SIMPLE = "simple"      # Single component, straightforward
    MEDIUM = "medium"      # Multiple components, some integration
    COMPLEX = "complex"    # Full system, multiple layers, high requirements


class TaskType(Enum):
    """Task type classification."""
    FULL_STACK = "full_stack"          # Frontend + Backend + Database
    API = "api"                         # REST/GraphQL API
    FRONTEND = "frontend"               # UI/UX only
    BACKEND = "backend"                 # Server-side only
    DATABASE = "database"               # Data modeling/queries
    DATA_PIPELINE = "data_pipeline"     # ETL, data processing
    SECURITY = "security"               # Security review/implementation
    INFRASTRUCTURE = "infrastructure"   # DevOps, deployment
    UTILITY = "utility"                 # Simple function/script
    REFACTOR = "refactor"               # Code improvement
    BUG_FIX = "bug_fix"                 # Fixing issues
    DOCUMENTATION = "documentation"     # Docs only
    UNKNOWN = "unknown"


@dataclass
class TaskAnalysis:
    """Result of task analysis."""
    complexity: TaskComplexity
    task_type: TaskType
    recommended_agents: list[str]
    detected_components: list[str]
    compliance_needs: list[str]
    reasoning: str
    confidence: float = 0.8


# Task type patterns - maps keywords/phrases to task types
TASK_TYPE_PATTERNS: dict[TaskType, list[str]] = {
    TaskType.FULL_STACK: [
        "full-stack", "fullstack", "full stack",
        "frontend and backend", "front-end and back-end",
        "react.*api", "vue.*api", "angular.*api",
        "web application", "web app",
        "e-commerce", "ecommerce",
        "saas", "platform",
    ],
    TaskType.API: [
        "rest api", "restful api", "graphql",
        "api endpoint", "microservice",
        "webhook", "api gateway",
        "crud api", "backend api",
    ],
    TaskType.FRONTEND: [
        "react component", "vue component", "angular component",
        "ui component", "user interface",
        "dashboard", "landing page",
        "form validation", "responsive design",
    ],
    TaskType.BACKEND: [
        "backend service", "server-side",
        "business logic", "service layer",
        "worker", "queue processor",
        "scheduler", "cron job",
    ],
    TaskType.DATABASE: [
        "database schema", "data model",
        "sql query", "migration",
        "postgresql", "mysql", "mongodb",
        "orm", "sqlalchemy",
    ],
    TaskType.DATA_PIPELINE: [
        "etl", "data pipeline",
        "data processing", "batch processing",
        "stream processing", "kafka",
        "data transformation", "data ingestion",
    ],
    TaskType.SECURITY: [
        "security review", "vulnerability",
        "penetration test", "security audit",
        "authentication", "authorization",
        "encryption", "oauth", "jwt",
        "access control", "rbac",
    ],
    TaskType.INFRASTRUCTURE: [
        "deploy", "kubernetes", "docker",
        "terraform", "infrastructure",
        "ci/cd", "pipeline",
        "monitoring", "logging",
    ],
    TaskType.UTILITY: [
        "utility function", "helper",
        "script", "simple function",
        "convert", "parse", "format",
        "validate email", "mask",
    ],
    TaskType.REFACTOR: [
        "refactor", "improve", "optimize",
        "clean up", "restructure",
        "performance improvement",
    ],
    TaskType.BUG_FIX: [
        "fix bug", "debug", "fix issue",
        "resolve error", "patch",
    ],
    TaskType.DOCUMENTATION: [
        "document", "readme", "api docs",
        "write documentation", "swagger",
    ],
}

# Agent combinations for each task type (using base role names)
# These will be mapped to vertical-specific roles when applicable
TASK_TYPE_AGENTS: dict[TaskType, dict[TaskComplexity, list[str]]] = {
    TaskType.FULL_STACK: {
        TaskComplexity.SIMPLE: ["coder", "tester"],
        TaskComplexity.MEDIUM: ["architect", "coder", "tester", "reviewer"],
        TaskComplexity.COMPLEX: ["architect", "coder", "security", "tester", "reviewer"],
    },
    TaskType.API: {
        TaskComplexity.SIMPLE: ["coder", "tester"],
        TaskComplexity.MEDIUM: ["coder", "security", "tester"],
        TaskComplexity.COMPLEX: ["architect", "coder", "security", "tester", "reviewer"],
    },
    TaskType.FRONTEND: {
        TaskComplexity.SIMPLE: ["coder"],
        TaskComplexity.MEDIUM: ["coder", "tester"],
        TaskComplexity.COMPLEX: ["architect", "coder", "tester", "reviewer"],
    },
    TaskType.BACKEND: {
        TaskComplexity.SIMPLE: ["coder", "tester"],
        TaskComplexity.MEDIUM: ["coder", "security", "tester"],
        TaskComplexity.COMPLEX: ["architect", "coder", "security", "tester", "reviewer"],
    },
    TaskType.DATABASE: {
        TaskComplexity.SIMPLE: ["coder"],
        TaskComplexity.MEDIUM: ["architect", "coder"],
        TaskComplexity.COMPLEX: ["architect", "coder", "security", "reviewer"],
    },
    TaskType.DATA_PIPELINE: {
        TaskComplexity.SIMPLE: ["coder", "tester"],
        TaskComplexity.MEDIUM: ["architect", "coder", "tester"],
        TaskComplexity.COMPLEX: ["architect", "coder", "security", "tester", "reviewer"],
    },
    TaskType.SECURITY: {
        TaskComplexity.SIMPLE: ["security"],
        TaskComplexity.MEDIUM: ["security", "reviewer"],
        TaskComplexity.COMPLEX: ["architect", "security", "reviewer"],
    },
    TaskType.INFRASTRUCTURE: {
        TaskComplexity.SIMPLE: ["devops"],
        TaskComplexity.MEDIUM: ["devops", "security"],
        TaskComplexity.COMPLEX: ["architect", "devops", "security", "reviewer"],
    },
    TaskType.UTILITY: {
        TaskComplexity.SIMPLE: ["coder"],
        TaskComplexity.MEDIUM: ["coder", "tester"],
        TaskComplexity.COMPLEX: ["coder", "tester", "reviewer"],
    },
    TaskType.REFACTOR: {
        TaskComplexity.SIMPLE: ["coder"],
        TaskComplexity.MEDIUM: ["coder", "reviewer"],
        TaskComplexity.COMPLEX: ["architect", "coder", "tester", "reviewer"],
    },
    TaskType.BUG_FIX: {
        TaskComplexity.SIMPLE: ["coder"],
        TaskComplexity.MEDIUM: ["coder", "tester"],
        TaskComplexity.COMPLEX: ["coder", "tester", "reviewer"],
    },
    TaskType.DOCUMENTATION: {
        TaskComplexity.SIMPLE: ["documenter"],
        TaskComplexity.MEDIUM: ["documenter", "reviewer"],
        TaskComplexity.COMPLEX: ["architect", "documenter", "reviewer"],
    },
    TaskType.UNKNOWN: {
        TaskComplexity.SIMPLE: ["coder"],
        TaskComplexity.MEDIUM: ["coder", "tester"],
        TaskComplexity.COMPLEX: ["architect", "coder", "tester", "reviewer"],
    },
}

# Vertical-specific role mappings
# Maps base role names to vertical-specific role names
VERTICAL_ROLE_MAPPINGS: dict[str, dict[str, str]] = {
    "fintech": {
        "architect": "fintech_architect",
        "coder": "fintech_coder",
        "security": "fintech_security",
        "tester": "fintech_tester",
        # These roles don't have fintech equivalents, use base
        "reviewer": "reviewer",
        "devops": "devops",
        "documenter": "documenter",
    },
}

# Complexity indicators
COMPLEXITY_INDICATORS = {
    "high": [
        "production", "enterprise", "scalable", "distributed",
        "microservice", "multi-tenant", "high availability",
        "pci", "compliance", "gdpr", "hipaa",
        "real-time", "machine learning", "ai",
        "complete system", "full implementation",
        "shopping cart", "payment", "checkout",
        "authentication", "authorization",
    ],
    "medium": [
        "api", "database", "frontend", "backend",
        "integration", "webhook", "queue",
        "crud", "dashboard", "admin panel",
        "search", "filter", "pagination",
    ],
    "low": [
        "simple", "basic", "utility", "helper",
        "script", "function", "convert", "parse",
        "validate", "format", "mask",
    ],
}

# Component detection patterns
COMPONENT_PATTERNS = {
    "frontend": ["react", "vue", "angular", "frontend", "ui", "component", "dashboard"],
    "backend": ["fastapi", "django", "flask", "express", "backend", "api", "server"],
    "database": ["postgresql", "mysql", "mongodb", "redis", "database", "sql", "schema"],
    "auth": ["authentication", "authorization", "jwt", "oauth", "login", "signup"],
    "payment": ["payment", "stripe", "checkout", "cart", "transaction"],
    "search": ["search", "elasticsearch", "filter", "query"],
    "cache": ["redis", "cache", "memcached"],
    "queue": ["celery", "rabbitmq", "kafka", "queue", "worker"],
    "storage": ["s3", "storage", "file upload", "blob"],
}


class TaskAnalyzer:
    """
    Intelligent task analyzer for determining complexity and required agents.
    """

    def __init__(self):
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile regex patterns for efficient matching."""
        self._type_patterns: dict[TaskType, list[re.Pattern]] = {}
        for task_type, patterns in TASK_TYPE_PATTERNS.items():
            self._type_patterns[task_type] = [
                re.compile(p, re.IGNORECASE) for p in patterns
            ]

    def analyze(
        self,
        task: str,
        compliance_requirements: list[str] | None = None,
        vertical: str | None = None
    ) -> TaskAnalysis:
        """
        Analyze a task to determine complexity, type, and required agents.

        Args:
            task: Task description
            compliance_requirements: Optional compliance requirements
            vertical: Optional vertical (fintech, healthcare, etc.)

        Returns:
            TaskAnalysis with recommendations
        """
        task_lower = task.lower()
        compliance_requirements = compliance_requirements or []

        # Detect task type
        task_type, type_confidence = self._detect_task_type(task_lower)

        # Detect components
        components = self._detect_components(task_lower)

        # Detect complexity
        complexity = self._detect_complexity(task_lower, components, compliance_requirements)

        # Get recommended agents (with vertical-specific mapping)
        agents = self._get_recommended_agents(task_type, complexity, components, compliance_requirements, vertical)

        # Detect compliance needs
        compliance_needs = self._detect_compliance_needs(task_lower, compliance_requirements)

        # Generate reasoning
        reasoning = self._generate_reasoning(task_type, complexity, components, agents)

        logger.info(
            "task_analyzed",
            task_type=task_type.value,
            complexity=complexity.value,
            agents=agents,
            components=components,
            confidence=type_confidence,
        )

        return TaskAnalysis(
            complexity=complexity,
            task_type=task_type,
            recommended_agents=agents,
            detected_components=components,
            compliance_needs=compliance_needs,
            reasoning=reasoning,
            confidence=type_confidence,
        )

    def _detect_task_type(self, task: str) -> tuple[TaskType, float]:
        """Detect the type of task."""
        best_match = TaskType.UNKNOWN
        best_score = 0.0

        for task_type, patterns in self._type_patterns.items():
            for pattern in patterns:
                if pattern.search(task):
                    # Calculate score based on pattern specificity
                    score = len(pattern.pattern) / 50.0  # Normalize
                    if score > best_score:
                        best_score = score
                        best_match = task_type

        # Clamp confidence
        confidence = min(0.95, max(0.5, best_score + 0.5))

        return best_match, confidence

    def _detect_components(self, task: str) -> list[str]:
        """Detect components mentioned in the task."""
        components = []
        for component, patterns in COMPONENT_PATTERNS.items():
            for pattern in patterns:
                if pattern in task:
                    components.append(component)
                    break
        return components

    def _detect_complexity(
        self,
        task: str,
        components: list[str],
        compliance_requirements: list[str]
    ) -> TaskComplexity:
        """Detect task complexity."""
        high_score = 0
        medium_score = 0
        low_score = 0

        # Check indicators
        for indicator in COMPLEXITY_INDICATORS["high"]:
            if indicator in task:
                high_score += 1

        for indicator in COMPLEXITY_INDICATORS["medium"]:
            if indicator in task:
                medium_score += 1

        for indicator in COMPLEXITY_INDICATORS["low"]:
            if indicator in task:
                low_score += 1

        # Factor in components
        if len(components) >= 4:
            high_score += 2
        elif len(components) >= 2:
            medium_score += 1

        # Factor in compliance requirements
        if compliance_requirements:
            high_score += len(compliance_requirements)

        # Factor in task length (longer tasks tend to be more complex)
        if len(task) > 200:
            high_score += 1
        elif len(task) > 100:
            medium_score += 1

        # Determine complexity
        if high_score >= 2 or (high_score >= 1 and len(components) >= 3):
            return TaskComplexity.COMPLEX
        elif medium_score >= 2 or high_score >= 1:
            return TaskComplexity.MEDIUM
        else:
            return TaskComplexity.SIMPLE

    def _get_recommended_agents(
        self,
        task_type: TaskType,
        complexity: TaskComplexity,
        components: list[str],
        compliance_requirements: list[str],
        vertical: str | None = None
    ) -> list[str]:
        """Get recommended agents based on task analysis."""
        # Get base agents for task type and complexity
        base_agents = TASK_TYPE_AGENTS.get(task_type, TASK_TYPE_AGENTS[TaskType.UNKNOWN])
        agents = list(base_agents.get(complexity, base_agents[TaskComplexity.SIMPLE]))

        # Add security agent if auth/payment components detected
        if any(c in components for c in ["auth", "payment"]) and "security" not in agents:
            agents.append("security")

        # Add devops for infrastructure-related tasks
        if "infrastructure" in components or task_type == TaskType.INFRASTRUCTURE:
            if "devops" not in agents:
                agents.append("devops")

        # Apply vertical-specific role mappings
        if vertical and vertical in VERTICAL_ROLE_MAPPINGS:
            role_mapping = VERTICAL_ROLE_MAPPINGS[vertical]
            mapped_agents = []
            for agent in agents:
                # Map to vertical-specific role if available
                mapped_role = role_mapping.get(agent, agent)
                mapped_agents.append(mapped_role)
            agents = mapped_agents

        # Ensure unique agents
        seen = set()
        unique_agents = []
        for agent in agents:
            if agent not in seen:
                seen.add(agent)
                unique_agents.append(agent)

        return unique_agents

    def _detect_compliance_needs(self, task: str, requirements: list[str]) -> list[str]:
        """Detect compliance needs from task and requirements."""
        needs = list(requirements)

        # Auto-detect compliance needs from task
        compliance_keywords = {
            "pci": ["payment", "credit card", "transaction", "checkout"],
            "gdpr": ["personal data", "user data", "privacy", "consent"],
            "hipaa": ["health", "medical", "patient"],
            "soc2": ["audit", "security controls"],
        }

        for compliance, keywords in compliance_keywords.items():
            if any(kw in task for kw in keywords) and compliance not in needs:
                needs.append(compliance)

        return needs

    def _generate_reasoning(
        self,
        task_type: TaskType,
        complexity: TaskComplexity,
        components: list[str],
        agents: list[str]
    ) -> str:
        """Generate human-readable reasoning for the analysis."""
        parts = [
            f"Task classified as {task_type.value} with {complexity.value} complexity.",
        ]

        if components:
            parts.append(f"Detected components: {', '.join(components)}.")

        parts.append(f"Recommended {len(agents)} agents: {', '.join(agents)}.")

        return " ".join(parts)


# Global analyzer instance
_analyzer: TaskAnalyzer | None = None


def get_analyzer() -> TaskAnalyzer:
    """Get the global task analyzer."""
    global _analyzer
    if _analyzer is None:
        _analyzer = TaskAnalyzer()
    return _analyzer
