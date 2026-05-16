# This migration is not needed since the column was manually created
# If you haven't run migrations yet, you can safely delete this file

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pequemundo', '0001_initial'),
    ]

    operations = [
        # No operations - column already exists in database
    ]
