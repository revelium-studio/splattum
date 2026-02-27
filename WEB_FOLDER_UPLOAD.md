# Upload Web Folder - Quick Guide

## ✅ Web Folder is Ready!

I've extracted a clean copy of your `web/` folder (excluding node_modules/.next/.vercel) to:

**📁 `~/Desktop/web-upload/web/`**

This folder contains **all 29 essential files** needed for RunPod, ready to upload!

## 🚀 Quick Upload Steps (2 minutes)

### Step 1: Open the Folder
1. **Open Finder** (I've opened it for you!)
2. **Navigate to**: Desktop → `web-upload` → `web`
3. You should see:
   - `src/` folder
   - `public/` folder
   - Config files (package.json, next.config.ts, etc.)

### Step 2: Select All Files
1. **Select everything** inside the `web` folder:
   - Click `src/` folder (entire folder)
   - Click `public/` folder (entire folder)
   - Select all config files (package.json, next.config.ts, tsconfig.json, etc.)
   - **OR** just select everything with Cmd+A

### Step 3: Upload to GitHub
1. **Go to**: https://github.com/revelium-studio/ml-sharp
2. **Click**: "Add file" → "Upload files"
3. **Drag and drop** all the selected files/folders from Finder to GitHub
4. **Scroll down** on GitHub
5. **Commit message**: `Add web folder: Next.js app with RunPod integration`
6. **Description** (optional): `Includes src/, public/, and all config files. Excludes node_modules/.next/.vercel`
7. **Click**: "Commit changes"

### Step 4: Verify Upload
After uploading, check that you see:
- ✅ `web/src/` folder with all files
- ✅ `web/public/` folder with all files
- ✅ `web/package.json`
- ✅ `web/next.config.ts`
- ✅ `web/tsconfig.json`
- ✅ All other config files

## 📋 Files in the Upload:

### Folders:
- ✅ `web/src/` - **Entire folder** (all source code)
- ✅ `web/public/` - **Entire folder** (all public assets)

### Config Files:
- ✅ `web/package.json`
- ✅ `web/package-lock.json`
- ✅ `web/next.config.ts`
- ✅ `web/tsconfig.json`
- ✅ `web/eslint.config.mjs`
- ✅ `web/postcss.config.mjs`
- ✅ `web/.gitignore`
- ✅ `web/.vercelignore`
- ✅ `web/README.md`

**Total: 29 files** (excluding node_modules/.next/.vercel)

## ❌ Don't Upload (Already Excluded):
- ❌ `node_modules/` - Will be installed via `npm install`
- ❌ `.next/` - Build output (generated)
- ❌ `.vercel/` - Deployment config (local only)
- ❌ `.DS_Store` - macOS system file

## After Upload:

Once the web folder is uploaded:
1. ✅ **Verify** all files are on GitHub
2. ✅ **Rename** `runpod_dockerfile` → `Dockerfile` (if not done)
3. ✅ **Connect to RunPod**: https://www.runpod.io/console/serverless
4. ✅ **Get Endpoint ID** from RunPod
5. ✅ **Set Vercel environment variables**:
   - `RUNPOD_API_KEY` = Your RunPod API key
   - `RUNPOD_ENDPOINT_ID` = RunPod Endpoint ID
6. ✅ **Deploy**: `cd web && vercel --prod`

## Alternative: Use Archive

If drag-and-drop doesn't work, you can:
1. **Extract**: `web-folder-clean.tar.gz` (145KB) - I've created this too
2. **Upload** the extracted files manually

**The archive is at**: `/Users/niccolomiranda/Cursor AI/ml-sharp/web-folder-clean.tar.gz`

---

**Ready to upload? The folder is on your Desktop - just drag and drop!** 🚀
