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
