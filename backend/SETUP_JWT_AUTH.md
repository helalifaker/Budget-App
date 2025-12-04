# Supabase JWT Authentication Setup Guide

This guide explains how to configure Supabase JWT authentication for the EFIR Budget Planning backend.

## Quick Start (TL;DR)

**For new developers setting up the project:**

1. **Get Supabase JWT Secret:**
   - Dashboard: https://supabase.com/dashboard/project/ssxwmxqvafesyldycqzy
   - Settings > API > JWT Settings > **JWT Secret** (click copy icon)

2. **Configure Backend:**
   ```bash
   cd backend
   # Add to .env.local:
   SUPABASE_URL=https://ssxwmxqvafesyldycqzy.supabase.co
   SUPABASE_JWT_SECRET=<paste-your-jwt-secret>
   # SKIP_AUTH_FOR_TESTS is auto-enabled during pytest
   ```

3. **Create Dev Users** (one-time setup):
   ```bash
   cd backend
   source .venv/bin/activate
   python -m scripts.seed_dev_users
   ```

4. **Start Backend:**
   ```bash
   uvicorn app.main:app --reload
   ```

5. **Login:** Use development credentials:
   - admin@efir.local / Admin123!
   - planner@efir.local / Planner123!
   - viewer@efir.local / Viewer123!

✅ You should see no 401 errors and be able to access the API with valid JWT tokens.

---

## Problem

If you're seeing `401 Unauthorized` errors after successful login, it means the backend cannot verify Supabase JWT tokens because the `SUPABASE_JWT_SECRET` environment variable is not configured.

## Solution

Configure the Supabase JWT Secret in your backend environment.

## Step-by-Step Instructions

### Step 1: Get Your Supabase JWT Secret

1. Go to your Supabase Dashboard: https://supabase.com/dashboard
2. Select your project (e.g., `ssxwmxqvafesyldycqzy`)
3. Navigate to **Settings** → **API**
4. Scroll down to the **JWT Settings** section
5. Find the **JWT Secret** field
6. Click the **Copy** button or manually copy the secret

**Important:** The JWT Secret is different from:
- The `anon` key (public, used by frontend)
- The `service_role` key (private, for backend operations)
- The database password

### Step 2: Add JWT Secret to Backend Environment

1. Open or create `backend/.env.local` file
2. Add the following line:

```bash
SUPABASE_JWT_SECRET=your-jwt-secret-here
```

Replace `your-jwt-secret-here` with the actual JWT secret you copied from Step 1.

**Example:**
```bash
SUPABASE_JWT_SECRET=your-super-secret-jwt-token-with-signing-key
```

### Step 3: Restart Backend Server

After adding the JWT secret, restart your backend server:

```bash
# Stop the current server (Ctrl+C)
# Then restart:
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload
```

Or if using `pnpm run dev`:
```bash
# Stop with Ctrl+C, then:
pnpm run dev
```

### Step 4: Verify Configuration

1. Try logging in through the frontend
2. Check the backend terminal logs - you should see:
   - `JWT token received for /api/v1/...`
   - `JWT verified successfully. User: ...`
3. API calls should now return `200 OK` instead of `401 Unauthorized`

## Troubleshooting

### Still Getting 401 Errors?

**Check 1: Is the secret correct?**
- Verify you copied the **JWT Secret**, not the anon key or service role key
- The JWT Secret is typically a long string (100+ characters)

**Check 2: Is the environment variable loaded?**
- Ensure the file is named `.env.local` (not `.env`)
- Check that the backend server was restarted after adding the variable
- Verify the file is in the `backend/` directory

**Check 3: Check backend logs**
- Look for error messages like: `SUPABASE_JWT_SECRET not configured`
- Look for: `JWT verification failed: ...`
- These messages will tell you what's wrong

**Check 4: Verify token is being sent**
- Check frontend console for: `[api-client] Adding Authorization header, token length: ...`
- If you see this, the frontend is sending the token correctly

### Common Errors

**Error: "SUPABASE_JWT_SECRET not configured"**
- Solution: Add `SUPABASE_JWT_SECRET` to `backend/.env.local`

**Error: "JWT verification failed: Invalid token"**
- Solution: Verify you copied the correct JWT Secret from Supabase dashboard
- Make sure there are no extra spaces or quotes in `.env.local`

