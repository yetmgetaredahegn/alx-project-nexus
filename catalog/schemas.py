# catalog/schemas.py

from drf_spectacular.utils import OpenApiRequest
from drf_spectacular.types import OpenApiTypes

product_image_upload_schema = OpenApiRequest(
    {
        "type": "object",
        "properties": {
            "image": {
                "type": "string",
                "format": "binary",
                "description": "Image file to upload for this product"
            }
        },
        "required": ["image"]
    }
)
