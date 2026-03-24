FROM python:3.11-slim

# System dependencies + Docker CLI (for controlling epoch containers)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git build-essential curl && \
    curl -fsSL https://download.docker.com/linux/static/stable/$(uname -m)/docker-27.5.1.tgz \
    | tar xz --strip-components=1 -C /usr/local/bin docker/docker && \
    rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy project code
WORKDIR /app
COPY core/ /app/core/
COPY run_swe.py /app/run_swe.py
COPY run_swe_docker.py /app/run_swe_docker.py
COPY .env /app/.env

ENTRYPOINT ["python3", "run_swe_docker.py"]
