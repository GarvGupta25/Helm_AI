"""Authenticated encryption for research visitor state, separate from generated exports."""
import json
import os

from cryptography.fernet import Fernet
from fastapi import HTTPException
from sqlalchemy import JSON
from sqlalchemy.types import TypeDecorator

from ..config import settings

_ephemeral_key = Fernet.generate_key()


def stable_key():
    return os.environ.get("RESEARCH_STATE_KEY", settings().research_state_key)


def cipher():
    return Fernet(stable_key().encode() or _ephemeral_key)


class EncryptedState(TypeDecorator):
    impl = JSON
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return {"format": "fernet-v1", "ciphertext": cipher().encrypt(json.dumps(value).encode()).decode()}

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if value.get("format") != "fernet-v1":
            raise HTTPException(410, "This old unencrypted demo session must be replaced. Start a new research session.")
        try:
            return json.loads(cipher().decrypt(value["ciphertext"].encode()))
        except Exception:
            raise HTTPException(410, "This research session key expired. Start a new session.") from None
