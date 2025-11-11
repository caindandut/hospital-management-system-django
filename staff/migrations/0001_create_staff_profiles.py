from django.db import migrations


DDL_CREATE = (
    """
    CREATE TABLE IF NOT EXISTS staff_profiles (
      id BIGINT PRIMARY KEY AUTO_INCREMENT,
      user_id BIGINT NOT NULL UNIQUE,
      employee_code VARCHAR(50) UNIQUE,
      full_name VARCHAR(255) NOT NULL,
      gender ENUM('MALE','FEMALE','OTHER') DEFAULT NULL,
      date_of_birth DATE DEFAULT NULL,
      cccd VARCHAR(20) UNIQUE,
      phone VARCHAR(20),
      address VARCHAR(255),
      position VARCHAR(100),
      shift ENUM('MORNING','AFTERNOON','ROTATE') DEFAULT 'ROTATE',
      start_date DATE,
      status ENUM('ACTIVE','INACTIVE','ON_LEAVE') DEFAULT 'ACTIVE',
      created_at DATETIME NOT NULL DEFAULT NOW(),
      updated_at DATETIME NOT NULL DEFAULT NOW() ON UPDATE NOW(),
      CONSTRAINT fk_staff_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    ) ENGINE=InnoDB;
    """
)

DDL_DROP = "DROP TABLE IF EXISTS staff_profiles;"


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.RunSQL(sql=DDL_CREATE, reverse_sql=DDL_DROP),
    ]


