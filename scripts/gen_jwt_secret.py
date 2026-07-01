"""
Generate a random JWT secret key.

Usage:
    python scripts/gen_jwt_secret.py
"""
import secrets


def main():
    key = secrets.token_urlsafe(48)
    print(f"JWT_SECRET={key}")


if __name__ == "__main__":
    main()
