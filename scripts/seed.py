import sys
import os
import asyncio
import uuid
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.common.db import AsyncSessionLocal
from app.models import Tenant, User, Application
from app.common.crypto import encrypt_secret
from app.config.settings import settings

async def seed():
    print(f"DEBUG: Starting seed...")
    async with AsyncSessionLocal() as db:
        # Step 1: Tenant
        print("DEBUG: Creating Tenant...")
        tenant = Tenant()
        tenant.id = uuid.uuid4()
        tenant.name = "Test Tenant"
        tenant.slug = f"test-{uuid.uuid4().hex[:6]}"
        db.add(tenant)
        await db.flush()
        print(f"DEBUG: Tenant created: {tenant.id}")

        # Step 2: User
        print("DEBUG: Creating User...")
        user = User()
        user.id = uuid.uuid4()
        user.tenant_id = tenant.id
        user.email = f"admin-{uuid.uuid4().hex[:6]}@example.com"
        user.first_name = "Admin"
        user.last_name = "Test"
        user.password_hash = "argon2"
        user.role = "admin"
        user.status = "active"
        db.add(user)
        await db.flush()
        print(f"DEBUG: User created: {user.id}")

        # Step 3: Application
        print("DEBUG: Creating Application...")
        app = Application()
        app.id = uuid.uuid4()
        app.tenant_id = tenant.id
        app.name = "Test Producer"
        app.type = "producer"
        app.client_id = f"client-{uuid.uuid4().hex[:6]}"
        secret_raw = "test_secret"
        app.client_secret_enc, _ = encrypt_secret(secret_raw.encode(), settings.ENCRYPTION_KEY)
        app.created_by = user.id
        db.add(app)
        await db.flush()
        print(f"DEBUG: Application created: {app.id}")

        await db.commit()
        print("Seeding successful!")

if __name__ == "__main__":
    asyncio.run(seed())
