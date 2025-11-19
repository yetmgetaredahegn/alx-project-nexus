from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import Category


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
