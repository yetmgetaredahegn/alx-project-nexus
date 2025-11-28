from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid
from django.utils import timezone

class User(AbstractUser):
    """
    Custom user: username kept for compatibility but login is by email.
    We keep inherited fields and add email uniqueness
    """

    email = models.EmailField(unique=True)
    is_seller = models.BooleanField(default=False)

    REQUIRED_FIELDS = ["username"]
    USERNAME_FIELD = "email"  # I use email to authenticate

    def __str__(self):
        return self.email

class Profile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField("accounts.User", on_delete=models.CASCADE, related_name="profile")
    phone = models.CharField(max_length=32, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"profile:{self.user.email}"
