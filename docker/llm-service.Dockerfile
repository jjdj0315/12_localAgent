FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

WORKDIR /app

# Install Python 3.11
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Install vLLM and dependencies
RUN pip3 install --no-cache-dir \
    vllm>=0.3.0 \
    fastapi>=0.109.0 \
    uvicorn[standard]>=0.27.0

# Copy LLM service code
COPY llm-service/ .

# Create models directory
RUN mkdir -p /models

# Expose port
EXPOSE 8001

# Run vLLM server
CMD ["python3", "server.py"]
