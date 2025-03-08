FROM python:3.8-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    git \
    make \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application
COPY . .

# Make scripts executable
RUN chmod +x *.sh backend/ai/*.sh backend/ai/backtesting/*.py

# Create necessary directories
RUN mkdir -p backend/ai/logs backend/ai/metrics/backtest backend/ai/config/backtest

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Set user to run the container
RUN groupadd -r arbitragex && \
    useradd -r -g arbitragex arbitragex && \
    chown -R arbitragex:arbitragex /app
USER arbitragex

# Volume for persisting data
VOLUME ["/app/backend/ai/logs", "/app/backend/ai/metrics", "/app/backend/ai/config"]

# Default command
ENTRYPOINT ["./arbitragex.sh"]
CMD ["--help"] 