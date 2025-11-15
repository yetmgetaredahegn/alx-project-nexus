# accounts/serializers.py
from rest_framework import serializers
from djoser.serializers import UserCreateSerializer as DjoserUserCreateSerializer
from djoser.serializers import UserSerializer as DjoserUserSerializer

from .models import User, Profile


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ("phone", "bio", "avatar")


class UserCreateSerializer(DjoserUserCreateSerializer):
    class Meta(DjoserUserCreateSerializer.Meta):
        model = User
        fields = ("id", "email", "username", "password")
        read_only_fields = ("id",)
        extra_kwargs = {"password": {"write_only": True}}


class UserSerializer(DjoserUserSerializer):
    profile = ProfileSerializer(read_only=True)

    class Meta(DjoserUserSerializer.Meta):
        model = User
        fields = ("id", "email", "username", "first_name", "last_name", "profile")
