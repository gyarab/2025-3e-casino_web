from datetime import date
from types import SimpleNamespace

from django.contrib.auth.models import User
from django.test import Client, TestCase

from .models import Quest, UserQuestProgress
from .views import (
    ACTIVE_DAILY_QUESTS,
    ACTIVE_WEEKLY_QUESTS,
    get_active_quests,
    get_or_reset_quest_progress,
    track_quest_progress,
)


class QuestRotationTests(TestCase):
    def setUp(self):
        Quest.objects.all().delete()
        self.user = User.objects.create_user(username='quester', password='pass')

    def create_quest(self, quest_type, title):
        return Quest.objects.create(
            title=title,
            description=f'{title} description',
            quest_type=quest_type,
            objective_type='games_played',
            objective_amount=2,
            reward_xp=10,
            reward_chips=25,
        )

    def test_active_quests_are_limited_and_stable_for_cycle(self):
        for index in range(6):
            self.create_quest('daily', f'Daily {index}')

        first_ids = [quest.id for quest in get_active_quests('daily', date(2026, 5, 4))[0]]
        second_ids = [quest.id for quest in get_active_quests('daily', date(2026, 5, 4))[0]]

        self.assertEqual(len(first_ids), ACTIVE_DAILY_QUESTS)
        self.assertEqual(first_ids, second_ids)

    def test_progress_resets_when_cycle_changes(self):
        quest = self.create_quest('daily', 'Reset Me')
        old_progress = UserQuestProgress.objects.create(
            user=self.user,
            quest=quest,
            current_progress=2,
            completed=True,
            cycle_key='2026-05-03',
        )

        progress = get_or_reset_quest_progress(self.user, quest, '2026-05-04')

        self.assertEqual(progress.id, old_progress.id)
        self.assertEqual(progress.current_progress, 0)
        self.assertFalse(progress.completed)
        self.assertEqual(progress.cycle_key, '2026-05-04')

    def test_tracking_only_updates_active_daily_and_weekly_quests(self):
        for index in range(5):
            self.create_quest('daily', f'Daily {index}')
            self.create_quest('weekly', f'Weekly {index}')

        request = SimpleNamespace(user=self.user)
        track_quest_progress(request, game='slots')

        progresses = UserQuestProgress.objects.filter(user=self.user)
        self.assertEqual(progresses.count(), ACTIVE_DAILY_QUESTS + ACTIVE_WEEKLY_QUESTS)
        self.assertTrue(all(progress.current_progress == 1 for progress in progresses))

    def test_guest_can_see_active_quest_preview(self):
        for index in range(5):
            self.create_quest('daily', f'Daily {index}')
            self.create_quest('weekly', f'Weekly {index}')

        response = Client().get('/api/quests/')
        data = response.json()

        self.assertEqual(len(data['daily']), ACTIVE_DAILY_QUESTS)
        self.assertEqual(len(data['weekly']), ACTIVE_WEEKLY_QUESTS)
        self.assertTrue(all(quest['current_progress'] == 0 for quest in data['daily']))
        self.assertTrue(all(not quest['completed'] for quest in data['weekly']))
