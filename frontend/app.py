import gradio as gr
import requests
import os

API_URL = os.getenv("API_URL", "http://localhost:8000")

def generate_model(image_path, topology_preset, texture_resolution, export_format, guidance_scale, poly_count_target):
    if not image_path:
        return None, "Please upload an image.", None
        
    try:
        with open(image_path, 'rb') as f:
            files = {'image': f}
            data = {
                'topology_preset': topology_preset,
                'texture_resolution': texture_resolution,
                'export_format': export_format,
                'guidance_scale': guidance_scale,
                'poly_count_target': poly_count_target
            }
            
            response = requests.post(f"{API_URL}/generate", files=files, data=data)
            
        if response.status_code == 200:
            ext = ".glb" if "GLB" in export_format else ".fbx"
            output_path = f"/tmp/generated_model{ext}"
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            preview_model = output_path if ext == ".glb" else None
            status_msg = "Success! (Preview requires GLB format)" if ext == ".fbx" else "Success! Model processed."
            
            return output_path, status_msg, preview_model
        else:
            return None, f"Error: {response.text}", None
            
    except Exception as e:
        return None, f"Connection Error: {str(e)}", None

with gr.Blocks(theme=gr.themes.Monochrome()) as app:
    gr.Markdown("# Boosted3D: AI to UE5 Model Generator")
    
    with gr.Row():
        with gr.Column():
            input_image = gr.Image(type="filepath", label="Input Image")
            
            with gr.Accordion("3D Model Personalization Settings", open=True):
                topology_preset = gr.Dropdown(
                    choices=[
                        "Nanite High-Fidelity",
                        "Deformable/Mobile Optimized",
                        "Proxy/Collision"
                    ],
                    value="Nanite High-Fidelity",
                    label="Topology Preset"
                )
                texture_resolution = gr.Dropdown(
                    choices=["1024", "2048", "4096"],
                    value="2048",
                    label="Texture Resolution"
                )
                export_format = gr.Dropdown(
                    choices=["FBX Binary", "GLB/glTF 2.0"],
                    value="FBX Binary",
                    label="Export Format",
                    info="All exports are Z-Up, Left-Handed (UE5 Standard)"
                )
                guidance_scale = gr.Slider(
                    minimum=1.0, maximum=15.0, value=7.5, step=0.1,
                    label="AI Guidance Scale"
                )
                poly_count_target = gr.Slider(
                    minimum=1000, maximum=100000, value=25000, step=1000,
                    label="Target Poly Count (Decimation)"
                )
            generate_btn = gr.Button("Generate 3D Model", variant="primary")
            
        with gr.Column():
            output_model = gr.Model3D(label="3D Preview (Interactable & Animated)", clear_color=[0.0, 0.0, 0.0, 0.0])
            output_file = gr.File(label="Download Asset")
            status_text = gr.Textbox(label="Status", interactive=False)

    generate_btn.click(
        fn=generate_model,
        inputs=[input_image, topology_preset, texture_resolution, export_format, guidance_scale, poly_count_target],
        outputs=[output_file, status_text, output_model]
    )

if __name__ == "__main__":
    os.environ["GRADIO_SERVER_NAME"] = "0.0.0.0"
    app.launch(server_port=7860)
