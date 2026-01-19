"""
Sovereign AI Platform - REST API

Enterprise API for regulated industries with:
- Multi-agent task execution
- Compliance checking
- Audit logging
- Rate limiting
- Project generation and export
"""

import io
import os
import sys
import zipfile

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from pathlib import Path

import structlog
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from api.auth import JWTBearer, OptionalJWTBearer, UserContext, create_dev_token, DEV_MODE
from api.ratelimit import RateLimitDependency, release_concurrent_slot
from core.agents.registry import get_registry
from core.models.qwen import QwenModel
from core.models.azure_openai import AzureOpenAIModel, HybridModel
from core.orchestrator import RAGOrchestrator
from core.output import ProjectGenerator
from core.tools.security_tools import SecurityScanner
from verticals.fintech import ComplianceChecker, register_fintech_roles
from verticals.fintech.region import FinTechRegion, get_region_config

logger = structlog.get_logger()

# Initialize FastAPI app
app = FastAPI(
    title="Sovereign AI Platform",
    description="Enterprise AI Agents for Regulated Industries",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration - hardened for production
ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "").split(",")
if not ALLOWED_ORIGINS or ALLOWED_ORIGINS == [""]:
    # Dev default: allow localhost and common local network IPs
    ALLOWED_ORIGINS = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://192.168.1.204:3000",  # Local network
    ]
    # In dev mode, also allow any origin for easier testing
    if DEV_MODE:
        ALLOWED_ORIGINS = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
)


@app.middleware("http")
async def rate_limit_cleanup_middleware(request: Request, call_next):
    """Release rate limit concurrent slots after response"""
    response = await call_next(request)
    await release_concurrent_slot(request)
    return response


# Global instances
model: QwenModel | None = None
orchestrator: RAGOrchestrator | None = None
security_scanner: SecurityScanner | None = None
project_generator: ProjectGenerator | None = None


# Valid regions
VALID_REGIONS = ["india", "eu", "uk"]


# Request/Response Models
class TaskRequest(BaseModel):
    task: str = Field(..., description="Task description", min_length=1)
    vertical: str | None = Field("fintech", description="Industry vertical")
    region: str | None = Field("india", description="Region: india, eu, or uk")
    compliance_requirements: list[str] | None = Field(default=[], description="Compliance requirements")
    use_rag: bool | None = Field(True, description="Use RAG for context retrieval")
    generate_project: bool | None = Field(True, description="Generate project structure from code output")


class TaskResponse(BaseModel):
    task_id: str
    success: bool
    output: str
    agents_used: list[str]
    compliance_status: dict[str, bool]
    execution_time_seconds: float
    project_id: str | None = Field(None, description="Project ID if project was generated")


class ComplianceRequest(BaseModel):
    code: str = Field(..., description="Code to check")
    filename: str | None = Field("code.py", description="Filename")
    standards: list[str] | None = Field(None, description="Standards to check (auto-detected from region if not set)")
    region: str | None = Field("india", description="Region: india, eu, or uk")


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    available_roles: int
    uptime_seconds: float
    rag_enabled: bool = True


class RAGIndexRequest(BaseModel):
    directory: str = Field(..., description="Directory to index")
    vertical: str = Field("fintech", description="Vertical for the documents")


class RAGSearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    vertical: str = Field("fintech", description="Vertical to search")
    n_results: int = Field(5, description="Number of results")


class SecurityScanRequest(BaseModel):
    code: str = Field(..., description="Code to scan")
    filename: str = Field("code.py", description="Filename for reporting")


# Startup time tracking
startup_time = datetime.now()


