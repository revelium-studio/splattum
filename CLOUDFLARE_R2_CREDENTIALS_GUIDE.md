# How to Find R2 Credentials in Cloudflare - Step-by-Step Guide

## 📋 What You Need

You need these 5 values:
1. `R2_ACCOUNT_ID` - Your Cloudflare Account ID
2. `R2_ACCESS_KEY_ID` - API Token Access Key ID
3. `R2_SECRET_ACCESS_KEY` - API Token Secret Access Key
4. `R2_BUCKET_NAME` - Name of your R2 bucket (or create new one)
5. `R2_PUBLIC_URL` - Public URL for your bucket (custom domain or default)

## 🚀 Step-by-Step Instructions

### Step 1: Find Your Account ID

1. **Go to**: https://dash.cloudflare.com/
2. **Login** to your Cloudflare account
3. **Click** on any domain in your account (or go to homepage)
4. **Scroll down** on the right sidebar
5. **Look for**: "Account ID" (it's in the "API" section on the right sidebar)
6. **Copy** the Account ID (format: `31178c53271846bd9cb48918a4fdd72e`)

**Alternative method**:
- Go to: https://dash.cloudflare.com/profile/api-tokens
- Your Account ID is shown at the top of the page

---

### Step 2: Navigate to R2

1. **Go to**: https://dash.cloudflare.com/
2. **In the left sidebar**, scroll down and click on **"R2"** (under "Object Storage")
3. **Or go directly**: https://dash.cloudflare.com/r2

---

### Step 3: Create or Select a Bucket

#### Option A: Use Existing Bucket
1. **Find** your existing bucket in the list
2. **Note** the bucket name (e.g., `ml-sharp-outputs`)
3. **Click** on the bucket name to open it

#### Option B: Create New Bucket
1. **Click** "Create bucket" button (top right)
2. **Enter** bucket name: `ml-sharp-outputs` (or any name you prefer)
3. **Choose** location: Select closest region (e.g., "Western North America")
4. **Click** "Create bucket"
5. **Open** the newly created bucket

---

### Step 4: Set Up Public Access (Required)

The bucket needs to allow public read access for PLY files:

1. **Inside your bucket**, click on **"Settings"** tab (or gear icon)
2. **Find**: "Public Access" section
3. **Enable**: "Allow Access" or "Public Bucket"
4. **Save** changes

**Note**: Without public access, the PLY files won't be downloadable via URL.

---

### Step 5: Set Up Custom Domain (Optional but Recommended)

This gives you a clean public URL for your bucket:

1. **Still in bucket Settings**, scroll to **"Custom Domain"** section
2. **Click**: "Connect Domain"
3. **Enter** domain: `pub-31178c53271846bd9cb48918a4fdd72e.r2.dev`
   - **Or** use your own subdomain if you have one: `ply.yourdomain.com`
4. **Follow** Cloudflare's instructions to verify domain
5. **Note** the domain URL (this is your `R2_PUBLIC_URL`)

**If you skip this step**, use the default R2 URL format:
- Format: `https://pub-<account-id>.r2.dev/<bucket-name>/<file-path>`
- Example: `https://pub-31178c53271846bd9cb48918a4fdd72e.r2.dev/ml-sharp-outputs/ply/file.ply`

---

### Step 6: Create R2 API Token

This gives you the `R2_ACCESS_KEY_ID` and `R2_SECRET_ACCESS_KEY`:

1. **Go to**: https://dash.cloudflare.com/r2/api-tokens
   - **Or**: From R2 homepage, click "Manage R2 API Tokens" (top right)
2. **Click**: "Create API token" button
3. **Configure token**:
   - **Token name**: `ml-sharp-runpod` (or any descriptive name)
   - **Permissions**: 
     - ✅ **Object Read & Write** (required)
     - **Bucket**: Select your bucket (`ml-sharp-outputs`) or "All buckets"
   - **TTL**: Leave as "Never" or set expiration (optional)
4. **Click**: "Create API Token"
5. **IMPORTANT**: Copy **both** values:
   - **Access Key ID** - Copy this immediately (format: `abc123def456...`)
   - **Secret Access Key** - Copy this immediately (format: `xyz789abc123...`)
   - ⚠️ **Warning**: You can only see the secret key once! If you lose it, you'll need to create a new token.

---

### Step 7: Get Your Values

Now you should have all the information:

1. **R2_ACCOUNT_ID**: `31178c53271846bd9cb48918a4fdd72e` (from Step 1)
2. **R2_ACCESS_KEY_ID**: `abc123def456...` (from Step 6)
3. **R2_SECRET_ACCESS_KEY**: `xyz789abc123...` (from Step 6)
4. **R2_BUCKET_NAME**: `ml-sharp-outputs` (from Step 3)
5. **R2_PUBLIC_URL**: 
   - If custom domain: `https://pub-31178c53271846bd9cb48918a4fdd72e.r2.dev`
   - Or default: `https://pub-<your-account-id>.r2.dev`

---

## 📝 Example Configuration

Once you have all values, set them in RunPod like this:

```
R2_ACCOUNT_ID=31178c53271846bd9cb48918a4fdd72e
R2_ACCESS_KEY_ID=abc123def456ghi789jkl012mno345pqr678
R2_SECRET_ACCESS_KEY=xyz789abc123def456ghi789jkl012mno345pqr678stu901vwx234
R2_BUCKET_NAME=ml-sharp-outputs
R2_PUBLIC_URL=https://pub-31178c53271846bd9cb48918a4fdd72e.r2.dev
```

**Replace** with your actual values!

---

## 🎯 Quick Reference Links

- **Cloudflare Dashboard**: https://dash.cloudflare.com/
- **R2 Home**: https://dash.cloudflare.com/r2
- **R2 API Tokens**: https://dash.cloudflare.com/r2/api-tokens
- **Account ID**: https://dash.cloudflare.com/profile/api-tokens

---

## 🔒 Security Notes

- **Keep credentials secure**: Don't share your Secret Access Key
- **Use specific permissions**: Limit API token to specific bucket if possible
- **Rotate tokens**: Consider setting expiration dates for tokens
- **Monitor usage**: Check R2 usage in Cloudflare dashboard regularly

---

## ❓ Troubleshooting

### "Access Denied" when uploading
- ✅ Check API token has "Object Read & Write" permissions
- ✅ Verify bucket name is correct
- ✅ Check token hasn't expired (if TTL was set)

### "Public access denied" when downloading
- ✅ Enable "Public Access" in bucket settings
- ✅ Check custom domain is properly configured (if using one)
- ✅ Verify public URL is correct

### "Bucket not found"
- ✅ Check bucket name spelling (case-sensitive)
- ✅ Verify API token has access to the bucket
- ✅ Make sure bucket exists in your account

---

**Once you have all values, set them in RunPod endpoint environment variables!** 🚀
