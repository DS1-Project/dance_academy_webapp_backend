from pathlib import Path

from django.conf import settings
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

ALLOWED_PREFIXES = ("video/", "image/")
MAX_UPLOAD_BYTES = 100 * 1024 * 1024  # 100 MB


class MediaUploadView(APIView):
    """Accept a local file upload and return a publicly reachable MEDIA URL."""

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        upload = request.FILES.get("file")
        if upload is None:
            return Response(
                {"detail": "Debes enviar un archivo en el campo 'file'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        content_type = (upload.content_type or "").lower()
        if not any(content_type.startswith(prefix) for prefix in ALLOWED_PREFIXES):
            return Response(
                {"detail": "Solo se permiten archivos de video o imagen."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if upload.size and upload.size > MAX_UPLOAD_BYTES:
            return Response(
                {"detail": "El archivo supera el límite de 100 MB."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        media_root = Path(settings.MEDIA_ROOT)
        media_root.mkdir(parents=True, exist_ok=True)

        # Keep basename safe and unique-ish
        from django.utils.text import get_valid_filename
        from uuid import uuid4

        safe_name = get_valid_filename(upload.name) or "upload.bin"
        stored_name = f"{uuid4().hex}_{safe_name}"
        destination = media_root / stored_name

        with destination.open("wb+") as out:
            for chunk in upload.chunks():
                out.write(chunk)

        relative_url = f"{settings.MEDIA_URL.rstrip('/')}/{stored_name}"
        absolute_url = request.build_absolute_uri(relative_url)

        return Response({"url": absolute_url}, status=status.HTTP_201_CREATED)
