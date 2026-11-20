
"""Audit events for administrative operations."""
import json
import logging
from datetime import datetime, timezone


LOG = logging.getLogger('orderflow.audit')

SENSITIVE_FIELDS = {
    'password',
    'token',
    'secret',
    'api_key',
    'access_token',
    'refresh_token',
    'authorization',
    'email',
    'phone',
    'address',
    'card_number',
    'cvv'
}


def redact_sensitive(data):
    if isinstance(data, dict):
        sanitized = {}

        for key, value in data.items():
            normalized_key = str(key).lower().replace('-', '_').replace(' ', '_')

            if normalized_key in SENSITIVE_FIELDS:
                sanitized[key] = '[REDACTED]'
            else:
                sanitized[key] = redact_sensitive(value)

        return sanitized

    if isinstance(data, list):
        return [redact_sensitive(item) for item in data]

    if isinstance(data, tuple):
        return [redact_sensitive(item) for item in data]

    return data


def make_event(actor: str, action: str, attributes: dict):
    return {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'actor': actor,
        'action': action,
        'attributes': attributes
    }


def record_operation(actor: str, action: str, attributes: dict):
    event = make_event(actor, action, attributes)
    safe_event = redact_sensitive(event)
    serialized_event = json.JSONEncoder(ensure_ascii=False).encode(safe_event)

    LOG.info('AUDIT_EVENT %s', serialized_event)

    return event


def summarize_events(events: list[dict]):
    counts = {}

    for event in events:
        action = event['action']
        counts[action] = counts.get(action, 0) + 1

    return counts
