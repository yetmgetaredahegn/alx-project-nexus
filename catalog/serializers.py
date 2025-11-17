# catalog/serializers.py
from rest_framework import serializers
from .models import Category

class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "parent", "children"]

    def get_children(self, obj):
        request = self.context.get("request")
        if request and request.query_params.get("include_children") == "1":
            return CategorySerializer(obj.children.filter(is_active=True), many=True).data
        return []
