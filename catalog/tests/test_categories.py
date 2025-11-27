import pytest
from django.core.cache import cache
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from catalog.models import Category

User = get_user_model()


@pytest.fixture
def client():
    """APIClient fixture for making API requests"""
    return APIClient()


@pytest.fixture
def admin_user(db):
    """Create an admin user for testing"""
    return User.objects.create_superuser(
        username="admin",
        password="admin123",
        email="admin@example.com",
    )


@pytest.fixture
def regular_user(db):
    """Create a regular user for testing"""
    return User.objects.create_user(
        username="testuser",
        password="password123",
        email="testuser@example.com",
    )


@pytest.fixture
def parent_category(db):
    """Create a parent category"""
    return Category.objects.create(
        name="Electronics",
        is_active=True
    )


@pytest.fixture
def child_category(db, parent_category):
    """Create a child category"""
    return Category.objects.create(
        name="Laptops",
        parent=parent_category,
        is_active=True
    )


@pytest.fixture
def multiple_categories(db):
    """Create multiple categories for listing tests"""
    cat1 = Category.objects.create(name="Category 1", is_active=True)
    cat2 = Category.objects.create(name="Category 2", is_active=True)
    cat3 = Category.objects.create(name="Category 3", is_active=True)
    return [cat1, cat2, cat3]


@pytest.mark.django_db
class TestCategoryList:
    """Test cases for GET /api/catalog/categories/ endpoint"""

    def test_list_categories_unauthenticated(self, client, multiple_categories):
        """Test that unauthenticated users can list categories"""
        # Clear cache to ensure fresh data
        cache.clear()
        
        url = "/api/catalog/categories/"
        response = client.get(url)
        
        assert response.status_code == 200
        assert len(response.data) == 3
        assert all("id" in item for item in response.data)
        assert all("name" in item for item in response.data)
        assert all("slug" in item for item in response.data)

    def test_list_categories_without_children(self, client, parent_category, child_category):
        """Test listing categories without including children"""
        # Clear cache to ensure fresh data
        cache.clear()
        
        url = "/api/catalog/categories/"
        response = client.get(url)
        
        assert response.status_code == 200
        # Should include both parent and child categories in the list
        category_ids = [item["id"] for item in response.data]
        assert parent_category.id in category_ids
        assert child_category.id in category_ids
        
        # Find parent category in response
        parent_data = next(item for item in response.data if item["id"] == parent_category.id)
        assert parent_data["children"] == []  # Children should be empty when include_children is not set

    def test_list_categories_with_children(self, client, parent_category, child_category):
        """Test listing categories with include_children=1"""
        # Clear cache to ensure fresh data with include_children=1
        cache.clear()
        
        url = "/api/catalog/categories/?include_children=1"
        response = client.get(url)
        
        assert response.status_code == 200
        
        # Find parent category in response
        parent_data = next(item for item in response.data if item["id"] == parent_category.id)
        assert len(parent_data["children"]) == 1
        assert parent_data["children"][0]["id"] == child_category.id
        assert parent_data["children"][0]["name"] == child_category.name

    def test_list_categories_caching(self, client, multiple_categories):
        """Test that category list is cached"""
        url = "/api/catalog/categories/"
        
        # Clear cache first
        cache.clear()
        
        # First request - should hit database
        response1 = client.get(url)
        assert response1.status_code == 200
        
        # Second request - should use cache
        response2 = client.get(url)
        assert response2.status_code == 200
        assert response1.data == response2.data

    def test_list_categories_only_active(self, client, db):
        """Test that only active categories are returned"""
        # Clear cache to ensure fresh data
        cache.clear()
        
        active_cat = Category.objects.create(name="Active Category", is_active=True)
        inactive_cat = Category.objects.create(name="Inactive Category", is_active=False)
        
        url = "/api/catalog/categories/"
        response = client.get(url)
        
        assert response.status_code == 200
        # Should only return active category
        category_ids = [item["id"] for item in response.data]
        assert active_cat.id in category_ids
        assert inactive_cat.id not in category_ids
        # Find and verify the active category
        active_data = next(item for item in response.data if item["id"] == active_cat.id)
        assert active_data["name"] == "Active Category"


