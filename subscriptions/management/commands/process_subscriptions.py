from django.core.management.base import BaseCommand
from subscriptions.services import process_due_subscriptions


class Command(BaseCommand):
    help = 'Auto-renew or expire subscriptions that are due.'

    def handle(self, *args, **options):
        renewed, expired = process_due_subscriptions()
        self.stdout.write(self.style.SUCCESS(f'Renewed: {renewed}, Expired: {expired}'))

