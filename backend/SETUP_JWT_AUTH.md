# Supabase JWT Authentication Setup Guide

This guide explains how to configure Supabase JWT authentication for the EFIR Budget Planning backend.

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

## Additional Resources

- [Supabase JWT Documentation](https://supabase.com/docs/guides/auth/jwts)
- [Supabase API Settings](https://supabase.com/dashboard/project/_/settings/api)
- Backend README: See `backend/README.md` for other environment variables

---

**Last Updated:** 2025-12-03
**Maintained By:** EFIR Development Team