@pytest.mark.django_db
class TestCategoryRetrieve:
    """Test cases for GET /api/catalog/categories/{id}/ endpoint"""

    def test_retrieve_category_unauthenticated(self, client, parent_category):
        """Test that unauthenticated users can retrieve a category"""
        url = f"/api/catalog/categories/{parent_category.id}/"
        response = client.get(url)
        
        assert response.status_code == 200
        assert response.data["id"] == parent_category.id
        assert response.data["name"] == parent_category.name
        assert response.data["slug"] == parent_category.slug

    def test_retrieve_category_without_children(self, client, parent_category, child_category):
        """Test retrieving a category without children"""
        # Clear cache to ensure fresh data
        cache.clear()
        
        url = f"/api/catalog/categories/{parent_category.id}/"
        response = client.get(url)
        
        assert response.status_code == 200
        assert response.data["children"] == []

    def test_retrieve_category_with_children(self, client, parent_category, child_category):
        """Test retrieving a category with include_children=1"""
        # Clear cache to ensure fresh data with include_children=1
        cache.clear()
        
        url = f"/api/catalog/categories/{parent_category.id}/?include_children=1"
        response = client.get(url)
        
        assert response.status_code == 200
        assert len(response.data["children"]) == 1
        assert response.data["children"][0]["id"] == child_category.id
        assert response.data["children"][0]["name"] == child_category.name

    def test_retrieve_category_caching(self, client, parent_category):
        """Test that category retrieval is cached"""
        url = f"/api/catalog/categories/{parent_category.id}/"
        
        # Clear cache first
        cache.clear()
        
        # First request
        response1 = client.get(url)
        assert response1.status_code == 200
        
        # Second request - should use cache
        response2 = client.get(url)
        assert response2.status_code == 200
        assert response1.data == response2.data

    def test_retrieve_nonexistent_category(self, client):
        """Test retrieving a category that doesn't exist"""
        url = "/api/catalog/categories/99999/"
        response = client.get(url)
        
        assert response.status_code == 404

    def test_retrieve_inactive_category(self, client, db):
        """Test that inactive categories cannot be retrieved"""
        inactive_cat = Category.objects.create(name="Inactive", is_active=False)
        url = f"/api/catalog/categories/{inactive_cat.id}/"
        response = client.get(url)
        
        assert response.status_code == 404


@pytest.mark.django_db
class TestCategoryCreate:
    """Test cases for POST /api/catalog/categories/ endpoint"""

    def test_create_category_as_admin(self, client, admin_user):
        """Test that admin users can create categories"""
        client.force_authenticate(user=admin_user)
        url = "/api/catalog/categories/"
        data = {
            "name": "New Category",
            "parent": None
        }
        
        response = client.post(url, data, format="json")
        
        assert response.status_code == 201
        assert response.data["name"] == "New Category"
        assert "slug" in response.data
        assert Category.objects.filter(name="New Category").exists()

    def test_create_category_with_parent(self, client, admin_user, parent_category):
        """Test creating a category with a parent"""
        client.force_authenticate(user=admin_user)
        url = "/api/catalog/categories/"
        data = {
            "name": "Child Category",
            "parent": parent_category.id
        }
        
        response = client.post(url, data, format="json")
        
        assert response.status_code == 201
        assert response.data["name"] == "Child Category"
        assert response.data["parent"] == parent_category.id

    def test_create_category_unauthorized(self, client, regular_user):
        """Test that regular users cannot create categories"""
        client.force_authenticate(user=regular_user)
        url = "/api/catalog/categories/"
        data = {
            "name": "Unauthorized Category",
            "parent": None
        }
        
        response = client.post(url, data, format="json")
        
        assert response.status_code == 403

    def test_create_category_unauthenticated(self, client):
        """Test that unauthenticated users cannot create categories"""
        url = "/api/catalog/categories/"
        data = {
            "name": "Unauthorized Category",
            "parent": None
        }
        
        response = client.post(url, data, format="json")
        
        assert response.status_code == 401

    def test_create_category_invalidates_cache(self, client, admin_user, multiple_categories):
        """Test that creating a category invalidates the cache"""
        client.force_authenticate(user=admin_user)
        
        # Populate cache first
        list_url = "/api/catalog/categories/"
        client.get(list_url)
        
        # Create new category
        create_url = "/api/catalog/categories/"
        data = {"name": "New Category", "parent": None}
        response = client.post(create_url, data, format="json")
        
        assert response.status_code == 201
        
        # List should now include the new category (cache invalidated)
        list_response = client.get(list_url)
        assert len(list_response.data) == 4  # 3 original + 1 new


