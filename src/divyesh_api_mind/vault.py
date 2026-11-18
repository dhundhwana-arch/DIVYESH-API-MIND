"""Optional passphrase-encrypted API key vault and safe .env parsing.

No master secret is generated, stored, printed, or recovered by this module.
A caller must explicitly provide it to unlock the vault. API values are only
returned to a Python caller that asks for them; CLI commands never print them.
"""

from __future__ import annotations

import base64
import getpass
import hashlib
import json
import os
import re
import secrets
import stat
import tempfile
from pathlib import Path
from typing import Mapping

_FORMAT = "divyesh-api-mind-key-vault"
_VERSION = 1
_SCRYPT_N = 2**15
_SCRYPT_R = 8
_SCRYPT_P = 1
_KEY_BYTES = 32
_SALT_BYTES = 16
_NONCE_BYTES = 12
_MAX_FILE_BYTES = 1024 * 1024
_MAX_PASSPHRASE_BYTES = 1024
_ENV_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class VaultError(ValueError):
    """Safe vault configuration, decryption, or storage error."""


def default_vault_path() -> Path:
    """Return the per-user config path without creating it."""
    configured = os.environ.get("APIMIND_VAULT_PATH")
    if configured:
        return Path(configured).expanduser()
    config_home = os.environ.get("XDG_CONFIG_HOME")
    base = Path(config_home).expanduser() if config_home else Path.home() / ".config"
    return base / "divyesh-api-mind" / "keys.vault"


def _validate_env_name(name: str) -> None:
    if not isinstance(name, str) or not _ENV_NAME.fullmatch(name):
        raise VaultError("key name must be a valid environment-variable name")


def _password_bytes(password: str, *, for_creation: bool = False) -> bytes:
    if not isinstance(password, str) or not password:
        raise VaultError("a user-supplied master passphrase is required")
    encoded = password.encode("utf-8")
    if len(encoded) > _MAX_PASSPHRASE_BYTES:
        raise VaultError(f"master passphrase exceeds the {_MAX_PASSPHRASE_BYTES}-byte safe length limit")
    if for_creation and len(password) < 12:
        raise VaultError("use a master passphrase of at least 12 characters")
    return encoded


def _crypto():
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    except ImportError:
        raise VaultError("encrypted vault support requires the optional 'security' extra (cryptography)") from None
    return AESGCM


def _derive(password: bytes, salt: bytes) -> bytes:
    try:
        return hashlib.scrypt(password, salt=salt, n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P, dklen=_KEY_BYTES, maxmem=64 * 1024 * 1024)
    except (ValueError, OSError):
        raise VaultError("could not derive the vault encryption key") from None


def _aad() -> bytes:
    return f"{_FORMAT}:{_VERSION}:AES-256-GCM".encode("ascii")


def _safe_path(path: str | Path | None) -> Path:
    target = Path(path).expanduser() if path is not None else default_vault_path()
    if target.is_symlink():
        raise VaultError("vault path must not be a symbolic link")
    if target.exists() and not target.is_file():
        raise VaultError("vault path must be a regular file")
    return target


