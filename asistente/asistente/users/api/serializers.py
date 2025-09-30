# asistente/users/api/serializers.py

from django.contrib.auth import get_user_model
from rest_framework import serializers
from core.models import Rol

User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    rol = serializers.PrimaryKeyRelatedField(
        queryset=Rol.objects.all()
    )

    class Meta:
        model = User
        fields = (
            "id", "username", "email", "password", "name", "rol"
        )
        read_only_fields = ("id",)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "Este correo ya está registrado."
            )
        return value

    def create(self, validated_data):
        rol = validated_data.pop('rol')
        name = validated_data.pop('name', '')
        # Usa create_user para manejar hashing de password
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email'),
            password=validated_data['password'],
            rol=rol,
        )
        # Asigna campo name si viene
        user.name = name
        user.save(update_fields=['name'])
        return user

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    rol = serializers.PrimaryKeyRelatedField(
        queryset=Rol.objects.all()
    )
    rol_nombre = serializers.CharField(
        source='rol.rol_nombre',
        read_only=True
    )

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "name",
            "rol",
            "rol_nombre",
            "password"
        )
        read_only_fields = ("id",)

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        rol = validated_data.pop('rol')
        # Usa super().create para crear instancia básica
        user = super().create(validated_data)
        user.rol = rol
        if password:
            user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        rol = validated_data.pop('rol', None)
        user = super().update(instance, validated_data)
        if rol is not None:
            user.rol = rol
        if password:
            user.set_password(password)
        user.save()
        return user
