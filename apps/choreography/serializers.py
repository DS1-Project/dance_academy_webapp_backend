from rest_framework import serializers
from .models import Choreography

class ChoreographySerializer(serializers.ModelSerializer):
    class Meta:
        model = Choreography
        fields = "__all__"