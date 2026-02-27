# R2 Setup Guide - Fix for 90% Block Issue

## 🐛 Root Cause Found!

The issue was discovered from RunPod logs:
- ✅ Processing completes successfully
- ✅ PLY file generated (66MB = 88MB base64)
- ❌ **"Failed to return job results. | 400, message='Bad Request'"**

**Problem**: PLY files (~66MB, 88MB base64) exceed RunPod's response size limit (~10MB).

**Solution**: Upload PLY files to Cloudflare R2 and return a URL instead of base64.

## ✅ Fix Applied

1. **Updated Handler** (`runpod_handler.py`): Now uploads PLY to R2 instead of returning base64
2. **Updated API Route** (`web/src/app/api/process/route.ts`): Downloads from R2 URL when received
3. **Updated Dockerfile**: Added `boto3` for S3-compatible API access

## 🔧 Required: Configure R2 Environment Variables

You need to set R2 credentials in **RunPod endpoint environment variables**:

### Step 1: Get R2 Credentials

1. **Go to**: https://dash.cloudflare.com/
2. **Navigate to**: R2 → Create bucket (if needed) → Manage R2 API Tokens
3. **Create API Token** with:
   - **Permissions**: Object Read & Write
   - **Bucket**: Your bucket (or all buckets)
4. **Copy**:
   - `Account ID`
   - `Access Key ID`
   - `Secret Access Key`

### Step 2: Set Environment Variables in RunPod

1. **Go to**: https://www.runpod.io/console/serverless
2. **Click on**: `ml-sharp` endpoint
3. **Go to**: "Settings" tab (or endpoint settings)
4. **Find**: "Environment Variables" section
5. **Add these variables**:

```
R2_ACCOUNT_ID=your_account_id_here
R2_ACCESS_KEY_ID=your_access_key_id_here
R2_SECRET_ACCESS_KEY=your_secret_access_key_here
R2_BUCKET_NAME=ml-sharp-outputs
R2_PUBLIC_URL=https://pub-31178c53271846bd9cb48918a4fdd72e.r2.dev
```

**Note**: 
- Use your existing R2 bucket or create a new one
- `R2_PUBLIC_URL` should match your R2 public domain
- The bucket must allow public read access for the PLY files

### Step 3: Configure R2 Bucket for Public Access

1. **Go to**: Cloudflare Dashboard → R2 → Your bucket
2. **Enable Public Access** for the bucket
3. **Set up Custom Domain** (optional but recommended):
   - Go to bucket settings → Custom Domain
   - Add: `pub-31178c53271846bd9cb48918a4fdd72e.r2.dev` (or your domain)
   - This allows direct downloads

### Step 4: Update RunPod Endpoint

After setting environment variables:
1. **Save** the endpoint settings
2. **RunPod will automatically rebuild** the endpoint (or manually trigger rebuild)
3. Wait for build to complete

## 🧪 Testing

After configuration:

1. **Upload an image** through your app
2. **Check RunPod logs** for:
   - `📤 Uploading PLY to R2 bucket: ...`
   - `✅ Uploaded to R2: https://...`
3. **Check browser console** for:
   - `✅ Found PLY URL, downloading from R2: ...`
   - `✅ Downloaded PLY from R2 (... bytes)`
4. **Verify** the 90% block is resolved

## 🔄 Fallback Behavior

If R2 credentials are not configured:
- Handler will try to return base64
- Will fail with error if file > 10MB
- Error message will indicate R2 needs to be configured

## 📋 Alternative: Use Existing R2 Bucket

If you already have R2 credentials from your favicon setup:
- Use the same account ID, access key, and secret
- Create a new bucket: `ml-sharp-outputs` (or use existing)
- Make sure it has public read access

## ⚡ Next Steps

1. ✅ Code updated and pushed to GitHub
2. ⏳ **Configure R2 environment variables in RunPod** (required!)
3. ⏳ Wait for RunPod to rebuild endpoint
4. ⏳ Test with new image upload
5. ✅ Verify 90% block is resolved

---

**Once R2 is configured, the 90% block should be resolved!** 🎉
