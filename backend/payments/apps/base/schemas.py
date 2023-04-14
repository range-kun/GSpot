import enum
from dataclasses import dataclass
from typing import NewType

URL = NewType('URLField', str)


class PaymentServices(enum.Enum):
    yookassa = 'yookassa'
    from_balance = 'from_balance'


class PaymentTypes(enum.Enum):
    bank_card = 'bank_card'
    yoo_money = 'yoo_money'
    sberbank = 'sberbank'
    qiwi = 'qiwi'


@dataclass(kw_only=True)
class PaymentServiceInfo:
    payment_service: PaymentServices
    payment_type: PaymentTypes | None = None
