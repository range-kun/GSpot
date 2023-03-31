import json

from rest_framework.generics import CreateAPIView
from rest_framework.response import Response

from .schemas import PaymentCreateDataClass, PaymentInfo
from .serializers import CreatePaymentSerializer, PaymentCommissionSerializer
from .services.create_payment import create_yookassa_payment
from .services.payment_acceptance import payment_acceptance
from .services.payment_commission import calculate_payment_with_commission


class CalculatePaymentCommissionView(CreateAPIView):
    serializer_class = PaymentCommissionSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.POST)
        serializer.is_valid(raise_exception=True)
        amount_with_commission = calculate_payment_with_commission(
            PaymentInfo(**serializer.validated_data)
        )
        return Response({'amount with commission': amount_with_commission})


class CreatePaymentView(CreateAPIView):
    serializer_class = CreatePaymentSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.POST)

        serializer.is_valid(raise_exception=True)
        payment_data = PaymentCreateDataClass(**serializer.validated_data)
        confirmation_url = create_yookassa_payment(payment_data)

        return Response({'confirmation_url': confirmation_url}, 200)


class CreatePaymentAcceptanceView(CreateAPIView):

    def post(self, request, *args, **kwargs):
        response = json.loads(request.body)

        if payment_acceptance(response):
            return Response(200)
        return Response(404)
