# Build stage
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create a Python virtual environment
RUN python -m venv /opt/venv
# Make sure we use the virtualenv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Final stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends wait-for-it && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Make sure we use the virtualenv
ENV PATH="/opt/venv/bin:$PATH"

# Copy only necessary files (avoid copying everything)
COPY app ./app
COPY migrations ./migrations
COPY requirements.txt ./

# Make sure Python can find our app module
ENV PYTHONPATH=/app

# Create necessary directories that might not exist
RUN mkdir -p /app/scripts /app/tests

# Wait for MySQL to be ready before starting
CMD ["sh", "-c", "wait-for-it mysql:3306 -- python -m uvicorn app.main:app --host 0.0.0.0 --port 4100 --reload"]