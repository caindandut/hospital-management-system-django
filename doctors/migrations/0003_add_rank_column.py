from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("doctors", "0002_doctorsettings_userextras"),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                "ALTER TABLE `doctors` "
                "ADD COLUMN `rank` VARCHAR(10) NULL AFTER `consultation_fee`;"
            ),
            reverse_sql=(
                "ALTER TABLE `doctors` "
                "DROP COLUMN `rank`;"
            ),
        )
    ]


