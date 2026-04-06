import gradio as gr
import requests
import os

API_URL = os.getenv("API_URL", "http://localhost:8000")

def generate_model(image_path, topology_preset):
    if not image_path:
        return None, "Please upload an image."
        
    try:
        with open(image_path, 'rb') as f:
            files = {'image': f}
            data = {'topology_preset': topology_preset}
            
            response = requests.post(f"{API_URL}/generate", files=files, data=data)
            
        if response.status_code == 200:
            output_path = "/tmp/generated_model.fbx"
            with open(output_path, 'wb') as f:
                f.write(response.content)
            return output_path, "Success! Model processed."
        else:
            return None, f"Error: {response.text}"
            
    except Exception as e:
        return None, f"Connection Error: {str(e)}"

with gr.Blocks(theme=gr.themes.Monochrome()) as app:
    gr.Markdown("# Boosted3D: AI to UE5 Model Generator")
    
    with gr.Row():
        with gr.Column():
            input_image = gr.Image(type="filepath", label="Input Image")
            topology_preset = gr.Dropdown(
                choices=[
                    "Nanite High-Fidelity",
                    "Deformable/Mobile Optimized",
                    "Proxy/Collision"
                ],
                value="Nanite High-Fidelity",
                label="Topology Preset"
            )
            generate_btn = gr.Button("Generate 3D Model", variant="primary")
            
        with gr.Column():
            output_file = gr.File(label="Download Asset (UE5 FBX)")
            status_text = gr.Textbox(label="Status", interactive=False)

    generate_btn.click(
        fn=generate_model,
        inputs=[input_image, topology_preset],
        outputs=[output_file, status_text]
    )

if __name__ == "__main__":
    app.launch(server_name="0.0.0.0", server_port=7860)
