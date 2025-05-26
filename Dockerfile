# Stage 1: Builder
FROM python:3.9-slim as builder

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Install build dependencies if any (e.g., for compiling certain packages)
# RUN apt-get update && apt-get install -y --no-install-recommends gcc

# Copy requirements and build wheels
COPY requirements.txt .
# If you have a requirements-dev.txt for build tools, copy it too
# COPY requirements-dev.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Stage 2: Final image
FROM python:3.9-slim

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Create a non-root user and group
RUN groupadd -r appuser && useradd -r -g appuser -d /home/appuser -s /sbin/nologin -c "Application User" appuser

# Create work directory for the non-root user
WORKDIR /home/appuser/app

# Copy built wheels from the builder stage
COPY --from=builder /app/wheels /wheels

# Install the wheels
# Ensure pip is available; it should be in python:3.9-slim
RUN pip install --no-cache /wheels/*

# Copy the application source code
# Ensure correct ownership if USER was switched earlier, or copy then chown
COPY . .
RUN chown -R appuser:appuser /home/appuser/app

# Switch to the non-root user
USER appuser

# Expose the port the app runs on
EXPOSE 8000

# Define environment variables that can be overridden at runtime
# These are examples; sensitive values should NOT be hardcoded here.
# ENV DEBUG="False"
# ENV DATABASE_URL="" 
# ENV JWT_SECRET_KEY=""
# Add other necessary runtime ENV variables with empty defaults or placeholders

# Command to run the application
# Default to running main:app. Ensure main.py and app object are correctly located.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
