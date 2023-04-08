from django.conf import settings
from django.core.validators import MinValueValidator
from rest_enumfield import EnumField
from rest_framework import serializers

from apps.external_payments.schemas import PaymentTypes


class ItemPaymentData(serializers.Serializer):
    owner_uuid = serializers.UUIDField()
    item_uuid = serializers.UUIDField()
    developer_uuid = serializers.UUIDField()
    price = serializers.DecimalField(
        decimal_places=2,
        max_digits=settings.MAX_BALANCE_DIGITS,
        validators=[MinValueValidator(0, message='Insufficient Funds')],
    )


class PurchaseItemsSerializer(serializers.Serializer):
    user_uuid = serializers.UUIDField()
    payment_type = EnumField(choices=PaymentTypes)
    items_payment_data = ItemPaymentData(many=True)
    return_url = serializers.URLField()
