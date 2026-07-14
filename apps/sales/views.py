from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Sale, SaleDetail
from apps.authentication.models import User   # Ajusta el import según tu proyecto


class DashboardStatisticsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        total_sales = Sale.objects.count()

        total_income = (
            Sale.objects.aggregate(
                total=Sum("total_amount")
            )["total"] or 0
        )

        total_clients = User.objects.count()

        sales_by_month = (
            Sale.objects.annotate(
                month=TruncMonth("created_at")
            )
            .values("month")
            .annotate(total=Count("id"))
            .order_by("month")
        )

        top_choreographies = (
            SaleDetail.objects.values("choreography__name")
            .annotate(total=Count("id"))
            .order_by("-total")[:5]
        )

        return Response({
            "total_sales": total_sales,
            "total_income": total_income,
            "total_clients": total_clients,
            "sales_by_month": sales_by_month,
            "top_choreographies": top_choreographies,
        })