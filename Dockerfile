# ============================================================
# Stage 1: Builder
# Install Python deps using uv for fast, reproducible installs
# ============================================================
FROM python:3.12-slim AS builder

# Install uv (fast Python package installer)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /build

# Copy dependency files first (layer cache)
COPY pyproject.toml uv.lock ./

# Install all dependencies into a virtual environment
RUN uv sync --frozen --no-dev --no-install-project

# ============================================================
# Stage 2: Runtime
# Slim image with only what's needed to run the app
# ============================================================
FROM python:3.12-slim AS runtime

# System dependencies:
#   - texlive-xetex: xelatex engine for LaTeX → PDF compilation
#   - texlive-latex-extra: extra LaTeX packages (geometry, hyperref, etc.)
#   - texlive-fonts-recommended: common fonts
#   - texlive-fonts-extra: FontAwesome5 and other extra fonts
#   - fontconfig: font discovery for xelatex
RUN apt-get update && apt-get install -y --no-install-recommends \
        texlive-xetex \
        texlive-latex-extra \
        texlive-fonts-recommended \
        texlive-fonts-extra \
        fontconfig \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN groupadd --gid 1001 appgroup && \
    useradd --uid 1001 --gid appgroup --shell /bin/bash --create-home appuser

WORKDIR /app

# Copy the virtual environment from the builder stage
COPY --from=builder /build/.venv /app/.venv

# Copy application source code
COPY app/ ./app/
COPY main.py ./

# Create the generated_pdfs directory and set ownership
RUN mkdir -p /app/generated_pdfs && \
    chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# Add the venv to PATH
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Expose FastAPI port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Production start command (no hot-reload)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
