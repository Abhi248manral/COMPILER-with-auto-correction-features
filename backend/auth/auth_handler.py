"""
File-Based Authentication Handler
Stores credentials in data/users.txt with hashed passwords.
No database required — simple text file storage.
"""
import os
import hashlib
import secrets
import re

# Path to user credentials file
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data'))
USERS_FILE = os.path.join(DATA_DIR, 'users.txt')

# In-memory session tokens (simple — resets on server restart)
_active_sessions = {}


def _ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w') as f:
            f.write("# username:password_hash:salt\n")


def _hash_password(password: str, salt: str = None) -> tuple:
    """Hash password with SHA-256 + salt. Returns (hash, salt)."""
    if salt is None:
        salt = secrets.token_hex(16)
    hashed = hashlib.sha256((salt + password).encode()).hexdigest()
    return hashed, salt


def _read_users() -> dict:
    """Read all users from file. Returns {username: (hash, salt)}."""
    _ensure_data_dir()
    users = {}
    with open(USERS_FILE, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split(':')
            if len(parts) == 3:
                users[parts[0]] = (parts[1], parts[2])
    return users


def _write_user(username: str, pw_hash: str, salt: str):
    """Append a new user to the credentials file."""
    _ensure_data_dir()
    with open(USERS_FILE, 'a') as f:
        f.write(f"{username}:{pw_hash}:{salt}\n")


def validate_username(username: str) -> str | None:
    """Validate username. Returns error message or None if valid."""
    if not username or len(username) < 3:
        return "Username must be at least 3 characters"
    if len(username) > 30:
        return "Username must be at most 30 characters"
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return "Username can only contain letters, numbers, and underscores"
    return None


def validate_password(password: str) -> str | None:
    """Validate password. Returns error message or None if valid."""
    if not password or len(password) < 4:
        return "Password must be at least 4 characters"
    if len(password) > 100:
        return "Password must be at most 100 characters"
    return None


def register_user(username: str, password: str) -> dict:
    """Register a new user. Returns result dict."""
    # Validate
    err = validate_username(username)
    if err:
        return {"success": False, "error": err}
    err = validate_password(password)
    if err:
        return {"success": False, "error": err}

    users = _read_users()
    if username.lower() in {u.lower() for u in users}:
        return {"success": False, "error": "Username already exists"}

    pw_hash, salt = _hash_password(password)
    _write_user(username, pw_hash, salt)

    # Auto-login: generate session token
    token = secrets.token_hex(32)
    _active_sessions[token] = username

    return {"success": True, "token": token, "username": username}


def login_user(username: str, password: str) -> dict:
    """Login an existing user. Returns result dict."""
    users = _read_users()

    if username not in users:
        return {"success": False, "error": "Invalid username or password"}

    stored_hash, salt = users[username]
    check_hash, _ = _hash_password(password, salt)

    if check_hash != stored_hash:
        return {"success": False, "error": "Invalid username or password"}

    token = secrets.token_hex(32)
    _active_sessions[token] = username

    return {"success": True, "token": token, "username": username}


def verify_token(token: str) -> str | None:
    """Verify session token. Returns username or None."""
    return _active_sessions.get(token)


def logout(token: str):
    """Remove session token."""
    _active_sessions.pop(token, None)
