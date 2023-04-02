from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from apps.payment_accounts.schemas import YookassaPaymentTypes

"""
2) Когда нажимают оплатить, к нам на отдельную ручку (или по шине? хз) должен прийти следующие данные
 - user-id плаельщика
 - список [id игры, цена,  user-id кому принадлежит]
 - способ оплаты
"""


@dataclass
class PaymentTypes(YookassaPaymentTypes):
    from_balance = 'from_balance'


@dataclass
class ItemPaymentData:
    owner_id: UUID
    item_uuid: UUID
    price: Decimal


@dataclass
class InvoiceData:
    user_uuid: UUID
    payment_type: PaymentTypes
    items_payment_data: list[ItemPaymentData]
    return_url: str
