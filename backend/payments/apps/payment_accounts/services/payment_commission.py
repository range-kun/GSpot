from decimal import Decimal

from apps.external_payments.schemas import YookassaPaymentTypes, YookassaPaymentInfo

TWO_PLACES = Decimal(10) ** -2


def get_commission_percent(payment_type: YookassaPaymentTypes) -> Decimal:
    # maybe store that data in DB or somewhere else ?
    commission_amount = {
        payment_type.bank_card: Decimal(3.5),
        payment_type.yoo_money: Decimal(3.5),
        payment_type.sberbank: Decimal(3.5),
        payment_type.qiwi: Decimal(6),
    }
    return commission_amount[payment_type]


def calculate_payment_with_commission(
        payment_type: YookassaPaymentTypes,
        payment_amount: Decimal
) -> Decimal:
    commission = get_commission_percent(payment_type)
    return (payment_amount * (1 / (1 - commission / 100))).quantize(TWO_PLACES)


def calculate_payment_without_commission(
        payment_type: YookassaPaymentTypes,
        payment_amount: Decimal
) -> Decimal:
    commission = get_commission_percent(payment_type)
    return (payment_amount * ((100 - commission)/100)).quantize(TWO_PLACES)
