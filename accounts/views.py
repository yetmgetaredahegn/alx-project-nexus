from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema

from .models import Profile
from .serializers import ProfileSerializer
from .permissions import IsOwnerOrAdmin
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from .schemas import profile_update_schema


class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.all().order_by("id")
    serializer_class = ProfileSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    # Profiles are auto-created via signals, so POST /profiles/ is disabled
    http_method_names = ["get", "patch", "put", "delete", "head", "options"]

    # 🔒 Default → must be authenticated, and owner/admin for detail routes
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    # =========================
    # ADMIN-ONLY LIST
    # =========================
    def list(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return Response(
                {"detail": "Only admin can list profiles."}, status=403
            )
        return super().list(request, *args, **kwargs)

    # =========================
    # ADMIN-ONLY DELETE
    # =========================
    def destroy(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return Response(
                {"detail": "Only admin can delete profiles."}, status=403
            )
        return super().destroy(request, *args, **kwargs)

    # =========================
    # /api/accounts/profiles/me/
    # GET → fetch your profile
    # PATCH → update your profile + avatar upload
    # =========================
    @swagger_auto_schema(
        operation_description="Retrieve your profile.",
        methods=["get"],
        responses={200: ProfileSerializer},
    )
    @swagger_auto_schema(
        operation_description="Update your profile (supports avatar image upload).",
        methods=["patch", "put"],
        request_body=profile_update_schema,
    )
    @action(detail=False, methods=["get", "patch", "put"], url_path="me")
    def me(self, request):
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
