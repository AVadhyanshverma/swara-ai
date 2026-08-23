import os
import secrets
from pathlib import Path

# Try to load keyring, if not, fallback to a local hidden file
try:
    import keyring
except ImportError:
    keyring = None

def get_or_create_device_key(service_name="SWARA_chat", username="device_user"):
    # Generate a robust device-specific key
    # 1. Try keyring
    if keyring:
        try:
            key = keyring.get_password(service_name, username)
            if key:
                return key
            
            # Create a new key
            key = secrets.token_hex(32)
            keyring.set_password(service_name, username, key)
            return key
        except Exception as e:
            pass # fallback
    
    # 2. Fallback to hidden file
    key_file = Path.home() / ".config" / "SWARA" / "db.key"
    if key_file.exists():
        with open(key_file, "r") as f:
            return f.read().strip()
    else:
        key_file.parent.mkdir(parents=True, exist_ok=True)
        key = secrets.token_hex(32)
        with open(key_file, "w") as f:
            f.write(key)
        os.chmod(key_file, 0o600)
        return key

print("Device key:", get_or_create_device_key()[:10] + "...")
