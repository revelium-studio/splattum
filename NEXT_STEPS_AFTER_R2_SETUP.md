# Next Steps After R2 Setup - Complete Guide

## ✅ You've Set R2 Environment Variables

Great! Now you need to rebuild the RunPod endpoint so it picks up the new environment variables.

## 🚀 Step 1: Rebuild RunPod Endpoint

RunPod needs to rebuild with the new environment variables. There are two ways:

### Option A: Automatic Rebuild (Recommended)

1. **Go to**: https://www.runpod.io/console/serverless
2. **Click on**: `ml-sharp` endpoint
3. **Go to**: "Releases" tab (or "Builds" tab)
4. **Look for**: "Redeploy" or "Rebuild" button
5. **Click**: "Redeploy" or "Rebuild"
6. **Wait** for build to complete (usually 5-10 minutes)

### Option B: Trigger Rebuild via Git Push

RunPod will automatically rebuild when it detects changes:

1. **Make a small change** to trigger rebuild:
   ```bash
   cd /Users/niccolomiranda/Cursor\ AI/ml-sharp
   echo "# R2 configured" >> .gitignore
   git add .gitignore
   git commit -m "Trigger RunPod rebuild after R2 config"
   git push origin main
   ```

2. **Wait** for RunPod to detect the push and rebuild automatically

### Option C: Check if Rebuild Already Started

Sometimes RunPod automatically rebuilds when environment variables are updated:

1. **Go to**: https://www.runpod.io/console/serverless
2. **Click on**: `ml-sharp` endpoint
3. **Go to**: "Builds" tab
4. **Check**: If there's a new build in progress
5. **Wait** for it to complete

---

## ✅ Step 2: Verify Build Completed

1. **Go to**: RunPod dashboard → `ml-sharp` endpoint → "Builds" tab
2. **Check**: Latest build shows "Completed" (green checkmark)
3. **Verify**: Build includes the new environment variables
   - Check build logs to confirm R2 variables are available
   - Look for any errors during build

---

## 🧪 Step 3: Test the Integration

Once the build completes:

### Test 1: Upload an Image

1. **Go to**: https://lab.revelium.studio/ml-sharp
2. **Upload** a test image
3. **Watch** the processing progress
4. **Check** if it progresses past 90% (should complete now!)

### Test 2: Check RunPod Logs

1. **Go to**: RunPod dashboard → `ml-sharp` endpoint → "Logs" tab
2. **Look for**:
   - `📤 Uploading PLY to R2 bucket: ml-sharp-outputs`
   - `✅ Uploaded to R2: https://pub-...`
   - **Should NOT see**: "Failed to return job results. | 400"

### Test 3: Check Browser Console

1. **Open** browser console (F12 or Cmd+Option+I)
2. **Upload** an image
3. **Look for**:
   - `✅ Found PLY URL, downloading from R2: https://...`
   - `✅ Downloaded PLY from R2 (... bytes)`
   - `✅ Polling: Job completed, setting progress to 100%`

### Test 4: Check Vercel Logs

```bash
cd /Users/niccolomiranda/Cursor\ AI/ml-sharp/web
vercel logs https://web-beta-gilt-54.vercel.app --json | grep -i "r2\|ply"
```

Look for:
- `✅ Found PLY URL, downloading from R2`
- `✅ Downloaded PLY from R2`

---

## 🔍 Troubleshooting

### If Build Fails

**Check build logs** for errors:
- R2 credentials might be incorrect
- Bucket might not exist
- Public access might not be enabled

**Common issues**:
- `Access Denied` → Check R2 credentials are correct
- `Bucket not found` → Verify bucket name matches
- `Public access denied` → Enable public access in bucket settings

### If Upload Fails

**Check RunPod logs** for:
- `⚠️ R2 credentials not configured` → Environment variables not set correctly
- `❌ Failed to upload to R2` → Check R2 credentials and bucket permissions
- `❌ R2 upload error` → Check bucket exists and public access is enabled

### If Still Stuck at 90%

**Check**:
1. RunPod logs show R2 upload succeeded?
2. Browser console shows URL being downloaded?
3. Vercel logs show successful download from R2?

**If R2 upload works but download fails**:
- Check public URL is correct
- Verify bucket has public access enabled
- Check custom domain is configured (if using one)

---

## ✅ Success Indicators

You'll know it's working when:

1. ✅ **Processing completes** (progress goes to 100%)
2. ✅ **3D viewer loads** with the PLY file
3. ✅ **RunPod logs show**: `✅ Uploaded to R2: https://...`
4. ✅ **Browser console shows**: `✅ Downloaded PLY from R2`
5. ✅ **No more 400 errors** in RunPod logs

---

## 🎯 Quick Checklist

- [ ] R2 environment variables set in RunPod
- [ ] RunPod endpoint rebuilt (check Builds tab)
- [ ] Build completed successfully (green checkmark)
- [ ] Test image uploaded
- [ ] Processing completes (progress goes to 100%)
- [ ] 3D viewer loads successfully
- [ ] RunPod logs show R2 upload success
- [ ] Browser console shows R2 download success

---

**Once all steps are complete, the 90% block should be resolved!** 🎉
