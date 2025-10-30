from django.core.management.base import BaseCommand
from assignment.models import User, Record
from datetime import timedelta
import random
from django.utils import timezone
import hashlib


class Command(BaseCommand):
    help = "Generate records data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--user-id",
            type=int,
            default=1,
            help="ID of existing user to associate with records data",
        )
        parser.add_argument(
            "--num-records",
            type=int,
            default=100,
            help="Number of records data to generate",
        )
        parser.add_argument(
            "--clear-existing",
            action="store_true",
            help="Clear existing records for this user",
        )

    def handle(self, *args, **options):
        user_id = options["user_id"]
        num_records = options["num_records"]
        clear_existing = options["clear_existing"]

        try:
            user = User.objects.get(id=user_id)
            self.stdout.write(f"Found user: {user.email} (ID: {user.id})")
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"User with ID {user_id} does not exist.")
            )
            self.stdout.write("Available users:")
            for u in User.objects.all():
                self.stdout.write(f"  ID: {u.id}, Email: {u.email}")
            return

        # Clear existing records if requested
        if clear_existing:
            deleted_count, _ = Record.objects.filter(user=user).delete()
            self.stdout.write(f"Cleared {deleted_count} existing test records")

        base_date = timezone.now() - timedelta(days=30)

        records_created = 0
        for i in range(num_records):
            # Ensure unique timestamps
            record_date = base_date + timedelta(
                days=random.randint(0, 30),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59),
                seconds=i,
                milliseconds=random.randint(0, 999),
            )

            word_count = random.randint(10, 100)
            study_time = random.randint(5, 60)

            # unique hash
            hash_data = (
                f"{user.id}_{record_date.isoformat()}_{word_count}_{study_time}_{i}"
            )
            submission_id = hashlib.sha256(hash_data.encode()).hexdigest()

            Record.objects.create(
                user=user,
                word_count=word_count,
                study_time_minutes=study_time,
                timestamp=record_date,
                submission_id=submission_id,
            )
            records_created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully generated {records_created} test records for user: {user.email}"
            )
        )
