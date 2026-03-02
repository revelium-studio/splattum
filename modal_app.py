"""
Modal app for running AnySplat on GPU.
AnySplat: Feed-forward 3D Gaussian Splatting from Unconstrained Views
Project page: https://city-super.github.io/anysplat/
Code: https://github.com/InternRobotics/AnySplat
Hugging Face: https://huggingface.co/lhjiang/anysplat

Deploy with: modal deploy modal_app.py
"""

import modal

# Create the Modal app
app = modal.App("anysplat")

# AnySplat is developed for Python 3.10, PyTorch 2.2.0 and CUDA 12.1.
# We start from NVIDIA's PyTorch image, then replace the preinstalled torch
# with the exact 2.2.0/cu121 stack and install AnySplat + its dependencies.
image = (
    modal.Image.from_registry(
        "nvcr.io/nvidia/pytorch:24.07-py3",  # PyTorch 2.4.0 + CUDA 12.5, Python 3.10
        add_python=None,
    )
    .env(
        {
            "TORCH_CUDA_ARCH_LIST": "8.0",  # Optimise for A100
            "DEBIAN_FRONTEND": "noninteractive",
        }
    )
    .run_commands(
        # System dependencies: git + FFmpeg + basic GL for OpenCV / Open3D + build tools
        "apt-get update && apt-get install -y "
        "git ffmpeg libgl1-mesa-glx libglib2.0-0 "
        "build-essential ninja-build cmake "
        "&& rm -rf /var/lib/apt/lists/*",
        # Clone AnySplat
        "git clone https://github.com/InternRobotics/AnySplat.git /opt/anysplat",
        # ── Phase 1: Remove the base-image torch and install the exact CUDA 12.1
        #    build that AnySplat was developed against.  This MUST happen BEFORE
        #    requirements.txt so that pytorch3d / torch_scatter / gsplat compile
        #    against the right torch ABI.
        "pip uninstall -y torch torchvision torchaudio torch-tensorrt || true",
        "pip install --no-cache-dir "
        "torch==2.2.0+cu121 torchvision==0.17.0+cu121 torchaudio==2.2.0+cu121 "
        "--index-url https://download.pytorch.org/whl/cu121",

        # ── Phase 2: Install AnySplat requirements.  pytorch3d, torch_scatter,
        #    gsplat etc. will now be compiled / resolved against torch 2.2.0+cu121.
        "pip install --no-cache-dir -r /opt/anysplat/requirements.txt",

        # ── Phase 3: CRITICAL FIX for torch_scatter — the version built from source
        #    by requirements.txt compiles WITHOUT CUDA support (known AnySplat issue #40).
        #    We must reinstall it from PyG's prebuilt CUDA wheels.
        #    See: https://github.com/InternRobotics/AnySplat/issues/40
        "pip install --no-cache-dir --force-reinstall torch-scatter "
        "-f https://data.pyg.org/whl/torch-2.2.0+cu121.html",

        # ── Phase 4: NUCLEAR FIX for OpenCV (NVIDIA base image conflict)
        "pip uninstall -y opencv-python opencv-python-headless "
        "opencv-contrib-python opencv-contrib-python-headless 2>/dev/null || true",
        "find /usr -name 'cv2*' -exec rm -rf {} + 2>/dev/null || true",
        "find /usr -name 'opencv*' -path '*/dist-packages/*' -exec rm -rf {} + 2>/dev/null || true",
        "pip install --no-cache-dir opencv-python-headless==4.8.0.76",

        # ── Phase 5: Pin numpy < 2 (must be LAST to override any 2.x)
        "pip install --no-cache-dir 'numpy<2'",

        # ── Phase 6: Verify torch CUDA, gsplat, and torch_scatter all work
        'python -c "'
        "import torch; "
        "print(f'torch={torch.__version__}  cuda={torch.version.cuda}  cudnn={torch.backends.cudnn.is_available()}'); "
        "assert torch.version.cuda is not None, 'torch has NO CUDA support!'; "
        "import gsplat; print(f'gsplat={gsplat.__version__}'); "
        "import torch_scatter; print(f'torch_scatter OK'); "
        # Quick smoke-test: scatter_add on a CUDA-like tensor (CPU is fine at build time)
        "src = torch.ones(4); idx = torch.tensor([0,0,1,1]); "
        "from torch_scatter import scatter_add; "
        "out = scatter_add(src, idx, dim=0); "
        "print(f'scatter_add smoke test passed: {out}')\"",
    )
)

# Volume for caching Hugging Face weights and AnySplat assets
volume = modal.Volume.from_name("anysplat-cache", create_if_missing=True)


