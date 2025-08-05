# Use official minimal base image (Best Practice #1)
FROM python:3.11-slim

# Install system dependencies including Deno and clean up in same layer (Best Practice #3 & #4)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        unzip \
        supervisor && \
    # Install Deno with explicit environment variable
    curl -fsSL https://deno.land/install.sh | DENO_INSTALL=/usr/local sh && \
    # Clean up
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user (Best Practice #2)
RUN useradd -m -u 1000 appuser

# Set working directory
WORKDIR /app

# Copy requirements first for better caching (Best Practice #5)
COPY requirements.txt .

# Install Python dependencies as root (needed for some packages)
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Copy supervisor configuration and startup script
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY start.sh /app/start.sh

# Make startup script executable and change ownership
RUN chmod +x /app/start.sh && \
    chown -R appuser:appuser /app

# Note: We don't switch to non-root user here because supervisord needs root privileges
# The individual processes will run as appuser as specified in supervisord.conf

# Expose ports for both services
EXPOSE 8001 3001

# Add health check (Best Practice #7) - check both services
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8001/health && curl -f http://localhost:3001 || exit 1

# Run the startup script
CMD ["/app/start.sh"]