def quest(title, description, quest_type, objective_type, objective_amount, reward_xp, reward_chips):
    return {
        'title': title,
        'description': description,
        'quest_type': quest_type,
        'objective_type': objective_type,
        'objective_amount': objective_amount,
        'reward_xp': reward_xp,
        'reward_chips': reward_chips,
    }


DAILY_QUESTS = [
    quest('Casino Warmup', 'Play any casino game 2 times', 'daily', 'games_played', 2, 25, 50),
    quest('Table Hopper', 'Play any casino game 4 times', 'daily', 'games_played', 4, 45, 100),
    quest('Daily Grinder', 'Play any casino game 6 times', 'daily', 'games_played', 6, 65, 150),
    quest('Lucky Session', 'Play any casino game 8 times', 'daily', 'games_played', 8, 85, 250),
    quest('Win Any 2 Games', 'Win 2 games in any mode', 'daily', 'games_won', 2, 65, 150),
    quest('Win Any 3 Games', 'Win 3 games in any mode', 'daily', 'games_won', 3, 85, 250),
    quest('Win Any 5 Games', 'Win 5 games in any mode', 'daily', 'games_won', 5, 115, 400),
    quest('Chip Spark', 'Win a total of 75 chips today', 'daily', 'money_won', 75, 55, 150),
    quest('Chip Stack', 'Win a total of 150 chips today', 'daily', 'money_won', 150, 80, 300),
    quest('Pocket Profit', 'Win a total of 250 chips today', 'daily', 'money_won', 250, 110, 500),
    quest('Blackjack Check-In', 'Play Blackjack 2 times', 'daily', 'blackjack_games', 2, 35, 75),
    quest('Play BJ 5 Times', 'Play Blackjack 5 times', 'daily', 'blackjack_games', 5, 75, 180),
    quest('Blackjack Focus', 'Play Blackjack 7 times', 'daily', 'blackjack_games', 7, 95, 275),
    quest('Blackjack Winner', 'Win 2 Blackjack games', 'daily', 'blackjack_wins', 2, 80, 250),
    quest('Blackjack Streak', 'Win 4 Blackjack games', 'daily', 'blackjack_wins', 4, 120, 450),
    quest('Slot Tap', 'Play the slot machine 3 times', 'daily', 'slots_games', 3, 40, 90),
    quest('Slot Spinner', 'Play the slot machine 6 times', 'daily', 'slots_games', 6, 75, 180),
    quest('Slot Sprint', 'Play the slot machine 9 times', 'daily', 'slots_games', 9, 105, 320),
    quest('Slot Payday', 'Win 2 slot games', 'daily', 'slots_wins', 2, 80, 250),
    quest('Slot Heater', 'Win 4 slot games', 'daily', 'slots_wins', 4, 125, 450),
    quest('Roulette Tap', 'Play Roulette 3 times', 'daily', 'roulette_games', 3, 40, 90),
    quest('Roulette Spin-Up', 'Play Roulette 5 times', 'daily', 'roulette_games', 5, 70, 175),
    quest('Roulette Runner', 'Play Roulette 8 times', 'daily', 'roulette_games', 8, 100, 300),
    quest('Red Or Black', 'Win 2 Roulette rounds', 'daily', 'roulette_wins', 2, 85, 250),
    quest('Wheel Streak', 'Win 4 Roulette rounds', 'daily', 'roulette_wins', 4, 130, 475),
]


WEEKLY_QUESTS = [
    quest('Weekly Warmup', 'Play any casino game 12 times this week', 'weekly', 'games_played', 12, 120, 350),
    quest('Casino Regular', 'Play any casino game 20 times this week', 'weekly', 'games_played', 20, 160, 600),
    quest('Big Week', 'Play any casino game 35 times this week', 'weekly', 'games_played', 35, 240, 1200),
    quest('Marathon Session', 'Play any casino game 50 times this week', 'weekly', 'games_played', 50, 320, 1800),
    quest('Winning Week', 'Win 8 games this week', 'weekly', 'games_won', 8, 180, 700),
    quest('Hot Hands', 'Win 12 games this week', 'weekly', 'games_won', 12, 230, 1000),
    quest('Casino Champion', 'Win 18 games this week', 'weekly', 'games_won', 18, 320, 1700),
    quest('Chip Builder', 'Win a total of 500 chips this week', 'weekly', 'money_won', 500, 200, 1000),
    quest('Chip Collector', 'Win a total of 1000 chips this week', 'weekly', 'money_won', 1000, 280, 1700),
    quest('Chip Tycoon', 'Win a total of 2000 chips this week', 'weekly', 'money_won', 2000, 420, 3000),
    quest('Blackjack Marathon', 'Play Blackjack 15 times this week', 'weekly', 'blackjack_games', 15, 160, 600),
    quest('BJ Table Regular', 'Play Blackjack 25 times this week', 'weekly', 'blackjack_games', 25, 240, 1000),
    quest('Blackjack Mainstay', 'Play Blackjack 40 times this week', 'weekly', 'blackjack_games', 40, 340, 1800),
    quest('Blackjack Winner', 'Win 7 Blackjack games this week', 'weekly', 'blackjack_wins', 7, 210, 900),
    quest('Blackjack Boss', 'Win 12 Blackjack games this week', 'weekly', 'blackjack_wins', 12, 330, 1800),
    quest('Slot Regular', 'Play the slot machine 15 times this week', 'weekly', 'slots_games', 15, 150, 550),
    quest('Slot Machine Fan', 'Play the slot machine 25 times this week', 'weekly', 'slots_games', 25, 230, 950),
    quest('Slot Marathon', 'Play the slot machine 40 times this week', 'weekly', 'slots_games', 40, 330, 1700),
    quest('Slot Winner', 'Win 7 slot games this week', 'weekly', 'slots_wins', 7, 210, 900),
    quest('Slot Boss', 'Win 12 slot games this week', 'weekly', 'slots_wins', 12, 330, 1800),
    quest('Roulette Regular', 'Play Roulette 15 times this week', 'weekly', 'roulette_games', 15, 150, 550),
    quest('Wheel Grinder', 'Play Roulette 25 times this week', 'weekly', 'roulette_games', 25, 230, 950),
    quest('Roulette Marathon', 'Play Roulette 40 times this week', 'weekly', 'roulette_games', 40, 330, 1700),
    quest('Roulette Heater', 'Win 7 Roulette rounds this week', 'weekly', 'roulette_wins', 7, 220, 950),
    quest('Wheel Master', 'Win 12 Roulette rounds this week', 'weekly', 'roulette_wins', 12, 340, 1900),
]


def seed_default_quests(QuestModel, reset=False):
    if reset:
        QuestModel.objects.all().delete()

    created_count = 0
    for quest_data in DAILY_QUESTS + WEEKLY_QUESTS:
        _, created = QuestModel.objects.get_or_create(
            title=quest_data['title'],
            quest_type=quest_data['quest_type'],
            defaults=quest_data,
        )
        if created:
            created_count += 1

    return created_count
