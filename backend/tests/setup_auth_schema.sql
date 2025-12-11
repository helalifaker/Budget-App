-- Setup auth schema for E2E/CI testing
-- This mimics Supabase's auth schema structure (minimal version)
-- Used only in test environments where Supabase is not available

-- =============================================================================
-- Create Supabase roles (authenticated, anon, service_role)
-- These roles are used by Supabase for RLS policies and permission grants
-- In production Supabase, these roles exist by default
-- =============================================================================
DO $$
BEGIN
    -- Create 'authenticated' role (for logged-in users)
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'authenticated') THEN
        CREATE ROLE authenticated NOLOGIN NOINHERIT;
    END IF;

    -- Create 'anon' role (for anonymous/public access)
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'anon') THEN
        CREATE ROLE anon NOLOGIN NOINHERIT;
    END IF;

    -- Create 'service_role' (for backend service access, bypasses RLS)
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'service_role') THEN
        CREATE ROLE service_role NOLOGIN NOINHERIT BYPASSRLS;
    END IF;
END
$$;

-- Grant usage on public schema to Supabase roles
GRANT USAGE ON SCHEMA public TO authenticated, anon, service_role;

-- Create auth schema if it doesn't exist
CREATE SCHEMA IF NOT EXISTS auth;

-- Create users table (minimal Supabase auth.users structure)
CREATE TABLE IF NOT EXISTS auth.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE,
    encrypted_password VARCHAR(255),
    email_confirmed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    raw_app_meta_data JSONB,
    raw_user_meta_data JSONB,
    is_super_admin BOOLEAN DEFAULT FALSE,
    role VARCHAR(255),
    aud VARCHAR(255)
);

-- Create auth.uid() function (mimics Supabase's built-in function)
-- In real Supabase, this extracts the user ID from JWT claims.
-- For E2E tests, we return the test user's ID (allows RLS policies to work).
CREATE OR REPLACE FUNCTION auth.uid()
RETURNS UUID
LANGUAGE SQL
STABLE
AS $$
    SELECT 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'::uuid;
$$;

-- Create auth.role() function (mimics Supabase's built-in function)
-- Returns the current user's role (authenticated/anon)
CREATE OR REPLACE FUNCTION auth.role()
RETURNS TEXT
LANGUAGE SQL
STABLE
AS $$
    SELECT 'authenticated'::text;
$$;

-- Create a test user for E2E tests
INSERT INTO auth.users (id, email, encrypted_password, email_confirmed_at, role, aud)
VALUES (
    'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'::uuid,
    'test@efir-school.com',
    'hashed_password_placeholder',
    NOW(),
    'authenticated',
    'authenticated'
) ON CONFLICT (email) DO NOTHING;

-- Create Supabase Realtime publication (needed for migrations referencing it)
-- In real Supabase, this publication enables real-time subscriptions
-- Note: PostgreSQL doesn't support IF NOT EXISTS for publications, so we use DO block
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_publication WHERE pubname = 'supabase_realtime') THEN
        CREATE PUBLICATION supabase_realtime;
    END IF;
END
$$;

-- Grant necessary permissions (if needed)
-- This ensures the test database can access the auth schema
COMMENT ON SCHEMA auth IS 'Mock auth schema for E2E/CI testing (mimics Supabase auth)';
