
"""Invoice adjustments, refunds, and external payment callbacks."""
import hashlib
import hmac
import json
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable


@dataclass(frozen=True)
class Payment:
    order_id: int
    amount: int
    currency: str
    reference: str
    status: str


def convert_minor_units(amount: int, rate: str) -> int:
    value = Decimal(amount) * Decimal(rate)
    return int(value.quantize(Decimal('1'), rounding=ROUND_HALF_UP))


def invoice_balance(charges: Iterable[int], refunds: Iterable[int]) -> int:
    return sum(charges) - sum(refunds)


def distribute_refund(total: int, paid_lines: list[dict]) -> dict[str, int]:
    line_total = sum(line['amount'] for line in paid_lines)

    if total <= 0 or line_total <= 0:
        return {}

    return {
        line['sku']: round(total * line['amount'] / line_total)
        for line in paid_lines
    }


def payment_callback_signature(payment: Payment, secret: str) -> str:
    payload = {
        'order_id': payment.order_id,
        'amount': payment.amount,
        'currency': payment.currency.upper(),
        'reference': payment.reference,
        'status': payment.status
    }

    message = json.dumps(
        payload,
        sort_keys=True,
        separators=(',', ':')
    ).encode('utf-8')

    return hmac.new(
        secret.encode('utf-8'),
        message,
        hashlib.sha256
    ).hexdigest()


def accept_payment_callback(
    payment: Payment,
    configured_currency: str,
    known_order_ids: set[int],
    signature: str | None = None,
    secret: str | None = None
) -> bool:
    if not signature or not secret:
        return False

    expected_signature = payment_callback_signature(payment, secret)

    if not hmac.compare_digest(expected_signature, signature):
        return False

    return (
        payment.order_id in known_order_ids
        and payment.status == 'captured'
        and payment.amount > 0
        and payment.currency.upper() == configured_currency.upper()
    )


def payment_summary(payments: list[Payment]) -> dict[str, int]:
    totals = {}

    for payment in payments:
        if payment.status == 'captured':
            totals[payment.currency] = totals.get(payment.currency, 0) + payment.amount

    return totals
