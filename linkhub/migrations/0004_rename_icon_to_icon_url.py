# linkhub/migrations/0004_rename_icon_to_icon_url.py
from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('linkhub', '0003_alter_linkhub_options_link_author_link_description_and_more'), 
    ]

    operations = [
        migrations.RenameField(
            model_name='link',
            old_name='icon',
            new_name='icon_url',
        ),
    ]
