# Set Vercel Environment Variables - Quick Guide

## 📋 What You Need

You need **2 environment variables** for Vercel:

1. **RUNPOD_API_KEY** = Your RunPod API token (you have this ✅)
2. **RUNPOD_ENDPOINT_ID** = Your RunPod Endpoint ID (find this now)

## 🔍 Finding RunPod Endpoint ID

### Quick Steps:

1. **Go to**: https://www.runpod.io/console/serverless
   - Or: https://console.runpod.io/serverless/endpoints

2. **Click on your endpoint** (the one you just created for ML-Sharp)

3. **Find "Endpoint ID"** - it will be:
   - **Near the top** of the endpoint details page
   - **Labeled as**: "Endpoint ID", "ID", or "Endpoint"
   - **Format**: Long alphanumeric string (e.g., `abc123def456...`)
   - **Or in the URL**: `.../endpoints/[ENDPOINT_ID]`

4. **Copy the Endpoint ID**

### Where to Look:

The Endpoint ID is typically displayed:
- ✅ **Top of endpoint details page** (most common)
- ✅ **In the endpoint URL** (browser address bar when viewing endpoint)
- ✅ **In API URLs** shown on the page (e.g., `https://api.runpod.io/v2/[ENDPOINT_ID]/run`)
- ✅ **Endpoint settings** page

## ⚙️ Setting Vercel Environment Variables

Once you have both values:

### Step 1: Go to Vercel Dashboard

1. **Go to**: https://vercel.com/dashboard
2. **Select project**: `ml-sharp` or `revelium-studios/ml-sharp` (your project)
3. **Click**: Settings (gear icon)
4. **Click**: Environment Variables (left sidebar)

### Step 2: Add Environment Variables

1. **Click**: "Add New" (or "Add Environment Variable")

2. **Add first variable**:
   - **Key**: `RUNPOD_API_KEY`
   - **Value**: Your RunPod API token (paste it here)
   - **Environment**: Select:
     - ✅ Production
     - ✅ Preview
     - ✅ Development (optional)
   - **Click**: "Save"

3. **Click**: "Add New" again

4. **Add second variable**:
   - **Key**: `RUNPOD_ENDPOINT_ID`
   - **Value**: Your RunPod Endpoint ID (paste it here)
   - **Environment**: Select:
     - ✅ Production
     - ✅ Preview
     - ✅ Development (optional)
   - **Click**: "Save"

### Step 3: Redeploy

After setting environment variables, **redeploy** your project:

```bash
cd /Users/niccolomiranda/Cursor\ AI/ml-sharp/web
vercel --prod
```

**Or** from Vercel dashboard:
1. Go to your project
2. Click "Deployments" tab
3. Click "..." on the latest deployment
4. Click "Redeploy"

## ✅ Verify Environment Variables

After deploying, verify they're set:

1. Go to Vercel Dashboard → Your Project → Settings → Environment Variables
2. You should see:
   - ✅ `RUNPOD_API_KEY` (hidden value)
   - ✅ `RUNPOD_ENDPOINT_ID` (your endpoint ID visible)

## 🧪 Test the Integration

After deploying with environment variables:

1. **Go to**: https://lab.revelium.studio/ml-sharp
2. **Upload an image**
3. **Check Vercel logs**:
   ```bash
   cd web
   vercel logs --follow
   ```
4. **Look for**:
   - `🚀 Creating RunPod job for {filename}...`
   - `✅ RunPod job created with ID: {job_id}`
   - `🔍 Polling RunPod status for job ID: {job_id}`

## 🆘 Troubleshooting

### "RunPod not configured" error
- ✅ Check environment variables are set in Vercel
- ✅ Verify variable names: `RUNPOD_API_KEY` and `RUNPOD_ENDPOINT_ID` (exact spelling!)
- ✅ Make sure they're set for **Production** environment
- ✅ Redeploy after setting variables

### "Failed to create RunPod job"
- ✅ Verify API key is correct
- ✅ Verify Endpoint ID is correct
- ✅ Check RunPod dashboard - is endpoint active?
- ✅ Check RunPod billing - do you have credits?

### Job stuck in "processing"
- ✅ Check RunPod dashboard for job status
- ✅ Check RunPod logs in dashboard
- ✅ Verify handler code is correct
- ✅ Check if GPU is available

---

**Find your Endpoint ID first, then set both environment variables in Vercel!** 🚀
