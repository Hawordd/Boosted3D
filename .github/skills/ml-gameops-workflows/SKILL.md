---
name: ml-gameops-workflows
description: 'Execute 3D geometry conversions, UV unwrapping, H100 ML pipeline quantization, and deploy to Ubuntu/Docker/Nginx. Use for 3D model processing, inference optimization, and server setup.'
argument-hint: 'Task type (geometry, inference, infrastructure)'
---

# ML-GameOps Workflows

This skill provides step-by-step procedures and knowledge grounding for 3D geometry manipulation, ML inference optimization on H100s, and deployment infrastructure.

## When to Use
- Converting coordinate spaces (Y-Up/Right-Hand to Z-Up/Left-Hand).
- Cleaning meshes, smart projecting UVs, and exporting to FBX Binary or GLB.
- Optimizing PyTorch/TensorRT inference for `InstantMesh`, `CRM`, or `Unique3D`.
- Managing VRAM during 3D generation tasks.
- Setting up or debugging Ubuntu 24.04 infrastructure (Docker, Nginx, Let's Encrypt).

## 1. 3D Geometry & Math Workflow
**Goal:** Prepare and export game-ready 3D assets.

1. **Transformations:** Convert all incoming meshes to **Z-Up, Left-Handed** coordinate space (Unreal Engine standard).
2. **Topology & Cleaning:** 
   - Remove degenerate faces.
   - Merge coincident vertices to create a manifold mesh.
   - Perform automated UV unwrapping (Smart Project) to ensure zero overlap.
3. **Exporting:** Compile the cleaned mesh and textures into **FBX Binary** or **GLB/glTF 2.0 PBR** formats exclusively.

## 2. Machine Learning Pipeline Workflow
**Goal:** Maximize throughput and prevent OOM errors on H100.

1. **Inference Execution:** Configure inference loops for local models (`InstantMesh`, `CRM`, `Unique3D`).
2. **Quantization & Compilation:** Apply TensorRT or `torch.compile` (AOT) to squeeze H100-specific speedups. Ensure BF16/FP16 limits are respected.
3. **VRAM Management:**
   - Execute explicit `torch.cuda.empty_cache()` at safe intervals (e.g., between generation stages).
   - Implement gradient-checkpointing equivalent strategies during heavy forward passes if batching is used.

## 3. Infrastructure (H100/DigitalOcean) Workflow
**Goal:** Deploy a secure, high-performance generation endpoint.

1. **OS Configuration:** Ensure Ubuntu 24.04 LTS is provisioned with appropriate NVIDIA drivers.
2. **Containerization:** Create multi-stage `Dockerfile`s using the NVIDIA Container Toolkit (`NVIDIA_VISIBLE_DEVICES=all`). Ensure models and datasets are mapped via volume persistence, not baked into the image.
3. **Networking & Security:** 
   - Proxy FastAPI traffic through Nginx as an upstream.
   - Automate SSL renewal via ACME/Certbot challenges.

## Quality Criteria & Completion Checks
- [ ] Are exported models strictly Z-Up and Left-Handed?
- [ ] Are UVs cleanly unwrapped with embedded PBR textures in the FBX/GLB?
- [ ] Is VRAM explicitly released between heavy inference calls?
- [ ] Is the Dockerized FastAPI service successfully terminating SSL at the Nginx layer?
