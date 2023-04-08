from decimal import Decimal

import rollbar
from django.conf import settings
from django.db import transaction

from apps.external_payments.schemas import (PaymentResponseStatuses,
                                            YookassaPaymentResponse)
from apps.payment_accounts.models import Account, BalanceChange
from apps.payment_accounts.services.payment_commission import \
    calculate_payment_without_commission
from apps.transactions.models import Invoice

from . import payment_proccessor as pay_proc
from .utils import parse_model_instance


class YookassaIncomePayment:
    def __init__(self, yookassa_response: YookassaPaymentResponse):
        self.yookassa_response = yookassa_response
        self.payment_body = yookassa_response.object_
        self.income_value = self.payment_body.income_amount.value
        self.yookassa_payment_status = yookassa_response.event
        self.account_id = int(self.payment_body.metadata['account_id'])


class PaymentAcceptance(YookassaIncomePayment):
    def __init__(self, yookassa_response: YookassaPaymentResponse):
        super().__init__(yookassa_response)

        self.balance_handler: BalanceChangeHandler | None = None
        self.income_invoice_handler: IncomeInvoiceHandler | None = None

        self.payment_status = False
        self._run_payment_acceptance()

    def _run_payment_acceptance(self):
        rollbar.report_message(
            (
                f'Received payment data for: '
                f'account_id: f{self.account_id}'
                f'with payment amount: {self.income_value}'
            ),
            'info',
        )
        self.balance_handler = BalanceChangeHandler(
            self.yookassa_response,
        )
        self.balance_handler.change_user_balance()
        if 'invoice_id' not in self.payment_body.metadata:
            self.payment_status = self.balance_handler.payment_status
            return
        self.payment_status = True

        self.income_invoice_handler = IncomeInvoiceHandler(
            self.yookassa_response,
        )
        if self.income_invoice_handler.is_invoice_valid():
            execute_invoice_operations(
                invoice_instance=self.income_invoice_handler.invoice_object,
                account_id=self.account_id,
            )


class BalanceChangeHandler(YookassaIncomePayment):
    def __init__(self, yookassa_response: YookassaPaymentResponse):
        super().__init__(yookassa_response)
        self.balance_change_object = self._parse_balance_object()

    def _parse_balance_object(self) -> BalanceChange | None:
        return parse_model_instance(
            django_model=BalanceChange,
            error_message=(
                f"Can't get payment instance for payment id {self.payment_body.id_}"
            ),
            pk=int(self.payment_body.metadata['balance_change_id']),
        )

    def change_user_balance(self):
        if not self.balance_change_object:
            return

        if self.yookassa_payment_status == PaymentResponseStatuses.succeeded:
            increase_user_balance(
                balance_change_object=self.balance_change_object,
                amount=Decimal(self.income_value),
            )
        elif self.yookassa_payment_status == PaymentResponseStatuses.canceled.value:
            self.balance_change_object.delete()

    @property
    def payment_status(self) -> bool:
        return self.balance_change_object is not None


class IncomeInvoiceHandler(YookassaIncomePayment):
    def __init__(self, yookassa_response: YookassaPaymentResponse):
        super().__init__(yookassa_response)
        self.invoice_object = self._parse_invoice_object()

    def is_invoice_valid(self):
        if not self._is_invoice_price_correct():
            return False

    def _parse_invoice_object(self) -> Invoice:
        return parse_model_instance(
            django_model=Invoice,
            error_message=f"Can't get invoice instance for payment id {self.payment_body.id}",
            pk=int(self.payment_body.metadata['invoice_id']),
        )

    def _is_invoice_price_correct(self):
        price_without_commission = calculate_payment_without_commission(
            self.payment_body.payment_method.type_,
            self.invoice_object.total_price,
        )
        if price_without_commission != self.income_value:
            rollbar.report_message(
                (
                    f'Received payment amount: {self.income_value}'
                    f'But purchased price equal to: {price_without_commission}'
                    f'For invoice {self.invoice_object.invoice_id}'
                ),
                'error',
            )
            return False
        return True


def increase_user_balance(
        *,
        balance_change_object: BalanceChange,
        amount: Decimal,
) -> None:
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


def decrease_user_balance(*, account_pk: int, amount: Decimal):
    with transaction.atomic():
        balance_change_object = BalanceChange.objects.create(
            account_id=account_pk,
            amount=amount,
            is_accepted=True,
            operation_type='WITHDRAW',
        )

        Account.withdraw(
            pk=account_pk,
            amount=Decimal(amount),
        )
    rollbar.report_message((
        f'Withdraw {balance_change_object.amount} {settings.DEFAULT_CURRENCY} from '
        f'user account {balance_change_object.account_id}'
    ),
        'info',
    )


def execute_invoice_operations(*, invoice_instance: Invoice, account_id: int):
    invoice_executioner = pay_proc.InvoiceExecution(invoice_instance)
    invoice_executioner.process_invoice_transactions()
    if invoice_executioner.invoice_success_status is True:
        # TO BE DONE: it has to put money on our account
        # and developer account
        decrease_user_balance(
            account_pk=account_id,
            amount=invoice_instance.total_price,
        )
