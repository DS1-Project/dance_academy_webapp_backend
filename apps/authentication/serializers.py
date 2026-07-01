from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .captcha import validate_captcha_token
from .models import User
from .permissions import INTERNAL_ROLES, INTERNAL_ROLE_CHOICES

USER_READ_ONLY_FIELDS = ('id', 'created_at', 'date_joined')
USER_PUBLIC_FIELDS = (
    'id',
    'email',
    'username',
    'first_name',
    'last_name',
    'role',
    'is_active',
    'is_approved',
    'created_at',
    'date_joined',
)
USER_INTERNAL_WRITE_FIELDS = (
    'email',
    'username',
    'first_name',
    'last_name',
    'role',
    'is_approved',
    'is_active',
)


class UserSerializer(serializers.ModelSerializer):
    role = serializers.ChoiceField(choices=User.Role.choices, read_only=True)

    class Meta:
        model = User
        fields = USER_PUBLIC_FIELDS
        read_only_fields = USER_READ_ONLY_FIELDS


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    role = serializers.ChoiceField(choices=INTERNAL_ROLE_CHOICES)

    class Meta:
        model = User
        fields = ['password', *USER_INTERNAL_WRITE_FIELDS]

    def validate_role(self, value):
        role = User.Role(value)
        if role not in INTERNAL_ROLES:
            raise serializers.ValidationError(
                'Solo se pueden crear usuarios internos (admin, director o teacher).'
            )
        return role

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('Ya existe un usuario con este correo.')
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        username = validated_data.pop('username', None) or validated_data['email'].split('@')[0]

        return User.objects.create_user(
            username=username,
            email=validated_data['email'],
            password=password,
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            role=validated_data['role'],
            is_approved=validated_data.get('is_approved', True),
            is_active=validated_data.get('is_active', True),
        )


class UserInternalUpdateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, min_length=8)
    role = serializers.ChoiceField(choices=INTERNAL_ROLE_CHOICES)

    class Meta:
        model = User
        fields = ['password', *USER_INTERNAL_WRITE_FIELDS]

    def validate_role(self, value):
        role = User.Role(value)
        if role not in INTERNAL_ROLES:
            raise serializers.ValidationError(
                'Solo se pueden asignar roles internos (admin, director o teacher).'
            )
        return role

    def validate_email(self, value):
        user = self.instance
        if User.objects.filter(email__iexact=value).exclude(pk=user.pk).exists():
            raise serializers.ValidationError('Ya existe un usuario con este correo.')
        return value

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    captcha_token = serializers.CharField(write_only=True)

    def validate(self, attrs):
        validate_captcha_token(attrs['captcha_token'])

        user = authenticate(
            username=attrs['email'],
            password=attrs['password'],
        )
        if user is None:
            raise serializers.ValidationError('Correo o contraseña incorrectos.')

        if not user.is_active:
            raise serializers.ValidationError('Esta cuenta está desactivada.')

        if not user.is_approved:
            raise serializers.ValidationError(
                'Tu cuenta aún no ha sido aprobada por un administrador.'
            )

        refresh = RefreshToken.for_user(user)
        attrs['user'] = user
        attrs['access'] = str(refresh.access_token)
        attrs['refresh'] = str(refresh)
        return attrs

    def to_representation(self, instance):
        return {
            'access': instance['access'],
            'refresh': instance['refresh'],
            'user': UserSerializer(instance['user']).data,
        }


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['email', 'password', 'password_confirm', 'first_name', 'last_name']

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError(
                {'password_confirm': 'Las contraseñas no coinciden.'}
            )
        return attrs

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('Ya existe un usuario con este correo.')
        return value

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        email = validated_data['email']
        user = User(
            username=email.split('@')[0],
            email=email,
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            role=User.Role.CLIENT,
            is_approved=False,
            is_active=True,
        )
        user.set_password(password)
        user.save()
        return user


class ClientProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'role',
            'is_approved',
            'created_at',
        ]
        read_only_fields = ['id', 'email', 'role', 'is_approved', 'created_at']

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
