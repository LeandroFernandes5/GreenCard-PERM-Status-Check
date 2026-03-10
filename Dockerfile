FROM python:3.11-slim
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y cron \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright and browsers 
RUN playwright install --with-deps chromium

COPY check.py .
RUN chmod +x check.py

COPY entrypoint.sh .
# Strip Windows CRLF line endings to prevent Linux shebang failure
RUN sed -i 's/\r$//' entrypoint.sh && chmod +x entrypoint.sh

# Create log file
RUN touch /var/log/cron.log

# Run cron and the script initially
ENTRYPOINT ["/app/entrypoint.sh"]
