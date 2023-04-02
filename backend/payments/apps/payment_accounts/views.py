import rollbar
from dacite import from_dict, MissingValueError
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response

from . import schemas
from . import serializers
from .services.create_payment import deposit_to_balance
from .services.payment_acceptance import payment_acceptance
from .services.payment_commission import calculate_payment_with_commission


class CalculatePaymentCommissionView(CreateAPIView):
    serializer_class = serializers.PaymentCommissionSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.POST)
        serializer.is_valid(raise_exception=True)
        try:
            commission_data = schemas.PaymentInfo(**serializer.validated_data)
        except KeyError as error:
            rollbar.report_message(
                f'Schemas and serializers got different structure. Got next error: {str(error)}'
                'error',
            )
            return

        amount_with_commission = calculate_payment_with_commission(
            commission_data,
        )
        return Response({'amount with commission': amount_with_commission})


class CreatePaymentView(CreateAPIView):
    serializer_class = serializers.CreatePaymentSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.POST)
        serializer.is_valid(raise_exception=True)
        try:
            payment_data = schemas.PaymentCreateDataClass(
                **serializer.validated_data,
            )
        except KeyError as error:
            rollbar.report_message(
                f'Schemas and serializers got different structure. Got next error: {str(error)}',
                'error',
            )
            return

        confirmation_url = deposit_to_balance(payment_data)

        return Response({'confirmation_url': confirmation_url}, 200)


class CreatePaymentAcceptanceView(CreateAPIView):
    serializer_class = serializers.YookassaPaymentResponseSerializer

    def post(self, request, *args, **kwargs):
        # I think we should store that request.data somewhere,
        # until this function is not finished
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            rollbar.report_message(
                "Can't parse response from yookassa.",
                'error',
            )
            return

        try:
            # used from_dict function because
            # dataclasses cant parse nested models properly
            yookassa_data = from_dict(
                schemas.YookassaPaymentResponse, serializer.validated_data,
            )
        except MissingValueError as error:
            rollbar.report_message(
                f'Schemas and serializers got different structure. Got next error: {str(error)}',
                'error',
            )
            return

        if payment_acceptance(yookassa_data):
            return Response(200)
        return Response(404)
