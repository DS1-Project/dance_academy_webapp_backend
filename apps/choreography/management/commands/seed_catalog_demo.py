"""
Seed catalog demo data: 5 teachers, 5 genres, 2-10 choreographies each,
and 1-20 videos per choreography.

Usage:
  python manage.py seed_catalog_demo
  python manage.py seed_catalog_demo --password 'TeacherPass123'
"""

from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.authentication.models import User
from apps.choreography.models import (
    Choreography,
    ChoreographyStat,
    DanceStyle,
    VideoClip,
)

STYLE_NAMES = [
    ("Salsa", "Ritmo caribeño clásico"),
    ("Bachata", "Sensual y melódica"),
    ("Merengue", "Energía dominicana"),
    ("Hip-Hop", "Estilo urbano contemporáneo"),
    ("Reggaetón", "Ritmo urbano latino"),
]

TEACHERS = [
    {
        "email": "maria.garcia@danceflow.test",
        "username": "maria.garcia",
        "first_name": "María",
        "last_name": "García",
        "choreography_count": 4,
        "styles": ["Bachata", "Reggaetón", "Salsa"],
    },
    {
        "email": "carlos.fuentes@danceflow.test",
        "username": "carlos.fuentes",
        "first_name": "Carlos",
        "last_name": "Fuentes",
        "choreography_count": 5,
        "styles": ["Merengue", "Salsa", "Bachata"],
    },
    {
        "email": "ana.rodriguez@danceflow.test",
        "username": "ana.rodriguez",
        "first_name": "Ana",
        "last_name": "Rodríguez",
        "choreography_count": 3,
        "styles": ["Salsa", "Bachata"],
    },
    {
        "email": "david.chen@danceflow.test",
        "username": "david.chen",
        "first_name": "David",
        "last_name": "Chen",
        "choreography_count": 6,
        "styles": ["Hip-Hop", "Reggaetón"],
    },
    {
        "email": "lucia.morales@danceflow.test",
        "username": "lucia.morales",
        "first_name": "Lucía",
        "last_name": "Morales",
        "choreography_count": 4,
        "styles": ["Merengue", "Salsa", "Bachata"],
    },
]

SAMPLE_VIDEO_URLS = [
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "https://www.youtube.com/watch?v=3JZ_D3ELwOQ",
    "https://www.youtube.com/watch?v=eY52Zsg-KVI",
    "https://www.youtube.com/watch?v=kJQP7kiw5Fk",
    "https://www.youtube.com/watch?v=OPf0YbXqDm0",
]

THUMBNAILS = [
    "https://picsum.photos/seed/dance1/640/360",
    "https://picsum.photos/seed/dance2/640/360",
    "https://picsum.photos/seed/dance3/640/360",
    "https://picsum.photos/seed/dance4/640/360",
    "https://picsum.photos/seed/dance5/640/360",
]

DIFFICULTIES = [
    Choreography.Difficulty.BEGINNER,
    Choreography.Difficulty.INTERMEDIATE,
    Choreography.Difficulty.ADVANCED,
]


class Command(BaseCommand):
    help = "Crea 5 profesores con 2-10 coreografías y 1-20 videos cada una (5 géneros)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--password",
            default="TeacherPass123",
            help="Contraseña para los profesores seed.",
        )
        parser.add_argument(
            "--reset-seed",
            action="store_true",
            help="Elimina coreografías/videos previamente sembrados de estos emails antes de recrear.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        password = options["password"]
        styles = {}
        for name, description in STYLE_NAMES:
            style, _ = DanceStyle.objects.get_or_create(
                name=name,
                defaults={"description": description},
            )
            styles[name] = style

        teachers = []
        for teacher_data in TEACHERS:
            if options["reset_seed"]:
                existing = User.objects.filter(email=teacher_data["email"]).first()
                if existing:
                    Choreography.objects.filter(main_teacher=existing).delete()

            user, created = User.objects.get_or_create(
                email=teacher_data["email"],
                defaults={
                    "username": teacher_data["username"],
                    "first_name": teacher_data["first_name"],
                    "last_name": teacher_data["last_name"],
                    "role": User.Role.TEACHER,
                    "is_approved": True,
                    "is_active": True,
                },
            )
            if created:
                user.set_password(password)
                user.save()
            else:
                user.first_name = teacher_data["first_name"]
                user.last_name = teacher_data["last_name"]
                user.role = User.Role.TEACHER
                user.is_approved = True
                user.is_active = True
                user.save(update_fields=[
                    "first_name",
                    "last_name",
                    "role",
                    "is_approved",
                    "is_active",
                ])
            teachers.append((user, teacher_data))

        created_choreos = 0
        created_videos = 0

        for index, (user, teacher_data) in enumerate(teachers):
            count = teacher_data["choreography_count"]
            style_cycle = teacher_data["styles"]

            for n in range(count):
                style_name = style_cycle[n % len(style_cycle)]
                title = f"{style_name} con {user.first_name} #{n + 1}"
                choreography, was_created = Choreography.objects.get_or_create(
                    title=title,
                    main_teacher=user,
                    defaults={
                        "description": (
                            f"Paquete de {style_name.lower()} impartido por "
                            f"{user.first_name} {user.last_name}."
                        ),
                        "difficulty_level": DIFFICULTIES[n % len(DIFFICULTIES)],
                        "thumbnail_url": THUMBNAILS[(index + n) % len(THUMBNAILS)],
                        "is_approved": True,
                        "dance_style": styles[style_name],
                    },
                )

                # Assign one guest from another teacher when possible
                guest_candidates = [t for t, _ in teachers if t.id != user.id]
                if guest_candidates:
                    guest = guest_candidates[(index + n) % len(guest_candidates)]
                    choreography.guest_teachers.set([guest])

                price = Decimal("19.99") + Decimal(n) * Decimal("5.00")
                stats, _ = ChoreographyStat.objects.get_or_create(
                    choreography=choreography,
                    defaults={
                        "actual_price": price,
                        "total_views": 10 + n * 7 + index * 3,
                        "total_sales_count": n + index,
                        "average_rating": Decimal("3.50") + Decimal(n % 3) * Decimal("0.50"),
                    },
                )
                if not was_created:
                    stats.actual_price = price
                    stats.save(update_fields=["actual_price", "last_updated"])

                # 1-20 videos: vary by teacher/choreo index, clamped
                video_count = max(1, min(20, 2 + ((index + 1) * (n + 2)) % 19))
                existing_videos = choreography.videos.count()
                for v in range(existing_videos, video_count):
                    VideoClip.objects.create(
                        choreography=choreography,
                        title=f"Clip {v + 1} — {title}",
                        video_url=SAMPLE_VIDEO_URLS[v % len(SAMPLE_VIDEO_URLS)],
                        sequence_order=v + 1,
                        duration_seconds=60 + (v * 15) % 180,
                    )
                    created_videos += 1

                if was_created:
                    created_choreos += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Seed listo: {len(teachers)} profesores, "
                f"{DanceStyle.objects.filter(name__in=[s[0] for s in STYLE_NAMES]).count()} géneros, "
                f"+{created_choreos} coreografías nuevas, +{created_videos} videos."
            )
        )
        self.stdout.write(
            f"Password profesores seed: {password}"
        )
