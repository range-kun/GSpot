from decimal import Decimal
from uuid import UUID

from apps.transactions.models import Transaction, Invoice, TransactionHistory
from apps.transactions.schemas import InvoiceData, ItemPaymentData


class InvoiceCreator:
    def __init__(self, invoice_data: InvoiceData):
        self.invoice_data = invoice_data
        self.total_price = self.calculate_total_price()
        self.invoice_id = self.create_invoice_instance()

    def calculate_total_price(self) -> Decimal:
        total_price = 0
        for item_payment_data in self.invoice_data.items_payment_data:
            total_price += item_payment_data.price
        return total_price

    def create_invoice_instance(self) -> int:
        list_of_transaction: list[int] = []
        for item_payment_data in self.invoice_data.items_payment_data:
            transaction_id = self.create_transaction_instance(
                self.invoice_data.user_uuid,
                item_payment_data,
            )
            list_of_transaction.append(transaction_id)

        invoice = Invoice.objects.create(
            transactions=list_of_transaction,
        )
        return invoice.pk

    @staticmethod
    def create_transaction_instance(
            payer_uuid: UUID,
            item_payment_data: ItemPaymentData,
    ) -> int:
        transaction = Transaction.objects.create(
            account_from=payer_uuid,
            account_to=item_payment_data.owner_id,
            item_price=item_payment_data.price,
            item_uuid=item_payment_data.item_uuid,
        )
        TransactionHistory.objects.create(
            transaction_id=transaction,
            operation_type='CREATED',
        )
        return transaction.pk
