#!/usr/bin/env python3
"""
Secret Manager für API-Keys (Gemini & Perplexity)
- Auto-Installation aller Dependencies
- Verschlüsselt mit cryptography.Fernet
- Passwortbasierte Key-Ableitung mit Scrypt
"""

import os
import sys
import subprocess
import json
import base64
import getpass
from typing import Tuple

# ============================================================================
# AUTO-INSTALLATION DEPENDENCIES
# ============================================================================

REQUIRED_PACKAGES = {
    'cryptography': 'cryptography>=41.0.0',
}

def check_and_install_dependencies():
    """Überprüft und installiert fehlende Pakete"""
    print("\n" + "="*60)
    print("🔍 Überprüfe erforderliche Python-Pakete...")
    print("="*60 + "\n")
    
    missing = []
    for pkg_import, pkg_pip in REQUIRED_PACKAGES.items():
        try:
            __import__(pkg_import)
            print(f"✓ {pkg_pip.split('>=')[0]} ist installiert")
        except ImportError:
            print(f"✗ {pkg_pip.split('>=')[0]} FEHLT - installiere...")
            missing.append(pkg_pip)
    
    if missing:
        print("\n" + "-"*60)
        for pkg in missing:
            try:
                print(f"📦 Installiere {pkg}...")
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install", pkg, "--quiet"
                ])
                print(f"✅ {pkg} erfolgreich installiert")
            except subprocess.CalledProcessError as e:
                print(f"❌ FEHLER beim Installieren von {pkg}")
                print(f"   Bitte manuell installieren: pip install {pkg}")
                return False
        print("-"*60)
    
    print("\n✅ Alle Pakete sind bereit!\n")
    return True

# Führe Installation SOFORT aus
if not check_and_install_dependencies():
    print("\n❌ Abhängigkeitsinstallation fehlgeschlagen!")
    sys.exit(1)

# Jetzt importieren nach Installation
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet


SALT_FILE = "salt.bin"
SECRETS_FILE = "secrets.enc"


def _derive_key_from_password(password: str, salt_file: str = SALT_FILE) -> bytes:
    """
    Leitet aus Passwort + Salt einen symmetrischen Key ab (für Fernet).
    """
    backend = default_backend()

    # Salt erzeugen oder laden
    if os.path.exists(salt_file):
        with open(salt_file, "rb") as f:
            salt = f.read()
    else:
        salt = os.urandom(16)
        with open(salt_file, "wb") as f:
            f.write(salt)

    kdf = Scrypt(
        salt=salt,
        length=32,
        n=2**14,
        r=8,
        p=1,
        backend=backend,
    )

    key = kdf.derive(password.encode("utf-8"))
    return base64.urlsafe_b64encode(key)


def create_encrypted_secrets():
    """
    Interaktiv: API Keys eingeben und verschlüsselt speichern
    """
    print("\n" + "="*60)
    print("🔐 API-Keys verschlüsselt speichern")
    print("="*60 + "\n")

    gemini = input("📌 Gemini API Key: ").strip()
    if not gemini:
        print("❌ Gemini API Key darf nicht leer sein.")
        return False

    perplexity = input("📌 Perplexity API Key: ").strip()
    if not perplexity:
        print("❌ Perplexity API Key darf nicht leer sein.")
        return False

    password = getpass.getpass("🔑 Master-Passwort (zum Verschlüsseln): ").strip()
    if not password:
        print("❌ Passwort darf nicht leer sein.")
        return False

    password_confirm = getpass.getpass("🔑 Passwort wiederholen: ").strip()
    if password != password_confirm:
        print("❌ Passwörter stimmen nicht überein.")
        return False

    # Verschlüsseln
    key = _derive_key_from_password(password)
    fernet = Fernet(key)

    data = {
        "gemini_api_key": gemini,
        "perplexity_api_key": perplexity,
    }

    plaintext = json.dumps(data).encode("utf-8")
    ciphertext = fernet.encrypt(plaintext)

    # Speichern
    with open(SECRETS_FILE, "wb") as f:
        f.write(ciphertext)

    print("\n" + "="*60)
    print("✅ Secrets erfolgreich verschlüsselt gespeichert!")
    print("="*60)
    print(f"   Datei: {SECRETS_FILE}")
    print(f"   Salt-Datei: {SALT_FILE}")
    print("\n⚠️  WICHTIG: Merke dir dein Passwort!")
    print("   Ohne Passwort sind die Keys verloren!\n")
    return True


def load_secrets_interactive() -> Tuple[str, str]:
    """
    Fragt nach Passwort und gibt entschlüsselte API-Keys zurück
    """
    if not os.path.exists(SECRETS_FILE):
        raise FileNotFoundError(
            f"❌ {SECRETS_FILE} nicht gefunden.\n"
            f"   Führe erst aus: python rag_cli.py --setup-secrets"
        )

    password = getpass.getpass("🔑 Master-Passwort: ").strip()
    if not password:
        raise ValueError("❌ Passwort darf nicht leer sein.")

    key = _derive_key_from_password(password)
    fernet = Fernet(key)

    with open(SECRETS_FILE, "rb") as f:
        ciphertext = f.read()

    try:
        plaintext = fernet.decrypt(ciphertext)
    except Exception as e:
        raise ValueError(f"❌ Entschlüsselung fehlgeschlagen (falsches Passwort?)")

    data = json.loads(plaintext.decode("utf-8"))

    gemini = data.get("gemini_api_key", "")
    perplexity = data.get("perplexity_api_key", "")

    if not gemini or not perplexity:
        raise ValueError("❌ Secrets-Datei ist unvollständig oder beschädigt.")

    return gemini, perplexity


if __name__ == "__main__":
    print("Secret Manager CLI")
    create_encrypted_secrets()
