# How to Set Environment Variables in RunPod - Step-by-Step Guide

## 🎯 Goal

Set R2 environment variables in your RunPod endpoint so the handler can upload PLY files to Cloudflare R2.

## 📋 Required Values

You need these 5 environment variables:
- `R2_ACCOUNT_ID`
- `R2_ACCESS_KEY_ID`
- `R2_SECRET_ACCESS_KEY`
- `R2_BUCKET_NAME`
- `R2_PUBLIC_URL`

---

## 🚀 Step-by-Step Instructions

### Step 1: Login to RunPod Console

1. **Go to**: https://www.runpod.io/
2. **Click**: "Login" or "Sign In" (top right)
3. **Enter** your credentials and login

---

### Step 2: Navigate to Serverless Endpoints

1. **Once logged in**, you'll be on the RunPod dashboard
2. **In the left sidebar**, click on **"Serverless"** (or look for it in the menu)
   - It might be under "Compute" or "Workloads"
   - Or go directly to: https://www.runpod.io/console/serverless

---

### Step 3: Find Your Endpoint

1. **You should see** a list of your serverless endpoints
2. **Find** the endpoint named **"ml-sharp"**
   - If you named it differently, look for the endpoint you created
3. **Click on** the endpoint name (not the checkbox, but the name itself)
   - This will open the endpoint details page

---

### Step 4: Go to Settings

1. **On the endpoint details page**, you'll see several tabs at the top:
   - Overview
   - Metrics
   - Logs
   - Requests
   - Workers
   - Builds
   - Releases
   - **Settings** ← Click this!

2. **Click on** the **"Settings"** tab

---

### Step 5: Find Environment Variables Section

1. **In the Settings page**, scroll down
2. **Look for** a section called:
   - "Environment Variables"
   - "ENV Variables"
   - "Container Environment Variables"
   - Or similar

3. **You should see**:
   - A list of existing environment variables (if any)
   - An **"Add Variable"** or **"Add Environment Variable"** button

---

### Step 6: Add Environment Variables

For each of the 5 variables, follow these steps:

#### Add Variable 1: R2_ACCOUNT_ID

1. **Click** the **"Add Variable"** or **"Add Environment Variable"** button
2. **In the form that appears**, fill in:
   - **Name/Key**: `R2_ACCOUNT_ID`
   - **Value**: `31178c53271846bd9cb48918a4fdd72e` (your actual Account ID)
   - **Environment**: Select **"Production"** (and optionally Preview/Development)
3. **Click**: "Save" or "Add"

#### Add Variable 2: R2_ACCESS_KEY_ID

1. **Click** "Add Variable" again
2. **Fill in**:
   - **Name/Key**: `R2_ACCESS_KEY_ID`
   - **Value**: `abc123def456...` (your actual Access Key ID from Cloudflare)
   - **Environment**: Select **"Production"**
3. **Click**: "Save"

#### Add Variable 3: R2_SECRET_ACCESS_KEY

1. **Click** "Add Variable" again
2. **Fill in**:
   - **Name/Key**: `R2_SECRET_ACCESS_KEY`
   - **Value**: `xyz789abc123...` (your actual Secret Access Key from Cloudflare)
   - **Environment**: Select **"Production"**
   - ⚠️ **Important**: Make sure this is marked as **"Secret"** or **"Sensitive"** if there's an option
3. **Click**: "Save"

#### Add Variable 4: R2_BUCKET_NAME

1. **Click** "Add Variable" again
2. **Fill in**:
   - **Name/Key**: `R2_BUCKET_NAME`
   - **Value**: `ml-sharp-outputs` (or your bucket name)
   - **Environment**: Select **"Production"**
3. **Click**: "Save"

#### Add Variable 5: R2_PUBLIC_URL

1. **Click** "Add Variable" again
2. **Fill in**:
   - **Name/Key**: `R2_PUBLIC_URL`
   - **Value**: `https://pub-31178c53271846bd9cb48918a4fdd72e.r2.dev` (your actual public URL)
   - **Environment**: Select **"Production"**
3. **Click**: "Save"

---

### Step 7: Verify All Variables Are Set

1. **After adding all 5 variables**, you should see them listed in the Environment Variables section:
   - ✅ `R2_ACCOUNT_ID`
   - ✅ `R2_ACCESS_KEY_ID`
   - ✅ `R2_SECRET_ACCESS_KEY` (might be hidden/masked)
   - ✅ `R2_BUCKET_NAME`
   - ✅ `R2_PUBLIC_URL`

