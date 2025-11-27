# catalog/views.py
import hashlib
from datetime import datetime, timezone as dt_timezone

from django.core.cache import cache
from django.db import models
from django.db.models import Avg, Count, Max, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.http import http_date, parse_http_date
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response

from catalog.cache_utils import invalidate_product_cache
from catalog.schemas import product_image_upload_schema

from .filters import ProductFilter
from .models import Category, Product, ProductImage, Review
from .permissions import IsReviewOwnerOrAdmin, IsSellerOrAdmin
from .serializers import (
    CategorySerializer,
    ProductImageSerializer,
    ProductSerializer,
    ReviewSerializer,
)


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


class ProductViewSet(viewsets.ModelViewSet):
    """
    Provides list/create/detail/update/delete endpoints for products with
    caching, filtering, and conditional requests.
    """

    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ["title", "description", "slug"]
    ordering_fields = ["price", "title", "created_at", "updated_at"]
    cache_timeout = 300  # seconds

    def get_queryset(self):
        return (
            Product.objects.filter(is_active=True)
            .select_related("category", "seller")
            .prefetch_related("images")
            .annotate(
                rating_avg=Coalesce(
                    Avg("reviews__rating"),
                    Value(0.0),
                ),
                review_count=Coalesce(
                    Count("reviews"),
                    Value(0, output_field=models.IntegerField()),
                ),
            )
        )

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsSellerOrAdmin()]
        return [permissions.AllowAny()]

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        sort_value = self.request.query_params.get("sort")
        if sort_value:
            allowed_fields = {"price", "title", "created_at", "updated_at"}
            normalized = sort_value.lstrip("-")
            if normalized in allowed_fields:
                queryset = queryset.order_by(sort_value)
        return queryset

    def _build_list_cache_key(self, request):
        return f"products:list:{request.get_full_path()}"

    def _build_detail_cache_key(self, pk):
        return f"products:detail:{pk}"

    def _build_etag(self, cache_key, last_modified):
        sig = f"{cache_key}:{last_modified.isoformat() if last_modified else '0'}"
        return hashlib.md5(sig.encode("utf-8")).hexdigest()

    def _serialize_last_modified(self, value):
        return value.isoformat() if value else None

    def _parse_last_modified(self, value):
        if not value:
            return None
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None

    def _should_return_not_modified(self, request, etag, last_modified):
        if_none_match = request.headers.get("If-None-Match")
        if if_none_match and etag and if_none_match.strip() == etag:
            return True

        if_modified_since = request.headers.get("If-Modified-Since")
        if if_modified_since and last_modified:
            try:
                since_ts = parse_http_date(if_modified_since)
                if since_ts is not None:
                    since_dt = datetime.fromtimestamp(since_ts, tz=dt_timezone.utc)
                    if last_modified <= since_dt:
                        return True
            except (ValueError, OverflowError, OSError):
                pass
        return False

    def _attach_cache_headers(self, response, etag, last_modified):
        if etag:
            response["ETag"] = etag
        if last_modified:
            response["Last-Modified"] = http_date(last_modified.timestamp())

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="page",
                type=OpenApiTypes.INT,
                required=False,
                location=OpenApiParameter.QUERY,
                description="Page number for pagination",
            ),
            OpenApiParameter(
                name="category",
                type=OpenApiTypes.INT,
                required=False,
                location=OpenApiParameter.QUERY,
                description="Filter by category ID",
            ),
            OpenApiParameter(
                name="min_price",
                type=OpenApiTypes.NUMBER,
                required=False,
                location=OpenApiParameter.QUERY,
                description="Filter by minimum price",
            ),
            OpenApiParameter(
                name="max_price",
                type=OpenApiTypes.NUMBER,
                required=False,
                location=OpenApiParameter.QUERY,
                description="Filter by maximum price",
            ),
            OpenApiParameter(
                name="q",
                type=OpenApiTypes.STR,
                required=False,
                location=OpenApiParameter.QUERY,
                description="Full-text search in title & description",
            ),
            OpenApiParameter(
                name="seller",
                type=OpenApiTypes.INT,
                required=False,
                location=OpenApiParameter.QUERY,
                description="Filter by seller ID",
            ),
            OpenApiParameter(
                name="sort",
                type=OpenApiTypes.STR,
                required=False,
                location=OpenApiParameter.QUERY,
                description="Sort by price, title, created_at, updated_at (prefix with - for descending)",
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        cache_key = self._build_list_cache_key(request)
        cached_entry = cache.get(cache_key)

        if cached_entry:
            data = cached_entry.get("payload")
            last_modified = self._parse_last_modified(cached_entry.get("last_modified"))
        else:
            queryset = self.filter_queryset(self.get_queryset())
            last_modified = queryset.aggregate(last=Max("updated_at"))["last"]
            page = self.paginate_queryset(queryset)
            serializer = self.get_serializer(
                page if page is not None else queryset, many=True
            )
            if page is not None:
                paginated = self.get_paginated_response(serializer.data)
                data = paginated.data
            else:
                data = serializer.data
            cache.set(
                cache_key,
                {
                    "payload": data,
                    "last_modified": self._serialize_last_modified(last_modified),
                },
                timeout=self.cache_timeout,
            )

        etag = self._build_etag(cache_key, last_modified)
        if self._should_return_not_modified(request, etag, last_modified):
            response = Response(status=status.HTTP_304_NOT_MODIFIED)
        else:
            response = Response(data)
        self._attach_cache_headers(response, etag, last_modified)
        return response

    def retrieve(self, request, *args, **kwargs):
        product = self.get_object()
        cache_key = self._build_detail_cache_key(product.pk)
        cached_entry = cache.get(cache_key)

        if cached_entry:
            data = cached_entry.get("payload")
            last_modified = self._parse_last_modified(cached_entry.get("last_modified"))
        else:
            serializer = self.get_serializer(product)
            data = serializer.data
            last_modified = product.updated_at
            cache.set(
                cache_key,
                {
                    "payload": data,
                    "last_modified": self._serialize_last_modified(last_modified),
                },
                timeout=self.cache_timeout,
            )

        etag = self._build_etag(cache_key, last_modified or product.updated_at)
        if self._should_return_not_modified(
            request, etag, last_modified or product.updated_at
        ):
            response = Response(status=status.HTTP_304_NOT_MODIFIED)
        else:
            response = Response(data)
        self._attach_cache_headers(response, etag, last_modified or product.updated_at)
        return response

    def perform_create(self, serializer):
        instance = serializer.save(seller=self.request.user)
        invalidate_product_cache(instance.pk)
        return instance

    def perform_update(self, serializer):
        instance = serializer.save()
        invalidate_product_cache(instance.pk)
        return instance

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=["is_active", "updated_at"])
        invalidate_product_cache(instance.pk)

    @extend_schema(
        description="Upload an image for the specified product (seller-only).",
        methods=["post"],
        request=product_image_upload_schema,
        responses={201: ProductImageSerializer},
    )
    @action(
        detail=True,
        methods=["post"],
        url_path="upload-image",
        permission_classes=[IsSellerOrAdmin],
    )
    def upload_image(self, request, pk=None):
        """Upload a product image (seller-only)."""
        product = self.get_object()

        # Ensure sellers upload only to their own products
        if not request.user.is_staff and product.seller_id != request.user.id:
            return Response(
                {"detail": "You can only upload images for your own products."},
                status=403
            )

        serializer = ProductImageSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(product=product)

            # Invalidate product cache
            invalidate_product_cache(product.pk)

            return Response(serializer.data, status=201)

        return Response(serializer.errors, status=400)

