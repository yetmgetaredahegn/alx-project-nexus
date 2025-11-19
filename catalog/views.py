# catalog/views.py
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Category
from .serializers import CategorySerializer
from django.core.cache import cache
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

@extend_schema(
    parameters=[
        OpenApiParameter(
            name="include_children",
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            required=False,
            description="Set to 1 to include children categories in the response. Default is 0 (no children)."
        )
    ]
)
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]

    def get_serializer_context(self):
        """Add include_children to serializer context"""
        context = super().get_serializer_context()
        include_children = self.request.query_params.get('include_children', '0')
        context['include_children'] = include_children
        return context

    def list(self, request, *args, **kwargs):
        cache_key = f"categories_list_{request.query_params.get('include_children', '0')}"
        data = cache.get(cache_key)

        if not data:
            queryset = self.filter_queryset(self.get_queryset())
            serializer = self.get_serializer(
                queryset,
                many=True,
                context=self.get_serializer_context()
            )
            data = serializer.data
            cache.set(cache_key, data, timeout=60*60)

        return Response(data)


    def perform_create(self, serializer):
        instance = serializer.save()
        cache.delete("categories_list")
        return instance

    def perform_update(self, serializer):
        instance = serializer.save()
        cache.delete("categories_list")
        return instance

    def retrieve(self, request, *args, **kwargs):
        """Retrieve a single category, optionally with children"""
        instance = self.get_object()
        serializer = self.get_serializer(instance, context=self.get_serializer_context())
        return Response(serializer.data)

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()
        cache.delete("categories_list")
