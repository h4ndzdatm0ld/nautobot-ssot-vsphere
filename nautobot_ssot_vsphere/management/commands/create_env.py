"""Management command to bootstrap dummy data for Reservations."""

from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError

from nautobot_ssot_vsphere.tests.fixtures import create_env


class Command(BaseCommand):
    """Publish command to bootstrap dummy data."""

    def handle(self, *args, **options):
        """Publish command to bootstrap dummy data."""
        self.stdout.write("Attempting to populate dummy data.")
        try:
            create_env()
            self.stdout.write(self.style.SUCCESS("Successfully populated dummy data!"))
        except IntegrityError:
            self.stdout.write(
                self.style.ERROR(
                    "Unable to populate data, command is not idempotent. Please validate objects do not already exist."
                )
            )
