# accounts/serializers.py
from rest_framework import serializers
from djoser.serializers import UserCreateSerializer as DjoserUserCreateSerializer
from djoser.serializers import UserSerializer as DjoserUserSerializer
from djoser.serializers import UserCreatePasswordRetypeSerializer as DjoserUserCreatePasswordRetypeSerializer

from .models import User, Profile


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ("phone", "bio", "avatar")


class UserCreateSerializer(DjoserUserCreateSerializer):
    is_seller = serializers.BooleanField(default=False, required=False, write_only=False)

    class Meta(DjoserUserCreateSerializer.Meta):
        model = User
        fields = ("id", "email", "username", "password", "is_seller")
        read_only_fields = ("id",)
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        is_seller = validated_data.pop("is_seller", False)
        user = super().create(validated_data)
        user.is_seller = is_seller
        user.save(update_fields=["is_seller"])
        return user


class UserCreatePasswordRetypeSerializer(DjoserUserCreatePasswordRetypeSerializer):
    """Custom password retype serializer that includes is_seller field"""
    is_seller = serializers.BooleanField(default=False, required=False)

    class Meta(DjoserUserCreatePasswordRetypeSerializer.Meta):
        model = User
        fields = ("id", "email", "username", "password", "is_seller")
        read_only_fields = ("id",)
        extra_kwargs = {"password": {"write_only": True}}


class UserSerializer(DjoserUserSerializer):
    profile = ProfileSerializer(read_only=True)

    class Meta(DjoserUserSerializer.Meta):
        model = User
        fields = ("id", "email", "username", "first_name", "last_name", "is_seller", "profile")
