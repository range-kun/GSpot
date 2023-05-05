from apps.base.schemas import URL, PaymentServices
from apps.external_payments.services.payment_serivces.yookassa_payment import (
    YookassaService,
)

from ..models import Account, BalanceChange


def request_balance_deposit_url(
    balance_increase_data: BalanceChange,
) -> URL:
    user_account, _ = Account.objects.get_or_create(
        user_uuid=balance_increase_data.user_uuid,
    )

    balance_change = BalanceChange.objects.create(
        account_id=user_account,
        is_accepted=False,
        operation_type='DEPOSIT',
    )

    if balance_increase_data.payment_service == PaymentServices.yookassa:
        payment_data = YookassaService.create_balance_increase_data(
            balance_increase_data,
            user_account,
            balance_change,
        )
        return YookassaService().request_balance_deposit_url(
            payment_data,
        )