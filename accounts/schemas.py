from drf_yasg import openapi

profile_update_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=[],
    properties={
        'phone': openapi.Schema(type=openapi.TYPE_STRING),
        'bio': openapi.Schema(type=openapi.TYPE_STRING),
        'avatar': openapi.Schema(
            type=openapi.TYPE_FILE,
            description="Image file for avatar upload"
        ),
    },
)
