# Use full Debian base with Python
FROM python:3.11

# Set DNS fallback
#RUN echo "nameserver 9.9.9.9" > /etc/resolv.conf

# Install required packages
RUN apt-get update && \
    apt-get install -y ffmpeg cron && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy source code
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Entrypoint
ENTRYPOINT ["./entrypoint.sh"]
