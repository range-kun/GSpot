from decimal import Decimal

import rollbar
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction

from ..models import Account, BalanceChange
from ..schemas import PaymentResponseStatuses, YookassaPaymentResponse


def payment_acceptance(yookassa_response: YookassaPaymentResponse) -> bool:
    payment_status = yookassa_response.event
    payment_body = yookassa_response.object
    income_value = payment_body.income_amount.value

    rollbar.report_message(
        (
            f'Received payment data for: '
            f'account_id: f{payment_body.metadata["account_id"]}'
            f'with payment amount: {income_value}'
        ),
        'info',
    )

    try:
        balance_change_object = BalanceChange.objects.get(
            id=payment_body.metadata['balance_change_id'],
        )
    except ObjectDoesNotExist:
        rollbar.report_message(
            f"Can't get payment instance for payment id {payment_body.id}",
            'warning',
        )
        return False

    if payment_status == PaymentResponseStatuses.succeeded.value:
        increase_user_balance(
            balance_change_object=balance_change_object,
            amount=Decimal(income_value),
        )
    elif payment_status == PaymentResponseStatuses.canceled.value:
        balance_change_object.delete()

    return True


def increase_user_balance(*, balance_change_object, amount: Decimal) -> None:
    # in future handle situation if database not connected
    # and code below throw exception
    with transaction.atomic():
        balance_change_object.is_accepted = True
        balance_change_object.amount = amount
        balance_change_object.save()

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
