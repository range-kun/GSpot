import rollbar
from apps.external_payments.schemas import YookassaPayoutModel
from apps.external_payments.services.payment_serivces.yookassa_payment import (
    YookassaPayOut,
)
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response

from . import serializers
from .exceptions import (
    InsufficientFundsError,
    NotPayoutDayError,
    PayOutLimitExceededError,
)
from .models import Account
from .schemas import BalanceIncreaseData, CommissionCalculationInfo
from .services.balance_change import request_balance_deposit_url
from .services.payment_commission import calculate_payment_with_commission
from .services.payout import PrePayoutProcessor


class CalculatePaymentCommissionView(CreateAPIView):
    serializer_class = serializers.PaymentCommissionSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            commission_data = CommissionCalculationInfo(**serializer.validated_data)
        except KeyError as error:
            rollbar.report_message(
                f'Schemas and serializers got different structure. Got next error: {str(error)}'
                'error',
            )
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        amount_with_commission = calculate_payment_with_commission(
            commission_data.payment_type,
            commission_data.payment_amount,
        )
        return Response({'amount with commission': amount_with_commission})


class BalanceIncreaseView(CreateAPIView):
    serializer_class = serializers.BalanceIncreaseSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            balance_increase_data = BalanceIncreaseData(
                **serializer.validated_data,
            )
        except KeyError as error:
            rollbar.report_message(
                f'Schemas and serializers got different structure. Got next error: {str(error)}',
                'error',
            )
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        confirmation_url = request_balance_deposit_url(balance_increase_data)

        return Response(
            {'confirmation_url': confirmation_url},
            status=status.HTTP_201_CREATED,
        )


class UserAccountAPIView(CreateAPIView):
    serializer_class = serializers.AccountSerializer


class AccountBalanceViewSet(viewsets.ViewSet):
    def retrieve(self, request, user_uuid=None):
        account = get_object_or_404(Account, user_uuid=user_uuid)
        serializer = serializers.AccountBalanceSerializer(account)
        return Response(serializer.data)


class PayoutView(viewsets.GenericViewSet):
    serializer_class = serializers.PayoutSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        pre_payout_processor = PrePayoutProcessor(serializer.validated_data)
        try:
            pre_payout_processor.validate_payout(YookassaPayoutModel)
        except (NotPayoutDayError, InsufficientFundsError, PayOutLimitExceededError) as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        YookassaPayOut.request_payout(pre_payout_processor.payout_model_data)