@pytest.mark.django_db
class TestCategoryUpdate:
    """Test cases for PUT/PATCH /api/catalog/categories/{id}/ endpoint"""

    def test_update_category_as_admin(self, client, admin_user, parent_category):
        """Test that admin users can update categories"""
        client.force_authenticate(user=admin_user)
        url = f"/api/catalog/categories/{parent_category.id}/"
        data = {
            "name": "Updated Category Name",
            "parent": None
        }
        
        response = client.put(url, data, format="json")
        
        assert response.status_code == 200
        assert response.data["name"] == "Updated Category Name"
        parent_category.refresh_from_db()
        assert parent_category.name == "Updated Category Name"

    def test_partial_update_category_as_admin(self, client, admin_user, parent_category):
        """Test that admin users can partially update categories"""
        client.force_authenticate(user=admin_user)
        url = f"/api/catalog/categories/{parent_category.id}/"
        data = {"name": "Partially Updated"}
        
        response = client.patch(url, data, format="json")
        
        assert response.status_code == 200
        assert response.data["name"] == "Partially Updated"

    def test_update_category_unauthorized(self, client, regular_user, parent_category):
        """Test that regular users cannot update categories"""
        client.force_authenticate(user=regular_user)
        url = f"/api/catalog/categories/{parent_category.id}/"
        data = {"name": "Unauthorized Update"}
        
        response = client.patch(url, data, format="json")
        
        assert response.status_code == 403

    def test_update_category_invalidates_cache(self, client, admin_user, parent_category):
        """Test that updating a category invalidates the cache"""
        client.force_authenticate(user=admin_user)
        
        # Populate cache
        retrieve_url = f"/api/catalog/categories/{parent_category.id}/"
        client.get(retrieve_url)
        
        # Update category
        update_url = f"/api/catalog/categories/{parent_category.id}/"
        data = {"name": "Updated Name", "parent": None}
        response = client.put(update_url, data, format="json")
        
        assert response.status_code == 200
        
        # Retrieve should show updated data
        retrieve_response = client.get(retrieve_url)
        assert retrieve_response.data["name"] == "Updated Name"


@pytest.mark.django_db
class TestCategoryDelete:
    """Test cases for DELETE /api/catalog/categories/{id}/ endpoint"""

    def test_delete_category_as_admin(self, client, admin_user, parent_category):
        """Test that admin users can delete (soft delete) categories"""
        client.force_authenticate(user=admin_user)
        url = f"/api/catalog/categories/{parent_category.id}/"
        
        response = client.delete(url)
        
        assert response.status_code == 204
        
        # Category should be soft deleted (is_active=False)
        parent_category.refresh_from_db()
        assert parent_category.is_active is False
        
        # Category should not appear in list
        list_response = client.get("/api/catalog/categories/")
        category_ids = [cat["id"] for cat in list_response.data]
        assert parent_category.id not in category_ids

    def test_delete_category_unauthorized(self, client, regular_user, parent_category):
        """Test that regular users cannot delete categories"""
        client.force_authenticate(user=regular_user)
        url = f"/api/catalog/categories/{parent_category.id}/"
        
        response = client.delete(url)
        
        assert response.status_code == 403

    def test_delete_category_invalidates_cache(self, client, admin_user, parent_category):
        """Test that deleting a category invalidates the cache"""
        client.force_authenticate(user=admin_user)
        
        # Populate cache
        list_url = "/api/catalog/categories/"
        client.get(list_url)
        
        # Delete category
        delete_url = f"/api/catalog/categories/{parent_category.id}/"
        response = client.delete(delete_url)
        
        assert response.status_code == 204
        
        # List should not include deleted category
        list_response = client.get(list_url)
        category_ids = [cat["id"] for cat in list_response.data]
        assert parent_category.id not in category_ids


