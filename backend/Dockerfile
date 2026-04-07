FROM nvidia/cuda:12.1.0-cudnn8-devel-ubuntu22.04

# Set non-interactive to avoid tzdata prompt
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-dev \
    curl \
    git \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Clone the TripoSR repository directly into the container
RUN git clone https://github.com/VAST-AI-Research/TripoSR.git /app/TripoSR
RUN pip3 install --no-cache-dir ninja setuptools
RUN pip3 install --no-cache-dir -r /app/TripoSR/requirements.txt
ENV PYTHONPATH="/app/TripoSR:${PYTHONPATH}"

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
