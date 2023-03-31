import enum
from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from django.conf import settings


class PaymentResponseStatuses(enum.Enum):
    succeeded = 'payment.succeeded'
    canceled = 'payment.canceled'
    waiting_for_capture = 'payment.waiting_for_capture'
    refund_succeeded = 'refund.succeeded'


class PaymentTypes(enum.Enum):
    bank_card = 'bank_card'
    yoo_money = 'yoo_money'
    sberbank = 'sberbank'
    qiwi = 'qiwi'


@dataclass
class PaymentInfo:
    payment_type: PaymentTypes
    payment_amount: Decimal


@dataclass
class PaymentCreateDataClass(PaymentInfo):
    user_uuid: UUID
    return_url: str


@dataclass
class AmountDataClass:
    value: Decimal
    currency: str = settings.DEFAULT_CURRENCY


@dataclass
class PaymentMethodData:
    type: PaymentTypes


@dataclass
class ConfirmationDataClass:
    type: str
    return_url: str


@dataclass
class YookassaFullPaymentDataClass:
    amount: AmountDataClass
    payment_method_data: PaymentMethodData
    confirmation: ConfirmationDataClass
    metadata: dict
    capture: bool = True
    refundable: bool = False
    description: str | None = None
