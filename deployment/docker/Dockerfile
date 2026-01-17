# Sovereign AI Platform - Docker Image
# Optimized for GPU inference with CUDA support

FROM nvidia/cuda:12.4.0-runtime-ubuntu22.04

LABEL maintainer="Sovereign AI Team"
LABEL description="Enterprise AI Platform for Regulated Industries"
LABEL version="1.0.0"

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-venv \
    python3-pip \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python3.11 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY core/ ./core/
COPY verticals/ ./verticals/
COPY api/ ./api/
COPY configs/ ./configs/

# Create non-root user for security
RUN useradd -m -u 1000 sovereign && \
    chown -R sovereign:sovereign /app
USER sovereign

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
