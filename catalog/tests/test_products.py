import pytest
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
