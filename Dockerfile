# NoiseSignal Docker Container
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    cron \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY *.py ./
COPY .env .
COPY secret.json .
COPY token.pickle .
COPY *.html .
COPY *.csv .
COPY *.txt .
COPY data/ ./data/
COPY scripts/ ./scripts/

# Create necessary directories
RUN mkdir -p /app/data/logs

# Make scripts executable
RUN chmod +x scripts/*.sh

# Set up log file for cron
RUN touch /var/log/cron.log

# Copy cron configuration
COPY scripts/crontab /etc/cron.d/noisesignal-cron

# Give execution rights on the cron job
RUN chmod 0644 /etc/cron.d/noisesignal-cron

# Apply cron job
RUN crontab /etc/cron.d/noisesignal-cron

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose port for potential health checks
EXPOSE 8080

# Start cron daemon and tail logs
CMD ["sh", "-c", "cron && tail -f /var/log/cron.log"]