from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import Category, Product, Review


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


class ProductSerializer(serializers.ModelSerializer):
    images = serializers.ListField(
        child=serializers.ImageField(allow_empty_file=False, required=False),
        required=False,
        allow_empty=True,
        write_only=True,
        help_text="List of image files to upload. Send empty list [] to clear all images."
    )
    images_urls = serializers.SerializerMethodField(read_only=True)
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
            "images_urls",
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
            "images_urls",
            "rating_avg",
            "review_count",
            "is_active",
            "created_at",
            "updated_at",
        ]

    def get_images_urls(self, obj):
        """Return list of image URLs from the images JSONField"""
        if not obj.images:
            return []
        # If images are stored as relative paths, convert them to full URLs
        request = self.context.get('request')
        if request:
            from django.conf import settings
            from django.core.files.storage import default_storage
            urls = []
            for img_path in obj.images:
                if img_path.startswith('http'):
                    urls.append(img_path)
                else:
                    # Build URL using MEDIA_URL
                    url = default_storage.url(img_path)
                    if request:
                        # Make it absolute if we have a request
                        if not url.startswith('http'):
                            url = request.build_absolute_uri(url)
                    urls.append(url)
            return urls
        return obj.images

    def validate_images(self, value):
        """Validate images field - allow empty list in JSON format"""
        request = self.context.get('request')
        if request and 'application/json' in request.content_type:
            # In JSON format, allow empty list to clear images
            if isinstance(value, list) and len(value) == 0:
                return []
        # For multipart/form-data, validate as normal
        return value

    def validate_stock_quantity(self, value):
        if value < 0:
            raise serializers.ValidationError("Stock quantity cannot be negative.")
        return value

    def create(self, validated_data):
        images = validated_data.pop('images', [])
        product = super().create(validated_data)
        
        # Handle image uploads
        if images:
            image_paths = []
            from django.core.files.storage import default_storage
            import os
            from django.utils import timezone
            
            for idx, image in enumerate(images):
                # Generate unique filename to avoid conflicts
                timestamp = int(timezone.now().timestamp())
                file_ext = os.path.splitext(image.name)[1] or '.jpg'
                filename = f"{timestamp}_{idx}{file_ext}"
                image_path = f"products/{product.id}/{filename}"
                
                # Save the file using default storage
                saved_path = default_storage.save(image_path, image)
                image_paths.append(saved_path)
            
            product.images = image_paths
            product.save(update_fields=['images'])
        
        return product

    def update(self, instance, validated_data):
        # Check if images field was explicitly provided in the request
        # For JSON format, check initial_data; for multipart, check if field exists
        request = self.context.get('request')
        is_json = request and request.content_type and 'application/json' in request.content_type
        
        images_provided = False
        images = None
        
        if is_json and 'images' in self.initial_data:
            # JSON format: can send empty list to clear
            images_provided = True
            if isinstance(self.initial_data['images'], list) and len(self.initial_data['images']) == 0:
                images = []  # Empty list to clear
            else:
                images = validated_data.pop('images', None)
        elif 'images' in validated_data:
            # Multipart format: files were uploaded
            images_provided = True
            images = validated_data.pop('images', None)
        elif 'images' in self.initial_data:
            # Field was provided but might be empty in multipart
            images_provided = True
            images = []
        
        product = super().update(instance, validated_data)
        
        # Handle image uploads
        # Only update images if explicitly provided in the request
        if images_provided:
            if images and len(images) > 0:
                # Save new images
                image_paths = []
                from django.core.files.storage import default_storage
                import os
                from django.utils import timezone
                
                for idx, image in enumerate(images):
                    if image:  # Skip None values
                        # Generate unique filename to avoid conflicts
                        timestamp = int(timezone.now().timestamp())
                        file_ext = os.path.splitext(image.name)[1] if hasattr(image, 'name') and image.name else '.jpg'
                        filename = f"{timestamp}_{idx}{file_ext}"
                        image_path = f"products/{product.id}/{filename}"
                        
                        # Save the file using default storage
                        saved_path = default_storage.save(image_path, image)
                        image_paths.append(saved_path)
                product.images = image_paths
            else:
                # Empty list means clear all images
                product.images = []
            product.save(update_fields=['images'])
        
        return product

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

