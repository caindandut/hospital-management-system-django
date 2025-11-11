from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Create doctor_rank_fees table and populate with default data'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            # Tạo bảng
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS doctor_rank_fees (
                    id BIGINT PRIMARY KEY AUTO_INCREMENT,
                    `rank` VARCHAR(10) NOT NULL UNIQUE,
                    default_fee DECIMAL(12,2) NOT NULL
                ) ENGINE=InnoDB
            """)
            
            # Kiểm tra xem bảng có dữ liệu chưa
            cursor.execute("SELECT COUNT(*) FROM doctor_rank_fees")
            count = cursor.fetchone()[0]
            
            if count == 0:
                # Thêm dữ liệu mặc định
                cursor.execute("""
                    INSERT INTO doctor_rank_fees (`rank`, default_fee) VALUES
                    ('BS', 200000),
                    ('ThS', 300000),
                    ('TS', 500000),
                    ('PGS', 700000),
                    ('GS', 1000000)
                """)
                self.stdout.write(
                    self.style.SUCCESS('Table created and populated with default data')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS('Table already exists with data')
                )
