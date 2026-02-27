# How to Find Your RunPod Endpoint ID

## 🔍 Finding Your Endpoint ID (2 minutes)

### Method 1: From RunPod Dashboard (Easiest)

1. **Go to**: https://www.runpod.io/console/serverless
2. **Find your endpoint** (should be named something like `sharp-ml-processor` or whatever you named it)
3. **Click on the endpoint name** to open its details
4. **Look for "Endpoint ID"** or "ID" - it will look like:
   - `abc123def456...` (long alphanumeric string)
   - OR it might be displayed as a clickable link
5. **Copy the Endpoint ID** - this is what you need!

### Method 2: From Endpoint URL

1. **Go to**: https://www.runpod.io/console/serverless
2. **Click on your endpoint**
3. **Check the URL** in your browser - it might look like:
   - `https://www.runpod.io/console/serverless/[ENDPOINT_ID]`
   - The Endpoint ID is in the URL path

### Method 3: From Endpoint Settings

1. **Go to**: https://www.runpod.io/console/serverless
2. **Click on your endpoint**
3. **Click "Settings"** or look for endpoint details
4. **Endpoint ID** should be visible in the settings page

### Method 4: From API Test (Alternative)

Once you have the Endpoint ID, you can test it with:

```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_RUNPOD_API_KEY" \
  -H "Content-Type: application/json" \
  https://api.runpod.io/v2/YOUR_ENDPOINT_ID/run \
  -d '{"input": {"test": "data"}}'
```

## 📋 What You Need for Vercel

You need these **two values**:

1. **RUNPOD_API_KEY** = Your RunPod API token (you mentioned you have this)
   - Get from: https://www.runpod.io/console/user/settings
   - Or: https://www.runpod.io/console/user/api

2. **RUNPOD_ENDPOINT_ID** = Your endpoint ID (this is what we're finding now)
   - Get from: https://www.runpod.io/console/serverless
   - Click on your endpoint to see the ID

## 🎯 Quick Checklist

- [ ] Go to https://www.runpod.io/console/serverless
- [ ] Find your endpoint (the one you just created)
- [ ] Click on it
- [ ] Find "Endpoint ID" or "ID" field
- [ ] Copy it - it's usually a long string like `abc123def456...`

## 💡 Tip

The Endpoint ID is usually:
- **Long alphanumeric string** (e.g., `abc123def456ghi789`)
- **Visible in the endpoint details page**
- **Sometimes in the URL** when viewing the endpoint
- **Might be labeled as "Endpoint ID", "ID", or "Endpoint"**

---

**Once you have the Endpoint ID, we can set it in Vercel environment variables!** 🚀
