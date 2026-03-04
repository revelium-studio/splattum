#!/usr/bin/env python3
"""
Integration test: compare AnySplat (single image) vs GEN3C → AnySplat (multi-view).

Usage:
    modal run test_pipeline.py -- examples/input.jpg

What it does:
  1. Runs AnySplat with a single image (GEN3C OFF) → output_single.ply
  2. Runs GEN3C + AnySplat (GEN3C ON, steps=22, dist=0.3) → output_multi.ply
  3. Saves both PLY files + prints stats for visual comparison.

The output_multi.ply MUST show denser coverage and fewer holes than output_single.ply.
If not, inspect:
  - GEN3C sampled frames in /cache/debug/gen3c_run_*/anysplat_input/
  - AnySplat input tensor shape in logs
  - AnySplat warnings
"""

import modal

app = modal.App("anysplat-test")


@app.local_entrypoint()
def main():
    import sys
    import time
    from pathlib import Path

    if len(sys.argv) < 2:
        print("Usage: modal run test_pipeline.py -- <image_path>")
        print("  e.g. modal run test_pipeline.py -- examples/input.jpg")
        return

    image_path = Path(sys.argv[1])
    if not image_path.exists():
        print(f"❌ Image not found: {image_path}")
        return

    image_bytes = image_path.read_bytes()
    print(f"📷 Input: {image_path} ({len(image_bytes) / 1024:.0f} KB)")

    # Import the production app's functions
    from modal_app import process_image, gen3c_pipeline

    # ── Test 1: AnySplat ONLY (single image, no GEN3C) ──────────────
    print("\n" + "=" * 60)
    print("TEST 1: AnySplat only (single image, GEN3C OFF)")
    print("=" * 60)
    t0 = time.time()
    try:
        ply_single = process_image.remote(
            [image_bytes],
            [image_path.name],
            prompt="",
            elevation=20,
        )
        t1 = time.time()
        out_single = Path("debug/output_single.ply")
        out_single.parent.mkdir(parents=True, exist_ok=True)
        out_single.write_bytes(ply_single)
        print(f"✅ Single-image PLY: {len(ply_single):,} bytes ({len(ply_single)/1024/1024:.1f} MB)")
        print(f"   Saved to: {out_single}")
        print(f"   Time: {t1 - t0:.1f}s")
    except Exception as e:
        print(f"❌ Single-image test failed: {e}")
        ply_single = None

    # ── Test 2: GEN3C → AnySplat (multi-view) ───────────────────────
    print("\n" + "=" * 60)
    print("TEST 2: GEN3C → AnySplat (multi-view, GEN3C ON)")
    print("  diffusion_steps=22, movement_distance=0.3")
    print("=" * 60)
    t0 = time.time()
    try:
        ply_multi = gen3c_pipeline.remote(
            [image_bytes],
            [image_path.name],
            diffusion_steps=22,
            movement_distance=0.3,
            prompt="",
            elevation=20,
        )
        t1 = time.time()
        out_multi = Path("debug/output_multi.ply")
        out_multi.parent.mkdir(parents=True, exist_ok=True)
        out_multi.write_bytes(ply_multi)
        print(f"✅ Multi-view PLY: {len(ply_multi):,} bytes ({len(ply_multi)/1024/1024:.1f} MB)")
        print(f"   Saved to: {out_multi}")
        print(f"   Time: {t1 - t0:.1f}s")
    except Exception as e:
        print(f"❌ Multi-view test failed: {e}")
        ply_multi = None

    # ── Summary ──────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("COMPARISON SUMMARY")
    print("=" * 60)
    if ply_single:
        print(f"  Single-image PLY: {len(ply_single):,} bytes")
    if ply_multi:
        print(f"  Multi-view PLY:   {len(ply_multi):,} bytes")
    if ply_single and ply_multi:
        ratio = len(ply_multi) / len(ply_single)
        print(f"  Size ratio:       {ratio:.2f}x")
        if ratio > 1.2:
            print("  → Multi-view is larger → likely more Gaussians → denser coverage ✅")
        elif ratio > 0.8:
            print("  → Similar size → check debug frames for parallax quality")
        else:
            print("  → Multi-view is smaller → something may be wrong ⚠️")
    print()
    print("Next steps:")
    print("  1. Open both PLY files in a 3DGS viewer")
    print("  2. Check /cache/debug/ on Modal for GEN3C frames")
    print("  3. output_multi should have denser coverage, fewer holes")
    print("  4. If identical, GEN3C frames may lack parallax — increase movement_distance")
