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

    def _invalidate_category_cache(self):
        """Invalidate all category-related cache keys"""
        # Delete all keys matching the pattern using django-redis
        try:
            # django-redis supports delete_pattern method (available in django-redis 5.0+)
            if hasattr(cache, 'delete_pattern'):
                cache.delete_pattern("categories_list_*")
                cache.delete_pattern("category_*")
            else:
                # Fallback: use redis client directly with pattern matching
                redis_client = cache.get_master_client()
                # Get cache backend to access key_prefix
                backend = cache._cache if hasattr(cache, '_cache') else None
                if backend:
                    key_prefix = getattr(backend, 'key_prefix', '')
                    version = getattr(backend, 'version', 1)
                    # Construct full pattern: prefix:version:pattern
                    if key_prefix:
                        pattern = f"{key_prefix}:{version}:categories_list_*"
                    else:
                        pattern = f"{version}:categories_list_*" if version else "categories_list_*"
                    keys = redis_client.keys(pattern)
                    if keys:
                        redis_client.delete(*keys)
                    
                    if key_prefix:
                        pattern = f"{key_prefix}:{version}:category_*"
                    else:
                        pattern = f"{version}:category_*" if version else "category_*"
                    keys = redis_client.keys(pattern)
                    if keys:
                        redis_client.delete(*keys)
        except Exception:
            # Final fallback: delete known common keys (Django handles prefix automatically)
            # This ensures at least the most common cache keys are cleared
            for include_children in ['0', '1']:
                cache.delete(f"categories_list_{include_children}")

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
        self._invalidate_category_cache()
        return instance

    def perform_update(self, serializer):
        instance = serializer.save()
        self._invalidate_category_cache()
        return instance

    def retrieve(self, request, *args, **kwargs):
        """Retrieve a single category, optionally with children"""
        instance = self.get_object()
        include_children = request.query_params.get('include_children', '0')
        cache_key = f"category_{instance.id}_{include_children}"
        data = cache.get(cache_key)

        if not data:
            serializer = self.get_serializer(instance, context=self.get_serializer_context())
            data = serializer.data
            cache.set(cache_key, data, timeout=60*60)

        return Response(data)

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()
        self._invalidate_category_cache()
