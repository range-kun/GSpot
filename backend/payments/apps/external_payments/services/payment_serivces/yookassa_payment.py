from dataclasses import asdict

from apps.base.classes import AbstractPaymentClass
from apps.base.schemas import URL
from apps.external_payments import schemas
from apps.payment_accounts.models import Account, BalanceChange
from apps.transactions.models import Invoice
from apps.transactions.schemas import PurchaseItemsData
from yookassa import Payment


class YookassaPayment(AbstractPaymentClass):
    def request_balance_deposit_url(self, payment_data):
        yookassa_payment_info = schemas.YookassaPaymentCreate(
            amount=schemas.AmountDataClass(
                value=payment_data.payment_amount,
            ),
            payment_method_data=schemas.PaymentMethodDataCreate(
                payment_type=payment_data.payment_type.value,
            ),
            confirmation=schemas.ConfirmationDataClass(
                confirmation_type='redirect',
                return_url=payment_data.return_url,
            ),
            metadata=payment_data.metadata,
            description=f'Пополнение на {str(payment_data.payment_amount)}',
        )

        payment = Payment.create(yookassa_payment_info.to_dict())

        return URL(payment.confirmation.confirmation_url)

    @staticmethod
    def create_balance_increase_data(
            balance_increase_data: schemas.BalanceIncreaseData,
            user_account: Account,
            balance_change: BalanceChange,
    ) -> schemas.YookassaRequestPayment:
        metadata = {
            'account_id': user_account.pk,
            'balance_change_id': balance_change.pk,
        }
        return schemas.YookassaRequestPayment(
            **asdict(balance_increase_data),
            metadata=metadata,
        )

    @staticmethod
    def create_purchase_items_data(
            purchase_items_data: PurchaseItemsData,
            user_account: Account,
            balance_change: BalanceChange,
            invoice_instance: Invoice,
    ) -> schemas.YookassaRequestPayment:
        metadata = {
            'account_id': user_account.pk,
            'balance_change_id': balance_change.pk,
            'invoice_id': str(invoice_instance.invoice_id),
        }

        return schemas.YookassaRequestPayment(
            payment_amount=invoice_instance.total_price,
            payment_service=purchase_items_data.payment_service,
            payment_type=purchase_items_data.payment_type,
            user_uuid=purchase_items_data.user_uuid,
            return_url=purchase_items_data.return_url,
            metadata=metadata,
        )

    def request_balance_withdraw_url(self, payment_data):
        pass

    def validate_income_data(self, balance_object, invoice_object: None = None):
        pass

    def parse_income_data(self):
        pass
