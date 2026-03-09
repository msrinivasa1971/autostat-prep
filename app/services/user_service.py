"""
User service — load, save, and create users in storage/users/users.json.
"""
import json
from datetime import datetime, timezone
from typing import List

from app.config import USERS_JSON, USERS_STORAGE_DIR
from app.models.user import User


def load_users() -> List[User]:
    """Load all users from users.json. Returns empty list if file does not exist."""
    if not USERS_JSON.exists():
        return []
    data = json.loads(USERS_JSON.read_text(encoding="utf-8"))
    return [
        User(
            user_id=u["user_id"],
            email=u["email"],
            created_at=datetime.fromisoformat(u["created_at"]),
        )
        for u in data.get("users", [])
    ]


def save_users(users: List[User]) -> None:
    """Persist the user list to users.json."""
    USERS_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "users": [
            {
                "user_id": u.user_id,
                "email": u.email,
                "created_at": u.created_at.isoformat(),
            }
            for u in users
        ]
    }
    USERS_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def create_user(user_id: str, email: str) -> User:
    """
    Create a new user and append them to users.json.
    Raises ValueError if the user_id already exists.
    """
    existing = load_users()
    if any(u.user_id == user_id for u in existing):
        raise ValueError(f"User already exists: {user_id!r}")
    user = User(user_id=user_id, email=email, created_at=datetime.now(timezone.utc))
    save_users(existing + [user])
    return user
