from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import Category, Product, ProductImage, Review


class CategoryChildSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'parent']
        read_only_fields = ['id', 'slug']


class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    @extend_schema_field(
        serializers.ListSerializer(
            child=CategoryChildSerializer(),
            allow_empty=True
        )
    )
    def get_children(self, obj):
        include_children = self.context.get("include_children", False)
        # Check if it's a string "1" or "true" or actual boolean True
        if isinstance(include_children, str):
            include_children = include_children.lower() in ('1', 'true', 'yes')
        
        if not include_children:
            return []

        children_queryset = obj.children.filter(is_active=True)
        return CategoryChildSerializer(children_queryset, many=True, context=self.context).data

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'parent', 'children']
        read_only_fields = ['id', 'slug']



class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ["id", "image", "uploaded_at"]



class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    rating_avg = serializers.FloatField(read_only=True)
    review_count = serializers.IntegerField(read_only=True)
    seller = serializers.PrimaryKeyRelatedField(read_only=True)
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.filter(is_active=True)
    )
    slug = serializers.SlugField(required=False, allow_blank=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "price",
            "stock_quantity",
            "category",
            "seller",
            "images",
            "rating_avg",
            "review_count",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "seller",
            "slug",
            "rating_avg",
            "review_count",
            "is_active",
            "created_at",
            "updated_at",
        ]

    def validate_stock_quantity(self, value):
        if value < 0:
            raise serializers.ValidationError("Stock quantity cannot be negative.")
        return value

class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Review
        fields = [
            "id",
            "user",
            "rating",
            "comment",
            "created_at",
        ]
        read_only_fields = ["id", "user", "created_at"]

    def validate_rating(self, value):
        if not 1 <= value <= 10:
            raise serializers.ValidationError("Rating must be between 1 and 10.")
        return value

