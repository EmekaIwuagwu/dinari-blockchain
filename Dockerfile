# DinariBlockchain - Docker Container
# Dockerfile - Simple container image for blockchain node deployment

# Use Python 3.11 slim image (smaller, faster)
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for Docker layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directories
RUN mkdir -p data logs wallets

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV NODE_ENV=production

# Expose ports
EXPOSE 8333 8334 5000

# Create non-root user for security
RUN useradd -m -u 1000 Dinari && \
    chown -R Dinari:Dinari /app
USER Dinari

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Default command - start API server
CMD ["python", "app.py"]

# Alternative commands:
# For blockchain node: CMD ["python", "tools/start_node.py", "single", "$NODE_ID", "--port", "$P2P_PORT"]
# For validator: CMD ["python", "-c", "from Dinari import DinariNode; node = DinariNode('$NODE_ID'); node.start()"]
# For API only: CMD ["python", "app.py"]