"""
Admin script — create a new user in storage/users/users.json.

Usage:
    python scripts/create_user.py <user_id> <email>

Example:
    python scripts/create_user.py alice alice@example.com
"""
import sys
from pathlib import Path

# Add project root to sys.path so app imports work when run from any directory.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.user_service import create_user  # noqa: E402


def main() -> None:
    if len(sys.argv) != 3:
        print("Usage: python scripts/create_user.py <user_id> <email>")
        sys.exit(1)

    user_id = sys.argv[1].strip()
    email = sys.argv[2].strip()

    if not user_id:
        print("Error: user_id cannot be empty.")
        sys.exit(1)
    if not email:
        print("Error: email cannot be empty.")
        sys.exit(1)

    try:
        user = create_user(user_id, email)
        print(f"Created user: user_id={user.user_id!r}  email={user.email!r}  created_at={user.created_at.isoformat()}")
    except ValueError as exc:
        print(f"Error: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
