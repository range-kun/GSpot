import datetime
from typing import TypeVar

from apps.base.utils import get_payout_amount_for_last_month
from apps.payment_accounts.exceptions import (
    InsufficientFundsError,
    NotPayoutDayError,
    PayOutLimitExceededError,
)
from apps.payment_accounts.models import Account
from django.conf import settings
from django.shortcuts import get_object_or_404
from pydantic import BaseModel

PydanticModel = TypeVar('PydanticModel', bound=BaseModel)


class PrePayoutProcessor:
    def __init__(self, payout_data: dict):
        self.payout_data = payout_data
        self.payout_model_data: PydanticModel | None = None

    def validate_payout(self, payout_model: type[PydanticModel]) -> PydanticModel | None:
        if not self._is_it_payout_date():
            raise NotPayoutDayError(f'The payout day is {settings.PAYOUT_DAY_OF_MONTH}')

        developer_account: Account = get_object_or_404(
            Account,
            user_uuid=self.payout_data.pop('user_uuid'),
        )
        self.set_payout_model_data(payout_model)
        if not self._is_enough_funds(developer_account):
            raise InsufficientFundsError('Developer has not required balance to withdraw')
        if self._is_payout_limit_exceeded(developer_account):
            raise PayOutLimitExceededError(
                (
                    f'You exceeded your payout limit '
                    f'[{settings.MAXIMUM_PAYOUTS_PER_MONTH}] for this month'
                ),
            )

    def set_payout_model_data(self, payout_model: type[PydanticModel]):
        self.payout_model_data = payout_model(**self.payout_data)

    @staticmethod
    def _is_it_payout_date():
        return datetime.datetime.today().day == settings.PAYOUT_DAY_OF_MONTH

    def _is_enough_funds(
        self,
        developer_account: Account,
    ):
        return developer_account.balance > self.payout_model_data.amount.value

    def _is_payout_limit_exceeded(self, developer_account: Account):
        return (
            get_payout_amount_for_last_month(developer_account)
            >= settings.MAXIMUM_PAYOUTS_PER_MONTH
        )
