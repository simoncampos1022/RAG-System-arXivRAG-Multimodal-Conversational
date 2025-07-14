FROM python:3.10-slim as builder

WORKDIR /app

# Install build dependencies and runtime dependencies 
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    # pip install --no-cache-dir -r requirements.txt
    pip install --no-cache-dir --user -r requirements.txt

# Second stage: runtime image
FROM python:3.10-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    tesseract-ocr \
    libreoffice \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy the installed packages from the builder stage
COPY --from=builder /root/.local /root/.local

# Make sure scripts in .local are usable:
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/data/temp

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

# Expose the port
EXPOSE 8000

# Healthcheck to ensure the application is running
HEALTHCHECK CMD curl --fail http://localhost:8000/health || exit 1

# Set a non-root user
RUN useradd -m appuser
RUN chown -R appuser:appuser /app
USER appuser

# Run the application
CMD ["python", "app.py"]