def _read_envelope(path: Path) -> dict[str, object]:
    if path.is_symlink():
        raise VaultError("vault path must not be a symbolic link")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
    if os.name == "posix":
        # Avoid blocking on a FIFO or following a last-component symlink if the
        # path changes between validation and open. Ancestor races still depend
        # on the filesystem/platform and are documented as a residual limit.
        flags |= getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    try:
        descriptor = os.open(path, flags)
    except FileNotFoundError:
        raise VaultError("vault does not exist; add a key to create it") from None
    except OSError:
        raise VaultError("vault file could not be opened safely") from None
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            raise VaultError("vault path must be a regular file")
        if os.name == "posix":
            if metadata.st_mode & 0o077:
                raise VaultError("vault file permissions are too broad; restrict them to 0600")
            if hasattr(os, "geteuid") and metadata.st_uid != os.geteuid():
                raise VaultError("vault file must be owned by the current user")
        if metadata.st_size > _MAX_FILE_BYTES:
            raise VaultError("vault file exceeds the safe size limit")
        with os.fdopen(descriptor, "rb") as stream:
            descriptor = -1
            raw = stream.read(_MAX_FILE_BYTES + 1)
    except VaultError:
        raise
    except OSError:
        raise VaultError("vault file could not be read safely") from None
    finally:
        if descriptor >= 0:
            os.close(descriptor)
    if len(raw) > _MAX_FILE_BYTES:
        raise VaultError("vault file exceeds the safe size limit")
    try:
        envelope = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError):
        raise VaultError("vault file is malformed or corrupted") from None
    if not isinstance(envelope, dict):
        raise VaultError("vault file is malformed or corrupted")
    if envelope.get("format") != _FORMAT or envelope.get("version") != _VERSION:
        raise VaultError("vault format or version is unsupported")
    if envelope.get("cipher") != "AES-256-GCM" or envelope.get("kdf") != {
        "name": "scrypt", "n": _SCRYPT_N, "r": _SCRYPT_R, "p": _SCRYPT_P, "dklen": _KEY_BYTES
    }:
        raise VaultError("vault cryptographic parameters are unsupported")
    return envelope


def _decode_field(envelope: Mapping[str, object], field: str, expected: int | None = None) -> bytes:
    value = envelope.get(field)
    if not isinstance(value, str):
        raise VaultError("vault file is malformed or corrupted")
    try:
        result = base64.b64decode(value, validate=True)
    except (ValueError, base64.binascii.Error):
        raise VaultError("vault file is malformed or corrupted") from None
    if expected is not None and len(result) != expected:
        raise VaultError("vault file is malformed or corrupted")
    return result


def _decrypt(path: Path, passphrase: str) -> dict[str, str]:
    envelope = _read_envelope(path)
    salt = _decode_field(envelope, "salt", _SALT_BYTES)
    nonce = _decode_field(envelope, "nonce", _NONCE_BYTES)
    ciphertext = _decode_field(envelope, "ciphertext")
    AESGCM = _crypto()
    try:
        plaintext = AESGCM(_derive(_password_bytes(passphrase), salt)).decrypt(nonce, ciphertext, _aad())
        payload = json.loads(plaintext.decode("utf-8"))
    except Exception:
        # AES-GCM authentication deliberately makes wrong-password and tamper
        # errors indistinguishable; never return cryptographic exception text.
        raise VaultError("vault could not be decrypted (wrong passphrase or corrupted data)") from None
    if not isinstance(payload, dict) or payload.get("schema_version") != _VERSION or not isinstance(payload.get("keys"), dict):
        raise VaultError("decrypted vault payload has an unsupported structure")
    keys: dict[str, str] = {}
    for name, value in payload["keys"].items():
        _validate_env_name(name)
        if not isinstance(value, str) or not value or "\n" in value or "\r" in value:
            raise VaultError("decrypted vault contains an invalid key entry")
        keys[name] = value
    return keys


def _write_private_atomic(path: Path, content: bytes) -> None:
    path = _safe_path(path)
    parent = path.parent
    try:
        parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    except OSError:
        raise VaultError("vault directory could not be created") from None
    if parent.is_symlink():
        raise VaultError("vault directory must not be a symbolic link")
    if os.name == "posix":
        try:
            mode = stat.S_IMODE(parent.stat().st_mode)
            if mode & 0o077:
                raise VaultError("vault directory permissions are too broad; restrict them to 0700")
        except OSError:
            raise VaultError("vault directory permissions could not be checked") from None
    fd = -1
    temp_name = None
    try:
        fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=parent)
        if os.name == "posix":
            os.fchmod(fd, 0o600)
        with os.fdopen(fd, "wb") as stream:
            fd = -1
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        if path.exists() and path.is_symlink():
            raise VaultError("vault path must not be a symbolic link")
        os.replace(temp_name, path)
        temp_name = None
        if os.name == "posix":
            os.chmod(path, 0o600)
        try:
            dir_fd = os.open(parent, os.O_RDONLY)
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)
        except OSError:
            pass
    except VaultError:
        raise
    except OSError:
        raise VaultError("vault could not be written safely") from None
    finally:
        if fd >= 0:
            os.close(fd)
        if temp_name:
            try:
                os.unlink(temp_name)
            except OSError:
                pass


