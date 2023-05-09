from apps.base.fields import MoneySerializerField
from apps.base.serializer import PaymentServiceSerializer
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from rest_enumfield import EnumField
from rest_framework import serializers

from ..external_payments.schemas import PayOutMethod
from .models import Account


class PaymentCommissionSerializer(PaymentServiceSerializer):
    payment_amount = MoneySerializerField(
        validators=[MinValueValidator(0, message='Insufficient Funds')],
    )


class BalanceIncreaseSerializer(PaymentCommissionSerializer):
    user_uuid = serializers.UUIDField()
    return_url = serializers.URLField()


class AccountSerializer(serializers.ModelSerializer):
    user_uuid = serializers.UUIDField()

    class Meta:
        model = Account
        fields = ('user_uuid',)


class AccountBalanceSerializer(serializers.ModelSerializer):
    balance = MoneySerializerField()

    class Meta:
        model = Account
        fields = ('balance',)


class AmountPayoutSerializer(serializers.Serializer):
    value = MoneySerializerField(
        validators=[
            MinValueValidator(
                settings.MINIMUM_PAYOUT_AMOUNT,
                message=f'Should be more then {settings.MINIMUM_PAYOUT_AMOUNT}',
            ),
            MaxValueValidator(
                settings.MAXIMUM_YOOKASSA_PAYOUT,
                message=f'Payout service limit exceeded {settings.MAXIMUM_YOOKASSA_PAYOUT}',
            ),
        ],
    )
    currency = serializers.CharField(max_length=3)


class PayoutDestination(serializers.Serializer):
    type_ = EnumField(choices=PayOutMethod)
    account_number = serializers.IntegerField()

    def to_internal_value(self, data):
        if 'type' in data.keys():
            data['type_'] = data['type']
            del data['type']
        return super().to_internal_value(data)


class PayoutSerializer(serializers.Serializer):
    amount = AmountPayoutSerializer()
    payout_destination = PayoutDestination()
    user_uuid = serializers.UUIDField()
