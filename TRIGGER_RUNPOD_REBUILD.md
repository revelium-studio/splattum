# How to Trigger RunPod Rebuild - Complete Guide

## 🎯 Why You Need to Rebuild

After setting environment variables in RunPod, you need to rebuild the endpoint so the new variables are available to your handler. Since your endpoint is connected to GitHub, the easiest way is to trigger a rebuild via a new commit.

## ✅ Method 1: Trigger via GitHub Push (Recommended)

Since your endpoint is connected to GitHub (`revelium-studio/ml-sharp`), RunPod will automatically rebuild when it detects a new commit.

### Steps:

1. **Make a small change** to trigger rebuild:
   ```bash
   cd /Users/niccolomiranda/Cursor\ AI/ml-sharp
   echo "# R2 configured" >> README.md
   git add README.md
   git commit -m "Trigger RunPod rebuild after R2 config"
   git push origin main
   ```

2. **Wait** for RunPod to detect the push (usually 1-2 minutes)

3. **Check** if rebuild started:
   - Go to: https://www.runpod.io/console/serverless
   - Click on: `ml-sharp` endpoint
   - Go to: "Builds" tab
   - Look for: A new build in progress

4. **Wait** 5-10 minutes for the build to complete

---

## ✅ Method 2: Check Builds Tab

1. **Go to**: https://www.runpod.io/console/serverless
2. **Click on**: `ml-sharp` endpoint
3. **Click**: "Builds" tab (at the top)
4. **Look for**:
   - "Rebuild" button
   - "New Build" button
   - "Trigger Build" button
5. **If you see one**: Click it to trigger rebuild
6. **If not**: Use Method 1 (GitHub push)

---

## ✅ Method 3: Edit Endpoint Configuration

Sometimes editing the endpoint configuration triggers a rebuild:

1. **Go to**: `ml-sharp` endpoint page
2. **Look for**: "Edit" or "Configure" button (usually top right)
3. **Click**: "Edit" or "Configure"
4. **Make a small change** (e.g., change Max Workers from 3 to 3 - no actual change needed)
5. **Click**: "Save" or "Update"
6. **This might trigger**: A rebuild automatically

---

## ✅ Method 4: Check if Already Rebuilding

Sometimes RunPod automatically rebuilds when environment variables are updated:

1. **Go to**: `ml-sharp` endpoint → "Builds" tab
2. **Check**: If there's already a new build in progress
3. **If yes**: Wait for it to complete ✅
4. **If no**: Use Method 1 (GitHub push)

---

## 🔍 How to Verify Rebuild Started

After triggering a rebuild (via any method):

1. **Go to**: RunPod dashboard → `ml-sharp` endpoint → "Builds" tab
2. **Look for**: New build entry with status:
   - "Building" (in progress) 🔄
   - "Queued" (waiting) ⏳
   - "Completed" (done) ✅

3. **Click on** the build to see:
   - Build logs
   - Status
   - Timeline

---

## ⏱️ Expected Timeline

- **Trigger to detection**: 1-2 minutes (if using GitHub push)**
- **Build duration**: 5-10 minutes
- **Total wait**: ~10-15 minutes from trigger to completion

---

## 🎯 What Happens After Rebuild

Once the build completes:

1. ✅ New environment variables (R2 credentials) are available
2. ✅ Handler can upload PLY files to R2
3. ✅ Jobs should no longer fail with 400 errors
4. ✅ 90% block should be resolved

---

## 🧪 After Rebuild Completes

1. **Go to**: https://lab.revelium.studio/ml-sharp
2. **Upload**: A test image
3. **Check**: If progress goes past 90%
4. **Verify**: RunPod logs show `✅ Uploaded to R2`

---

**Let's trigger the rebuild now using GitHub push!** 🚀
