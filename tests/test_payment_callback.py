
from orderflow.billing import (
    Payment,
    accept_payment_callback,
    payment_callback_signature
)


def test_accept_authenticated_payment_callback():
    payment = Payment(1, 1500, 'RUB', 'payment-1', 'captured')
    secret = 'test-secret'
    signature = payment_callback_signature(payment, secret)

    assert accept_payment_callback(
        payment,
        'RUB',
        {1},
        signature,
        secret
    )


def test_reject_payment_callback_without_signature():
    payment = Payment(1, 1500, 'RUB', 'payment-1', 'captured')

    assert not accept_payment_callback(payment, 'RUB', {1})


def test_reject_payment_callback_with_invalid_signature():
    payment = Payment(1, 1500, 'RUB', 'payment-1', 'captured')

    assert not accept_payment_callback(
        payment,
        'RUB',
        {1},
        'invalid-signature',
        'test-secret'
    )


def test_reject_payment_callback_for_unknown_order():
    payment = Payment(1, 1500, 'RUB', 'payment-1', 'captured')
    secret = 'test-secret'
    signature = payment_callback_signature(payment, secret)

    assert not accept_payment_callback(
        payment,
        'RUB',
        {2},
        signature,
        secret
    )
