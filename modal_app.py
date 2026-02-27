"""
Modal app for running DiffSplat model on GPU.
DiffSplat: Repurposing Image Diffusion Models for Scalable 3D Gaussian Splat Generation
https://github.com/chenguolin/DiffSplat (MIT License - Commercial use allowed)

Deploy with: modal deploy modal_app.py
"""

import modal

# Create the Modal app
app = modal.App("diffsplat")

# Define the container image with all dependencies for DiffSplat
image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install(
        "git", "wget", "ffmpeg", "libsm6", "libxext6", "libgl1-mesa-glx",
        "build-essential", "ninja-build"
    )
    .pip_install(
        # PyTorch 2.4+ required by DiffSplat
        "torch==2.4.0",
        "torchvision==0.19.0",
        # Core dependencies
        "numpy",
        "scipy",
        "pillow",
        "pillow-heif",
        "plyfile",
        "click",
        "tqdm",
        "timm",
        "matplotlib",
        "imageio",
        "imageio-ffmpeg",
        "huggingface_hub",
        "fastapi",
        # DiffSplat specific dependencies  
        "transformers>=4.40.0,<5.0.0",  # Pin to avoid breaking changes
        "diffusers>=0.32.0",
        "accelerate",
        "safetensors",
        "omegaconf",
        "einops",
        "kiui>=0.2.10",  # For camera utilities and rendering
        "rembg[gpu]",  # Background removal
        "onnxruntime-gpu",
        "pygltflib",
        "trimesh",
        "open3d",
        "opencv-python",
    )
    .run_commands(
        # Clone DiffSplat repository
        "git clone https://github.com/chenguolin/DiffSplat.git /opt/diffsplat",
        # Run DiffSplat setup
        "cd /opt/diffsplat && bash settings/setup.sh || true",
    )
    .env({"PYTHONPATH": "/opt/diffsplat:/opt/diffsplat/src:/opt/diffsplat/extensions"})
)

# Create a volume for caching the models
volume = modal.Volume.from_name("diffsplat-model-cache", create_if_missing=True)


