# Rebuild RunPod Endpoint and Test - Step-by-Step Guide

## ✅ Environment Variables Set!

Great! You've added the R2 environment variables to RunPod. Now you need to rebuild the endpoint so the new variables take effect.

---

## 🚀 Step 1: Rebuild RunPod Endpoint

### Option A: Rebuild from Releases Tab (Recommended)

1. **Go to**: https://www.runpod.io/console/serverless
2. **Click on**: `ml-sharp` endpoint
3. **Click**: "Releases" tab (at the top)
4. **Look for**: "New Release" or "Update Release" button
5. **Click**: "New Release" or "Update Release"
6. **If prompted**: Confirm that you want to create a new release with the updated environment variables
7. **Wait**: 5-10 minutes for the build to complete

### Option B: Rebuild from Builds Tab

1. **Go to**: RunPod dashboard → `ml-sharp` endpoint
2. **Click**: "Builds" tab (at the top)
3. **Look for**: "Rebuild" or "New Build" button
4. **Click**: "Rebuild" or "New Build"
5. **Wait**: 5-10 minutes for the build to complete

### Option C: Automatic Rebuild

Sometimes RunPod automatically rebuilds when environment variables are updated. Check:

1. **Go to**: `ml-sharp` endpoint → "Builds" tab
2. **Check**: If there's already a new build in progress
3. **If yes**: Wait for it to complete
4. **If no**: Use Option A or B above

---

## ✅ Step 2: Verify Build Completed Successfully

1. **Go to**: RunPod dashboard → `ml-sharp` endpoint → "Builds" tab
2. **Check**: Latest build shows "Completed" (green checkmark) ✅
3. **Look for**: No errors in the build logs
4. **Verify**: Build status shows "Ready" or "Active"

**If build failed**:
- Check build logs for errors
- Common issues:
  - R2 credentials incorrect → Verify credentials
  - Bucket doesn't exist → Create bucket in Cloudflare R2
  - Public access not enabled → Enable in bucket settings

---

## 🧪 Step 3: Test the Integration

Once the build completes successfully:

### Test 1: Upload an Image

1. **Go to**: https://lab.revelium.studio/ml-sharp
2. **Click**: "Upload" or drag and drop an image
3. **Watch**: The processing progress
4. **Success**: Progress should go past 90% and reach 100% ✅

### Test 2: Check RunPod Logs

1. **Go to**: RunPod dashboard → `ml-sharp` endpoint → "Logs" tab
2. **Look for**:
   - ✅ `📤 Uploading PLY to R2 bucket: ml-sharp-outputs`
   - ✅ `✅ Uploaded to R2: https://pub-...`
   - ✅ `✅ Processing completed successfully!`
   - ❌ **Should NOT see**: "Failed to return job results. | 400"

### Test 3: Check Browser Console

1. **Open** browser console (F12 or Cmd+Option+I)
2. **Upload** an image
3. **Look for**:
   - ✅ `✅ Found PLY URL, downloading from R2: https://...`
   - ✅ `✅ Downloaded PLY from R2 (... bytes)`
   - ✅ `✅ Polling: Job completed, setting progress to 100%`
   - ✅ `✅ Polling: Transitioning to viewer`

### Test 4: Check Vercel Logs

To see what's happening on the API side:

```bash
cd /Users/niccolomiranda/Cursor\ AI/ml-sharp/web
vercel logs https://web-beta-gilt-54.vercel.app --json | grep -i "r2\|ply\|runpod" | tail -20
```

**Look for**:
- ✅ `✅ Found PLY URL, downloading from R2`
- ✅ `✅ Downloaded PLY from R2`
- ✅ `✅ RunPod job completed`

---

## ✅ Success Indicators

You'll know it's working when:

1. ✅ **Processing completes** (progress goes to 100%)
2. ✅ **3D viewer loads** with the PLY file
3. ✅ **RunPod logs show**: `✅ Uploaded to R2: https://...`
4. ✅ **Browser console shows**: `✅ Downloaded PLY from R2`
5. ✅ **No more 400 errors** in RunPod logs
6. ✅ **No more 90% block**

---

## 🔍 Troubleshooting

### If Build Fails

**Check build logs** for errors:

1. **Go to**: Builds tab → Click on failed build → "Build Logs"
2. **Common errors**:
   - `ModuleNotFoundError: No module named 'boto3'` → Rebuild should fix (boto3 added to Dockerfile)
   - `Access Denied` → Check R2 credentials are correct
   - `Bucket not found` → Verify bucket name matches
   - `Public access denied` → Enable public access in R2 bucket

### If Still Stuck at 90%

**Check RunPod logs** for:

1. **R2 Upload Issues**:
   - `⚠️ R2 credentials not configured` → Environment variables not set correctly
   - `❌ Failed to upload to R2` → Check R2 credentials and bucket permissions
   - `❌ R2 upload error` → Check bucket exists and public access enabled

2. **Status Polling Issues**:
   - `📊 Polling response status: processing` (never changes) → Job might still be processing
   - `❌ RunPod status check failed` → Check RunPod endpoint is active

3. **Download Issues**:
   - `❌ Failed to download PLY from R2` → Check public URL is correct and accessible

### If R2 Upload Works but Download Fails

**Check**:
1. **Public URL is correct**: `https://pub-<account-id>.r2.dev/<bucket-name>/<file-path>`
2. **Bucket has public access enabled**: Cloudflare R2 → Bucket → Settings → Public Access
3. **File is accessible**: Try opening the R2 URL directly in browser

---

## 🎯 Quick Checklist

- [ ] Environment variables set in RunPod
- [ ] Endpoint rebuilt (check Builds tab)
- [ ] Build completed successfully (green checkmark)
- [ ] Test image uploaded
- [ ] Processing completes (progress goes to 100%)
- [ ] 3D viewer loads successfully
- [ ] RunPod logs show R2 upload success
- [ ] Browser console shows R2 download success
- [ ] No more 90% block

---

## 📊 Expected Timeline

- **Rebuild time**: 5-10 minutes (depending on Docker image size)
- **Test processing**: 2-5 minutes per image (depending on image complexity)
- **Total wait**: ~10-15 minutes from rebuild start to first successful test

---

**Once the rebuild completes, test it and let me know if the 90% block is resolved!** 🚀
