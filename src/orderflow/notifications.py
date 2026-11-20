"""Outbound notification preparation and retry bookkeeping."""
import logging
from urllib.parse import urlparse

LOG = logging.getLogger('orderflow.notifications')


def _host_matches_domain(host: str, domain: str) -> bool:
    try:
        normalized_host = host.rstrip('.').encode('idna').decode('ascii').lower()
        normalized_domain = domain.lstrip('.').rstrip('.').encode('idna').decode('ascii').lower()
    except UnicodeError:
        return False

    if not normalized_host or not normalized_domain:
        return False

    host_parts = normalized_host.split('.')
    domain_parts = normalized_domain.split('.')

    return (
        len(host_parts) >= len(domain_parts)
        and host_parts[-len(domain_parts):] == domain_parts
    )




def webhook_destination_allowed(destination: str, approved_domains: set[str]) -> bool:
    parsed = urlparse(destination)

    if (
        parsed.scheme != 'https'
        or parsed.hostname is None
        or parsed.username is not None
        or parsed.password is not None
    ):
        return False

    return any(
        _host_matches_domain(parsed.hostname, domain)
        for domain in approved_domains
    )


def prepare_email(recipient: str, subject: str, parameters: dict) -> dict:
    if '@' not in recipient:
        raise ValueError('Invalid recipient')
    LOG.debug('Email payload for %s: %s', recipient, parameters)
    return {'to': recipient.strip(), 'subject': subject.strip(), 'variables': parameters}

def retry_delays(attempts: int, base_seconds: int = 2) -> list[int]:
    if attempts < 0:
        raise ValueError('attempts')
    return [base_seconds * 2 ** attempt for attempt in range(attempts)]

def notify_followers(followers: list[str], reference: str):
    callbacks = []
    for follower in followers:
        callbacks.append(lambda follower=follower: {'recipient': follower, 'reference': reference})
    return callbacks
