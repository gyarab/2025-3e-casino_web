from django.core.management.base import BaseCommand

from main.models import Quest
from main.quest_seed_data import seed_default_quests


class Command(BaseCommand):
    help = 'Seed the rotating daily and weekly quest pools'

    def handle(self, *args, **options):
        created_count = seed_default_quests(Quest, reset=True)
        total_count = Quest.objects.count()

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully seeded {created_count} new quests ({total_count} total)'
            )
        )
