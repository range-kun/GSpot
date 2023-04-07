import enum
from dataclasses import dataclass, field
from decimal import Decimal
from uuid import UUID

from dataclasses_json import config, dataclass_json
from django.conf import settings


class PaymentResponseStatuses(enum.Enum):
    succeeded = 'payment.succeeded'
    canceled = 'payment.canceled'
    waiting_for_capture = 'payment.waiting_for_capture'
    refund_succeeded = 'refund.succeeded'


class YookassaPaymentTypes(enum.Enum):
    bank_card = 'bank_card'
    yoo_money = 'yoo_money'
    sberbank = 'sberbank'
    qiwi = 'qiwi'


@dataclass
class AmountDataClass:
    value: Decimal
    currency: str = settings.DEFAULT_CURRENCY


# RESPONSE PAYMENT SCHEMAS
@dataclass
class PaymentMethodDataResponse:
    type_: YookassaPaymentTypes


@dataclass_json
@dataclass
class YookassaPaymentResponseObject:
    id_: UUID = field(metadata=config(field_name='id'))
    income_amount: AmountDataClass
    description: str
    metadata: dict
    payment_method: PaymentMethodDataResponse


@dataclass_json
@dataclass
class YookassaPaymentResponse:
    event: PaymentResponseStatuses
    object_: YookassaPaymentResponseObject = field(
        metadata=config(field_name='object'),
    )


# CREATE PAYMENT SCHEMAS
@dataclass_json
@dataclass
class ConfirmationDataClass:
    confirmation_type: str = field(metadata=config(field_name='type'))
    return_url: str


@dataclass_json
@dataclass
class PaymentMethodDataCreate:
    payment_type: YookassaPaymentTypes = field(
        metadata=config(field_name='type'),
    )


@dataclass_json
@dataclass
class YookassaPaymentCreate:
    amount: AmountDataClass
    payment_method_data: PaymentMethodDataCreate
    confirmation: ConfirmationDataClass
    metadata: dict
    capture: bool = True
    refundable: bool = False
    description: str | None = None


class PaymentTypes(enum.Enum):
    from_balance = 'from_balance'
    yookassa_payments: YookassaPaymentTypes


@dataclass
class YookassaPaymentInfo:
    payment_type: YookassaPaymentTypes
    payment_amount: Decimal


@dataclass
class PaymentCreateDataClass(YookassaPaymentInfo):
    user_uuid: UUID
    return_url: str