def _encrypt(path: Path, keys: Mapping[str, str], passphrase: str) -> None:
    pass_bytes = _password_bytes(passphrase, for_creation=True)
    sanitized: dict[str, str] = {}
    for name, value in keys.items():
        _validate_env_name(name)
        if not isinstance(value, str) or not value.strip() or "\n" in value or "\r" in value:
            raise VaultError("key values must be non-empty single-line strings")
        sanitized[name] = value
    AESGCM = _crypto()
    salt = secrets.token_bytes(_SALT_BYTES)
    nonce = secrets.token_bytes(_NONCE_BYTES)
    plaintext = json.dumps(
        {"schema_version": _VERSION, "keys": sanitized}, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    if len(plaintext) > _MAX_FILE_BYTES // 2:
        raise VaultError("vault contents exceed the safe size limit")
    ciphertext = AESGCM(_derive(pass_bytes, salt)).encrypt(nonce, plaintext, _aad())
    envelope = {
        "format": _FORMAT,
        "version": _VERSION,
        "cipher": "AES-256-GCM",
        "kdf": {"name": "scrypt", "n": _SCRYPT_N, "r": _SCRYPT_R, "p": _SCRYPT_P, "dklen": _KEY_BYTES},
        "salt": base64.b64encode(salt).decode("ascii"),
        "nonce": base64.b64encode(nonce).decode("ascii"),
        "ciphertext": base64.b64encode(ciphertext).decode("ascii"),
    }
    raw = (json.dumps(envelope, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    _write_private_atomic(path, raw)


class KeyVault:
    """Passphrase-encrypted AES-GCM vault for user-authorized key values.

    Applications explicitly call :meth:`environment` and pass the result to
    ``APIMind(env=...)``. The vault never logs or prints values.
    """

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = _safe_path(path)

    def status(self) -> dict[str, object]:
        """Report existence and permissions only; never decrypt or list keys."""
        exists = self.path.is_file() and not self.path.is_symlink()
        result: dict[str, object] = {"exists": exists, "path": str(self.path), "encrypted": exists, "permissions": "UNKNOWN"}
        if exists and os.name == "posix":
            try:
                mode = stat.S_IMODE(self.path.stat().st_mode)
                result["permissions"] = oct(mode)
                result["permissions_secure"] = not bool(mode & 0o077)
            except OSError:
                result["permissions_secure"] = False
        return result

    def list_names(self, passphrase: str) -> list[str]:
        """List variable names only after explicitly unlocking the vault."""
        return sorted(_decrypt(self.path, passphrase))

    def get(self, name: str, passphrase: str) -> str:
        """Return one secret to an explicit Python caller; CLI never calls this for display."""
        _validate_env_name(name)
        keys = _decrypt(self.path, passphrase)
        try:
            return keys[name]
        except KeyError:
            raise VaultError(f"vault contains no entry named {name}") from None

    def environment(self, passphrase: str) -> dict[str, str]:
        """Unlock keys for in-process client configuration; do not log the result."""
        return _decrypt(self.path, passphrase)

    def set(self, name: str, value: str, passphrase: str) -> None:
        """Add or rotate one key; replacing an entry re-encrypts the whole vault."""
        _validate_env_name(name)
        if not isinstance(value, str) or not value.strip() or "\n" in value or "\r" in value:
            raise VaultError("key values must be non-empty single-line strings")
        if self.path.exists():
            keys = _decrypt(self.path, passphrase)
            _password_bytes(passphrase, for_creation=True)
        else:
            keys = {}
            _password_bytes(passphrase, for_creation=True)
        keys[name] = value
        _encrypt(self.path, keys, passphrase)

    def delete(self, name: str, passphrase: str) -> None:
        """Delete one entry and atomically re-encrypt the remaining keys."""
        _validate_env_name(name)
        keys = _decrypt(self.path, passphrase)
        if name not in keys:
            raise VaultError(f"vault contains no entry named {name}")
        del keys[name]
        _encrypt(self.path, keys, passphrase)

    def rekey(self, old_passphrase: str, new_passphrase: str) -> None:
        """Change the master passphrase without changing key names or values."""
        keys = _decrypt(self.path, old_passphrase)
        _password_bytes(new_passphrase, for_creation=True)
        _encrypt(self.path, keys, new_passphrase)


def load_env_file(path: str | Path) -> dict[str, str]:
    """Parse a restricted, non-executing .env subset (no expansion/shell code).

    Blank lines and comments are ignored. Values may be single/double quoted;
    multiline values, duplicate names, invalid variable names, and symlinks are
    rejected. The file is only read when the caller explicitly names it.
    """
    target = Path(path).expanduser()
    if target.is_symlink():
        raise VaultError(".env file must not be a symbolic link")
    max_bytes = 64 * 1024
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
    if os.name == "posix":
        flags |= getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    try:
        descriptor = os.open(target, flags)
    except OSError:
        raise VaultError(".env file could not be opened safely") from None
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            raise VaultError(".env path must be a regular file")
        if metadata.st_size > max_bytes:
            raise VaultError(".env file exceeds the safe size limit")
        with os.fdopen(descriptor, "rb") as stream:
            descriptor = -1
            raw_bytes = stream.read(max_bytes + 1)
    except VaultError:
        raise
    except OSError:
        raise VaultError(".env file could not be read safely") from None
    finally:
        if descriptor >= 0:
            os.close(descriptor)
    if len(raw_bytes) > max_bytes:
        raise VaultError(".env file exceeds the safe size limit")
    try:
        raw = raw_bytes.decode("utf-8")
    except UnicodeError:
        raise VaultError(".env file could not be read as UTF-8") from None
    values: dict[str, str] = {}
    for line_number, line in enumerate(raw.splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("export "):
            stripped = stripped[7:].lstrip()
        if "=" not in stripped:
            raise VaultError(f".env line {line_number} must be NAME=VALUE")
        name, value = stripped.split("=", 1)
        name, value = name.strip(), value.strip()
        _validate_env_name(name)
        if name in values:
            raise VaultError(f".env contains duplicate variable {name}")
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        elif "\"" in value or "'" in value:
            raise VaultError(f".env line {line_number} has unmatched quotes")
        if "\n" in value or "\r" in value:
            raise VaultError(f".env line {line_number} contains a multiline value")
        if value:
            values[name] = value
    return values


def compose_environment(
    *,
    process_environment: Mapping[str, str] | None = None,
    env_file: str | Path | None = None,
    vault: KeyVault | None = None,
    master_passphrase: str | None = None,
) -> dict[str, str]:
    """Merge explicitly loaded sources; shell values take precedence over files/vault."""
    combined: dict[str, str] = {}
    if env_file is not None:
        combined.update(load_env_file(env_file))
    if vault is not None:
        if master_passphrase is None:
            raise VaultError("unlocking the key vault requires an explicit master passphrase")
        for name, value in vault.environment(master_passphrase).items():
            combined.setdefault(name, value)
    if process_environment is not None:
        combined.update({str(k): str(v) for k, v in process_environment.items()})
    else:
        combined.update(os.environ)
    return combined


def prompt_secret(prompt: str) -> str:
    """Prompt without echo; exposed separately for the interactive CLI."""
    return getpass.getpass(prompt)