@pytest.mark.django_db
class TestCategoryPermissions:
    """Test cases for category endpoint permissions"""

    def test_public_read_access(self, client, parent_category):
        """Test that categories are publicly readable"""
        # List
        list_response = client.get("/api/catalog/categories/")
        assert list_response.status_code == 200
        
        # Retrieve
        retrieve_response = client.get(f"/api/catalog/categories/{parent_category.id}/")
        assert retrieve_response.status_code == 200

    def test_admin_write_access_required(self, client, regular_user, parent_category):
        """Test that only admins can write to categories"""
        client.force_authenticate(user=regular_user)
        
        # Create
        create_response = client.post("/api/catalog/categories/", {"name": "Test"}, format="json")
        assert create_response.status_code == 403
        
        # Update
        update_response = client.patch(f"/api/catalog/categories/{parent_category.id}/", {"name": "Test"}, format="json")
        assert update_response.status_code == 403
        
        # Delete
        delete_response = client.delete(f"/api/catalog/categories/{parent_category.id}/")
        assert delete_response.status_code == 403


@pytest.mark.django_db
class TestCategoryHierarchy:
    """Test cases for category parent-child relationships"""

    def test_category_with_multiple_children(self, client, parent_category, db):
        """Test category with multiple children"""
        child1 = Category.objects.create(name="Child 1", parent=parent_category, is_active=True)
        child2 = Category.objects.create(name="Child 2", parent=parent_category, is_active=True)
        child3 = Category.objects.create(name="Child 3", parent=parent_category, is_active=True)
        
        url = f"/api/catalog/categories/{parent_category.id}/?include_children=1"
        response = client.get(url)
        
        assert response.status_code == 200
        assert len(response.data["children"]) == 3
        child_ids = [child["id"] for child in response.data["children"]]
        assert child1.id in child_ids
        assert child2.id in child_ids
        assert child3.id in child_ids

    def test_nested_category_hierarchy(self, client, parent_category, child_category, db):
        """Test nested category hierarchy (grandparent -> parent -> child)"""
        grandchild = Category.objects.create(
            name="Grandchild",
            parent=child_category,
            is_active=True
        )
        
        # Parent should have child
        parent_url = f"/api/catalog/categories/{parent_category.id}/?include_children=1"
        parent_response = client.get(parent_url)
        assert len(parent_response.data["children"]) == 1
        
        # Child should have grandchild
        child_url = f"/api/catalog/categories/{child_category.id}/?include_children=1"
        child_response = client.get(child_url)
        assert len(child_response.data["children"]) == 1
        assert child_response.data["children"][0]["id"] == grandchild.id

    def test_inactive_children_not_included(self, client, parent_category, db):
        """Test that inactive children are not included in response"""
        active_child = Category.objects.create(
            name="Active Child",
            parent=parent_category,
            is_active=True
        )
        inactive_child = Category.objects.create(
            name="Inactive Child",
            parent=parent_category,
            is_active=False
        )
        
        url = f"/api/catalog/categories/{parent_category.id}/?include_children=1"
        response = client.get(url)
        
        assert response.status_code == 200
        assert len(response.data["children"]) == 1
        assert response.data["children"][0]["id"] == active_child.id
        assert response.data["children"][0]["name"] == "Active Child"

