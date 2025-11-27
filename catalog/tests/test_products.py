import pytest
from io import BytesIO
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from catalog.models import Product

@pytest.mark.django_db
class TestProductList:
    def test_list_products(self, api_client, product_factory):
        product_factory.create_batch(5)

        url = reverse("product-list")
        res = api_client.get(url)

        assert res.status_code == 200
        assert "results" in res.data
        assert len(res.data["results"]) == 5


@pytest.mark.django_db
class TestProductCreate:
    def test_create_product_requires_auth(self, api_client, category_factory):
        category = category_factory()
        url = reverse("product-list")

        body = {
            "title": "Laptop",
            "price": 999.99,
            "stock_quantity": 10,
            "category": category.id,
        }

        res = api_client.post(url, body)
        assert res.status_code == 401  # unauthorized without credentials

    def test_seller_can_create_product(
        self, api_client, seller_user, category_factory
    ):
        category = category_factory()
        api_client.force_authenticate(seller_user)

        url = reverse("product-list")

        body = {
            "title": "Laptop",
            "price": 999.99,
            "stock_quantity": 10,
            "category": category.id,
        }

        res = api_client.post(url, body)
        assert res.status_code == 201
        assert Product.objects.count() == 1
        assert res.data["title"] == "Laptop"
        assert "images_urls" in res.data
        assert res.data["images_urls"] == []

    def test_seller_can_create_product_with_images(
        self, api_client, seller_user, category_factory
    ):
        """Test that seller can create a product with images"""
        category = category_factory()
        api_client.force_authenticate(seller_user)

        # Create test image files
        def create_image_file(name):
            img = Image.new('RGB', (100, 100), color='red')
            img_file = BytesIO()
            img.save(img_file, format='JPEG')
            img_file.seek(0)
            return SimpleUploadedFile(name, img_file.read(), content_type='image/jpeg')

        image1 = create_image_file("test1.jpg")
        image2 = create_image_file("test2.jpg")

        url = reverse("product-list")
        data = {
            "title": "Laptop with Images",
            "price": 999.99,
            "stock_quantity": 10,
            "category": category.id,
        }

        res = api_client.post(url, data, format='multipart')
        assert res.status_code == 201

        # Now update with images
        product_id = res.data["id"]
        update_url = reverse("product-detail", args=[product_id])
        data_with_images = {
            "title": "Laptop with Images",
            "price": 999.99,
            "stock_quantity": 10,
            "category": category.id,
            "images": [image1, image2]
        }

        res = api_client.put(update_url, data_with_images, format='multipart')
        assert res.status_code == 200
        assert "images_urls" in res.data
        assert len(res.data["images_urls"]) == 2

        # Verify in database
        product = Product.objects.get(id=product_id)
        assert len(product.images) == 2


@pytest.mark.django_db
class TestProductDetail:
    def test_retrieve_product(self, api_client, product_factory):
        product = product_factory()

        url = reverse("product-detail", args=[product.id])
        res = api_client.get(url)

        assert res.status_code == 200
        assert res.data["id"] == product.id

    def test_update_product(self, api_client, seller_user, product_factory):
        product = product_factory(seller=seller_user)
        api_client.force_authenticate(seller_user)

        url = reverse("product-detail", args=[product.id])
        res = api_client.patch(url, {"price": 50})

        assert res.status_code == 200
        product.refresh_from_db()
        assert product.price == 50

    def test_update_product_with_images(self, api_client, seller_user, product_factory):
        """Test that seller can update product with images"""
        product = product_factory(seller=seller_user)
        api_client.force_authenticate(seller_user)

        # Create test image file
        def create_image_file(name):
            img = Image.new('RGB', (100, 100), color='blue')
            img_file = BytesIO()
            img.save(img_file, format='JPEG')
            img_file.seek(0)
            return SimpleUploadedFile(name, img_file.read(), content_type='image/jpeg')

        image = create_image_file("update_test.jpg")
        url = reverse("product-detail", args=[product.id])
        
        data = {
            "images": [image]
        }
        res = api_client.patch(url, data, format='multipart')
        
        assert res.status_code == 200
        assert "images_urls" in res.data
        assert len(res.data["images_urls"]) == 1
        
        product.refresh_from_db()
        assert len(product.images) == 1

    def test_update_product_keeps_existing_images(self, api_client, seller_user, product_factory):
        """Test that partial update without images keeps existing images"""
        # Create product with images
        product = product_factory(seller=seller_user, images=["products/1/image1.jpg", "products/1/image2.jpg"])
        api_client.force_authenticate(seller_user)

        url = reverse("product-detail", args=[product.id])
        # Update only price, not images
        res = api_client.patch(url, {"price": 75.50})

        assert res.status_code == 200
        product.refresh_from_db()
        assert product.price == 75.50
        # Images should remain unchanged
        assert len(product.images) == 2

    def test_update_product_clears_images_with_empty_list(self, api_client, seller_user, product_factory):
        """Test that providing empty images list clears all images"""
        # Create product with images
        product = product_factory(seller=seller_user, images=["products/1/image1.jpg"])
        api_client.force_authenticate(seller_user)

        url = reverse("product-detail", args=[product.id])
        # For clearing images, we need to send an empty list explicitly
        # In multipart form data, we'll use JSON format or send images field with no files
        # Let's use JSON format for this specific case
        res = api_client.patch(url, {"images": []}, format='json')

        assert res.status_code == 200
        product.refresh_from_db()
        assert product.images == []

    def test_delete_product(self, api_client, seller_user, product_factory):
        product = product_factory(seller=seller_user)
        api_client.force_authenticate(seller_user)

        url = reverse("product-detail", args=[product.id])
        res = api_client.delete(url)

        assert res.status_code == 204
        product.refresh_from_db()
        assert product.is_active is False

    def test_product_detail_updates_after_review(
        self, api_client, product_factory, user
    ):
        product = product_factory()
        api_client.force_authenticate(user)

        review_url = reverse(
            "product-reviews-list",
            kwargs={"product_pk": product.id},
        )
        res = api_client.post(review_url, {"rating": 4, "comment": "Solid"})
        assert res.status_code == 201

        detail_url = reverse("product-detail", args=[product.id])
        detail_res = api_client.get(detail_url)

        assert detail_res.status_code == 200
        assert detail_res.data["rating_avg"] == pytest.approx(4)
        assert detail_res.data["review_count"] == 1
