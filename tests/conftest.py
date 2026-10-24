import os
import time

import jwt
import pytest

os.environ.setdefault("APP_ENV", "development")  # the demo-login test needs it; production is tested explicitly
os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("DEPARTMENT_MODULE_MAP_PATH", "config/department_module_map.yaml")
os.environ.setdefault("OPENAI_API_KEY", "test-key")


def make_token(
    user_id: str = "user-1",
    tenant_id: str = "tenant-1",
    role: str = "USER",
    email: str = "user@example.com",
    secret: str = "test-secret",
    expired: bool = False,
) -> str:
    now = int(time.time())
    payload = {
        "userId": user_id,
        "tenantId": tenant_id,
        "role": role,
        "email": email,
        "exp": now - 10 if expired else now + 3600,
    }
    return jwt.encode(payload, secret, algorithm="HS256")


@pytest.fixture
def valid_token():
    return make_token()


@pytest.fixture
def admin_token():
    return make_token(role="ADMIN")


@pytest.fixture
def expired_token():
    return make_token(expired=True)
