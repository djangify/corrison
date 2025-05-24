from django.db import migrations, models
import uuid

class Migration(migrations.Migration):
    dependencies = [
        ('products', '0002_alter_product_description'),
    ]

    operations = [
        # First, remove the integer id field
        migrations.RemoveField(
            model_name='product',
            name='id',
        ),
        # Then add the UUID id field
        migrations.AddField(
            model_name='product',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False),
            preserve_default=False,
        ),
    ]
    