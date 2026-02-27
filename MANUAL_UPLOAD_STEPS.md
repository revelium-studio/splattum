# Manual Upload to GitHub - Step by Step

Since git push is having token permission issues, here's the easiest way to get your code on GitHub:

## Option 1: Upload via GitHub Web UI (Recommended - 5 minutes)

### Step 1: Go to Your Repository
1. **Go to**: https://github.com/revelium-studio/ml-sharp
2. You should see: "Quick setup — if you've done this kind of thing before"

### Step 2: Upload Files via Web UI

**Method A: Upload Files Individually**
1. Click **"uploading an existing file"**
2. Click **"choose your files"**
3. **Upload these essential files**:
   - ✅ `runpod_handler.py`
   - ✅ `runpod_dockerfile` (rename to `Dockerfile` if RunPod requires it)
   - ✅ All files in `web/` folder (upload the entire folder)
   - ✅ `modal_app.py`
   - ✅ `.gitignore`
   - ✅ `package.json`

4. **Commit message**: `Migrate from Modal to RunPod - Initial commit`
5. Click **"Commit changes"**

**Method B: Use the Archive I Created**
1. I've created `ml-sharp-essential-files.tar.gz` in your project folder
2. Extract it and upload the files

### Step 3: Verify Upload
- Go to https://github.com/revelium-studio/ml-sharp
- You should see all your files

## Option 2: Use GitHub Desktop (If Installed)

1. **Install GitHub Desktop**: https://desktop.github.com/
2. **Open** GitHub Desktop
3. **File** → **Add Local Repository**
4. **Browse** to `/Users/niccolomiranda/Cursor AI/ml-sharp`
5. **Click** "Publish repository"
6. **Name**: `ml-sharp`
7. **Description**: `ML-Sharp: Transform photographs into explorable 3D scenes using SHARP ML model on RunPod`
8. **Visibility**: Public (or Private)
9. **Click** "Publish repository"

## Option 3: Set Up SSH (Most Reliable - 10 minutes)

### Step 1: Generate SSH Key
```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
# Press Enter for default location
# Press Enter for passphrase (or set one for security)
```

### Step 2: Copy Public Key
```bash
cat ~/.ssh/id_ed25519.pub
# Copy the output (starts with ssh-ed25519)
```

### Step 3: Add to GitHub
1. **Go to**: https://github.com/settings/keys
2. **Click**: "New SSH key"
3. **Title**: `MacBook - ml-sharp`
4. **Key**: Paste the output from step 2
5. **Click**: "Add SSH key"

### Step 4: Test SSH Connection
```bash
ssh -T git@github.com
# Should say: "Hi revelium-studio! You've successfully authenticated..."
```

### Step 5: Update Remote and Push
```bash
cd /Users/niccolomiranda/Cursor\ AI/ml-sharp
git remote set-url origin git@github.com:revelium-studio/ml-sharp.git
git push -u origin main
```

## After Code is on GitHub

### Connect to RunPod:

1. **Go to**: https://www.runpod.io/console/serverless
2. **Click**: "Create Endpoint"
3. **Choose**: "GitHub" as source
4. **Connect GitHub** (if not already connected):
   - Click "Connect GitHub"
   - Authorize RunPod to access your GitHub account
   - Select repositories you want to give access to
5. **Select repository**: `revelium-studio/ml-sharp`
6. **Select Dockerfile path**: `runpod_dockerfile` (or rename it to `Dockerfile` in repo)
7. **Configure endpoint**:
   - **Name**: `sharp-ml-processor`
   - **GPU Type**: `RTX 3090` ($0.29/hr) or `A10G`
   - **Container Disk**: `20 GB`
   - **Idle Timeout**: `30 seconds`
   - **Max Workers**: `3`
   - **Flashboot**: Enable ✅
8. **Click**: "Create"
9. **Copy the Endpoint ID** - You'll need this for Vercel environment variables!

## Essential Files Needed for RunPod

Make sure these files are in the GitHub repo:

- ✅ `runpod_handler.py` - Handler for RunPod serverless
- ✅ `runpod_dockerfile` - Docker image for RunPod (Rename to `Dockerfile` if needed)
- ✅ `web/src/app/api/process/route.ts` - Updated API route using RunPod
- ✅ `.gitignore` - Excludes node_modules, etc.

**Once uploaded, you can connect the repo to RunPod!**
