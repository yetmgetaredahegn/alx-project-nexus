# catalog/views.py
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Category
from .serializers import CategorySerializer
from django.core.cache import cache

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]

    def list(self, request, *args, **kwargs):
        cache_key = "categories_list"
        data = cache.get(cache_key)
        if not data:
            queryset = self.filter_queryset(self.get_queryset())
            serializer = self.get_serializer(queryset, many=True)
            data = serializer.data
            cache.set(cache_key, data, timeout=60*60)  # cache for 1 hour
        return Response(data)

    def perform_create(self, serializer):
        instance = serializer.save()
        cache.delete("categories_list")
        return instance

    def perform_update(self, serializer):
        instance = serializer.save()
        cache.delete("categories_list")
        return instance

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()
        cache.delete("categories_list")
