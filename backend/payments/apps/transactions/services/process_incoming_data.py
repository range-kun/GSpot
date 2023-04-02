from apps.payment_accounts.models import Account, BalanceChange
from apps.payment_accounts.schemas import PaymentCreateDataClass
from apps.payment_accounts.services.create_payment import create_yookassa_payment
from apps.transactions import schemas
from apps.transactions.services.invoice_creation import InvoiceCreator


def purchase_items(invoice_data: schemas.InvoiceData) -> str:
    user_account, _ = Account.objects.get_or_create(
        user_uuid=invoice_data.user_uuid,
    )
    balance_change = BalanceChange.objects.create(
        account_id=user_account,
        is_accepted=False,
        operation_type='DEPOSIT',
    )
    invoice_instance = InvoiceCreator(invoice_data)
    metadata = {
        'account_id': user_account.pk,
        'balance_change_id': balance_change.pk,
        'invoice_id': invoice_data.invoice_id,
    }

    payment_data = PaymentCreateDataClass(
        user_uuid=invoice_data.user_uuid,
        payment_amount=invoice_instance.total_price,
        payment_type=invoice_data.payment_type,
        return_url=invoice_data.return_url,
    )
    return create_yookassa_payment(payment_data, metadata)
