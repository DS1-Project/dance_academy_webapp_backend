from django.urls import path
from .views import ChoreographyDetailView

urlpatterns = [
    path(
        "coreografias/<uuid:pk>/",
        ChoreographyDetailView.as_view(),
        name="coreografia-detail",
    ),
]