@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    global model, orchestrator, security_scanner, project_generator

    logger.info("starting_sovereign_ai")

    # Register FinTech roles
    register_fintech_roles()
    logger.info("fintech_roles_registered")

    # Load model based on environment
    model_size = os.environ.get("MODEL_SIZE", "14b")
    quantize = os.environ.get("QUANTIZE", "true").lower() == "true"
    use_hybrid = os.environ.get("USE_HYBRID_MODEL", "false").lower() == "true"

    # Initialize local model
    local_model = QwenModel(model_size=model_size, quantize=quantize)

    # Check if Azure OpenAI is configured
    azure_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
    azure_key = os.environ.get("AZURE_OPENAI_API_KEY")
    azure_deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1")

    if use_hybrid and azure_endpoint and azure_key:
        # Use hybrid model (local + Azure)
        azure_model = AzureOpenAIModel(
            endpoint=azure_endpoint,
            api_key=azure_key,
            deployment=azure_deployment,
        )
        complexity_threshold = int(os.environ.get("COMPLEXITY_THRESHOLD", "500"))
        model = HybridModel(
            local_model=local_model,
            azure_model=azure_model,
            complexity_threshold=complexity_threshold,
        )
        logger.info("hybrid_model_configured", azure_deployment=azure_deployment)
    else:
        model = local_model
        if use_hybrid:
            logger.warning("hybrid_requested_but_azure_not_configured")

    # Don't load model at startup in dev mode
    if os.environ.get("LOAD_MODEL_AT_STARTUP", "false").lower() == "true":
        model.load()

    # Initialize RAG-enhanced orchestrator
    max_agents = int(os.environ.get("MAX_AGENTS", "10"))
    default_vertical = os.environ.get("VERTICAL", "fintech")
    rag_persist_dir = os.environ.get("RAG_PERSIST_DIR", "./data/vectordb")

    orchestrator = RAGOrchestrator(
        model_interface=model if model.is_loaded else None,
        max_agents=max_agents,
        default_vertical=default_vertical,
        rag_persist_dir=rag_persist_dir
    )

    # Initialize security scanner
    security_scanner = SecurityScanner()

    # Initialize project generator
    projects_dir = os.environ.get("PROJECTS_DIR", "./projects")
    project_generator = ProjectGenerator(base_dir=projects_dir)

    logger.info("sovereign_ai_ready",
               model_size=model_size,
               quantize=quantize,
               max_agents=max_agents,
               rag_enabled=True,
               projects_dir=projects_dir)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global model
    if model and model.is_loaded:
        model.unload()
    logger.info("sovereign_ai_shutdown")


# Health endpoint (public - no auth required)
@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint"""
    registry = get_registry()
    uptime = (datetime.now() - startup_time).total_seconds()

    return HealthResponse(
        status="healthy",
        model_loaded=model.is_loaded if model else False,
        available_roles=len(registry.list_roles()),
        uptime_seconds=uptime,
        rag_enabled=True
    )


# Auth token endpoint (dev mode only)
class TokenRequest(BaseModel):
    user_id: str = Field("dev-user", description="User ID for the token")
    email: str = Field("dev@example.com", description="Email for the token")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


@app.post("/auth/token", response_model=TokenResponse)
async def get_token(request: TokenRequest):
    """
    Generate a JWT token (dev mode only)

    This endpoint is only available when DEV_MODE=true
    """
    return create_dev_token(user_id=request.user_id, email=request.email)


# Load model endpoint (protected)
@app.post("/model/load")
async def load_model(user: UserContext = Depends(JWTBearer())):
    """Load the AI model into memory"""
    global model, orchestrator

    if model.is_loaded:
        return {"status": "already_loaded", "info": model.model_info}

    model.load()
    orchestrator.model = model
    orchestrator.factory.model_interface = model  # Also update factory

    return {"status": "loaded", "info": model.model_info}


# Unload model endpoint (protected)
@app.post("/model/unload")
async def unload_model(user: UserContext = Depends(JWTBearer())):
    """Unload the AI model from memory"""
    global model

    if not model.is_loaded:
        return {"status": "not_loaded"}

    model.unload()
    return {"status": "unloaded"}


# Model info endpoint (protected)
@app.get("/model/info")
async def model_info(user: UserContext = Depends(JWTBearer())):
    """Get model information"""
    if not model:
        raise HTTPException(status_code=503, detail="Model not initialized")
    return model.model_info


# Execute task endpoint (protected + rate limited)
@app.post("/task/execute", response_model=TaskResponse)
async def execute_task(
    request: TaskRequest,
    user: UserContext = Depends(JWTBearer()),
    rate_limit: dict = Depends(RateLimitDependency(check_concurrent=True))
):
    """Execute a task using AI agents"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    # Validate region
    region = (request.region or "india").lower()
    if region not in VALID_REGIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid region: {region}. Must be one of: {VALID_REGIONS}"
        )

    # Load model if not loaded
    if model and not model.is_loaded:
        model.load()
        orchestrator.model = model
        orchestrator.factory.model_interface = model  # Also update factory

    result = await orchestrator.execute(
        task=request.task,
        vertical=request.vertical,
        region=region,
        compliance_requirements=request.compliance_requirements,
        use_rag=request.use_rag
    )

    # Generate project structure if requested
    project_id = None
    if request.generate_project and result.success and project_generator:
        try:
            manifest = await project_generator.generate(
                task_id=result.task_id,
                results=result.results,
                task=request.task,
                agents_used=result.agents_used,
            )
            project_id = manifest.task_id
        except Exception as e:
            logger.warning("project_generation_failed", error=str(e))

    return TaskResponse(
        task_id=result.task_id,
        success=result.success,
        output=result.aggregated_output,
        agents_used=result.agents_used,
        compliance_status=result.compliance_status,
        execution_time_seconds=result.execution_time_seconds,
        project_id=project_id,
    )


