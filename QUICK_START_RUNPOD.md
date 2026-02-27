# Quick Start: RunPod Migration

## ✅ Code Migration Complete!

The code has been migrated from Modal to RunPod. Here's what you need to do:

## 🚀 Quick Setup (5 Steps)

### Step 1: Get RunPod API Key (2 minutes)
1. Go to https://www.runpod.io/
2. Sign up / Login
3. Go to Settings → API Keys
4. Copy your API key

### Step 2: Deploy Handler to RunPod (10 minutes)

**Option A: Using RunPod Web UI (Easiest)**
1. Go to https://www.runpod.io/console/serverless
2. Click "Create Endpoint"
3. Name: `sharp-ml-processor`
4. **Template**: Choose "Custom" or "Blank"
5. **Docker Image**: 
   - Click "Build from Dockerfile"
   - Upload `runpod_dockerfile` (rename it to `Dockerfile`)
   - OR manually build and push:
     ```bash
     docker build -f runpod_dockerfile -t sharp-ml-handler .
     docker tag sharp-ml-handler:latest runpod.io/YOUR_USERNAME/sharp-ml-handler:latest
     docker push runpod.io/YOUR_USERNAME/sharp-ml-handler:latest
     ```
6. **GPU**: Choose `RTX 3090` ($0.29/hr) or `A10G`
7. **Container Disk**: 20 GB
8. **Idle Timeout**: 30 seconds
9. **Max Workers**: 3
10. **Flashboot**: Enable ✅
11. Click "Create"
12. **Copy the Endpoint ID** (you'll need this!)

**Option B: Using RunPod CLI**
```bash
pip install runpod
runpod serverless create \
  --name "sharp-ml-processor" \
  --image "YOUR_USERNAME/sharp-ml-handler:latest" \
  --gpu-type "RTX 3090" \
  --container-disk 20 \
  --idle-timeout 30
```

### Step 3: Set Vercel Environment Variables (2 minutes)

1. Go to https://vercel.com/dashboard
2. Select your project: `ml-sharp` or `revelium-studios/ml-sharp`
3. Go to **Settings** → **Environment Variables**
4. Add these two variables:
   - `RUNPOD_API_KEY` = `your-runpod-api-key-from-step-1`
   - `RUNPOD_ENDPOINT_ID` = `your-endpoint-id-from-step-2`
5. Select **Production**, **Preview**, and **Development**
6. Click **Save**

### Step 4: Deploy to Vercel (1 minute)

```bash
cd web
vercel --prod
```

### Step 5: Test! 🎉

1. Go to https://lab.revelium.studio/ml-sharp
2. Upload an image
3. **Expected behavior**:
   - ✅ Progress should reach 90% and stay there while processing
   - ✅ Should complete successfully (no more 90% blocking!)
   - ✅ PLY file should be returned and displayed

## 🔍 Verify It's Working

### Check Vercel Logs:
```bash
cd web
vercel logs --follow
```

Look for:
- `🚀 Creating RunPod job for {filename}...`
- `✅ RunPod job created with ID: {job_id}`
- `🔍 Polling RunPod status for job ID: {job_id}`
- `✅ Processing completed successfully`

### Check RunPod Dashboard:
1. Go to https://www.runpod.io/console/serverless
2. Click on your endpoint
3. Check "Jobs" tab
4. Should see job status: `IN_QUEUE` → `IN_PROGRESS` → `COMPLETED`

## 🐛 Troubleshooting

### "RunPod not configured" error
- ✅ Check environment variables are set in Vercel
- ✅ Verify variable names: `RUNPOD_API_KEY` and `RUNPOD_ENDPOINT_ID`
- ✅ Make sure they're set for **Production** environment
- ✅ Redeploy: `vercel --prod`

### "Failed to create RunPod job"
- ✅ Verify API key is correct
- ✅ Verify endpoint ID is correct
- ✅ Check RunPod dashboard - is endpoint active?
- ✅ Check RunPod billing - do you have credits?

### Job stuck in "processing"
- ✅ Check RunPod dashboard for actual job status
- ✅ Check RunPod logs for errors
- ✅ Verify handler code is correct
- ✅ Check if GPU is available

### Handler errors
- ✅ Check RunPod logs: Dashboard → Endpoint → Logs
- ✅ Verify Docker image built correctly
- ✅ Test handler locally first (see RUNPOD_DEPLOYMENT.md)

## 📊 What Changed

### Files Updated:
- ✅ `web/src/app/api/process/route.ts` - Now uses RunPod instead of Modal
- ✅ `web/src/app/api/process/route.ts` - Status polling uses RunPod API

### Files Created:
- ✅ `runpod_handler.py` - Handler for RunPod serverless
- ✅ `runpod_dockerfile` - Docker image for RunPod
- ✅ `RUNPOD_DEPLOYMENT.md` - Detailed deployment guide
- ✅ `MIGRATION_SUMMARY.md` - Full migration summary
- ✅ `QUICK_START_RUNPOD.md` - This file!

## 💰 Cost Estimate

- **RTX 3090**: $0.29/hour = ~$0.01-0.05 per image (30 seconds - 5 minutes processing)
- **A10G**: $0.39/hour = ~$0.02-0.08 per image
- **Idle costs**: $0 (workers shut down after 30 seconds idle)

**Much cheaper than Modal!**

## 🎯 Next Steps After Setup

1. ✅ Test with multiple images
2. ✅ Monitor RunPod dashboard for any issues
3. ✅ Monitor costs in RunPod billing
4. ✅ Adjust `max_workers` based on traffic
5. ✅ Consider enabling Network Volume for model caching

## 📚 Documentation

- **Detailed Guide**: See `RUNPOD_DEPLOYMENT.md`
- **Full Migration Details**: See `MIGRATION_SUMMARY.md`
- **RunPod Docs**: https://docs.runpod.io
- **RunPod Support**: support@runpod.io

## 🆘 Need Help?

If you run into issues:
1. Check RunPod dashboard for errors
2. Check Vercel logs: `vercel logs --follow`
3. Check RunPod documentation: https://docs.runpod.io
4. Check this troubleshooting guide above

---

**Ready to migrate? Follow the 5 steps above and you should be done in ~15 minutes!** 🚀
