# Modal Deployment & Diagnostics Instructions

## 1. Deploy Updated Modal App

```bash
cd /Users/niccolomiranda/Cursor\ AI/ml-sharp
modal deploy modal_app.py
```

After deployment, you'll see output showing the endpoint URLs. Note them down.

## 2. Test Health Check Endpoint

```bash
# Test if Modal responds at all
curl --max-time 5 https://revelium-studio--sharp-ml-health-check.modal.run
```

**Expected response if working:**
```json
{"status": "ok", "service": "sharp-ml", "endpoint": "healthy"}
```

**If it hangs/times out:**
- Modal infrastructure is down
- Contact Modal support immediately

## 3. Check Modal Dashboard

Go to: https://modal.com/apps

### Check App Status
- Find app: `sharp-ml`
- Status should be "Deployed" (green)
- If "Error" or "Deploying" - there's a deployment issue

### Check Function Calls/Runs
- Click on "Runs" or "Function Calls" tab
- Look for:
  - **Stuck in QUEUED**: GPU capacity exhausted, waiting for GPU
  - **Stuck in RUNNING**: Processing is taking too long (check logs)
  - **Failed**: Error messages will show what went wrong
  - **Multiple pending**: Too many concurrent requests

### Check Logs
- Click on a function call/run
- Look for:
  - `🔄 Received request` - Request reached Modal
  - `📦 Decoding image` - Image decoding started
  - `✅ Image decoded` - Image decoded successfully
  - `🔄 Processing synchronously` - Processing started
  - `❌ Error` messages - What failed

### Check Billing
- Go to: Modal Dashboard → Billing
- Check:
  - **Current usage** this billing cycle
  - **Billing limits** (daily/monthly)
  - **Warnings** about limits being hit
  - **GPU costs** - if too high, might have hit limits

## 4. Common Issues & Solutions

### Issue: All requests stuck in QUEUED
**Cause**: GPU capacity exhausted
**Solution**: 
- Wait for GPU availability
- Reduce concurrent requests
- Upgrade Modal plan for more GPU capacity

### Issue: Requests timeout/fail
**Cause**: Processing takes too long or errors out
**Solution**:
- Check Modal logs for errors
- Reduce image size
- Check if SHARP model is failing

### Issue: Billing limit reached
**Cause**: Monthly/daily spending limit hit
**Solution**:
- Increase billing limit in Modal dashboard
- Wait for billing cycle reset
- Check usage patterns

### Issue: Endpoint not responding (hanging)
**Cause**: Modal service degradation or bug
**Solution**:
- Redeploy Modal app
- Check Modal status page: https://status.modal.com
- Contact Modal support

## 5. Test Commands

```bash
# Test health check (should respond immediately)
curl --max-time 5 https://revelium-studio--sharp-ml-health-check.modal.run

# Test POST endpoint with minimal data
curl --max-time 30 -X POST \
  https://revelium-studio--sharp-ml-process-image-endpoint.modal.run \
  -H "Content-Type: application/json" \
  -d '{"image": "dGVzdA==", "filename": "test.jpg", "async": false}'

# Test async endpoint
curl --max-time 10 -X POST \
  https://revelium-studio--sharp-ml-process-image-endpoint.modal.run \
  -H "Content-Type: application/json" \
  -d '{"image": "dGVzdA==", "filename": "test.jpg", "async": true}'
```
