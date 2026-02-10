FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    portaudio19-dev \
    python3-pyaudio \
    alsa-utils \
    espeak \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download Whisper model during build
RUN python -c "import whisper; whisper.load_model('medium.en')"

# Copy application code
COPY src/ ./src/
COPY config/ ./config/

# Create necessary directories
RUN mkdir -p logs data/samples

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

# Expose ports (if needed for API/metrics)
EXPOSE 8000 9090

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import sys; sys.exit(0)" || exit 1

# Run application
CMD ["python", "src/main.py"]
