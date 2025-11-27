from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiResponse

from .models import Profile
from .serializers import ProfileSerializer
from .permissions import IsOwnerOrAdmin
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser


class ProfileViewSet(viewsets.ModelViewSet):
    """
    Profile management endpoints.
    Profiles are auto-created via signals, so POST /profiles/ is disabled.
    """
    queryset = Profile.objects.all().order_by("id")
    serializer_class = ProfileSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    # Profiles are auto-created via signals, so POST /profiles/ is disabled
    http_method_names = ["get", "patch", "put", "delete", "head", "options"]

    # 🔒 Default → must be authenticated, and owner/admin for detail routes
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    @extend_schema(
        summary="List all profiles (admin only)",
        description="Returns a paginated list of all user profiles. Only accessible by admin users.",
        responses={200: ProfileSerializer(many=True), 403: OpenApiResponse(description="Forbidden - admin only")},
        tags=["Accounts"],
    )
    def list(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return Response(
                {"detail": "Only admin can list profiles."}, status=403
            )
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Retrieve a profile",
        description="Retrieve a specific profile by ID. Users can only access their own profile unless they are admin.",
        responses={200: ProfileSerializer, 403: OpenApiResponse(description="Forbidden"), 404: OpenApiResponse(description="Not found")},
        tags=["Accounts"],
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Update a profile",
        description="Update a profile. Supports avatar image upload via multipart/form-data.",
        request=ProfileSerializer,
        responses={200: ProfileSerializer, 400: OpenApiResponse(description="Bad request")},
        tags=["Accounts"],
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(
        summary="Partially update a profile",
        description="Partially update a profile. Supports avatar image upload via multipart/form-data.",
        request=ProfileSerializer,
        responses={200: ProfileSerializer, 400: OpenApiResponse(description="Bad request")},
        tags=["Accounts"],
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        summary="Delete a profile (admin only)",
        description="Delete a user profile. Only accessible by admin users.",
        responses={204: OpenApiResponse(description="Profile deleted"), 403: OpenApiResponse(description="Forbidden - admin only")},
        tags=["Accounts"],
    )
    def destroy(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return Response(
                {"detail": "Only admin can delete profiles."}, status=403
            )
        return super().destroy(request, *args, **kwargs)

    @extend_schema(
        summary="Get current user's profile",
        description="Retrieve the authenticated user's own profile.",
        methods=["get"],
        responses={200: ProfileSerializer},
        tags=["Accounts"],
    )
    @extend_schema(
        summary="Update current user's profile",
        description="Update the authenticated user's profile. Supports avatar image upload via multipart/form-data.",
        methods=["patch", "put"],
        request=ProfileSerializer,
        responses={200: ProfileSerializer, 400: OpenApiResponse(description="Bad request")},
        tags=["Accounts"],
    )
    @action(detail=False, methods=["get", "patch", "put"], url_path="me")
    def me(self, request):
        """
        Custom endpoint for current user's profile.
        GET: Retrieve your profile
        PATCH/PUT: Update your profile (supports avatar upload)
        """
        profile = request.user.profile

        if request.method == "GET":
            serializer = self.get_serializer(profile)
            return Response(serializer.data)

        if request.method in ("PATCH", "PUT"):
            serializer = self.get_serializer(
                profile,
                data=request.data,
                partial=request.method == "PATCH",
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