2. **Double-check**:
   - All names are correct (case-sensitive!)
   - All values are correct
   - All are set for "Production" environment

---

### Step 8: Save Changes

1. **Look for** a **"Save"** button at the bottom of the Settings page
2. **Click** "Save" to apply changes
3. **Wait** for confirmation that settings are saved

---

### Step 9: Trigger Rebuild (Required!)

⚠️ **IMPORTANT**: After setting environment variables, you MUST rebuild the endpoint!

**Option A: Rebuild from Settings**

1. **Still in Settings**, look for a **"Rebuild"** or **"Redeploy"** button
2. **Click** it to trigger a rebuild
3. **Wait** 5-10 minutes for build to complete

**Option B: Rebuild from Builds Tab**

1. **Go to** the **"Builds"** tab (top navigation)
2. **Click** **"Rebuild"** or **"New Build"** button
3. **Wait** 5-10 minutes for build to complete

**Option C: Automatic Rebuild**

Sometimes RunPod automatically rebuilds when environment variables are updated. Check the "Builds" tab to see if a new build started automatically.

---

## ✅ Verification Checklist

After completing all steps, verify:

- [ ] All 5 environment variables are listed in Settings
- [ ] Variable names are exactly correct (case-sensitive)
- [ ] Values are correct (especially R2 credentials)
- [ ] All are set for "Production" environment
- [ ] Settings are saved successfully
- [ ] Endpoint is rebuilding (check Builds tab)
- [ ] Build completes successfully (green checkmark)

---

## 🔍 Alternative Navigation Paths

If you can't find "Settings" → "Environment Variables", try:

### Path 1: Endpoint → Edit → Environment Variables
1. Click on endpoint name
2. Look for "Edit" button
3. Find "Environment Variables" section
4. Add variables

### Path 2: Endpoint → Configure → Environment
1. Click on endpoint name
2. Look for "Configure" or "Configuration"
3. Find "Environment" or "Environment Variables"
4. Add variables

### Path 3: Direct API/CLI
If web UI doesn't work, you can use RunPod CLI or API, but web UI is recommended.

---

## 📸 What You Should See

After adding all variables, the Environment Variables section should look like:

```
Environment Variables:
─────────────────────────────────────────────
R2_ACCOUNT_ID            = 31178c53271846bd9cb48918a4fdd72e
R2_ACCESS_KEY_ID         = abc123def456...
R2_SECRET_ACCESS_KEY     = ••••••••••••••••  (hidden)
R2_BUCKET_NAME           = ml-sharp-outputs
R2_PUBLIC_URL            = https://pub-31178c53271846bd9cb48918a4fdd72e.r2.dev
─────────────────────────────────────────────
[Add Variable] [Save]
```

---

## ⚠️ Important Notes

1. **Case Sensitivity**: Variable names must be EXACT (uppercase, underscores)
   - ✅ `R2_ACCOUNT_ID` (correct)
   - ❌ `r2_account_id` (wrong)
   - ❌ `R2-ACCOUNT-ID` (wrong)

2. **No Spaces**: No spaces around the `=` sign
   - ✅ `R2_ACCOUNT_ID=value`
   - ❌ `R2_ACCOUNT_ID = value`

3. **Secret Values**: `R2_SECRET_ACCESS_KEY` should be marked as secret/sensitive if option exists

4. **Rebuild Required**: Environment variables only take effect after rebuild!

---

## 🆘 Troubleshooting

### "Can't find Settings tab"
- Look for "Configure", "Edit", or "Settings" in different locations
- Try clicking directly on endpoint name to see all options

### "Can't find Environment Variables"
- Look for "ENV Variables", "Container Environment", or "Runtime Environment"
- Some RunPod versions call it differently

### "Save button doesn't work"
- Make sure all required fields are filled
- Check for validation errors
- Try refreshing the page and trying again

### "Variables not showing after save"
- Refresh the page
- Check if they're set for the correct environment (Production)
- Verify you're looking at the right endpoint

---

## 🎯 Next Steps After Setting Variables

1. ✅ Verify all 5 variables are saved
2. ✅ Trigger rebuild (if not automatic)
3. ✅ Wait for build to complete (5-10 minutes)
4. ✅ Test by uploading an image
5. ✅ Check RunPod logs for "✅ Uploaded to R2"

---

**Once all variables are set and endpoint is rebuilt, the 90% block should be resolved!** 🚀
