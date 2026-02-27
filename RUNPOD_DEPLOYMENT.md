# RunPod Deployment Guide for SHARP ML Model

## Prerequisites

1. **RunPod Account**: Sign up at https://www.runpod.io/
2. **RunPod API Key**: Get your API key from https://www.runpod.io/console/user/settings
3. **Docker**: Install Docker on your machine for building images

## Step 1: Prepare Your Environment

### Set up RunPod CLI (Optional but Recommended)
```bash
pip install runpod
```

### Get Your API Key
1. Go to https://www.runpod.io/console/user/settings
2. Copy your API key
3. Set it as an environment variable:
   ```bash
   export RUNPOD_API_KEY="your-api-key-here"
   ```

## Step 2: Build and Push Docker Image

### Build the Docker Image
```bash
cd /Users/niccolomiranda/Cursor\ AI/ml-sharp
docker build -f runpod_dockerfile -t sharp-ml-handler:latest .
```

### Test Locally (Optional)
```bash
docker run -it sharp-ml-handler:latest python -c "from handler import handler; print('Handler imported successfully')"
```

### Push to RunPod Container Registry
```bash
# Tag for RunPod registry
docker tag sharp-ml-handler:latest runpod.io/sharp-ml-handler:latest

# Login to RunPod
docker login runpod.io -u $RUNPOD_API_KEY -p $RUNPOD_API_KEY

# Push image
docker push runpod.io/sharp-ml-handler:latest
```

**Alternative: Use RunPod's built-in registry**
1. Go to https://www.runpod.io/console/serverless
2. Click "Create Endpoint"
3. Use RunPod's image builder UI

## Step 3: Create RunPod Serverless Endpoint

### Using RunPod Web Console (Recommended)

1. **Go to Serverless**: https://www.runpod.io/console/serverless
2. **Click "Create Endpoint"**
3. **Configure Endpoint**:
   - **Name**: `sharp-ml-processor`
   - **Container Image**: `runpod.io/sharp-ml-handler:latest` (or your image)
   - **Container Disk**: `20 GB` (for model cache)
   - **GPU Type**: `RTX 3090` or `A10G` (choose based on availability/price)
   - **Max Workers**: `1-5` (start with 1, scale up if needed)
   - **Flashboot**: Enable for faster cold starts
   - **Idle Timeout**: `30 seconds` (to save costs)

4. **Environment Variables** (Optional):
   - `TORCH_HOME=/cache/torch`
   - `HF_HOME=/cache/huggingface`

5. **Network Volume** (Optional but Recommended for model caching):
   - Create a network volume named `sharp-model-cache`
   - Mount it at `/cache`
   - This will persist model downloads between cold starts

6. **Click "Create"**

### Using RunPod CLI

```bash
runpod serverless create \
  --name "sharp-ml-processor" \
  --image "runpod.io/sharp-ml-handler:latest" \
  --gpu-type "RTX 3090" \
  --container-disk 20 \
  --idle-timeout 30 \
  --max-workers 3
```

## Step 4: Get Your Endpoint ID

1. Go to https://www.runpod.io/console/serverless
2. Find your endpoint (e.g., `sharp-ml-processor`)
3. Copy the **Endpoint ID** (looks like: `abc123def456...`)

## Step 5: Configure Vercel Environment Variables

1. Go to your Vercel project dashboard
2. Navigate to **Settings** → **Environment Variables**
3. Add these variables:

   ```
   RUNPOD_API_KEY=your-runpod-api-key-here
   RUNPOD_ENDPOINT_ID=your-endpoint-id-here
   ```

4. **IMPORTANT**: Set them for:
   - ✅ Production
   - ✅ Preview
   - ✅ Development (optional)

5. Click **Save**

## Step 6: Deploy Updated Code

The code has already been updated to use RunPod. Just deploy:

```bash
cd web
vercel --prod
```

## Step 7: Test the Integration

1. **Upload an image** through your app
2. **Check Vercel logs** for RunPod job creation:
   ```bash
   vercel logs --follow
   ```
   Look for:
   - `🚀 Creating RunPod job for {filename}...`
   - `✅ RunPod job created with ID: {job_id}`
   - `🔍 Polling RunPod status for job ID: {job_id}`
3. **Monitor RunPod dashboard** for job status:
   - Go to https://www.runpod.io/console/serverless
   - Click on your endpoint
   - Check "Jobs" tab for status
4. **Verify PLY file** is returned correctly:
   - Check logs for `✅ Processing completed successfully`
   - Verify frontend receives PLY data

## Troubleshooting

### Issue: "RunPod not configured" error
- **Solution**: Check that `RUNPOD_API_KEY` and `RUNPOD_ENDPOINT_ID` are set in Vercel environment variables

### Issue: "Failed to create RunPod job"
- **Solution**: 
  - Verify your API key is correct
  - Check endpoint ID is correct
  - Check RunPod dashboard for endpoint status
  - Verify endpoint has available GPUs

### Issue: Job status always "processing"
- **Solution**:
  - Check RunPod dashboard for job status
  - Check RunPod logs for errors
  - Verify handler function is correct
  - Check if GPU is available

### Issue: "Handler function not found"
- **Solution**: 
  - Verify `runpod_handler.py` is in the Docker image
  - Check Dockerfile CMD is correct
  - Test handler locally with Docker

### Issue: Cold starts taking too long
- **Solution**:
  - Enable Flashboot in endpoint settings
  - Increase `idle_timeout` to keep workers warm longer
  - Use Network Volume to cache models
  - Consider increasing `max_workers`

## Cost Optimization

- **Idle Timeout**: Set to 30 seconds to minimize idle costs
- **GPU Type**: Use RTX 3090 ($0.29/hour) instead of A10G if possible
- **Max Workers**: Start with 1, scale up only if needed
- **Network Volume**: Use for model caching to avoid re-downloads

## Monitoring

### RunPod Dashboard
- View jobs: https://www.runpod.io/console/serverless
- Check logs: Click on endpoint → Logs tab
- Monitor costs: https://www.runpod.io/console/user/billing

### Vercel Logs
- View function logs: `vercel logs --follow`
- Check for RunPod API calls in logs

## Next Steps

1. ✅ Deploy Docker image to RunPod
2. ✅ Create serverless endpoint
3. ✅ Set environment variables in Vercel
4. ✅ Deploy updated code
5. ✅ Test with real images
6. ✅ Monitor costs and performance

## Support

- RunPod Docs: https://docs.runpod.io
- RunPod Discord: https://discord.gg/runpod
- RunPod Support: support@runpod.io
