# Boosted3D

Boosted3D is a high-performance AI-to-3D model generation pipeline explicitly designed for Unreal Engine 5.5 integration. Optimized for NVIDIA H100 hardware, it provides rapid geometry conversion, automated UV unwrapping, and direct exports to game-ready formats with a user-friendly web interface.

## Features

- **Unreal Engine 5.5 Ready**: Automatically transforms generated meshes to **Z-Up, Left-Handed** coordinate space.
- **High-Performance Inference**: Backend tailored for H100 hardware utilizing BF16/FP16 limits and TensorRT/AOT compilation.
- **Multiple Export Formats**: Supports FBX Binary (with embedded PBR textures) and GLB/glTF 2.0.
- **Topology Personalization**: Target specific poly counts and choose between Nanite High-Fidelity, Deformable, or Proxy meshes.
- **Interactive Web UI**: A fully functional Gradio frontend featuring a live 3D visualizer.

## Architecture

The project is containerized using Docker and Docker Compose, split into three main services:
- **`frontend/`**: Gradio-based web user interface for uploading images and viewing/downloading generated 3D models.
- **`backend/`**: FastAPI hardware-accelerated microservice executing the machine learning inference and geometry generation/cleaning (trimesh, PyTorch).
- **`nginx/`**: Reverse proxy handling web traffic and routing.

## Prerequisites

- Ubuntu 24.04 LTS (Recommended)
- NVIDIA GPU (H100 recommended for optimal ML inference speed)
- Docker & Docker Compose
- NVIDIA Container Toolkit

## Getting Started

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Hawordd/Boosted3D.git
   cd Boosted3D
   ```

2. **Run the setup script:**
   The `setup.sh` script prepares the environment, sets up necessary directories, and configures permissions.
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

3. **Launch the services:**
   Build and start the containerized application using Docker Compose.
   ```bash
   docker-compose up --build -d
   ```

4. **Access the Web Interface:**
   Once the containers are running, access the web UI via your browser to start generating models.

## Development

- Avoid hardcoding configurations; ensure updates are reflected in `setup.sh` or `docker-compose.yml`.
- Python microservices use Python 3.12+ with type hinting.
- Ensure strict VRAM management logic remains intact when editing inference pipelines (e.g., explicit `torch.cuda.empty_cache()`).
