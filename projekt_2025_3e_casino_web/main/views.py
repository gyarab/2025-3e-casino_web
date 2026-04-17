from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from decimal import Decimal
import json
import random
from .models import UserProfile, BattlePass, Quest, UserQuestProgress

def blackjack(request):
    return render(request, 'main/blackjack.html')

def signin(request):
    return render(request, 'main/signin.html')

def home(request):
    return render(request, 'main/home.html')

def gamemodes(request):
    return render(request, 'main/gamemodes.html')

@login_required
def slots(request):
    """Slot machine game page"""
    try:
        balance = request.user.userprofile.balance
    except UserProfile.DoesNotExist:
        balance = 0
    return render(request, 'main/slots.html', {'balance': balance})

@login_required
@require_http_methods(["POST"])
def spin_slot(request):
    """API endpoint for slot machine spin"""
    try:
        data = json.loads(request.body)
        bet = Decimal(str(data.get('bet', 0)))
        
        # Validation
        if bet <= 0:
            return JsonResponse({'error': 'Bet must be greater than 0'}, status=400)
        
        # Get user profile
        user_profile = request.user.userprofile
        
        # Check if user has enough balance
        if user_profile.balance < bet:
            return JsonResponse({'error': 'Insufficient balance'}, status=400)
        
        # Deduct bet from balance
        user_profile.balance -= bet
        
        # Generate random result
        symbols = ['🍒', '🍊', '🍋', '💎', '⭐', '🔔', '7️⃣']
        reels = [random.choice(symbols) for _ in range(3)]
        
        # Calculate win
        win = Decimal(0)
        multiplier = 0
        
        if reels[0] == reels[1] == reels[2]:
            # All three match - big win
            if reels[0] == '💎':
                multiplier = 10  # Diamond = 10x
            elif reels[0] == '7️⃣':
                multiplier = 8   # 7 = 8x
            elif reels[0] == '⭐':
                multiplier = 6   # Star = 6x
            elif reels[0] == '🔔':
                multiplier = 5   # Bell = 5x
            else:
                multiplier = 3   # Other symbols = 3x
            
            win = bet * Decimal(multiplier)
        elif reels[0] == reels[1] or reels[1] == reels[2] or reels[0] == reels[2]:
            # Two match - small win
            if '💎' in reels:
                win = bet * Decimal(2)
            else:
                win = bet * Decimal(1.5)
        
        # Add win to balance
        user_profile.balance += win + bet  # Add bet back + win
        user_profile.save()
        
        # Track quest progress
        try:
            user_quests = UserQuestProgress.objects.filter(
                user=request.user,
                completed=False
            )
            
            for quest_progress in user_quests:
                quest = quest_progress.quest
                
                # Track games played
                if quest.objective_type == 'games_played':
                    quest_progress.current_progress += 1
                    if quest_progress.current_progress >= quest.objective_amount:
                        quest_progress.completed = True
                        # Add rewards
                        battle_pass = request.user.battlepass
                        battle_pass.xp += quest.reward_xp
                        check_level_up(battle_pass)
                        battle_pass.save()
                
                # Track money won
                elif quest.objective_type == 'money_won':
                    if win > 0:
                        quest_progress.current_progress += float(win)
                        if quest_progress.current_progress >= quest.objective_amount:
                            quest_progress.completed = True
                            battle_pass = request.user.battlepass
                            battle_pass.xp += quest.reward_xp
                            check_level_up(battle_pass)
                            battle_pass.save()
                
                quest_progress.save()
        except:
            pass  # Quest tracking is not critical
        
        return JsonResponse({
            'success': True,
            'reels': reels,
            'bet': str(bet),
            'win': str(win),
            'multiplier': multiplier,
            'new_balance': str(user_profile.balance)
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


def check_level_up(battle_pass):
    """Check if battle pass leveled up and grant rewards"""
    while battle_pass.xp >= battle_pass.xp_for_level:
        battle_pass.xp -= battle_pass.xp_for_level
        battle_pass.level += 1
        
        # Grant rewards every 5 levels
        if battle_pass.level % 5 == 0:
            reward_chips = [100, 250, 500][(battle_pass.level // 5) - 1] if (battle_pass.level // 5) <= 3 else 500
            battle_pass.user.userprofile.balance += Decimal(reward_chips)
            battle_pass.user.userprofile.save()


def get_battle_pass_data(request):
    """Get user's battle pass data as JSON"""
    try:
        if not request.user.is_authenticated:
            return JsonResponse({
                'level': 1,
                'xp': 0,
                'xp_for_level': 100,
                'xp_progress': 0,
                'next_reward_level': 5
            })
        
        battle_pass = request.user.battlepass
        xp_progress = (battle_pass.xp / battle_pass.xp_for_level) * 100
        
        return JsonResponse({
            'level': battle_pass.level,
            'xp': battle_pass.xp,
            'xp_for_level': battle_pass.xp_for_level,
            'xp_progress': xp_progress,
            'next_reward_level': ((battle_pass.level // 5) + 1) * 5
        })
    except:
        return JsonResponse({
            'level': 1,
            'xp': 0,
            'xp_for_level': 100,
            'xp_progress': 0,
            'next_reward_level': 5
        })


def get_quests_data(request):
    """Get user's quests as JSON"""
    try:
        if not request.user.is_authenticated:
            return JsonResponse({'daily': [], 'weekly': []})
        
        # Get daily quests
        daily_quest_objs = Quest.objects.filter(quest_type='daily')
        daily_quests = []
        
        for quest in daily_quest_objs:
            progress = UserQuestProgress.objects.filter(
                user=request.user,
                quest=quest
            ).first()
            
            if not progress:
                progress = UserQuestProgress.objects.create(
                    user=request.user,
                    quest=quest,
                    current_progress=0,
                    completed=False
                )
            
            daily_quests.append({
                'id': quest.id,
                'title': quest.title,
                'objective_type': quest.objective_type,
                'objective_amount': quest.objective_amount,
                'current_progress': progress.current_progress,
                'completed': progress.completed,
                'reward_xp': quest.reward_xp,
                'progress_percent': (progress.current_progress / quest.objective_amount) * 100 if quest.objective_amount > 0 else 0
            })
        
        # Get weekly quests
        weekly_quest_objs = Quest.objects.filter(quest_type='weekly')
        weekly_quests = []
        
        for quest in weekly_quest_objs:
            progress = UserQuestProgress.objects.filter(
                user=request.user,
                quest=quest
            ).first()
            
            if not progress:
                progress = UserQuestProgress.objects.create(
                    user=request.user,
                    quest=quest,
                    current_progress=0,
                    completed=False
                )
            
            weekly_quests.append({
                'id': quest.id,
                'title': quest.title,
                'objective_type': quest.objective_type,
                'objective_amount': quest.objective_amount,
                'current_progress': progress.current_progress,
                'completed': progress.completed,
                'reward_xp': quest.reward_xp,
                'progress_percent': (progress.current_progress / quest.objective_amount) * 100 if quest.objective_amount > 0 else 0
            })
        
        return JsonResponse({
            'daily': daily_quests,
            'weekly': weekly_quests
        })
    except Exception as e:
        return JsonResponse({'daily': [], 'weekly': []})

