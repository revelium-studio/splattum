# Upload to GitHub - Web UI Method (100% Works)

Since the token is having write permission issues, let's use GitHub Web UI - it's the easiest and guaranteed to work!

## Step 1: Upload Files via GitHub Web UI (5 minutes)

1. **Go to**: https://github.com/revelium-studio/ml-sharp
2. You should see: "Get started by creating a new file or uploading an existing file"
3. **Click**: "uploading an existing file"

### Essential Files to Upload:

**Root files:**
- ✅ `runpod_handler.py`
- ✅ `runpod_dockerfile` (⚠️ After uploading, rename it to `Dockerfile` for RunPod)
- ✅ `modal_app.py`
- ✅ `.gitignore`
- ✅ `package.json`
- ✅ All `.md` files (documentation)

**Web folder (upload entire folder structure):**
- Upload the `web/` folder but **exclude**:
  - ❌ `web/node_modules/` (don't upload this)
  - ❌ `web/.next/` (don't upload this)
  - ❌ `web/.vercel/` (don't upload this)

**Or use the archive I created:**
- I've created `ml-sharp-for-github.tar.gz` (122KB) - extract and upload

4. **Commit message**: `Migrate from Modal to RunPod - Initial commit`
5. **Click**: "Commit changes"

### Step 2: Rename Dockerfile (Important!)

1. In the GitHub repo, find `runpod_dockerfile`
2. Click on it
3. Click "Edit" (pencil icon)
4. In the filename field, change `runpod_dockerfile` to `Dockerfile`
5. Scroll down, commit message: `Rename runpod_dockerfile to Dockerfile for RunPod`
6. Click "Commit changes"

## Step 3: Verify Files are on GitHub

Go to https://github.com/revelium-studio/ml-sharp - you should see:
- ✅ `Dockerfile` (renamed from runpod_dockerfile)
- ✅ `runpod_handler.py`
- ✅ `web/` folder
- ✅ Other files

## Step 4: Connect to RunPod (10 minutes)

1. **Go to**: https://www.runpod.io/console/serverless
2. **Click**: "Create Endpoint"

### Option A: Using GitHub (If Available)
1. **Choose**: "GitHub" as source
2. **Connect GitHub** (if not connected):
   - Click "Connect GitHub"
   - Authorize RunPod
   - Select repository: `revelium-studio/ml-sharp`
3. **Select Dockerfile path**: `Dockerfile` (or `/Dockerfile`)
4. **Configure endpoint**:
   - **Name**: `sharp-ml-processor`
   - **GPU Type**: `RTX 3090` ($0.29/hr) or `A10G`
   - **Container Disk**: `20 GB`
   - **Idle Timeout**: `30 seconds`
   - **Max Workers**: `3`
   - **Flashboot**: Enable ✅
5. **Click**: "Create"
6. **Copy the Endpoint ID** - Save this!

### Option B: Using Docker Image (Alternative)
If GitHub option isn't available:
1. **Build Docker image locally**:
   ```bash
   cd /Users/niccolomiranda/Cursor\ AI/ml-sharp
   docker build -f runpod_dockerfile -t sharp-ml-handler:latest .
   ```
2. **Push to Docker Hub** (or RunPod's registry if available)
3. **Use Docker image URL** in RunPod endpoint creation

## Step 5: Set Vercel Environment Variables

1. **Go to**: https://vercel.com/dashboard
2. **Select project**: `ml-sharp` or `revelium-studios/ml-sharp`
3. **Go to**: Settings → Environment Variables
4. **Add**:
   - `RUNPOD_API_KEY` = Your RunPod API key (you mentioned you have this)
   - `RUNPOD_ENDPOINT_ID` = The Endpoint ID from Step 4
5. **Select**: Production, Preview, Development
6. **Click**: Save

## Step 6: Deploy to Vercel

```bash
cd /Users/niccolomiranda/Cursor\ AI/ml-sharp/web
vercel --prod
```

## Done! 🎉

After these steps:
- ✅ Code is on GitHub
- ✅ RunPod endpoint is created
- ✅ Vercel is configured with RunPod credentials
- ✅ Code is deployed to Vercel
- ✅ Your app should now use RunPod instead of Modal!

## Test It!

1. Go to https://lab.revelium.studio/ml-sharp
2. Upload an image
3. **Should no longer get stuck at 90%!** 🎉

---

**Let me know when you've uploaded the files to GitHub and I can help you connect it to RunPod!**
