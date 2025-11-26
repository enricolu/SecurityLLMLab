# Containerized runtime for Security LLM Lab
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install system dependencies
RUN apt-get update \ 
    && apt-get install -y --no-install-recommends build-essential curl \ 
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY security_llm_lab ./security_llm_lab
COPY main.py ./main.py

RUN pip install --upgrade pip \
    && pip install .

# Default workspace mount
VOLUME ["/workspace"]
ENV ENABLE_PIPELINE_METRICS=0

CMD ["python", "main.py", "--help"]
