from django.core.management.base import BaseCommand
from main.models import Quest


class Command(BaseCommand):
    help = 'Seed initial quest data'

    def handle(self, *args, **options):
        # Clear existing quests
        Quest.objects.all().delete()
        
        # Daily quests
        daily_quests = [
            {
                'title': 'Play 5 Games',
                'description': 'Play any casino game 5 times',
                'quest_type': 'daily',
                'objective_type': 'games_played',
                'objective_amount': 5,
                'reward_xp': 50,
                'reward_chips': 0
            },
            {
                'title': 'Win $100',
                'description': 'Win a total of $100 in a single session',
                'quest_type': 'daily',
                'objective_type': 'money_won',
                'objective_amount': 100,
                'reward_xp': 75,
                'reward_chips': 500
            },
            {
                'title': 'Play Blackjack 3x',
                'description': 'Play Blackjack game 3 times',
                'quest_type': 'daily',
                'objective_type': 'blackjack_games',
                'objective_amount': 3,
                'reward_xp': 50,
                'reward_chips': 0
            },
        ]
        
        # Weekly quests
        weekly_quests = [
            {
                'title': 'Win $500',
                'description': 'Win a total of $500 throughout the week',
                'quest_type': 'weekly',
                'objective_type': 'money_won',
                'objective_amount': 500,
                'reward_xp': 200,
                'reward_chips': 1000
            },
            {
                'title': 'Play 20 Games',
                'description': 'Play any casino game 20 times',
                'quest_type': 'weekly',
                'objective_type': 'games_played',
                'objective_amount': 20,
                'reward_xp': 150,
                'reward_chips': 500
            },
            {
                'title': 'Win 10 Games',
                'description': 'Win 10 games throughout the week',
                'quest_type': 'weekly',
                'objective_type': 'games_won',
                'objective_amount': 10,
                'reward_xp': 175,
                'reward_chips': 750
            },
        ]
        
        # Create daily quests
        for quest_data in daily_quests:
            Quest.objects.create(**quest_data)
            self.stdout.write(self.style.SUCCESS(f'Created daily quest: {quest_data["title"]}'))
        
        # Create weekly quests
        for quest_data in weekly_quests:
            Quest.objects.create(**quest_data)
            self.stdout.write(self.style.SUCCESS(f'Created weekly quest: {quest_data["title"]}'))
        
        self.stdout.write(self.style.SUCCESS('Successfully seeded quests'))
