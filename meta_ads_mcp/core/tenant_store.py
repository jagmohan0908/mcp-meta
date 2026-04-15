"""Tenant and token persistence for self-hosted Meta Ads MCP."""

from __future__ import annotations

import base64
import hashlib
import os
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _xor_crypt(payload: bytes, secret: str) -> bytes:
    key = hashlib.sha256(secret.encode("utf-8")).digest()
    out = bytearray()
    for i, b in enumerate(payload):
        out.append(b ^ key[i % len(key)])
    return bytes(out)


def encrypt_token(token: str, secret: str) -> str:
    raw = token.encode("utf-8")
    encrypted = _xor_crypt(raw, secret)
    return base64.urlsafe_b64encode(encrypted).decode("utf-8")


def decrypt_token(token: str, secret: str) -> str:
    encrypted = base64.urlsafe_b64decode(token.encode("utf-8"))
    raw = _xor_crypt(encrypted, secret)
    return raw.decode("utf-8")


@dataclass
class TenantAuthContext:
    tenant_id: str
    user_id: Optional[str]
    access_token: str
    source: str


class TenantStore:
    """SQLite persistence for tenants, keys and encrypted access tokens."""

    def __init__(self, db_path: Optional[str] = None, encryption_key: Optional[str] = None):
        default_path = Path.home() / ".meta-ads-mcp" / "meta_ads_mcp.db"
        self.db_path = Path(db_path or os.environ.get("META_MCP_DB_PATH", str(default_path)))
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.encryption_key = encryption_key or os.environ.get("META_MCP_ENCRYPTION_KEY", "")
        if not self.encryption_key:
            raise RuntimeError("META_MCP_ENCRYPTION_KEY is required for multi-tenant token storage.")
        self._init_db()

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tenants (
                    tenant_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tenant_api_keys (
                    api_key_hash TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    user_id TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(tenant_id) REFERENCES tenants(tenant_id)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tenant_tokens (
                    tenant_id TEXT PRIMARY KEY,
                    access_token_encrypted TEXT NOT NULL,
                    expires_at INTEGER,
                    meta_user_id TEXT,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(tenant_id) REFERENCES tenants(tenant_id)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tenant_accounts (
                    tenant_id TEXT NOT NULL,
                    account_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (tenant_id, account_id),
                    FOREIGN KEY(tenant_id) REFERENCES tenants(tenant_id)
                )
                """
            )

    @staticmethod
    def _key_hash(api_key: str) -> str:
        return hashlib.sha256(api_key.encode("utf-8")).hexdigest()

    def ensure_tenant(self, tenant_id: str, name: Optional[str] = None) -> None:
        with self._conn() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO tenants (tenant_id, name, created_at) VALUES (?, ?, ?)",
                (tenant_id, name or tenant_id, utc_now_iso()),
            )

    def register_api_key(self, tenant_id: str, api_key: str, user_id: Optional[str] = None) -> None:
        self.ensure_tenant(tenant_id)
        with self._conn() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO tenant_api_keys (api_key_hash, tenant_id, user_id, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (self._key_hash(api_key), tenant_id, user_id, utc_now_iso()),
            )

    def resolve_api_key(self, api_key: str) -> Optional[tuple[str, Optional[str]]]:
        key_hash = self._key_hash(api_key)
        with self._conn() as conn:
            row = conn.execute(
                "SELECT tenant_id, user_id FROM tenant_api_keys WHERE api_key_hash = ?",
                (key_hash,),
            ).fetchone()
            if not row:
                return None
            return row["tenant_id"], row["user_id"]

    def store_meta_token(
        self,
        tenant_id: str,
        access_token: str,
        expires_at: Optional[int] = None,
        meta_user_id: Optional[str] = None,
    ) -> None:
        self.ensure_tenant(tenant_id)
        encrypted = encrypt_token(access_token, self.encryption_key)
        with self._conn() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO tenant_tokens
                (tenant_id, access_token_encrypted, expires_at, meta_user_id, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (tenant_id, encrypted, expires_at, meta_user_id, utc_now_iso()),
            )

    def get_meta_token(self, tenant_id: str) -> Optional[str]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT access_token_encrypted FROM tenant_tokens WHERE tenant_id = ?",
                (tenant_id,),
            ).fetchone()
            if not row:
                return None
            return decrypt_token(row["access_token_encrypted"], self.encryption_key)

    def grant_account_access(self, tenant_id: str, account_id: str) -> None:
        self.ensure_tenant(tenant_id)
        with self._conn() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO tenant_accounts (tenant_id, account_id, created_at) VALUES (?, ?, ?)",
                (tenant_id, account_id, utc_now_iso()),
            )

    def has_account_access(self, tenant_id: str, account_id: str) -> bool:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT 1 FROM tenant_accounts WHERE tenant_id = ? AND account_id = ?",
                (tenant_id, account_id),
            ).fetchone()
            return bool(row)

