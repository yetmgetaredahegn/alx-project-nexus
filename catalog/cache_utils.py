"""
Shared cache helpers for catalog viewsets.
"""
from django.core.cache import cache

PRODUCT_LIST_PATTERN = "products:list:*"
PRODUCT_DETAIL_KEY = "products:detail:{product_id}"


def invalidate_product_cache(product_id=None):
    """
    Clear cached entries for products. When delete_pattern is unavailable,
    fall back to cache.clear to avoid stale responses.
    """
    if product_id:
        cache.delete(PRODUCT_DETAIL_KEY.format(product_id=product_id))

    if hasattr(cache, "delete_pattern"):
        cache.delete_pattern(PRODUCT_LIST_PATTERN)
    else:
        cache.clear()