# List roles endpoint (protected)
@app.get("/roles")
async def list_roles(
    vertical: str | None = None,
    region: str | None = None,
    user: UserContext | None = Depends(OptionalJWTBearer())
):
    """List available agent roles (public endpoint)"""
    registry = get_registry()

    roles = registry.get_roles_by_vertical(vertical) if vertical else registry.list_roles()

    # Filter by region if specified
    if region:
        region = region.lower()
        if region == "india":
            # India roles don't have prefix
            roles = [r for r in roles if not r.startswith(("eu_", "uk_"))]
        elif region in ("eu", "uk"):
            roles = [r for r in roles if r.startswith(f"{region}_")]

    return {
        "roles": roles,
        "count": len(roles),
        "vertical_filter": vertical,
        "region_filter": region
    }


# Get role details endpoint (protected)
@app.get("/roles/{role_name}")
async def get_role(role_name: str, user: UserContext = Depends(JWTBearer())):
    """Get details for a specific role"""
    registry = get_registry()
    role = registry.get_role(role_name)

    if not role:
        raise HTTPException(status_code=404, detail=f"Role not found: {role_name}")

    return role


# Compliance check endpoint (protected + rate limited)
@app.post("/compliance/check")
async def check_compliance(
    request: ComplianceRequest,
    user: UserContext = Depends(JWTBearer()),
    rate_limit: dict = Depends(RateLimitDependency())
):
    """Check code for compliance issues"""
    # Validate region
    region = (request.region or "india").lower()
    if region not in VALID_REGIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid region: {region}. Must be one of: {VALID_REGIONS}"
        )

    # Get region-appropriate standards if not specified
    standards = request.standards
    if not standards:
        region_config = get_region_config(region)
        standards = region_config.compliance_standards

    checker = ComplianceChecker(standards=standards, region=region)
    report = checker.check_code(request.code, request.filename)

    return {
        "passed": report.passed,
        "summary": report.summary,
        "region": region,
        "standards_checked": standards,
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


# Orchestrator stats endpoint (protected)
@app.get("/stats")
async def get_stats(user: UserContext = Depends(JWTBearer())):
    """Get platform statistics"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    return {
        "orchestrator": orchestrator.stats,
        "model": model.model_info if model else None,
        "uptime_seconds": (datetime.now() - startup_time).total_seconds()
    }


# Task history endpoint (protected)
@app.get("/tasks/history")
async def task_history(limit: int = 10, user: UserContext = Depends(JWTBearer())):
    """Get task execution history"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    history = orchestrator.get_task_history()
    return {
        "tasks": history[-limit:],
        "total": len(history)
    }


# Audit trail endpoint (protected)
@app.get("/audit")
async def get_audit_trail(user: UserContext = Depends(JWTBearer())):
    """Get complete audit trail for compliance"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    return {
        "audit_trail": orchestrator.factory.get_audit_trail(),
        "generated_at": datetime.now().isoformat()
    }


# RAG endpoints (protected)
@app.post("/rag/index")
async def index_knowledge_base(
    request: RAGIndexRequest,
    user: UserContext = Depends(JWTBearer())
):
    """Index documents into the RAG knowledge base"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    try:
        result = await orchestrator.index_knowledge_base(
            directory=request.directory,
            vertical=request.vertical
        )
        return {
            "status": "indexed",
            "directory": request.directory,
            "vertical": request.vertical,
            "chunks_indexed": result.get("chunks_indexed", 0)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/rag/search")
async def search_knowledge(
    request: RAGSearchRequest,
    user: UserContext = Depends(JWTBearer()),
    rate_limit: dict = Depends(RateLimitDependency())
):
    """Search the RAG knowledge base"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    try:
        results = await orchestrator.search_knowledge(
            query=request.query,
            vertical=request.vertical,
            n_results=request.n_results
        )
        return {
            "query": request.query,
            "vertical": request.vertical,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/rag/stats")
async def rag_stats(user: UserContext = Depends(JWTBearer())):
    """Get RAG pipeline statistics"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    return orchestrator.get_rag_stats()


# Security scanning endpoint (protected + rate limited)
@app.post("/security/scan")
async def scan_code(
    request: SecurityScanRequest,
    user: UserContext = Depends(JWTBearer()),
    rate_limit: dict = Depends(RateLimitDependency())
):
    """Scan code for security vulnerabilities"""
    if not security_scanner:
        raise HTTPException(status_code=503, detail="Security scanner not initialized")

    result = security_scanner.scan_code(request.code, request.filename)
    return result


# Project endpoints
class ProjectFileResponse(BaseModel):
    path: str
    content: str
    language: str
    size: int


class ProjectManifestResponse(BaseModel):
    task_id: str
    task: str
    created_at: str
    files: list[dict]
    agents_used: list[str]
    total_files: int
    total_size: int


@app.get("/projects")
async def list_projects(user: UserContext = Depends(JWTBearer())):
    """List all generated projects"""
    if not project_generator:
        raise HTTPException(status_code=503, detail="Project generator not initialized")

    return {"projects": project_generator.list_projects()}


@app.get("/projects/{task_id}", response_model=ProjectManifestResponse)
async def get_project(task_id: str, user: UserContext = Depends(JWTBearer())):
    """Get project manifest and file list"""
    if not project_generator:
        raise HTTPException(status_code=503, detail="Project generator not initialized")

    manifest = await project_generator.get_project(task_id)
    if not manifest:
        raise HTTPException(status_code=404, detail=f"Project not found: {task_id}")

    return ProjectManifestResponse(
        task_id=manifest.task_id,
        task=manifest.task,
        created_at=manifest.created_at.isoformat(),
        files=[{"path": f.path, "language": f.language, "size": f.size} for f in manifest.files],
        agents_used=manifest.agents_used,
        total_files=manifest.total_files,
        total_size=manifest.total_size,
    )


@app.get("/projects/{task_id}/files/{path:path}", response_model=ProjectFileResponse)
async def get_project_file(
    task_id: str,
    path: str,
    user: UserContext = Depends(JWTBearer())
):
    """Get single file content from a project"""
    if not project_generator:
        raise HTTPException(status_code=503, detail="Project generator not initialized")

    file = await project_generator.get_file(task_id, path)
    if not file:
        raise HTTPException(status_code=404, detail=f"File not found: {path}")

    return ProjectFileResponse(
        path=file.path,
        content=file.content,
        language=file.language,
        size=file.size,
    )


@app.get("/projects/{task_id}/download")
async def download_project(task_id: str, user: UserContext = Depends(JWTBearer())):
    """Download project as ZIP file"""
    if not project_generator:
        raise HTTPException(status_code=503, detail="Project generator not initialized")

    project_path = Path(project_generator.base_dir) / task_id

    if not project_path.exists():
        raise HTTPException(status_code=404, detail=f"Project not found: {task_id}")

    # Create ZIP in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file in project_path.rglob('*'):
            if file.is_file():
                zf.write(file, file.relative_to(project_path))

    zip_buffer.seek(0)

    return StreamingResponse(
        zip_buffer,
        media_type='application/zip',
        headers={'Content-Disposition': f'attachment; filename="{task_id}.zip"'}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
