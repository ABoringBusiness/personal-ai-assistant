FROM python:3.10-slim

WORKDIR /app

# Install build dependencies and runtime dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    sqlite3 \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Create directory for SQLite database
RUN mkdir -p /app/db

# Script for handling OAuth flow
RUN echo '#!/bin/bash\n\
echo "Checking if credentials.json exists..."\n\
if [ ! -f "/app/credentials.json" ]; then\n\
  echo "ERROR: credentials.json not found. Please place your Google OAuth credentials in the project directory."\n\
  exit 1\n\
fi\n\
\n\
echo "Starting AI Personal Assistant..."\n\
exec python app.py\n\
' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Define environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Create a non-root user to run the application
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Use the entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"] 