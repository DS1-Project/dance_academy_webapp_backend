from decimal import Decimal

from django.db import transaction
from rest_framework import serializers

from apps.choreography.models import Choreography, ChoreographyStat

from .models import Enrollment, Sale, SaleDetail


class SaleDetailSerializer(serializers.ModelSerializer):
    choreography_title = serializers.CharField(
        source='choreography.title',
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = SaleDetail
        fields = [
            'id',
            'choreography',
            'choreography_title',
            'unit_price',
        ]
        read_only_fields = fields


class SaleSerializer(serializers.ModelSerializer):
    details = SaleDetailSerializer(many=True, read_only=True)
    client_email = serializers.EmailField(source='client.email', read_only=True)

    class Meta:
        model = Sale
        fields = [
            'id',
            'client',
            'client_email',
            'total_amount',
            'payment_status',
            'billing_address',
            'created_at',
            'details',
        ]
        read_only_fields = fields


class SaleCreateSerializer(serializers.Serializer):
    choreography_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        allow_empty=False,
    )
    billing_address = serializers.CharField(max_length=1000)

    def validate_choreography_ids(self, value):
        unique_ids = list(dict.fromkeys(value))
        if len(unique_ids) != len(value):
            raise serializers.ValidationError(
                'No se permiten coreografías duplicadas en la misma venta.'
            )

        choreographies = (
            Choreography.objects.filter(id__in=unique_ids, is_approved=True)
            .select_related('stats')
        )
        found_ids = {c.id for c in choreographies}
        missing = [str(cid) for cid in unique_ids if cid not in found_ids]
        if missing:
            raise serializers.ValidationError(
                f'Coreografías no encontradas o no aprobadas: {", ".join(missing)}'
            )

        client = self.context['request'].user
        already_owned = set(
            Enrollment.objects.filter(
                client=client,
                choreography_id__in=unique_ids,
            ).values_list('choreography_id', flat=True)
        )
        if already_owned:
            owned = ', '.join(str(cid) for cid in already_owned)
            raise serializers.ValidationError(
                f'Ya tienes acceso a estas coreografías: {owned}'
            )

        pending_same = set(
            SaleDetail.objects.filter(
                sale__client=client,
                sale__payment_status=Sale.PaymentStatus.PENDING,
                choreography_id__in=unique_ids,
            ).values_list('choreography_id', flat=True)
        )
        if pending_same:
            pending = ', '.join(str(cid) for cid in pending_same)
            raise serializers.ValidationError(
                f'Ya tienes una venta pendiente con estas coreografías: {pending}'
            )

        self.context['choreographies'] = list(choreographies)
        return unique_ids

    def create(self, validated_data):
        client = self.context['request'].user
        choreographies = self.context['choreographies']
        billing_address = validated_data['billing_address']

        with transaction.atomic():
            total = Decimal('0.00')
            priced_items = []
            for choreography in choreographies:
                try:
                    price = choreography.stats.actual_price
                except ChoreographyStat.DoesNotExist:
                    raise serializers.ValidationError(
                        {
                            'choreography_ids': (
                                f'La coreografía {choreography.id} no tiene precio configurado.'
                            )
                        }
                    )
                priced_items.append((choreography, price))
                total += price

            sale = Sale.objects.create(
                client=client,
                total_amount=total,
                payment_status=Sale.PaymentStatus.PENDING,
                billing_address=billing_address,
            )
            SaleDetail.objects.bulk_create(
                [
                    SaleDetail(
                        sale=sale,
                        choreography=choreography,
                        unit_price=price,
                    )
                    for choreography, price in priced_items
                ]
            )

        return sale

    def to_representation(self, instance):
        return SaleSerializer(instance, context=self.context).data


class CheckoutSerializer(serializers.Serializer):
    success = serializers.BooleanField(default=True)

    def validate(self, attrs):
        sale = self.context['sale']
        if sale.payment_status != Sale.PaymentStatus.PENDING:
            raise serializers.ValidationError(
                'Solo se puede hacer checkout de una venta en estado pending.'
            )
        return attrs

    def save(self, **kwargs):
        sale = self.context['sale']
        success = self.validated_data.get('success', True)

        with transaction.atomic():
            if not success:
                sale.payment_status = Sale.PaymentStatus.FAILED
                sale.save(update_fields=['payment_status'])
                return sale

            sale.payment_status = Sale.PaymentStatus.COMPLETED
            sale.save(update_fields=['payment_status'])

            details = sale.details.select_related('choreography').all()
            for detail in details:
                if detail.choreography_id is None:
                    continue
                Enrollment.objects.get_or_create(
                    client=sale.client,
                    choreography_id=detail.choreography_id,
                )
                stats, _ = ChoreographyStat.objects.get_or_create(
                    choreography_id=detail.choreography_id,
                    defaults={'actual_price': detail.unit_price},
                )
                stats.total_sales_count += 1
                stats.save(update_fields=['total_sales_count', 'last_updated'])

        return sale

    def to_representation(self, instance):
        return SaleSerializer(instance, context=self.context).data


class EnrollmentSerializer(serializers.ModelSerializer):
    choreography_title = serializers.CharField(
        source='choreography.title',
        read_only=True,
    )

    class Meta:
        model = Enrollment
        fields = [
            'id',
            'choreography',
            'choreography_title',
            'acquired_at',
        ]
        read_only_fields = fields
