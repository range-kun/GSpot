from decimal import Decimal

import rollbar
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from ..models import Account, BalanceChange
from ..schemas import PaymentResponseStatuses


def payment_acceptance(response) -> bool:
    try:
        payment_response = response['object']
        response_metadata = payment_response['metadata']
        payment_amount = payment_response['income_amount']['value']
    except KeyError:
        rollbar.report_message(
            "Can't parse response from yookassa.",
            'error',
        )
        return False

    try:
        balance_change_object = BalanceChange.objects.get(
            id=response_metadata['balance_change_id'],
        )
    except ObjectDoesNotExist:
        payment_id = payment_response['id']
        rollbar.report_message(
            f"Can't get payment instance for payment id {payment_id}",
            'warning',
        )
        return False

    if response['event'] == PaymentResponseStatuses.succeeded.value:
        increase_user_balance(
            balance_change_object=balance_change_object,
            amount=Decimal(payment_amount),
        )
    elif response['event'] == PaymentResponseStatuses.canceled.value:
        balance_change_object.delete()

    return True


def increase_user_balance(*, balance_change_object, amount: Decimal) -> None:
    balance_change_object.is_accepted = True
    balance_change_object.amount = amount
    balance_change_object.save()

    # in future handle situation if database not connected and code below throw exception
    Account.deposit(
        pk=balance_change_object.account_id.pk,
        amount=Decimal(amount),
    )
    rollbar.report_message((
        f'Deposit {balance_change_object.amount} {settings.DEFAULT_CURRENCY} to '
        f'user account {balance_change_object.account_id}'
    ),
        'info',
    )
