# Upload Full Folder to GitHub - Simple Guide

## ✅ Yes! You Can Upload the Entire Folder

GitHub's web UI allows you to upload entire folders and files. Here's how:

## Step 1: Go to Your Repository

1. **Go to**: https://github.com/revelium-studio/ml-sharp
2. You should see: "Get started by creating a new file or uploading an existing file"
3. **Click**: "uploading an existing file"

## Step 2: Upload Files

### Option A: Drag & Drop Entire Folder (Easiest)

1. **Open Finder** on your Mac
2. **Navigate to**: `/Users/niccolomiranda/Cursor AI/ml-sharp`
3. **Drag and drop** these folders/files into GitHub:
   - ✅ `web/` folder (entire folder)
   - ✅ Root files: Select all these files:
     - `runpod_handler.py`
     - `runpod_dockerfile` (will rename to `Dockerfile` later)
     - `modal_app.py`
     - `.gitignore`
     - `package.json`
     - All `.md` files (documentation)

**⚠️ Important**: When uploading the `web/` folder, **exclude** these subfolders:
   - ❌ `web/node_modules/` (too large, ~200MB+)
   - ❌ `web/.next/` (build output)
   - ❌ `web/.vercel/` (deployment config)

**How to exclude**: Don't drag the `node_modules`, `.next`, or `.vercel` folders inside `web/`.

### Option B: Upload Selectively (Recommended)

Upload folder by folder to avoid uploading large/unnecessary files:

1. **First, upload root files**:
   - Select and drag: `runpod_handler.py`, `runpod_dockerfile`, `modal_app.py`, `.gitignore`, `package.json`, `*.md`

2. **Then, upload web folder**:
   - Open the `web/` folder in Finder
   - Select **all files and folders EXCEPT**:
     - ❌ `node_modules/`
     - ❌ `.next/`
     - ❌ `.vercel/`
   - Drag and drop into GitHub's web UI (you can create a `web/` folder first)

### Option C: Use the Archive I Created (Easiest)

I've created `ml-sharp-for-github.tar.gz` (122KB) - it excludes node_modules:

1. **Extract the archive**:
   ```bash
   cd /Users/niccolomiranda/Cursor\ AI/ml-sharp
   tar -xzf ml-sharp-for-github.tar.gz
   # This will extract all essential files
   ```

2. **Upload the extracted files** to GitHub

## Step 3: Commit

1. **Scroll down** on GitHub's upload page
2. **Commit message**: `Migrate from Modal to RunPod - Initial commit`
3. **Description** (optional): `Add RunPod integration, handler, Dockerfile, and updated API routes`
4. **Click**: "Commit changes"

## Step 4: Rename Dockerfile (Important!)

After uploading:

1. **Find** `runpod_dockerfile` in the GitHub repo
2. **Click** on it
3. **Click** the pencil icon (Edit)
4. **Change filename** from `runpod_dockerfile` to `Dockerfile`
5. **Commit message**: `Rename runpod_dockerfile to Dockerfile for RunPod`
6. **Click**: "Commit changes"

## What Gets Installed Automatically

GitHub will show your code, but these will be **installed automatically** when RunPod builds:
- ✅ `node_modules/` - Will be installed via `npm install` in `web/`
- ✅ Python packages - Will be installed via `pip install` in the Dockerfile

## Verify Upload

After uploading, go to https://github.com/revelium-studio/ml-sharp - you should see:
- ✅ `Dockerfile` (after renaming)
- ✅ `runpod_handler.py`
- ✅ `web/` folder with source code
- ✅ `modal_app.py`
- ✅ `.gitignore`
- ✅ Documentation files (`.md`)

**No need to upload**: `node_modules/`, `.next/`, `.vercel/`, `.git/` - these are generated/ignored.

## Quick Checklist

Before uploading, make sure you have:
- ✅ `runpod_handler.py`
- ✅ `runpod_dockerfile` (rename to `Dockerfile` after)
- ✅ `modal_app.py`
- ✅ `web/` folder (source code, exclude node_modules/.next/.vercel)
- ✅ `.gitignore`
- ✅ `package.json`
- ✅ Documentation files

## After Upload

Once files are on GitHub:
1. ✅ Rename `runpod_dockerfile` → `Dockerfile`
2. ✅ Connect to RunPod (see `UPLOAD_TO_GITHUB.md`)
3. ✅ Set Vercel environment variables
4. ✅ Deploy!

**You're all set! Just drag and drop (excluding node_modules/.next/.vercel) and you're good to go!** 🚀
