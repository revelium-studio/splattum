# Simple Upload Guide - Upload to GitHub

## ✅ Yes, You Can Upload the Full Folder!

**But exclude `node_modules`, `.next`, and `.vercel`** (they're too large and not needed).

## Quick Steps:

### Step 1: Go to GitHub
1. **Open**: https://github.com/revelium-studio/ml-sharp
2. **Click**: "uploading an existing file"

### Step 2: What to Upload

**Drag and drop these into GitHub:**

#### ✅ Upload These Folders/Files:

1. **Root files** (select all at once):
   - `runpod_handler.py`
   - `runpod_dockerfile` 
   - `modal_app.py`
   - `.gitignore`
   - `package.json`
   - All `.md` files

2. **`web/` folder** - **BUT** when uploading:
   - ✅ Upload: `web/src/`, `web/public/`, `web/package.json`, `web/tsconfig.json`, etc.
   - ❌ **DON'T upload**: `web/node_modules/`, `web/.next/`, `web/.vercel/`

**How to exclude large folders:**
- In Finder, open the `web/` folder
- Select everything EXCEPT `node_modules`, `.next`, `.vercel`
- Drag selected files/folders to GitHub

3. **`src/` folder** (if it exists) - upload the entire folder

#### ❌ Don't Upload:
- ❌ `node_modules/` (744MB - too large, will be installed automatically)
- ❌ `.next/` (build output)
- ❌ `.vercel/` (deployment config)
- ❌ `.git/` (git metadata)
- ❌ `*.tar.gz` (archives)

### Step 3: Commit
1. **Scroll down** on GitHub
2. **Commit message**: `Migrate from Modal to RunPod - Initial commit`
3. **Click**: "Commit changes"

### Step 4: Rename Dockerfile
After upload:
1. Click on `runpod_dockerfile` in GitHub
2. Click Edit (pencil icon)
3. Change filename to `Dockerfile`
4. Commit

## Alternative: Use Archive (Easiest!)

I've created a clean archive without node_modules:

1. **Extract**: `ml-sharp-for-github.tar.gz` (122KB - already excludes node_modules!)
2. **Upload extracted files** to GitHub
3. **Rename** `runpod_dockerfile` → `Dockerfile`

**This is the easiest option!** 🎯

## After Upload

Once files are on GitHub:
1. ✅ Connect to RunPod (see next steps)
2. ✅ Get Endpoint ID
3. ✅ Set Vercel environment variables
4. ✅ Deploy!

---

**TL;DR: Upload everything EXCEPT `node_modules/`, `.next/`, `.vercel/`. Use the archive I created (122KB) for easiest upload!** 🚀
