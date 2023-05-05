from datetime import timedelta
from decimal import Decimal

DEFAULT_CURRENCY = 'RUB'
MAX_BALANCE_DIGITS = 11
MAX_COMMISSION_VALUE = Decimal(100)
PERIOD_FOR_MYSELF_TASK = timedelta(days=1)
PERIOD_FOR_GIFT_TASK = timedelta(days=7)
MINIMUM_PAYOUT_AMOUNT = Decimal(500)
MAXIMUM_YOOKASSA_PAYOUT = Decimal(500000)
MAXIMUM_PAYOUT_AMOUNTS = 1
PAYOUT_DAY_OF_MONTH = 5
MAXIMUM_PAYOUTS_PER_MONTH = 1