from django.contrib import admin

from .models import Enrollment, Sale, SaleDetail


class SaleDetailInline(admin.TabularInline):
    model = SaleDetail
    extra = 0
    readonly_fields = ('id', 'choreography', 'unit_price')


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'total_amount', 'payment_status', 'created_at')
    list_filter = ('payment_status', 'created_at')
    search_fields = ('id', 'client__email', 'billing_address')
    readonly_fields = ('id', 'created_at')
    inlines = [SaleDetailInline]


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'choreography', 'acquired_at')
    list_filter = ('acquired_at',)
    search_fields = ('client__email', 'choreography__title')
    readonly_fields = ('id', 'acquired_at')