@extend_schema(
    description="Manage reviews for a product.",
    methods=["get", "post", "put", "delete"],
    responses={200: ReviewSerializer(many=True), 201: ReviewSerializer, 400: "Error"},
)
class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsReviewOwnerOrAdmin]

    def get_queryset(self):
        product_id = self.kwargs["product_pk"]
        return Review.objects.filter(product_id=product_id).order_by("-created_at")

    def perform_create(self, serializer):
        product_id = self.kwargs["product_pk"]
        product = get_object_or_404(Product, pk=product_id)

        # Ensure user can only review once
        if Review.objects.filter(product=product, user=self.request.user).exists():
            raise ValidationError("You have already reviewed this product.")

        review = serializer.save(
            user=self.request.user,
            product=product,
        )

        # Update product statistics
        self._handle_product_side_effects(product)

        return review

    def perform_update(self, serializer):
        review = serializer.save()
        self._handle_product_side_effects(review.product)

    def perform_destroy(self, instance):
        product = instance.product
        instance.delete()
        self._handle_product_side_effects(product)

    def _handle_product_side_effects(self, product):
        """
        Ensure product caches stay in sync whenever related reviews change.
        """
        Product.objects.filter(pk=product.pk).update(updated_at=timezone.now())
        invalidate_product_cache(product.pk)
