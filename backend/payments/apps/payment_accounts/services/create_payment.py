from dataclasses import asdict

from environs import Env
from yookassa import Configuration, Payment

from .. import schemas
from ..models import Account, BalanceChange

env = Env()
env.read_env()
Configuration.account_id = env.int('SHOP_ACCOUNT_ID')
Configuration.secret_key = env.str('SHOP_SECRET_KEY')


def deposit_to_balance(payment_data: schemas.PaymentCreateDataClass) -> str:
    user_account, _ = Account.objects.get_or_create(
        user_uuid=payment_data.user_uuid,
    )

    balance_change = BalanceChange.objects.create(
        account_id=user_account,
        is_accepted=False,
        operation_type='DEPOSIT',
    )
    metadata = {
        'account_id': user_account.pk,
        'balance_change_id': balance_change.pk,
    }
    return create_yookassa_payment(payment_data, metadata)


def create_yookassa_payment(
        payment_data: schemas.PaymentCreateDataClass,
        metadata: dict,
) -> str:

    yookassa_payment_info = schemas.YookassaPaymentCreate(
        amount=schemas.AmountDataClass(
            value=payment_data.payment_amount,
        ),
        payment_method_data=schemas.PaymentMethodData(
            type=payment_data.payment_type.value,
        ),
        confirmation=schemas.ConfirmationDataClass(
            type='redirect',
            return_url=payment_data.return_url,
        ),
        metadata=metadata,
        description=f'Пополнение на {str(payment_data.payment_amount)}',
    )
    payment = Payment.create(asdict(yookassa_payment_info))

    return payment.confirmation.confirmation_url
