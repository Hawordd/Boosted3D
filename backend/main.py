from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
import shutil
import os
import tempfile
import logging
from mesh_processor import NaniteProcessor, DecimatedProcessor, ProxyProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Boosted3D API")

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/generate")
async def generate_3d(
    image: UploadFile = File(...),
    topology_preset: str = Form(...)
):
    try:
        # 1. Save uploaded image
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_img:
            shutil.copyfileobj(image.file, tmp_img)
            img_path = tmp_img.name

        # 2. Mock AI Generation (Replace with actual InstantMesh/CRM call)
        logger.info(f"Generating 3D from image for strategy: {topology_preset}")
        # In a real scenario, this would generate a raw mesh file.
        raw_mesh_path = os.path.join(tempfile.gettempdir(), "raw_model.obj")
        # Mocking creation of a raw mesh
        with open(raw_mesh_path, "w") as f:
            f.write("# Mock OBJ file\n")
            
        # Clear VRAM after generation
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        # 3. Post-Process
        output_dir = os.path.join(tempfile.gettempdir(), "output_mesh")
        os.makedirs(output_dir, exist_ok=True)
        final_fbx_path = os.path.join(output_dir, "final_ue5.fbx")

        # In a fully functional mock, we'd need a real OBJ to run pymeshlab. 
        # For setup, we'll bypass the actual processing if it's a mock string.
        # But here is how it maps:
        processor = None
        if topology_preset == "Nanite High-Fidelity":
            processor = NaniteProcessor()
        elif topology_preset == "Deformable/Mobile Optimized":
            processor = DecimatedProcessor()
        elif topology_preset == "Proxy/Collision":
            processor = ProxyProcessor()
        else:
            raise HTTPException(status_code=400, detail="Invalid topology preset.")
            
        # Due to the mock nature, processor.process will fail on a fake OBJ, 
        # so we'll just mock the output file creation for now of the API.
        with open(final_fbx_path, "w") as f:
            f.write("Mock FBX Content")
            
        return FileResponse(path=final_fbx_path, filename="final_ue5.fbx", media_type="application/octet-stream")

    except Exception as e:
        logger.error(f"Generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
