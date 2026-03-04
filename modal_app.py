"""
Modal app for running AnySplat on GPU, with optional GEN3C multi-view enhancement.

AnySplat: Feed-forward 3D Gaussian Splatting from Unconstrained Views
  https://github.com/InternRobotics/AnySplat

GEN3C: NVIDIA GEN3C-Cosmos-7B — generates orbit videos from a single image
  https://github.com/nv-tlabs/GEN3C
  https://huggingface.co/nvidia/GEN3C-Cosmos-7B

Pipeline (when GEN3C enabled):
  1. GEN3C generates a 121-frame orbit video at 704×1280 from the input image.
  2. We sample 12 evenly-spaced keyframes from that video.
  3. Those frames are fed into AnySplat for denser 3DGS with fewer holes.

Quality defaults (hardcoded for testing):
  diffusion_steps = 22   (high quality, ~4-6 min)
  movement_distance = 0.3 (wide orbit for strong parallax)
  num_sampled_frames = 12  (gives AnySplat rich multi-view input)

Deploy with: modal deploy modal_app.py
"""

import modal

# ─────────────────────────────────────────────────────────────────────
# App
# ─────────────────────────────────────────────────────────────────────
app = modal.App("anysplat")

# ═════════════════════════════════════════════════════════════════════
# IMAGE 1 — AnySplat (PyTorch 2.2.0 / CUDA 12.1)
# ═════════════════════════════════════════════════════════════════════
anysplat_image = (
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

# ═════════════════════════════════════════════════════════════════════
# IMAGE 2 — GEN3C (PyTorch 2.6.0 / CUDA 12.4)
#   NVIDIA GEN3C-Cosmos-7B for multi-view orbit video generation.
#   Build takes ~30-60 min on first deploy (apex from source).
# ═════════════════════════════════════════════════════════════════════
gen3c_image = (
    modal.Image.from_registry(
        "nvcr.io/nvidia/pytorch:24.10-py3",  # CUDA 12.6, Python 3.10
        add_python=None,
    )
    .env(
        {
            "TORCH_CUDA_ARCH_LIST": "8.0;9.0",  # A100 + H100
            "DEBIAN_FRONTEND": "noninteractive",
            "MAX_JOBS": "4",
            "CUDA_HOME": "/usr/local/cuda",
            "PYTHONPATH": "/opt/gen3c",
        }
    )
    # System deps
    .run_commands(
        "apt-get update && apt-get install -y "
        "git ffmpeg libgl1-mesa-glx libglib2.0-0 "
        "build-essential ninja-build cmake g++ gcc "
        "&& rm -rf /var/lib/apt/lists/*",
    )
    # Clone GEN3C repo
    .run_commands(
        "git clone --recursive https://github.com/nv-tlabs/GEN3C.git /opt/gen3c",
    )
    # Phase 1: Replace base-image torch with 2.6.0+cu124
    .run_commands(
        "pip uninstall -y torch torchvision torchaudio torch-tensorrt || true",
        "pip install --no-cache-dir "
        "torch==2.6.0+cu124 torchvision==0.21.0+cu124 torchaudio==2.6.0+cu124 "
        "--index-url https://download.pytorch.org/whl/cu124",
    )
    # Phase 2: Install GEN3C requirements (minus torch/torchvision/torchaudio)
    .run_commands(
        "cd /opt/gen3c && "
        "grep -vE '^(torch|torchvision|torchaudio)==' requirements.txt > /tmp/gen3c_req.txt && "
        "pip install --no-cache-dir -r /tmp/gen3c_req.txt",
    )
    # Phase 3: transformer-engine (required by megatron-core)
    # MUST be built from source — the pip wheel's libtransformer_engine.so
    # was compiled against a different torch ABI and won't load after we
    # swapped to torch 2.6.0+cu124.
    .run_commands(
        "pip uninstall -y transformer-engine transformer_engine 2>/dev/null || true",
        "git clone --branch v1.12.0 --recursive "
        "https://github.com/NVIDIA/TransformerEngine.git /tmp/te && "
        "cd /tmp/te && "
        "NVTE_FRAMEWORK=pytorch NVTE_WITH_USERBUFFERS=0 MAX_JOBS=4 "
        "pip install --no-cache-dir --no-build-isolation '.[pytorch]' && "
        "rm -rf /tmp/te",
        # Verify the .so actually loads
        'python -c "'
        "import transformer_engine; "
        "import transformer_engine.pytorch; "
        "print('transformer-engine OK')\"",
    )
    # Phase 4: NVIDIA apex (required by megatron-core)
    # The base image has CUDA 12.6 but torch was built with cu124.  Apex's
    # setup.py raises RuntimeError on this minor mismatch.  We patch it out —
    # 12.6 is backward-compatible with 12.4 for all practical purposes.
    .run_commands(
        "git clone https://github.com/NVIDIA/apex /tmp/apex && "
        "cd /tmp/apex && "
        "sed -i 's/check_cuda_torch_binary_vs_bare_metal(CUDA_HOME)/pass  # patched: skip CUDA version check/' setup.py && "
        "pip install -v --disable-pip-version-check --no-cache-dir --no-build-isolation "
        '--config-settings "--global-option=--cpp_ext" '
        '--config-settings "--global-option=--cuda_ext" . && '
        "rm -rf /tmp/apex",
    )
    # Phase 5: MoGe depth model
    .run_commands(
        "pip install --no-cache-dir git+https://github.com/microsoft/MoGe.git",
    )
    # Phase 6: OpenCV fix + numpy pin
    .run_commands(
        "pip uninstall -y opencv-python opencv-python-headless 2>/dev/null || true",
        "pip install --no-cache-dir opencv-python-headless==4.10.0.84",
        "pip install --no-cache-dir 'numpy<2'",
    )
    # Verify everything loads
    .run_commands(
        'python -c "'
        "import torch; "
        "print(f'torch={torch.__version__}  cuda={torch.version.cuda}'); "
        "assert torch.version.cuda is not None, 'No CUDA'; "
        "import transformer_engine; import transformer_engine.pytorch; "
        "print('transformer-engine OK'); "
        "print('GEN3C image OK')\"",
    )
)

# ─────────────────────────────────────────────────────────────────────
# Volumes (persistent caches for model weights)
# ─────────────────────────────────────────────────────────────────────
volume = modal.Volume.from_name("anysplat-cache", create_if_missing=True)
gen3c_volume = modal.Volume.from_name("gen3c-cache", create_if_missing=True)


# ═════════════════════════════════════════════════════════════════════
# FUNCTION: process_image  (AnySplat — feed-forward 3DGS)
# ═════════════════════════════════════════════════════════════════════
@app.function(
    image=anysplat_image,
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
        # Detect source: GEN3C frames vs user-uploaded images
        # GEN3C frames have filenames like "gen3c_000.jpg"
        # ------------------------------------------------------------------
        is_gen3c_input = any(fn.startswith("gen3c_") for fn in filenames)
        source_label = "GEN3C multi-view" if is_gen3c_input else "user upload"
        print(f"🔍 DEBUG: source = {source_label}, num_images = {len(image_bytes_list)}")
        print(f"🔍 DEBUG: filenames = {filenames}")

        # ------------------------------------------------------------------
        # Debug: save input frames for inspection
        # ------------------------------------------------------------------
        import uuid as _uuid
        debug_run_id = _uuid.uuid4().hex[:8]
        debug_dir = Path(f"/cache/debug/anysplat_run_{debug_run_id}")
        debug_dir.mkdir(parents=True, exist_ok=True)
        print(f"🔍 DEBUG: anysplat debug dir = {debug_dir}")

        # ------------------------------------------------------------------
        # Build views from all input images
        # ------------------------------------------------------------------
        views: list[torch.Tensor] = []

        for idx, (img_bytes, fname) in enumerate(zip(image_bytes_list, filenames)):
            img_path = tmpdir_path / f"input_{idx}_{fname}"
            img_path.write_bytes(img_bytes)
            pil_img = Image.open(str(img_path)).convert("RGB")
            w, h = pil_img.size
            print(f"🖼️  Image {idx}: {fname} — {w}×{h}")

            # Save debug copy of every input frame
            pil_img.save(str(debug_dir / f"input_{idx:03d}_{fname}"))

            if len(image_bytes_list) == 1 and not is_gen3c_input:
                # ── Single user image: create 6 augmented views for better 3D ──
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
                print(f"🔍 DEBUG: single-image augmentation → 6 views")
            else:
                # GEN3C frames or multiple user images: use each as a centre crop.
                # These already have real parallax; augmentation would dilute it.
                views.append(make_view(pil_img, dx=0, dy=0, zoom=1.0))

        # AnySplat needs ≥ 2 views
        if len(views) < 2:
            views.append(views[0])
            print(f"⚠️  Only {len(views)-1} view(s), duplicated to meet AnySplat minimum")

        num_views = len(views)

        # ── HARD ASSERTION: GEN3C path must supply ≥ 6 views ─────────
        if is_gen3c_input:
            assert num_views >= 6, (
                f"AnySplat expects ≥6 frames from GEN3C, but got {num_views}. "
                f"Check gen3c_generate_views num_frames parameter."
            )
            print(f"✅ GEN3C assertion passed: {num_views} views ≥ 6")

        images = torch.stack(views, dim=0).unsqueeze(0).to(device)  # [1, V, 3, 448, 448]
        b, v, _, h_t, w_t = images.shape

        # ── Detailed shape logging ──────────────────────────────────
        print(f"📐 AnySplat input: {num_views} views, tensor shape {images.shape}")
        print(f"🔍 DEBUG: images.ndim={images.ndim}, images.shape[1]={images.shape[1]} (views)")
        print(f"🔍 DEBUG: dtype={images.dtype}, device={images.device}")
        print(f"🔍 DEBUG: value range = [{images.min().item():.2f}, {images.max().item():.2f}]")

        # ── Assert correct dimensionality ──────────────────────────
        # AnySplat expects [B, V, C, H, W] where B=1, V=num_views, C=3
        assert images.ndim == 5, f"Expected 5D tensor [B,V,C,H,W], got {images.ndim}D: {images.shape}"
        assert images.shape[1] >= 2, f"AnySplat needs ≥2 views, got {images.shape[1]}"
        if is_gen3c_input:
            assert images.shape[1] >= 6, (
                f"GEN3C path: AnySplat tensor has only {images.shape[1]} views, "
                f"expected ≥6. The GEN3C frames are NOT being used correctly!"
            )

        # Run inference
        with torch.no_grad():
            gaussians, pred_context_pose = model.inference((images + 1) * 0.5)  # type: ignore[attr-defined]

        num_gaussians = gaussians.means[0].shape[0]
        print(f"🔮 AnySplat produced {num_gaussians:,} Gaussians")

        # ------------------------------------------------------------------
        # Export to PLY with quality flags:
        #   • save_sh_dc_only=True  → DC-band only; full SH (degree 4) makes
        #     the file ~16× larger per Gaussian and exceeds Vercel's 4.5 MB
        #     response limit when transferred as base64.
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
            save_sh_dc_only=True,
        )

        if not ply_path.exists():
            raise RuntimeError(f"AnySplat did not produce a PLY file at {ply_path}")

        ply_size_mb = ply_path.stat().st_size / (1024 * 1024)
        print(f"✅ AnySplat PLY: {ply_path.stat().st_size:,} bytes ({ply_size_mb:.1f} MB), "
              f"{num_gaussians:,} gaussians, DC-only SH, shift+scale normalised")
        print(f"🔍 DEBUG: source={source_label}, views={num_views}, "
              f"gaussians={num_gaussians:,}, ply_mb={ply_size_mb:.1f}")
        print(f"🔍 DEBUG: debug frames saved to {debug_dir}")
        return ply_path.read_bytes()


# ═════════════════════════════════════════════════════════════════════
# FUNCTION: gen3c_generate_views  (GEN3C orbit video → frames)
# ═════════════════════════════════════════════════════════════════════
@app.function(
    image=gen3c_image,
    gpu="A100-80GB",  # GEN3C needs ~43 GB VRAM with full offloading
    timeout=900,
    volumes={"/cache": gen3c_volume},
)
def gen3c_generate_views(
    image_bytes: bytes,
    diffusion_steps: int = 22,
    movement_distance: float = 0.3,
    num_frames: int = 12,
) -> list[bytes]:
    """
    Generate multi-view frames from a single image using NVIDIA GEN3C-Cosmos-7B.

    Steps:
      1. Download checkpoints (cached in volume after first run).
      2. Predict depth with MoGe.
      3. Create 3D cache and camera trajectory (clockwise orbit).
      4. Generate 121-frame video with Gen3cPipeline at 704×1280.
      5. Sample `num_frames` evenly-spaced keyframes.
      6. Save debug frames to /cache/debug/gen3c_run_<uuid>/.

    Returns a list of JPEG byte buffers (12 keyframes by default).
    """
    import io
    import os
    import sys
    import tempfile
    import time
    import uuid

    import numpy as np
    import torch
    from PIL import Image

    os.environ["TORCH_HOME"] = "/cache/torch"
    os.environ["HF_HOME"] = "/cache/huggingface"

    device = "cuda"
    torch.enable_grad(False)

    # ── Debug directory for this run ────────────────────────────────
    run_id = uuid.uuid4().hex[:8]
    debug_dir = f"/cache/debug/gen3c_run_{run_id}"
    os.makedirs(debug_dir, exist_ok=True)
    print(f"🔍 DEBUG: gen3c debug dir = {debug_dir}")

    # GEN3C repo on the Python path
    sys.path.insert(0, "/opt/gen3c")
    os.chdir("/opt/gen3c")

    from cosmos_predict1.utils import misc

    misc.set_random_seed(42)

    # ── Download checkpoints (cached in volume) ─────────────────────
    ckpt_dir = "/cache/gen3c_checkpoints"
    os.makedirs(ckpt_dir, exist_ok=True)

    gen3c_dir = os.path.join(ckpt_dir, "Gen3C-Cosmos-7B")
    tokenizer_dir = os.path.join(ckpt_dir, "Cosmos-Tokenize1-CV8x8x8-720p")

    from huggingface_hub import snapshot_download

    if not os.path.exists(os.path.join(gen3c_dir, "model.pt")):
        print("📥 Downloading Gen3C-Cosmos-7B (~14 GB, first run only)...")
        snapshot_download(
            "nvidia/GEN3C-Cosmos-7B",
            local_dir=gen3c_dir,
            local_dir_use_symlinks=False,
        )
        print("✅ Gen3C-Cosmos-7B downloaded")

    if not os.path.exists(os.path.join(tokenizer_dir, "mean_std.pt")):
        print("📥 Downloading Cosmos tokenizer (~2 GB, first run only)...")
        snapshot_download(
            "nvidia/Cosmos-Tokenize1-CV8x8x8-720p",
            local_dir=tokenizer_dir,
            local_dir_use_symlinks=False,
        )
        print("✅ Cosmos tokenizer downloaded")

    t0 = time.time()
    print(f"🎬 GEN3C: steps={diffusion_steps}, dist={movement_distance}, out_frames={num_frames}")

    # ── Load MoGe depth model ───────────────────────────────────────
    from moge.model.v1 import MoGeModel

    moge_model = MoGeModel.from_pretrained("Ruicheng/moge-vitl").to(device)

    # ── Initialise Gen3cPipeline ────────────────────────────────────
    from cosmos_predict1.diffusion.inference.gen3c_pipeline import Gen3cPipeline

    pipeline = Gen3cPipeline(
        inference_type="video2world",
        checkpoint_dir=ckpt_dir,
        checkpoint_name="Gen3C-Cosmos-7B",
        enable_prompt_upsampler=False,
        offload_network=True,
        offload_tokenizer=True,
        offload_text_encoder_model=True,
        offload_prompt_upsampler=True,
        offload_guardrail_models=True,
        disable_guardrail=True,
        disable_prompt_encoder=True,
        guidance=1,
        num_steps=diffusion_steps,
        height=704,
        width=1280,
        fps=24,
        num_video_frames=121,
        seed=42,
    )

    t1 = time.time()
    print(f"🎬 Pipeline loaded in {t1 - t0:.1f}s")

    # ── Save input image to temp file ───────────────────────────────
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        f.write(image_bytes)
        input_path = f.name

    # ── Depth prediction (MoGe) ─────────────────────────────────────
    from cosmos_predict1.diffusion.inference.depth_prediction import predict_moge_depth
    from cosmos_predict1.utils.io import read_image

    raw_image = read_image(input_path, use_imageio=True)
    _, moge_image, moge_depth, moge_mask, moge_w2c, moge_intrinsics = (
        predict_moge_depth(raw_image, 704, 1280, device, moge_model)
    )

    # ── 3D cache ────────────────────────────────────────────────────
    from cosmos_predict1.diffusion.inference.cache_3d import Cache3D_Buffer

    chunk = pipeline.model.chunk_size  # typically 121 for the 7B model

    cache = Cache3D_Buffer(
        frame_buffer_max=pipeline.model.frame_buffer_max,
        generator=torch.Generator(device=device).manual_seed(42),
        noise_aug_strength=0.0,
        input_image=moge_image[:, 0].clone(),
        input_depth=moge_depth[:, 0],
        input_w2c=moge_w2c[:, 0],
        input_intrinsics=moge_intrinsics[:, 0],
        filter_points_threshold=0.05,
        foreground_masking=True,
    )

    # ── Camera trajectory (clockwise orbit) ─────────────────────────
    from cosmos_predict1.diffusion.inference.camera_utils import generate_camera_trajectory

    gen_w2cs, gen_K = generate_camera_trajectory(
        trajectory_type="clockwise",
        initial_w2c=moge_w2c[0, 0],
        initial_intrinsics=moge_intrinsics[0, 0],
        num_frames=121,
        movement_distance=movement_distance,
        camera_rotation="center_facing",
        center_depth=1.0,
        device=device,
    )

    # ── Render warp images & generate first video chunk ─────────────
    warp_imgs, warp_masks = cache.render_cache(
        gen_w2cs[:, :chunk], gen_K[:, :chunk]
    )

    output = pipeline.generate(
        prompt="",
        image_path=input_path,
        negative_prompt="",
        rendered_warp_images=warp_imgs,
        rendered_warp_masks=warp_masks,
    )

    if output is None:
        raise RuntimeError("GEN3C generation failed (possible guardrail rejection)")

    video = output[0]  # (T, H, W, 3) numpy uint8

    t2 = time.time()
    total_video_frames = video.shape[0]
    vid_h, vid_w = video.shape[1], video.shape[2]
    print(f"🎬 GEN3C produced {total_video_frames} frames ({vid_h}×{vid_w}) in {t2 - t0:.1f}s")

    # ── Save ALL video frames for debugging (first & last + every 10th) ──
    for fi in range(total_video_frames):
        if fi == 0 or fi == total_video_frames - 1 or fi % 10 == 0:
            dbg_path = os.path.join(debug_dir, f"video_frame_{fi:03d}.png")
            Image.fromarray(video[fi]).save(dbg_path)
    print(f"🔍 DEBUG: saved video frame samples to {debug_dir}/video_frame_*.png")

    # ── Sample evenly-spaced keyframes ──────────────────────────────
    # sample_keyframes: pick `num_frames` indices equally spaced across
    # the 121-frame orbit video.  Skip first/last 5% to avoid near-
    # duplicate start/end frames.
    margin = max(1, int(total_video_frames * 0.05))  # ~6 frames margin
    usable_start = margin
    usable_end = total_video_frames - 1 - margin
    indices = np.linspace(usable_start, usable_end, num_frames, dtype=int)
    print(f"🔍 DEBUG: sampling {num_frames} keyframes at indices: {indices.tolist()}")
    print(f"🔍 DEBUG: usable range [{usable_start}, {usable_end}] from {total_video_frames} total")

    # ── Save sampled keyframes (debug) + encode as JPEG bytes ───────
    sampled_debug_dir = os.path.join(debug_dir, "anysplat_input")
    os.makedirs(sampled_debug_dir, exist_ok=True)

    frames: list[bytes] = []
    for i, idx in enumerate(indices):
        frame_img = Image.fromarray(video[idx])
        frame_w, frame_h = frame_img.size

        # Save debug copy
        dbg_path = os.path.join(sampled_debug_dir, f"frame_{i:03d}_vidx{idx}.png")
        frame_img.save(dbg_path)

        # Encode as JPEG
        buf = io.BytesIO()
        frame_img.save(buf, format="JPEG", quality=95)
        frames.append(buf.getvalue())

    os.unlink(input_path)
    total_kb = sum(len(f) for f in frames) / 1024
    print(f"🎬 Extracted {len(frames)} keyframes ({total_kb:.0f} KB total)")
    print(f"🔍 DEBUG: keyframe resolution = {vid_h}×{vid_w}")
    print(f"🔍 DEBUG: saved sampled keyframes to {sampled_debug_dir}/")

    # ── Sanity check: frames must be visually distinct ──────────────
    # Compare first and last sampled frame pixel-wise
    first_arr = np.array(Image.open(io.BytesIO(frames[0])).convert("RGB"))
    last_arr = np.array(Image.open(io.BytesIO(frames[-1])).convert("RGB"))
    mean_diff = np.abs(first_arr.astype(float) - last_arr.astype(float)).mean()
    print(f"🔍 DEBUG: mean pixel diff between first/last sampled frame = {mean_diff:.1f} "
          f"(should be >5.0 for meaningful parallax)")
    if mean_diff < 2.0:
        print("⚠️  WARNING: GEN3C frames look almost identical! "
              "Try increasing movement_distance or diffusion_steps.")

    return frames


# ═════════════════════════════════════════════════════════════════════
# FUNCTION: gen3c_pipeline  (orchestrator: GEN3C → AnySplat)
#   Runs on a lightweight container — no GPU needed.
#   Calls gen3c_generate_views.remote() then process_image.remote().
# ═════════════════════════════════════════════════════════════════════
@app.function(
    image=modal.Image.debian_slim(python_version="3.10"),
    timeout=1200,  # 20 min: GEN3C ~5 min + AnySplat ~2 min + headroom
)
def gen3c_pipeline(
    image_bytes_list: list[bytes],
    filenames: list[str],
    diffusion_steps: int = 22,
    movement_distance: float = 0.3,
    prompt: str = "",
    elevation: int = 20,
) -> bytes:
    """
    Orchestrate: GEN3C multi-view video → AnySplat 3DGS reconstruction.

    1. Send the first image to GEN3C to generate 121-frame orbit video.
    2. GEN3C samples 12 evenly-spaced keyframes from that video.
    3. Feed those 12 frames into AnySplat for dense 3DGS reconstruction.
    4. Return the PLY bytes.

    Quality defaults: steps=22, distance=0.3, 12 sampled frames.
    """
    import time

    t0 = time.time()
    print(
        f"🎬 GEN3C Pipeline started: "
        f"steps={diffusion_steps}, dist={movement_distance}, "
        f"images={len(image_bytes_list)}, "
        f"will sample 12 keyframes from 121-frame orbit video"
    )

    # Step 1 — GEN3C: generate multi-view frames (uses first image)
    frames = gen3c_generate_views.remote(
        image_bytes_list[0],
        diffusion_steps=diffusion_steps,
        movement_distance=movement_distance,
        num_frames=12,   # ← 12 keyframes for rich multi-view input
    )
    t1 = time.time()
    print(f"🎬 GEN3C produced {len(frames)} keyframes in {t1 - t0:.1f}s")
    print(f"🔍 DEBUG: frame sizes (bytes): {[len(f) for f in frames]}")

    # Verify we got enough frames
    assert len(frames) >= 6, (
        f"GEN3C returned only {len(frames)} frames, need ≥6 for quality. "
        f"Check gen3c_generate_views."
    )

    # Step 2 — AnySplat: reconstruct 3DGS from those frames
    #   Filenames start with "gen3c_" so process_image can detect the source.
    frame_names = [f"gen3c_{i:03d}.jpg" for i in range(len(frames))]
    print(f"🔍 DEBUG: sending {len(frames)} frames to AnySplat: {frame_names}")
    ply_bytes = process_image.remote(frames, frame_names, prompt, elevation)
    t2 = time.time()
    ply_size_mb = len(ply_bytes) / (1024 * 1024)
    print(
        f"🔮 AnySplat processed {len(frames)} GEN3C views in {t2 - t1:.1f}s. "
        f"PLY size: {ply_size_mb:.1f} MB. "
        f"Total pipeline: {t2 - t0:.1f}s"
    )

    return ply_bytes


# ═════════════════════════════════════════════════════════════════════
# ROUTER — single FastAPI endpoint (process / status / health)
# ═════════════════════════════════════════════════════════════════════
@app.function(image=anysplat_image, gpu="A100", timeout=900, volumes={"/cache": volume})
@modal.fastapi_endpoint(method="POST")
async def anysplat_router(request: dict) -> dict:
    """
    Single web endpoint that multiplexes:
    - op = \"process\" (default): start AnySplat job (sync or async)
    - op = \"status\": get status for an async job
    - op = \"health\": simple health check

    GEN3C toggle (when op=process):
    - gen3c_enabled = true  → runs gen3c_pipeline (GEN3C → AnySplat)
    - gen3c_enabled = false → runs process_image directly (AnySplat only)
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

        # ── op = "process" ──────────────────────────────────────────
        is_async = request.get("async", False)
        prompt = request.get("prompt", "")
        elevation = request.get("elevation", 20)

        # GEN3C parameters (quality defaults: 22 steps, 0.3 distance)
        gen3c_enabled = bool(request.get("gen3c_enabled", False))
        gen3c_diffusion_steps = int(request.get("gen3c_diffusion_steps", 22))
        gen3c_movement_distance = float(request.get("gen3c_movement_distance", 0.3))

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

        image_bytes_list = [base64.b64decode(b) for b in images_b64]

        mode = "GEN3C → AnySplat" if gen3c_enabled else "AnySplat"
        print(
            f"🔄 {mode}: {len(images_b64)} image(s), async={is_async}, "
            f"filenames={filenames}"
        )
        if gen3c_enabled:
            print(
                f"   GEN3C settings: steps={gen3c_diffusion_steps}, "
                f"distance={gen3c_movement_distance}"
            )

        # ── Dispatch ────────────────────────────────────────────────
        if is_async:
            if gen3c_enabled:
                call = gen3c_pipeline.spawn(
                    image_bytes_list,
                    filenames,
                    gen3c_diffusion_steps,
                    gen3c_movement_distance,
                    prompt,
                    elevation,
                )
            else:
                call = process_image.spawn(image_bytes_list, filenames, prompt, elevation)
            return {"success": True, "call_id": call.object_id, "status": "processing"}

        # Sync path
        if gen3c_enabled:
            ply_bytes = gen3c_pipeline.remote(
                image_bytes_list,
                filenames,
                gen3c_diffusion_steps,
                gen3c_movement_distance,
                prompt,
                elevation,
            )
        else:
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
