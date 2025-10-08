FROM python:3.12-slim

# Install uv for faster package installation
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set the working directory in the container
WORKDIR /app

# Install system dependencies required for building packages
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Configure uv to use system Python (required for Docker)
ENV UV_SYSTEM_PYTHON=1

# Copy requirements and install dependencies using uv
COPY docker/requirements-slim.txt .
RUN uv pip install --system --no-cache -r requirements-slim.txt

# Copy source code
COPY src/ ./src/
# Documents are mounted as volume at runtime (see docker-compose.yml)

# Set environment variables
ENV PYTHONPATH=/app/src
ENV IS_TESTING=0

# Expose port
EXPOSE 8008

# Run the FastAPI service
CMD ["python", "src/api/service.py"]
