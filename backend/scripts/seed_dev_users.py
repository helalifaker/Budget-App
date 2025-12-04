"""
Seed development users for local testing.

Requires: pip install supabase

Usage:
    cd backend
    source .venv/bin/activate
    python -m scripts.seed_dev_users
"""

import os
from pathlib import Path

from supabase import Client, create_client

# Load environment variables from .env.local
env_local_path = Path(__file__).parent.parent / ".env.local"
if env_local_path.exists():
    with open(env_local_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                # Remove quotes from value
                value = value.strip('"').strip("'")
                os.environ[key] = value


def seed_users():
    """Create development users via Supabase Auth Admin API."""
    supabase_url = os.getenv("SUPABASE_URL")
    service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not service_role_key:
        print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY required")
        print("   Set these in backend/.env.local")
        return

    print(f"🔄 Connecting to Supabase: {supabase_url}")
    supabase: Client = create_client(supabase_url, service_role_key)

    users = [
        {
            "email": "admin@efir.local",
            "password": "Admin123!",
            "email_confirm": True,
            "user_metadata": {"role": "admin", "name": "Admin User"},
        },
        {
            "email": "planner@efir.local",
            "password": "Planner123!",
            "email_confirm": True,
            "user_metadata": {"role": "planner", "name": "Planner User"},
        },
        {
            "email": "viewer@efir.local",
            "password": "Viewer123!",
            "email_confirm": True,
            "user_metadata": {"role": "viewer", "name": "Viewer User"},
        },
    ]

    print(f"\n📝 Creating {len(users)} development users...\n")

    for user_data in users:
        try:
            response = supabase.auth.admin.create_user(user_data)
            user_id = response.user.id if hasattr(response, "user") else "unknown"
            print(f"✅ Created: {user_data['email']:25} (ID: {user_id})")
        except Exception as e:
            error_str = str(e)
            if "already been registered" in error_str or "User already registered" in error_str:
                print(f"ℹ️  Exists:  {user_data['email']:25} (already registered)")
            else:
                print(f"❌ Failed:  {user_data['email']:25} - {e}")

    print("\n✅ Development users setup complete!")
    print("\nLogin credentials:")
    print("  • admin@efir.local / Admin123!")
    print("  • planner@efir.local / Planner123!")
    print("  • viewer@efir.local / Viewer123!")


if __name__ == "__main__":
    seed_users()
