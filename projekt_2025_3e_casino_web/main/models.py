from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import datetime, timedelta

class UserProfile(models.Model):
    THEME_CHOICES = [
        ('neon', 'Neon'),
        ('gold', 'Gold'),
        ('retro', 'Retro Vegas'),
        ('minimal', 'Minimal'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=20, decimal_places=2, default=1000.00)
    theme = models.CharField(max_length=20, choices=THEME_CHOICES, default='neon')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.user.username

class BattlePass(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    level = models.IntegerField(default=1)
    xp = models.IntegerField(default=0)
    xp_for_level = models.IntegerField(default=100)  # XP needed for next level
    total_xp = models.IntegerField(default=0)  # Total XP earned this season
    season_start = models.DateTimeField(auto_now_add=True)
    claimed_rewards = models.JSONField(default=list)
    
    def __str__(self):
        return f"{self.user.username} - Level {self.level}"

class Quest(models.Model):
    QUEST_TYPES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
    ]
    
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=255)
    quest_type = models.CharField(max_length=10, choices=QUEST_TYPES)
    objective_type = models.CharField(max_length=50)  # 'games_played', 'money_won', 'blackjack_games', 'slots_games', 'games_won', 'blackjack_wins', 'slots_wins'
    objective_amount = models.IntegerField()  # How many
    reward_xp = models.IntegerField()
    reward_coins = models.IntegerField(default=0)
    reward_chips = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.title} ({self.get_quest_type_display()})"

class UserQuestProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    quest = models.ForeignKey(Quest, on_delete=models.CASCADE)
    current_progress = models.IntegerField(default=0)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    cycle_key = models.CharField(max_length=20, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'quest')
    
    def __str__(self):
        return f"{self.user.username} - {self.quest.title}"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance, balance=1000.00)
        BattlePass.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    try:
        instance.userprofile.save()
        instance.battlepass.save()
    except UserProfile.DoesNotExist:
        UserProfile.objects.create(user=instance, balance=1000.00)
    except BattlePass.DoesNotExist:
        BattlePass.objects.create(user=instance)

class PokerGame(models.Model):
    # NOTE: Parts of the poker models (game/player/hand/action) were
    # implemented with assistance from GitHub Copilot.
    STATUS_CHOICES = [
        ('waiting', 'Waiting for players'),
        ('active', 'Game in progress'),
        ('completed', 'Game completed'),
    ]
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_poker_games')
    min_buy_in = models.DecimalField(max_digits=10, decimal_places=2, default=10.00)
    max_buy_in = models.DecimalField(max_digits=10, decimal_places=2, default=1000.00)
    big_blind = models.DecimalField(max_digits=10, decimal_places=2, default=1.00)
    small_blind = models.DecimalField(max_digits=10, decimal_places=2, default=0.50)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='waiting')
    current_hand_number = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Poker Game {self.id} - {self.get_status_display()}"

class PokerPlayer(models.Model):
    game = models.ForeignKey(PokerGame, on_delete=models.CASCADE, related_name='players')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    buy_in_amount = models.DecimalField(max_digits=10, decimal_places=2)
    current_stack = models.DecimalField(max_digits=10, decimal_places=2)
    seat_number = models.IntegerField()
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('game', 'user')
    
    def __str__(self):
        return f"{self.user.username} in Game {self.game.id}"

class PokerHand(models.Model):
    game = models.ForeignKey(PokerGame, on_delete=models.CASCADE, related_name='hands')
    hand_number = models.IntegerField()
    dealer = models.ForeignKey(PokerPlayer, on_delete=models.SET_NULL, null=True, related_name='dealt_hands')
    small_blind_player = models.ForeignKey(PokerPlayer, on_delete=models.SET_NULL, null=True, blank=True, related_name='small_blind_hands')
    big_blind_player = models.ForeignKey(PokerPlayer, on_delete=models.SET_NULL, null=True, blank=True, related_name='big_blind_hands')
    current_player_turn = models.ForeignKey(PokerPlayer, on_delete=models.SET_NULL, null=True, blank=True, related_name='turns')
    community_cards = models.JSONField(default=list)  # ['AH', 'KS', 'QD', 'JC', 'TH'] format
    pot = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    winner = models.ForeignKey(PokerPlayer, on_delete=models.SET_NULL, null=True, blank=True, related_name='won_hands')
    status = models.CharField(max_length=20, choices=[
        ('waiting', 'Waiting for ready'),
        ('pre-flop', 'Pre-Flop'),
        ('flop', 'Flop'),
        ('turn', 'Turn'),
        ('river', 'River'),
        ('completed', 'Completed'),
    ], default='waiting')
    current_round_bet = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Current bet amount in this round
    players_acted_this_round = models.JSONField(default=dict)  # {player_id: True/False}
    players_ready = models.JSONField(default=dict)  # {player_id: True/False} - tracks ready status
    deck = models.JSONField(default=list)  # Shuffled deck stored for dealing cards
    next_card_index = models.IntegerField(default=0)  # Track which card to deal next
    round_number = models.IntegerField(default=0)  # Track which round of betting
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Hand {self.hand_number} in Game {self.game.id}"

class PlayerHand(models.Model):
    hand = models.ForeignKey(PokerHand, on_delete=models.CASCADE, related_name='player_hands')
    player = models.ForeignKey(PokerPlayer, on_delete=models.CASCADE)
    hole_cards = models.JSONField(default=list)  # ['AH', 'KS'] format
    current_bet = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_invested = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_folded = models.BooleanField(default=False)
    is_all_in = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.player.user.username} - Hand {self.hand.hand_number}"

class PlayerAction(models.Model):
    ACTION_TYPES = [
        ('fold', 'Fold'),
        ('check', 'Check'),
        ('call', 'Call'),
        ('bet', 'Bet'),
        ('raise', 'Raise'),
        ('all_in', 'All In'),
    ]
    
    hand = models.ForeignKey(PokerHand, on_delete=models.CASCADE, related_name='actions')
    player = models.ForeignKey(PokerPlayer, on_delete=models.CASCADE)
    action_type = models.CharField(max_length=10, choices=ACTION_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.player.user.username} - {self.get_action_type_display()}"