@app.function(
    image=image,
    gpu="A100",  # A100 for better VRAM (DiffSplat needs ~16GB for SD1.5 model)
    timeout=600,  # 10 minute timeout
    volumes={"/cache": volume},
)
def process_image(image_bytes: bytes, filename: str, prompt: str = "", elevation: int = 20) -> bytes:
    """
    Process an image with DiffSplat and return the PLY file bytes.
    
    Args:
        image_bytes: Input image as bytes
        filename: Original filename
        prompt: Optional text prompt (helps with quality)
        elevation: Camera elevation angle (default 20 degrees)
    """
    import os
    import sys
    import tempfile
    from pathlib import Path
    
    # Set cache directories
    os.environ["TORCH_HOME"] = "/cache/torch"
    os.environ["HF_HOME"] = "/cache/huggingface"
    os.environ["HF_DATASETS_CACHE"] = "/cache/huggingface/datasets"
    
    # Add DiffSplat to path
    sys.path.insert(0, "/opt/diffsplat")
    sys.path.insert(0, "/opt/diffsplat/src")
    sys.path.insert(0, "/opt/diffsplat/extensions")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Save input image
        input_path = Path(tmpdir) / filename
        input_path.write_bytes(image_bytes)
        
        # Output directory
        output_dir = Path(tmpdir) / "output"
        output_dir.mkdir()
        
        print(f"🔄 Starting DiffSplat processing for {filename} ({len(image_bytes)} bytes)...")
        print(f"📷 Using elevation: {elevation}°, prompt: '{prompt or 'empty'}'")
        
        # Download model weights if not cached
        from huggingface_hub import hf_hub_download, snapshot_download
        
        print("📥 Ensuring models are downloaded...")
        model_dir = Path("/cache/diffsplat_models")
        model_dir.mkdir(exist_ok=True, parents=True)
        
        # Download the SD1.5 image-conditioned model (most efficient)
        model_name = "gsdiff_gobj83k_sd15_image__render"
        gsrecon_name = "gsrecon_gobj265k_cnp_even4"
        gsvae_name = "gsvae_gobj265k_sd"
        
        try:
            # Download all required models
            for name in [model_name, gsrecon_name, gsvae_name]:
                model_path = model_dir / name
                if not model_path.exists():
                    print(f"📥 Downloading {name}...")
                    snapshot_download(
                        repo_id="chenguolin/DiffSplat",
                        allow_patterns=[f"{name}/*"],
                        local_dir=str(model_dir),
                        local_dir_use_symlinks=False,
                    )
        except Exception as e:
            print(f"⚠️ Model download warning: {e}")
        
        # Run DiffSplat inference using their inference script
        import subprocess
        
        # Build the inference command
        # Using SD1.5 image-conditioned model for best efficiency
        cmd = [
            "bash", "/opt/diffsplat/scripts/infer.sh",
            "src/infer_gsdiff_sd.py",
            "configs/gsdiff_sd15.yaml",
            model_name,
            "--rembg_and_center",
            "--triangle_cfg_scaling",
            "--guidance_scale", "2",
            "--image_path", str(input_path),
            "--elevation", str(elevation),
            "--save_ply",
            "--opacity_threshold_ply", "0.1",
            "--half_precision",  # Use BF16 for memory efficiency
            "--output_dir", str(output_dir),
            "--gpu_id", "0",
            "--seed", "42",
        ]
        
        # Add prompt if provided
        if prompt:
            # Replace spaces with underscores for DiffSplat
            cmd.extend(["--prompt", prompt.replace(" ", "_")])
        
        env = os.environ.copy()
        env["PYTHONPATH"] = "/opt/diffsplat:/opt/diffsplat/src:/opt/diffsplat/extensions"
        
        print(f"🚀 Running command: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=540,  # 9 minutes
            cwd="/opt/diffsplat",
            env=env,
        )
        
        print("DiffSplat stdout:", result.stdout)
        if result.stderr:
            print("DiffSplat stderr:", result.stderr)
        
        if result.returncode != 0:
            # Try alternative approach: direct Python inference
            print("⚠️ Bash script failed, trying direct Python inference...")
            
            try:
                # Import DiffSplat modules
                from src.options import opt_dict
                from omegaconf import OmegaConf
                import torch
                
                # Load config
                config_path = "/opt/diffsplat/configs/gsdiff_sd15.yaml"
                cfg = OmegaConf.load(config_path)
                opt = opt_dict["gsdiff_sd15"]
                opt = OmegaConf.merge(opt, cfg)
                
                # Set image conditioning options
                opt.view_concat_condition = True
                opt.input_concat_binary_mask = True
                opt.prediction_type = "v_prediction"
                
                # Load and run inference
                # This is a simplified version - the actual DiffSplat has more complex setup
                from PIL import Image
                from rembg import remove
                
                # Load and preprocess image
                img = Image.open(input_path).convert("RGBA")
                
                # Remove background
                img_no_bg = remove(img)
                
                # Center the object
                # ... (simplified - actual DiffSplat does more preprocessing)
                
                # Save preprocessed image
                preprocessed_path = Path(tmpdir) / "preprocessed.png"
                img_no_bg.save(preprocessed_path)
                
                print(f"✅ Preprocessed image saved to {preprocessed_path}")
                
                # For now, raise to fall back to error
                raise Exception("Direct inference not fully implemented - use subprocess")
                
            except Exception as e2:
                print(f"❌ Direct inference also failed: {e2}")
                raise Exception(f"DiffSplat failed: {result.stderr or result.stdout}")
        
        # Find the output PLY file
        ply_files = list(output_dir.rglob("*.ply"))
        if not ply_files:
            # Check alternative output locations
            alt_output = Path("/opt/diffsplat/out") / model_name / "inference"
            ply_files = list(alt_output.rglob("*.ply")) if alt_output.exists() else []
        
        if not ply_files:
            raise Exception("No PLY file generated")
        
        # Return the PLY file bytes
        ply_path = ply_files[0]
        print(f"✅ Found PLY file: {ply_path} ({ply_path.stat().st_size} bytes)")
        return ply_path.read_bytes()


@app.function(image=image)
@modal.fastapi_endpoint(method="GET")
async def health_check():
    """Health check endpoint to verify Modal is responding."""
    return {"status": "ok", "service": "diffsplat", "endpoint": "healthy"}