**Error: "JWT verification failed: Signature verification failed"**
- Solution: The JWT secret doesn't match. Double-check you copied the correct secret.

## Security Notes

- **Never commit `.env.local` to git** - it contains sensitive secrets
- The JWT Secret should be kept private
- In production, use environment variables or a secrets manager
- The JWT Secret is used to verify tokens, not to create them (Supabase creates tokens)

## Production Deployment

For production, set `SUPABASE_JWT_SECRET` as an environment variable in your deployment platform:

- **Vercel/Railway/Render**: Add to environment variables in dashboard
- **Docker**: Pass via `-e SUPABASE_JWT_SECRET=...` or docker-compose.yml
- **Kubernetes**: Use Secrets
- **AWS/GCP/Azure**: Use their secrets management services

## Troubleshooting

### Issue: "Invalid user ID format: test-user"

**Root Cause:** Test bypass mode is incorrectly enabled in development.

**Solution:**
1. Remove `SKIP_AUTH_FOR_TESTS=true` from `backend/.env.local`
2. The test bypass is now **auto-enabled during pytest runs only**
3. In development, real JWT authentication should be used
4. Restart backend server

**Why this happens:**
- Old setup had test bypass enabled by default
- This set `user_id = "test-user"` (a string, not UUID)
- Backend expects UUID format for all user IDs
- Now fixed: test bypass only activates during pytest runs

### Issue: Frontend shows "Using placeholder Supabase configuration"

**Root Cause:** Frontend `.env.local` not configured.

**Solution:**
1. Create `frontend/.env.local`:
   ```bash
   VITE_SUPABASE_URL=https://ssxwmxqvafesyldycqzy.supabase.co
   VITE_SUPABASE_ANON_KEY=<your-anon-key>
   VITE_API_BASE_URL=http://localhost:8000/api/v1
   ```
2. Get anon key from Supabase Dashboard > Settings > API
3. Restart frontend dev server (`pnpm dev`)

### Issue: "JWT verification failed: Signature verification failed"

**Root Cause:** Wrong JWT secret or secret from different project.

**Solution:**
1. Verify you're copying the **JWT Secret**, not:
   - ❌ anon (public) key
   - ❌ service_role key
   - ❌ Database password
2. Dashboard > Settings > API > **JWT Settings** > JWT Secret
3. Copy exact value (should be ~88 characters, base64-encoded)
4. Update `SUPABASE_JWT_SECRET` in `backend/.env.local`
5. Restart backend server

### Issue: "JWT verification failed: Invalid issuer"

**Root Cause:** `SUPABASE_URL` doesn't match your project.

**Solution:**
1. Verify project URL in Supabase Dashboard
2. Should be: `https://ssxwmxqvafesyldycqzy.supabase.co`
3. Update `SUPABASE_URL` in `backend/.env.local`
4. Restart backend

### Issue: Tests failing after disabling test bypass

**This should not happen!** Test bypass is now auto-enabled during pytest.

**If it happens:**
1. Verify pytest is installed in venv
2. Check `sys.modules` contains `pytest` during test run
3. The fix detects pytest automatically via `"pytest" in sys.modules`

### Issue: Login succeeds but API calls return 401

**Diagnosis Steps:**

1. **Check Frontend Console:**
   ```
   [api-client] ✅ Adding Authorization header, token length: 500+
   ```
   ✅ If you see this, frontend is working correctly

2. **Check Backend Logs:**
   ```
   [AUTH] Token received, length: 500+
   [AUTH] ❌ JWT verification failed: ...
   ```
   This tells you the specific verification error

3. **Common Causes:**
   - Backend JWT secret doesn't match Supabase project
   - Backend `SUPABASE_URL` incorrect
   - Token expired (rare - auto-refreshes)

**Solution:**
- Review error message in backend logs
- Verify `SUPABASE_JWT_SECRET` and `SUPABASE_URL` match Dashboard
- Check that JWT secret is from the correct Supabase project

## Additional Resources

- [Supabase JWT Documentation](https://supabase.com/docs/guides/auth/jwts)
- [Supabase API Settings](https://supabase.com/dashboard/project/_/settings/api)
- Backend README: See `backend/README.md` for other environment variables

---

**Last Updated:** 2025-12-03
**Maintained By:** EFIR Development Team


