import pytest
from django.urls import reverse

from catalog.models import Review


@pytest.mark.django_db
class TestReviewListCreate:
    def test_list_reviews(self, api_client, review_factory, product_factory):
        product = product_factory()
        review_factory.create_batch(3, product=product)

        url = reverse("product-reviews-list", kwargs={"product_pk": product.id})
        res = api_client.get(url)

        assert res.status_code == 200
        assert len(res.data["results"]) == 3

    def test_create_review_requires_auth(self, api_client, product_factory):
        product = product_factory()
        url = reverse("product-reviews-list", kwargs={"product_pk": product.id})

        res = api_client.post(url, {"rating": 5, "comment": "Nice!"})

        assert res.status_code == 401

    def test_user_can_create_review(
        self, api_client, user, product_factory
    ):
        product = product_factory()
        api_client.force_authenticate(user)

        url = reverse("product-reviews-list", kwargs={"product_pk": product.id})
        body = {"rating": 5, "comment": "Excellent!"}

        res = api_client.post(url, body)

        assert res.status_code == 201
        assert Review.objects.count() == 1
        assert res.data["rating"] == 5

    def test_user_cannot_review_same_product_twice(
        self, api_client, user, product_factory
    ):
        product = product_factory()
        api_client.force_authenticate(user)
        url = reverse("product-reviews-list", kwargs={"product_pk": product.id})

        first = api_client.post(url, {"rating": 4, "comment": "Good"})
        assert first.status_code == 201

        second = api_client.post(url, {"rating": 5, "comment": "Great"})
        assert second.status_code == 400


@pytest.mark.django_db
class TestReviewDetail:
    def test_retrieve_review(self, api_client, review_factory):
        review = review_factory()

        url = reverse(
            "product-reviews-detail",
            kwargs={"product_pk": review.product.id, "pk": review.id},
        )
        res = api_client.get(url)

        assert res.status_code == 200
        assert res.data["id"] == review.id

    def test_owner_can_update_review(self, api_client, review_factory):
        review = review_factory()
        api_client.force_authenticate(review.user)

        url = reverse(
            "product-reviews-detail",
            kwargs={"product_pk": review.product.id, "pk": review.id},
        )
        res = api_client.patch(url, {"comment": "Updated"})

        assert res.status_code == 200
        review.refresh_from_db()
        assert review.comment == "Updated"

    def test_other_user_cannot_update_review(
        self, api_client, user_factory, review_factory
    ):
        review = review_factory()
        other_user = user_factory()
        api_client.force_authenticate(other_user)

        url = reverse(
            "product-reviews-detail",
            kwargs={"product_pk": review.product.id, "pk": review.id},
        )
        res = api_client.patch(url, {"comment": "Bad"})

        assert res.status_code == 403

    def test_owner_can_delete_review(self, api_client, review_factory):
        review = review_factory()
        api_client.force_authenticate(review.user)

        url = reverse(
            "product-reviews-detail",
            kwargs={"product_pk": review.product.id, "pk": review.id},
        )
        res = api_client.delete(url)

        assert res.status_code == 204
        assert Review.objects.count() == 0

    def test_admin_can_delete_any_review(
        self, api_client, admin_user, review_factory
    ):
        review = review_factory()
        api_client.force_authenticate(admin_user)

        url = reverse(
            "product-reviews-detail",
            kwargs={"product_pk": review.product.id, "pk": review.id},
        )
        res = api_client.delete(url)

        assert res.status_code == 204
