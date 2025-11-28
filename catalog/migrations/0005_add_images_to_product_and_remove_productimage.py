# Generated migration to add images field to Product and remove ProductImage model

from django.db import migrations, models
import django.db.models.deletion


def migrate_product_images_to_jsonfield(apps, schema_editor):
    """Migrate existing ProductImage records to Product.images JSONField"""
    Product = apps.get_model('catalog', 'Product')
    ProductImage = apps.get_model('catalog', 'ProductImage')
    
    # Use .update() directly to avoid reverse relation conflict
    # Get all product IDs that have images
    product_ids = ProductImage.objects.values_list('product_id', flat=True).distinct()
    
    for product_id in product_ids:
        # Get images for this product
        images = ProductImage.objects.filter(product_id=product_id).order_by('uploaded_at')
        image_paths = [str(img.image) for img in images]
        
        # Use .update() to set the JSONField directly, avoiding the reverse relation
        # This bypasses model instance creation which would trigger the reverse relation
        Product.objects.filter(pk=product_id).update(images=image_paths)


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0004_remove_productimage_alt_text_and_more'),
    ]

    operations = [
        # First, add the images field to Product
        migrations.AddField(
            model_name='product',
            name='images',
            field=models.JSONField(blank=True, default=list, help_text='List of image file paths/URLs'),
        ),
        # Migrate existing data from ProductImage to Product.images
        migrations.RunPython(migrate_product_images_to_jsonfield, migrations.RunPython.noop),
        # Then remove the ProductImage model
        migrations.DeleteModel(
            name='ProductImage',
        ),
    ]

