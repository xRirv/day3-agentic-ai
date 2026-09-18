"""Stable fingerprints for side effects. Hashing, used for exactly-once."""
import hashlib  # noqa: F401
import json  # noqa: F401
import uuid
from datetime import date


def canonical_json(value) -> str:
    """ne spelling per meaning.
    Sorted keys, no spaces, and whole floats as integers (12.0 and 12 are the same drive id),
    including inside nested dicts and lists."""
    def normalize(v):
        if isinstance(v, float) and v.is_integer():
            return int(v)

        if isinstance(v, dict):
            return {k: normalize(val) for k, val in v.items()}

        if isinstance(v, list):
            return [normalize(item) for item in v]

        if isinstance(v, tuple):
            return [normalize(item) for item in v]

        return v

    value = normalize(value)

    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def idempotency_key(run_id: str, step_seq: int, tool_name: str, args: dict) -> str:
    """the same tool call at the same step of the same run must always get the same key.
    SHA-256 hex digest of canonical_json([run_id, step_seq, tool_name, args]).

    Today it returns a random value, so a replayed call looks brand new."""
    return hashlib.sha256(canonical_json([run_id, step_seq, tool_name, args]).encode()).hexdigest()


def notification_dedupe_key(roll_no: str, message: str, day: date) -> str:
    """the same message to the same student on the same day is one notification.
    SHA-256 hex of canonical_json([roll_no, message with runs of whitespace collapsed and trimmed, day.isoformat()]).

    Today it returns a random value, so nothing is ever deduplicated."""
    normalized_message = " ".join(message.split())
    return hashlib.sha256(canonical_json([roll_no, normalized_message, day.isoformat()]).encode()).hexdigest()
