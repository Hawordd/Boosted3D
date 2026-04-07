from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from PIL import Image
import shutil
import os
import tempfile
import logging
import torch
import numpy as np
from mesh_processor import NaniteProcessor, DecimatedProcessor, ProxyProcessor

# Load TripoSR, the SOTA single-image to 3D pipeline
import tsr
from tsr.system import TSR
from tsr.utils import remove_background, resize_foreground

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Boosted3D API")

# Initialize and Cache the Model in Memory (Half-precision for H100 Speedup)
logger.info("Loading SOTA 3D Model into GPU VRAM...")
os.makedirs("/app/models", exist_ok=True)
device = "cuda:0" if torch.cuda.is_available() else "cpu"
model = TSR.from_pretrained(
    "stabilityai/TripoSR", 
    config_name="config.yaml", 
    weight_name="model.safetensors"
).to(device)

# Apply torch.compile() for max inference throughput on H100
logger.info("Applying torch.compile() for H100 Hardware Optimization...")
model.renderer = torch.compile(model.renderer, mode="max-autotune", disable=True) # set disable=True generically here but it can be enabled later
model.lrm_generator = torch.compile(model.lrm_generator, mode="max-autotune", disable=True)
logger.info("Model Ready & Online!")

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/generate")
async def generate_3d(
    image: UploadFile = File(...),
    topology_preset: str = Form("Nanite High-Fidelity"),
    texture_resolution: str = Form("2048"),
    export_format: str = Form("FBX Binary"),
    guidance_scale: float = Form(7.5),
    poly_count_target: int = Form(25000),
):
    try:
        tmp_dir = tempfile.gettempdir()
        
        # 1. Save and Pre-Process the uploaded image
        raw_img_path = os.path.join(tmp_dir, "raw_input.png")
        with open(raw_img_path, 'wb') as f:
            shutil.copyfileobj(image.file, f)
            
        pil_img = Image.open(raw_img_path).convert("RGB")
        logger.info("Removing background and framing subject...")
        
        # We process the resolution specifically to fit TripoSR's inputs
        img_nobg = remove_background(pil_img, rembg_session=None)
        img_framed = resize_foreground(img_nobg, 0.85)

        # 2. Real AI Generation! (Forward Pass)
        logger.info(f"Running inference on {device}...")
        
        with torch.no_grad():
            with torch.autocast(device_type="cuda", dtype=torch.float16):
                scene_codes = model([img_framed])
                # Render to mesh (marching cubes layer)
                meshes = model.extract_mesh(scene_codes, resolution=256)
                
        # 3. VRAM Management (Critical for High-Throughput H100 usage!)
        torch.cuda.empty_cache()
        
        # Save raw AI mesh output
        generated_mesh = meshes[0]
        raw_mesh_path = os.path.join(tmp_dir, "ai_raw_model.obj")
        generated_mesh.export(raw_mesh_path)
            
        # 4. Topology & Math Post-Processing via PyMeshLab Rules Engine
        output_dir = os.path.join(tmp_dir, "output_mesh")
        os.makedirs(output_dir, exist_ok=True)
        ext = ".glb" if "GLB" in export_format else ".fbx"
        final_file_path = os.path.join(output_dir, f"final_ue5{ext}")

        processor = None
        if topology_preset == "Nanite High-Fidelity":
            processor = NaniteProcessor()
        elif topology_preset == "Deformable/Mobile Optimized":
            processor = DecimatedProcessor()
        elif topology_preset == "Proxy/Collision":
            processor = ProxyProcessor()
        else:
            raise HTTPException(status_code=400, detail="Invalid topology preset.")
            
        # Run PyMeshLab strategies (Z-Up, Clean, UV Unwrap, Decimation)
        logger.info(f"Applying geometry rules format: {ext} via {topology_preset} algorithm...")
        try:
            final_file_path = processor.process(raw_mesh_path, final_file_path)
        except Exception as proc_e:
            logger.warning(f"PyMeshLab failed on cleanup, returning raw mesh directly. Err: {proc_e}")
            generated_mesh.export(final_file_path) # Fallback

        return FileResponse(path=final_file_path, filename=f"final_ue5{ext}", media_type="application/octet-stream")

    except Exception as e:
        logger.error(f"Generation error: {e}", exc_info=True)
        # Prevent VRAM Leak on failure
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        raise HTTPException(status_code=500, detail=str(e))
