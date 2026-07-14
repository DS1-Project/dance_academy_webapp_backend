from rest_framework import generics
from .models import Choreography
from .serializers import ChoreographySerializer

class ChoreographyDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Choreography.objects.all()
    serializer_class = ChoreographySerializer