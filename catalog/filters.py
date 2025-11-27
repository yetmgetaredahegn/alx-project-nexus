import django_filters
from django.db.models import Q

from .models import Product


class ProductFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(field_name="price", lookup_expr="gte")
    max_price = django_filters.NumberFilter(field_name="price", lookup_expr="lte")
    q = django_filters.CharFilter(method="filter_search")
    seller = django_filters.NumberFilter(field_name="seller_id")

    class Meta:
        model = Product
        fields = ["category", "min_price", "max_price", "q", "seller"]

    def filter_search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            Q(title__icontains=value)
            | Q(description__icontains=value)
            | Q(search_vector__icontains=value)
        )