@app.function(image=image, gpu="A100", timeout=600, volumes={"/cache": volume})
@modal.fastapi_endpoint(method="POST")
async def process_image_endpoint(request: dict) -> dict:
    """
    HTTP endpoint for processing images.
    Expects: { 
        "image": base64_encoded_image, 
        "filename": "image.jpg",
        "prompt": "optional description",
        "elevation": 20,
        "async": false 
    }
    Returns: { "ply": base64_encoded_ply } or { "call_id": "..." } for async
    """
    import base64

    try:
        print(f"🔄 Received request: async={request.get('async', False)}, filename={request.get('filename', 'N/A')}")
        
        image_b64 = request.get("image")
        filename = request.get("filename", "image.jpg")
        prompt = request.get("prompt", "")
        elevation = request.get("elevation", 20)
        is_async = request.get("async", False)

        if not image_b64:
            print("❌ No image provided in request")
            return {"error": "No image provided"}

        print(f"📦 Decoding image (base64 length: {len(image_b64)})...")
        image_bytes = base64.b64decode(image_b64)
        print(f"✅ Image decoded successfully ({len(image_bytes)} bytes)")

        if is_async:
            # Spawn async job and return call_id
            print(f"🚀 Spawning async job for {filename}...")
            call = process_image.spawn(image_bytes, filename, prompt, elevation)
            print(f"✅ Async job spawned with call_id: {call.object_id}")
            return {"success": True, "call_id": call.object_id, "status": "processing"}
        else:
            # Process synchronously
            print(f"🔄 Processing synchronously for {filename}...")
            ply_bytes = process_image.remote(image_bytes, filename, prompt, elevation)
            print(f"✅ Processing completed, encoding result ({len(ply_bytes)} bytes)...")
            ply_b64 = base64.b64encode(ply_bytes).decode("utf-8")
            print("✅ Result encoded successfully")
            return {"success": True, "ply": ply_b64}

    except Exception as e:
        error_msg = str(e)
        print(f"❌ Error in process_image_endpoint: {error_msg}")
        import traceback
        traceback.print_exc()
        return {"error": error_msg}


@app.function(image=image)
@modal.fastapi_endpoint()
async def get_job_status_endpoint(call_id: str):
    """
    Get status of async job.
    Expects: call_id as query parameter (?call_id=...)
    Returns: { "status": "processing|completed|failed", "ply": base64_encoded_ply (if completed), "error": str (if failed) }
    """
    import base64
    from modal.functions import FunctionCall

    try:
        if not call_id:
            print("❌ No call_id provided to status endpoint")
            return {"error": "call_id query parameter required"}
        
        print(f"🔍 Checking status for call_id: {call_id}")
        
        try:
            # New Modal API: from_id only takes call_id
            call = FunctionCall.from_id(call_id)
        except Exception as e:
            print(f"❌ Failed to get FunctionCall from call_id {call_id}: {e}")
            import traceback
            traceback.print_exc()
            return {"error": f"Invalid call_id: {call_id}. Error: {str(e)}"}
        
        print(f"📊 Checking call status with get(timeout=0)...")
        try:
            ply_bytes = call.get(timeout=0)
            print(f"✅ Job completed! Result retrieved ({len(ply_bytes)} bytes), encoding...")
            ply_b64 = base64.b64encode(ply_bytes).decode("utf-8")
            print(f"✅ Result encoded successfully")
            return {"status": "completed", "ply": ply_b64}
        except TimeoutError:
            print(f"⏳ Job still processing (get() timeout)")
            return {"status": "processing"}
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Job failed or error occurred: {error_msg}")
            import traceback
            traceback.print_exc()
            return {"status": "failed", "error": error_msg}

    except Exception as e:
        error_msg = str(e)
        print(f"❌ Exception in get_job_status_endpoint: {error_msg}")
        import traceback
        traceback.print_exc()
        return {"error": error_msg}


@app.local_entrypoint()
def main():
    """Test the function locally."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: modal run modal_app.py -- <image_path> [prompt] [elevation]")
        return

    image_path = sys.argv[1]
    prompt = sys.argv[2] if len(sys.argv) > 2 else ""
    elevation = int(sys.argv[3]) if len(sys.argv) > 3 else 20
    
    with open(image_path, "rb") as f:
        image_bytes = f.read()

    print(f"Processing {image_path} with prompt='{prompt}', elevation={elevation}...")
    ply_bytes = process_image.remote(image_bytes, "test.jpg", prompt, elevation)

    output_path = image_path.rsplit(".", 1)[0] + ".ply"
    with open(output_path, "wb") as f:
        f.write(ply_bytes)

    print(f"Saved to {output_path}")
