"""
Sovereign AI Platform - REST API

Enterprise API for regulated industries with:
- Multi-agent task execution
- Compliance checking
- Audit logging
- Rate limiting
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import structlog

from core.models.qwen import QwenModel
from core.orchestrator.main import Orchestrator
from core.agents.registry import get_registry
from verticals.fintech import register_fintech_roles, ComplianceChecker

logger = structlog.get_logger()

# Initialize FastAPI app
app = FastAPI(
    title="Sovereign AI Platform",
    description="Enterprise AI Agents for Regulated Industries",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
model: Optional[QwenModel] = None
orchestrator: Optional[Orchestrator] = None


# Request/Response Models
class TaskRequest(BaseModel):
    task: str = Field(..., description="Task description", min_length=1)
    vertical: Optional[str] = Field("fintech", description="Industry vertical")
    compliance_requirements: Optional[List[str]] = Field(default=[], description="Compliance requirements")


class TaskResponse(BaseModel):
    task_id: str
    success: bool
    output: str
    agents_used: List[str]
    compliance_status: Dict[str, bool]
    execution_time_seconds: float


class ComplianceRequest(BaseModel):
    code: str = Field(..., description="Code to check")
    filename: Optional[str] = Field("code.py", description="Filename")
    standards: Optional[List[str]] = Field(["pci_dss", "rbi"], description="Standards to check")


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    available_roles: int
    uptime_seconds: float


# Startup time tracking
startup_time = datetime.now()


@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    global model, orchestrator

    logger.info("starting_sovereign_ai")

    # Register FinTech roles
    register_fintech_roles()
    logger.info("fintech_roles_registered")

    # Load model based on environment
    model_size = os.environ.get("MODEL_SIZE", "7b")
    quantize = os.environ.get("QUANTIZE", "true").lower() == "true"

    model = QwenModel(model_size=model_size, quantize=quantize)

    # Don't load model at startup in dev mode
    if os.environ.get("LOAD_MODEL_AT_STARTUP", "false").lower() == "true":
        model.load()

    # Initialize orchestrator
    max_agents = int(os.environ.get("MAX_AGENTS", "10"))
    default_vertical = os.environ.get("VERTICAL", "fintech")

    orchestrator = Orchestrator(
        model_interface=model if model.is_loaded else None,
        max_agents=max_agents,
        default_vertical=default_vertical
    )

    logger.info("sovereign_ai_ready",
               model_size=model_size,
               quantize=quantize,
               max_agents=max_agents)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global model
    if model and model.is_loaded:
        model.unload()
    logger.info("sovereign_ai_shutdown")


# Health endpoint
@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint"""
    registry = get_registry()
    uptime = (datetime.now() - startup_time).total_seconds()

    return HealthResponse(
        status="healthy",
        model_loaded=model.is_loaded if model else False,
        available_roles=len(registry.list_roles()),
        uptime_seconds=uptime
    )


# Load model endpoint
@app.post("/model/load")
async def load_model():
    """Load the AI model into memory"""
    global model, orchestrator

    if model.is_loaded:
        return {"status": "already_loaded", "info": model.model_info}

    model.load()
    orchestrator.model = model

    return {"status": "loaded", "info": model.model_info}


# Unload model endpoint
@app.post("/model/unload")
async def unload_model():
    """Unload the AI model from memory"""
    global model

    if not model.is_loaded:
        return {"status": "not_loaded"}

    model.unload()
    return {"status": "unloaded"}


# Model info endpoint
@app.get("/model/info")
async def model_info():
    """Get model information"""
    if not model:
        raise HTTPException(status_code=503, detail="Model not initialized")
    return model.model_info


# Execute task endpoint
@app.post("/task/execute", response_model=TaskResponse)
async def execute_task(request: TaskRequest):
    """Execute a task using AI agents"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    # Load model if not loaded
    if model and not model.is_loaded:
        model.load()
        orchestrator.model = model

    result = await orchestrator.execute(
        task=request.task,
        vertical=request.vertical,
        compliance_requirements=request.compliance_requirements
    )

    return TaskResponse(
        task_id=result.task_id,
        success=result.success,
        output=result.aggregated_output,
        agents_used=result.agents_used,
        compliance_status=result.compliance_status,
        execution_time_seconds=result.execution_time_seconds
    )


# List roles endpoint
@app.get("/roles")
async def list_roles(vertical: Optional[str] = None):
    """List available agent roles"""
    registry = get_registry()

    if vertical:
        roles = registry.get_roles_by_vertical(vertical)
    else:
        roles = registry.list_roles()

    return {
        "roles": roles,
        "count": len(roles),
        "vertical_filter": vertical
    }


# Get role details endpoint
@app.get("/roles/{role_name}")
async def get_role(role_name: str):
    """Get details for a specific role"""
    registry = get_registry()
    role = registry.get_role(role_name)

    if not role:
        raise HTTPException(status_code=404, detail=f"Role not found: {role_name}")

    return role


# Compliance check endpoint
@app.post("/compliance/check")
async def check_compliance(request: ComplianceRequest):
    """Check code for compliance issues"""
    checker = ComplianceChecker(standards=request.standards)
    report = checker.check_code(request.code, request.filename)

    return {
        "passed": report.passed,
        "summary": report.summary,
        "issues": [
            {
                "rule_id": i.rule_id,
                "rule_name": i.rule_name,
                "severity": i.severity.value,
                "description": i.description,
                "evidence": i.evidence,
                "remediation": i.remediation,
                "line_number": i.line_number
            }
            for i in report.issues
        ],
        "recommendations": report.recommendations
    }


# Orchestrator stats endpoint
@app.get("/stats")
async def get_stats():
    """Get platform statistics"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    return {
        "orchestrator": orchestrator.stats,
        "model": model.model_info if model else None,
        "uptime_seconds": (datetime.now() - startup_time).total_seconds()
    }


# Task history endpoint
@app.get("/tasks/history")
async def task_history(limit: int = 10):
    """Get task execution history"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    history = orchestrator.get_task_history()
    return {
        "tasks": history[-limit:],
        "total": len(history)
    }


# Audit trail endpoint
@app.get("/audit")
async def get_audit_trail():
    """Get complete audit trail for compliance"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    return {
        "audit_trail": orchestrator.factory.get_audit_trail(),
        "generated_at": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
