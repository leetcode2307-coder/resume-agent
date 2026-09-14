# Use Python 3.12 slim image
FROM python:3.12-slim

# Install system dependencies, including LaTeX (XeTeX) for PDF generation
RUN apt-get update && apt-get install -y --no-install-recommends \
    texlive-xetex \
    texlive-fonts-recommended \
    texlive-plain-generic \
    texlive-latex-recommended \
    texlive-latex-extra \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml README.md ./

# Install dependencies directly into the system python
RUN uv pip install --system .

# Copy application code
COPY . .

# Create directory for generated PDFs
RUN mkdir -p generated_pdfs

# Expose ports for both FastAPI and Streamlit
EXPOSE 8000 8501