@app.function(
    image=image,
    gpu="A100",
    timeout=900,  # 15 minutes is plenty for feed-forward AnySplat
    volumes={"/cache": volume},
)
def process_image(image_bytes_list: list[bytes], filenames: list[str], prompt: str = "", elevation: int = 20) -> bytes:
    """
    Process one or more images with AnySplat and return a PLY file with 3D Gaussians.

    Quality improvements over the basic single-duplicate approach:
    1. Multi-view augmentation: generates 6 synthetic crops from a single image
       to provide parallax cues for better depth estimation.
    2. Full SH export: preserves all spherical harmonics (degree 4) for richer,
       view-dependent colours.
    3. Scene normalization: centers and scales the scene for better viewer compat.
    4. Multi-image support: when users upload multiple images the quality is
       dramatically better because the model gets real parallax.
    """
    import os
    import sys
    import tempfile
    from pathlib import Path

    import torch
    import torchvision.transforms as T
    from PIL import Image
    import torchvision

    # Route heavy downloads through the shared volume
    os.environ["TORCH_HOME"] = "/cache/torch"
    os.environ["HF_HOME"] = "/cache/huggingface"
    os.environ["HF_DATASETS_CACHE"] = "/cache/huggingface/datasets"

    # Add AnySplat to Python path
    sys.path.insert(0, "/opt/anysplat")

    from src.model.model.anysplat import AnySplat  # type: ignore
    from src.model.ply_export import export_ply  # type: ignore

    # ------------------------------------------------------------------
    # Helper: create a 448×448 tensor from a PIL image with a specific
    # crop offset (dx, dy in pixels) and zoom factor.
    # ------------------------------------------------------------------
    def make_view(pil_img: Image.Image, dx: int = 0, dy: int = 0, zoom: float = 1.0) -> torch.Tensor:
        """Crop, resize to 448×448, normalise to [-1, 1]."""
        w, h = pil_img.size
        # Apply zoom: zoom > 1 means crop tighter (zoom-in)
        crop_w = int(w / zoom)
        crop_h = int(h / zoom)
        # Centre + offset
        cx = w // 2 + dx
        cy = h // 2 + dy
        left = max(0, cx - crop_w // 2)
        top = max(0, cy - crop_h // 2)
        right = min(w, left + crop_w)
        bottom = min(h, top + crop_h)
        cropped = pil_img.crop((left, top, right, bottom))
        resized = cropped.resize((448, 448), Image.LANCZOS)
        tensor = torchvision.transforms.ToTensor()(resized) * 2.0 - 1.0
        return tensor  # [3, 448, 448]

    # Cache the model at module level to avoid re-loading on warm containers
    global _ANYSPLAT_MODEL  # type: ignore
    try:
        model = _ANYSPLAT_MODEL  # type: ignore[name-defined]
    except NameError:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model = AnySplat.from_pretrained("lhjiang/anysplat")
        model = model.to(device)
        model.eval()
        for param in model.parameters():
            param.requires_grad = False
        _ANYSPLAT_MODEL = model  # type: ignore

    device = next(model.parameters()).device  # type: ignore[attr-defined]

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # ------------------------------------------------------------------
        # Build views from all uploaded images
        # ------------------------------------------------------------------
        views: list[torch.Tensor] = []

        for idx, (img_bytes, fname) in enumerate(zip(image_bytes_list, filenames)):
            img_path = tmpdir_path / f"input_{idx}_{fname}"
            img_path.write_bytes(img_bytes)
            pil_img = Image.open(str(img_path)).convert("RGB")
            w, h = pil_img.size
            print(f"🖼️  Image {idx}: {fname} — {w}×{h}")

            if len(image_bytes_list) == 1:
                # ── Single image: create 6 augmented views for better 3D ──
                # The shift amount is ~3-5% of image dimension.  Small enough
                # to keep the subject in frame, large enough for parallax.
                shift_x = max(12, int(w * 0.04))
                shift_y = max(12, int(h * 0.04))
                views.append(make_view(pil_img, dx=0, dy=0, zoom=1.0))      # centre
                views.append(make_view(pil_img, dx=-shift_x, dy=0, zoom=1.0))  # left
                views.append(make_view(pil_img, dx=shift_x, dy=0, zoom=1.0))   # right
                views.append(make_view(pil_img, dx=0, dy=-shift_y, zoom=1.0))  # up
                views.append(make_view(pil_img, dx=0, dy=shift_y, zoom=1.0))   # down
                views.append(make_view(pil_img, dx=0, dy=0, zoom=1.08))     # zoom in
            else:
                # Multiple images: use each at centre crop
                views.append(make_view(pil_img, dx=0, dy=0, zoom=1.0))

        # AnySplat needs ≥ 2 views
        if len(views) < 2:
            views.append(views[0])

        num_views = len(views)
        images = torch.stack(views, dim=0).unsqueeze(0).to(device)  # [1, V, 3, 448, 448]
        b, v, _, h_t, w_t = images.shape
        print(f"📐 AnySplat input: {num_views} views, tensor shape {images.shape}")

        # Run inference
        with torch.no_grad():
            gaussians, pred_context_pose = model.inference((images + 1) * 0.5)  # type: ignore[attr-defined]

        num_gaussians = gaussians.means[0].shape[0]
        print(f"🔮 AnySplat produced {num_gaussians:,} Gaussians")

        # ------------------------------------------------------------------
        # Export to PLY with quality flags:
        #   • save_sh_dc_only=False → keep full SH (degree 4) for richer colour
        #   • shift_and_scale=True  → normalise the scene to [-1, 1]
        # ------------------------------------------------------------------
        ply_path = tmpdir_path / "gaussians.ply"
        export_ply(
            gaussians.means[0],
            gaussians.scales[0],
            gaussians.rotations[0],
            gaussians.harmonics[0],
            gaussians.opacities[0],
            ply_path,
            shift_and_scale=True,
            save_sh_dc_only=False,
        )

        if not ply_path.exists():
            raise RuntimeError(f"AnySplat did not produce a PLY file at {ply_path}")

        ply_size_mb = ply_path.stat().st_size / (1024 * 1024)
        print(f"✅ AnySplat PLY: {ply_path.stat().st_size:,} bytes ({ply_size_mb:.1f} MB), "
              f"{num_gaussians:,} gaussians, full SH, shift+scale normalised")
        return ply_path.read_bytes()


@app.function(image=image, gpu="A100", timeout=900, volumes={"/cache": volume})
@modal.fastapi_endpoint(method="POST")
async def anysplat_router(request: dict) -> dict:
    """
    Single web endpoint that multiplexes:
    - op = \"process\" (default): start AnySplat job (sync or async)
    - op = \"status\": get status for an async job
    - op = \"health\": simple health check
    """
    import base64
    from modal.functions import FunctionCall

    try:
        op = request.get("op") or "process"

        if op == "health":
            return {"status": "ok", "service": "anysplat", "endpoint": "router"}

        if op == "status":
            call_id = request.get("call_id")
            if not call_id:
                return {"error": "call_id required"}

            call = FunctionCall.from_id(call_id)
            try:
                ply_bytes = call.get(timeout=0)
                ply_b64 = base64.b64encode(ply_bytes).decode("utf-8")
                return {"status": "completed", "ply": ply_b64}
            except TimeoutError:
                return {"status": "processing"}
            except Exception as e:
                return {"status": "failed", "error": str(e)}

        # Default: process new image(s)
        # Supports both single image ("image" field) and multi-image ("images" array)
        is_async = request.get("async", False)
        prompt = request.get("prompt", "")
        elevation = request.get("elevation", 20)

        # Collect images into lists
        images_b64: list[str] = []
        filenames: list[str] = []

        if request.get("images"):
            # Multi-image mode: [{image: base64, filename: str}, ...]
            for item in request["images"]:
                images_b64.append(item["image"])
                filenames.append(item.get("filename", f"image_{len(filenames)}.jpg"))
        elif request.get("image"):
            # Single-image mode (backward compatible)
            images_b64.append(request["image"])
            filenames.append(request.get("filename", "image.jpg"))
        else:
            return {"error": "No image provided"}

        print(
            f"🔄 AnySplat process: {len(images_b64)} image(s), async={is_async}, "
            f"filenames={filenames}"
        )

        image_bytes_list = [base64.b64decode(b) for b in images_b64]

        if is_async:
            call = process_image.spawn(image_bytes_list, filenames, prompt, elevation)
            return {"success": True, "call_id": call.object_id, "status": "processing"}

        ply_bytes = process_image.remote(image_bytes_list, filenames, prompt, elevation)
        ply_b64 = base64.b64encode(ply_bytes).decode("utf-8")
        return {"success": True, "ply": ply_b64}

    except Exception as e:
        import traceback

        traceback.print_exc()
        return {"error": str(e)}


@app.local_entrypoint()
def main():
    """
    Local CLI helper:

        modal run modal_app.py -- <image_path>
    """
    import sys
    from pathlib import Path

    if len(sys.argv) < 2:
        print("Usage: modal run modal_app.py -- <image_path>")
        return

    image_path = Path(sys.argv[1])
    if not image_path.exists():
        print(f"Image not found: {image_path}")
        return

    with image_path.open("rb") as f:
        image_bytes = f.read()

    print(f"Processing {image_path} with AnySplat...")
    ply_bytes = process_image.remote([image_bytes], [image_path.name])

    output_path = image_path.with_suffix(".ply")
    with output_path.open("wb") as f:
        f.write(ply_bytes)

    print(f"Saved AnySplat PLY to {output_path}")
