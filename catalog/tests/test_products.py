import pytest
from django.urls import reverse
from catalog.models import Product, Category

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
            "slug": "laptop",
            "price": 999.99,
            "stock_quantity": 10,
            "category": str(category.id),
        }

        res = api_client.post(url, body)
        assert res.status_code == 403  # forbidden for unauthenticated

    def test_seller_can_create_product(
        self, api_client, seller_user, category_factory
    ):
        category = category_factory()
        api_client.force_authenticate(seller_user)

        url = reverse("product-list")

        body = {
            "title": "Laptop",
            "slug": "laptop",
            "price": 999.99,
            "stock_quantity": 10,
            "category": str(category.id),
        }

        res = api_client.post(url, body)
        assert res.status_code == 201
        assert Product.objects.count() == 1
        assert res.data["title"] == "Laptop"


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

    def test_delete_product(self, api_client, seller_user, product_factory):
        product = product_factory(seller=seller_user)
        api_client.force_authenticate(seller_user)

        url = reverse("product-detail", args=[product.id])
        res = api_client.delete(url)

        assert res.status_code == 204
        assert Product.objects.count() == 0
