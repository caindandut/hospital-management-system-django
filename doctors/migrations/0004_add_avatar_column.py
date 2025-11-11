from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('doctors', '0003_add_rank_column'),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                "ALTER TABLE doctors ADD COLUMN avatar VARCHAR(255) NULL;"
            ),
            reverse_sql=("ALTER TABLE doctors DROP COLUMN avatar;")
        ),
    ]


