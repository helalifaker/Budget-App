# 🔐 Supabase Credentials Setup Guide

Your Supabase credentials were exposed and need to be rotated immediately. This guide walks you through the process.

## ⚠️ Security Alert

Your exposed credentials:
- ❌ Database password
- ❌ Service Role Key (secret key)
- ❌ Brave API Key

**Action Required**: Rotate these credentials NOW before proceeding.

---

## 📋 Quick Start (TL;DR)

```bash
# 1. Open Supabase Dashboard and rotate your keys
#    (See detailed steps below)

# 2. Run the automated setup script
./setup-credentials.sh

# 3. Verify everything works
./verify-setup.sh

# 4. Start the servers
# Terminal 1:
cd backend && source .venv/bin/activate && uvicorn app.main:app --reload

# Terminal 2:
cd frontend && pnpm dev
```

---

## 🔑 Step 1: Rotate Your Credentials in Supabase

### Where to Find Your Project
- **Project ID**: `ssxwmxqvafesyldycqzy`
- **URL**: https://supabase.com/dashboard/projects/ssxwmxqvafesyldycqzy

### Step-by-Step: Reset Database Password

1. Go to **Project Settings** (⚙️ icon at bottom left)
2. Click **Database**
3. Scroll to "Password" section
4. Click **Reset Password**
5. Copy the new password and save it somewhere temporary (you'll paste it into the script)
6. Click **"I have copied my password"** to confirm

### Step-by-Step: Rotate API Keys

1. Go to **Settings** → **API**
2. Under "Project API keys":

**For Service Role Key:**
- Find the row labeled "service_role"
- Click the **three dots menu (•••)**
- Click **Rotate**
- A new key will appear (starts with `sb_secret_`)
- Click **Copy** and save it temporarily

**For Anon Key:**
- Find the row labeled "anon"
- Click the **three dots menu (•••)**
- Click **Rotate**
- A new key will appear (starts with `sb_anon_`)
- Click **Copy** and save it temporarily

### Step-by-Step: Rotate Brave API Key

1. Go to https://api.search.brave.com/res/
2. Sign in with your account
3. Click **Create New API Key**
4. Copy the new key

---

## 🛠️ Step 2: Run the Setup Script

Once you have your new credentials ready, run the automated setup script:

```bash
cd /Users/fakerhelali/Coding/Budget\ App
./setup-credentials.sh
```

**The script will:**
1. Ask you to confirm you've rotated your keys (it waits for your ENTER press)
2. Prompt you to enter each new credential (passwords are hidden)
3. Automatically update `backend/.env.local` with new database credentials
4. Automatically update `frontend/.env` with new anon key
5. Verify everything was updated correctly

**Example input:**
```
Step 1: Get Your New Supabase Credentials
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Follow these steps in your Supabase Dashboard...
Press ENTER when you've completed these steps...
[You press ENTER]

Step 2: Enter Your New Credentials
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Enter your NEW database password: [paste password]
Enter your NEW service_role key: [paste sb_secret_...]
Enter your NEW anon key: [paste sb_anon_...]
```

---

## ✅ Step 3: Verify Setup

After running the setup script, verify everything is working:

```bash
./verify-setup.sh
```

This script checks:
- ✓ Backend configuration file exists and has values
- ✓ Frontend configuration file exists and has values
- ✓ Backend Python environment is ready
- ✓ Frontend dependencies are installed
- ✓ Displays summary of your configuration

---

## 🚀 Step 4: Start the Application

### Terminal 1 - Start Backend API

```bash
cd /Users/fakerhelali/Coding/Budget\ App/backend
source .venv/bin/activate
uvicorn app.main:app --reload
```

Expected output:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

### Terminal 2 - Start Frontend Development Server

```bash
cd /Users/fakerhelali/Coding/Budget\ App/frontend
pnpm dev
```

Expected output:
```
  VITE v7.2.x  ready in 234 ms

  ➜  Local:   http://localhost:5173/
  ➜  press h to show help
```

### Terminal 3 - Test the Connection (Optional)

```bash
# Test backend is running
curl http://localhost:8000/health

# Test frontend is serving
curl http://localhost:5173
```

---

## 🧪 Testing Your Setup

Once both servers are running:

1. **Open your browser**: http://localhost:5173
2. **You should see**: The EFIR Budget App login page
3. **Try to sign up**: Create a test account using your email
4. **Check backend logs**: Should show requests coming through
5. **Check frontend console**: Should show no errors (F12 → Console)

---

## 📁 File Structure After Setup

```
/Users/fakerhelali/Coding/Budget\ App/
├── backend/
│   └── .env.local          ← Contains database credentials (SECRET)
├── frontend/
│   └── .env                ← Contains Supabase URL and public key
├── setup-credentials.sh    ← Run this to update credentials
├── verify-setup.sh         ← Run this to verify everything
└── SUPABASE_SETUP_GUIDE.md ← This file
```

---

## 🔒 Security Best Practices

### DO ✅
- ✅ Keep `.env.local` and `.env` files PRIVATE
- ✅ Add `.env*` to `.gitignore` (already done)
- ✅ Use different credentials for dev/staging/production
- ✅ Rotate keys every 90 days
- ✅ Use a password manager to store credentials
- ✅ Never share `.env` files with others

### DON'T ❌
- ❌ Don't commit `.env` files to git (they're in .gitignore)
- ❌ Don't share credentials in chat, email, or Slack
- ❌ Don't use the same credentials for multiple environments
- ❌ Don't expose service_role keys in frontend code
- ❌ Don't keep credentials in browser history

---

## 🆘 Troubleshooting

### Backend Connection Error
```
Error: could not translate host name "db.ssxwmxqvafesyldycqzy.supabase.co" to address
```
**Solution**: Check your internet connection and that the database password is correct

### Frontend Build Error
```
error: VITE_SUPABASE_URL is not set
```
**Solution**: Run `./setup-credentials.sh` again and verify `frontend/.env` has values

### "Password authentication failed"
```
FATAL: password authentication failed for user "postgres"
```
**Solution**: The database password is incorrect. Get the new password from Supabase Dashboard and run the setup script again.

### Port Already in Use
```
ERROR: Address already in use: ('0.0.0.0', 8000)
```
**Solution**: Another process is using port 8000
```bash
# Find and kill the process
lsof -i :8000
kill -9 <PID>

# Then start the server again
```

---

## 📞 Need Help?

If you encounter issues:

1. **Check the logs**: Look at terminal output for error messages
2. **Run verification script**: `./verify-setup.sh`
3. **Verify credentials**: Open Supabase Dashboard and confirm your keys match
4. **Check network**: Ensure you can ping Supabase
   ```bash
   ping db.ssxwmxqvafesyldycqzy.supabase.co
   ```

---

## ✨ Success Indicators

You'll know everything is working when:

- ✅ Backend server starts without errors
- ✅ Frontend dev server starts and opens browser
- ✅ You can navigate the app without 404 errors
- ✅ Login/signup form appears
- ✅ No red errors in browser console (F12)
- ✅ Backend logs show incoming requests

---

**Last Updated**: December 2, 2025
**Project**: EFIR School Budget Planning Application
**Status**: Ready for Supabase credential setup
