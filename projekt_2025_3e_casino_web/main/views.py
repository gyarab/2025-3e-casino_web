from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.shortcuts import redirect
from django.utils import timezone
from decimal import Decimal
import json
import random
from .models import UserProfile, BattlePass, Quest, UserQuestProgress


@login_required
def blackjack(request):
    try:
        balance = request.user.userprofile.balance
    except UserProfile.DoesNotExist:
        balance = 0
    return render(request, 'main/blackjack.html', {'balance': balance})


def signin(request):
    return render(request, 'main/signin.html')


def home(request):
    return render(request, 'main/home.html')


@login_required
def settings(request):
    theme_choices = [
        ('neon', 'Neon'),
        ('gold', 'Gold'),
        ('retro', 'Retro Vegas'),
        ('minimal', 'Minimal'),
    ]

    if request.method == 'POST':
        selected_theme = request.POST.get('theme', 'neon')
        if selected_theme in dict(theme_choices):
            profile = request.user.userprofile
            profile.theme = selected_theme
            profile.save()
            messages.success(request, 'Motiv byl uložen.')
        else:
            messages.error(request, 'Vybraný motiv není platný.')
        return redirect('settings')

    profile = request.user.userprofile
    context = {
        'theme_choices': theme_choices,
        'current_theme': profile.theme,
    }
    return render(request, 'main/settings.html', context)


@login_required
def update_balance(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            new_balance = float(data.get('balance', 0))
            game = data.get('game')
            print(f'Update balance: balance={new_balance}, game={game}')

            profile = request.user.userprofile
            profile.balance = new_balance
            profile.save()

            if game:
                won = str(data.get('won', '')).lower() in ['true', '1', 'yes']
                win_amount = float(data.get('win', 0) or 0)
                track_quest_progress(request, game=game, won=won, win_amount=win_amount)

            return JsonResponse({'success': True})
        except Exception as e:
            print(f'Update balance error: {e}')
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    return JsonResponse({'success': False}, status=400)


def gamemodes(request):
    return render(request, 'main/gamemodes.html')


@login_required
def roulette(request):
    try:
        balance = request.user.userprofile.balance
    except UserProfile.DoesNotExist:
        balance = 0
    return render(request, 'main/roulette.html', {'balance': balance})


@login_required
def slots(request):
    try:
        balance = request.user.userprofile.balance
    except UserProfile.DoesNotExist:
        balance = 0
    return render(request, 'main/slots.html', {'balance': balance})


@login_required
def battlepass(request):
    battlepass = request.user.battlepass
    progress_percent = int((battlepass.xp / battlepass.xp_for_level) * 100) if battlepass.xp_for_level > 0 else 0
    return render(request, 'main/battlepass.html', {'battlepass': battlepass, 'progress_percent': progress_percent})


@login_required
@require_http_methods(["POST"])
def claim_reward(request):
    data = json.loads(request.body)
    level = data.get('level')
    battlepass = request.user.battlepass

    if level <= battlepass.level and level not in battlepass.claimed_rewards:
        battlepass.claimed_rewards.append(level)
        chips = level * 100
        request.user.userprofile.balance += Decimal(chips)
        request.user.userprofile.save()
        battlepass.save()
        return JsonResponse({'success': True, 'chips': chips})

    return JsonResponse({'success': False})


@login_required
@require_http_methods(["POST"])
def spin_slot(request):
    try:
        data = json.loads(request.body)
        bet = Decimal(str(data.get('bet', 0)))

        if bet <= 0:
            return JsonResponse({'error': 'Bet must be greater than 0'}, status=400)

        user_profile = request.user.userprofile

        if user_profile.balance < bet:
            return JsonResponse({'error': 'Insufficient balance'}, status=400)

        user_profile.balance -= bet

        symbols = ['🍒', '🍊', '🍋', '💎', '⭐', '🔔', '7️⃣']
        reels = [random.choice(symbols) for _ in range(3)]

        win = Decimal(0)
        multiplier = 0

        if reels[0] == reels[1] == reels[2]:
            if reels[0] == '💎':
                multiplier = 10
            elif reels[0] == '7️⃣':
                multiplier = 8
            elif reels[0] == '⭐':
                multiplier = 6
            elif reels[0] == '🔔':
                multiplier = 5
            else:
                multiplier = 3

            win = bet * Decimal(multiplier)

        elif reels[0] == reels[1] or reels[1] == reels[2] or reels[0] == reels[2]:
            if '💎' in reels:
                win = bet * Decimal(2)
            else:
                win = bet * Decimal('1.5')

        if win > 0:
            user_profile.balance += bet + win

        user_profile.save()

        try:
            track_quest_progress(request, game='slots', won=(win > 0), win_amount=float(win))
        except Exception:
            pass

        return JsonResponse({
            'success': True,
            'reels': reels,
            'bet': str(bet),
            'win': str(win),
            'multiplier': multiplier,
            'new_balance': str(user_profile.balance),
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


ROULETTE_RED_NUMBERS = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}

# Jen čísla, která jsou opravdu na tvém obrázku rulety.
ROULETTE_WHEEL_NUMBERS = [
    0, 32, 15, 19, 4, 21, 2, 25, 17, 34, 6, 27, 13, 36, 11, 30,
    8, 23, 10, 5, 24, 16, 33, 1, 20, 14, 31, 9, 22, 18, 29, 7, 28
]


def get_roulette_color(number):
    if number == 0:
        return 'green'
    return 'red' if number in ROULETTE_RED_NUMBERS else 'black'


def roulette_bet_matches(bet_type, value, number):
    if bet_type == 'number':
        return int(value) == number

    if number == 0:
        return False

    if bet_type == 'red':
        return number in ROULETTE_RED_NUMBERS

    if bet_type == 'black':
        return number not in ROULETTE_RED_NUMBERS

    if bet_type == 'even':
        return number % 2 == 0

    if bet_type == 'odd':
        return number % 2 == 1

    if bet_type == 'low':
        return 1 <= number <= 18

    if bet_type == 'high':
        return 19 <= number <= 36

    if bet_type == 'dozen':
        return (
            (value == 'first' and 1 <= number <= 12) or
            (value == 'second' and 13 <= number <= 24) or
            (value == 'third' and 25 <= number <= 36)
        )

    if bet_type == 'column':
        return (
            (value == 'top' and number % 3 == 0) or
            (value == 'middle' and number % 3 == 2) or
            (value == 'bottom' and number % 3 == 1)
        )

    return False


def roulette_payout_multiplier(bet_type):
    if bet_type == 'number':
        return Decimal(35)

    if bet_type in ['dozen', 'column']:
        return Decimal(2)

    if bet_type in ['red', 'black', 'even', 'odd', 'low', 'high']:
        return Decimal(1)

    return Decimal(0)


@login_required
@require_http_methods(["POST"])
def spin_roulette(request):
    try:
        data = json.loads(request.body)
        bets = data.get('bets', [])

        if not bets:
            return JsonResponse({'error': 'Nejdřív položte chip na stůl.'}, status=400)

        parsed_bets = []
        total_bet = Decimal(0)

        for bet in bets:
            amount = Decimal(str(bet.get('amount', 0)))
            bet_type = str(bet.get('type', ''))
            value = bet.get('value')

            if amount <= 0:
                return JsonResponse({'error': 'Neplatná sázka.'}, status=400)

            if roulette_payout_multiplier(bet_type) <= 0:
                return JsonResponse({'error': 'Neplatné pole na stole.'}, status=400)

            if bet_type == 'number' and not (0 <= int(value) <= 36):
                return JsonResponse({'error': 'Neplatné číslo rulety.'}, status=400)

            parsed_bets.append({
                'type': bet_type,
                'value': value,
                'amount': amount,
            })
            total_bet += amount

        user_profile = request.user.userprofile

        if user_profile.balance < total_bet:
            return JsonResponse({'error': 'Nemáte dostatek chipů.'}, status=400)

        user_profile.balance -= total_bet

        result_number = random.choice(ROULETTE_WHEEL_NUMBERS)
        total_return = Decimal(0)
        winning_bets = []

        for bet in parsed_bets:
            if roulette_bet_matches(bet['type'], bet['value'], result_number):
                multiplier = roulette_payout_multiplier(bet['type'])
                returned = bet['amount'] * (multiplier + Decimal(1))
                total_return += returned

                winning_bets.append({
                    'type': bet['type'],
                    'value': bet['value'],
                    'amount': str(bet['amount']),
                    'returned': str(returned),
                })

        if total_return > 0:
            user_profile.balance += total_return

        user_profile.save()

        net_win = total_return - total_bet

        try:
            track_quest_progress(
                request,
                game='roulette',
                won=(total_return > total_bet),
                win_amount=float(max(net_win, Decimal(0)))
            )
        except Exception:
            pass

        return JsonResponse({
            'success': True,
            'number': result_number,
            'color': get_roulette_color(result_number),
            'total_bet': str(total_bet),
            'total_return': str(total_return),
            'net_win': str(net_win),
            'winning_bets': winning_bets,
            'new_balance': str(user_profile.balance),
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


def track_quest_progress(request, game=None, won=False, win_amount=0):
    try:
        for quest in Quest.objects.all():
            progress, _ = UserQuestProgress.objects.get_or_create(
                user=request.user,
                quest=quest,
                defaults={'current_progress': 0, 'completed': False}
            )

            if progress.completed:
                continue

            increment = 0

            if quest.objective_type == 'games_played' and game in ['blackjack', 'slots', 'roulette']:
                increment = 1
            elif quest.objective_type == 'blackjack_games' and game == 'blackjack':
                increment = 1
            elif quest.objective_type == 'slots_games' and game == 'slots':
                increment = 1
            elif quest.objective_type == 'games_won' and won:
                increment = 1
            elif quest.objective_type == 'blackjack_wins' and game == 'blackjack' and won:
                increment = 1
            elif quest.objective_type == 'slots_wins' and game == 'slots' and won:
                increment = 1
            elif quest.objective_type == 'money_won' and win_amount > 0:
                increment = int(win_amount)

            if increment <= 0:
                continue

            progress.current_progress += increment

            if progress.current_progress >= quest.objective_amount:
                progress.completed = True
                progress.completed_at = timezone.now()

                battle_pass = request.user.battlepass
                battle_pass.xp += quest.reward_xp
                battle_pass.total_xp += quest.reward_xp
                check_level_up(battle_pass)
                battle_pass.save()

            progress.save()

    except Exception as e:
        print(f'Quest tracking error: {e}')


def check_level_up(battle_pass):
    while battle_pass.xp >= battle_pass.xp_for_level:
        battle_pass.xp -= battle_pass.xp_for_level
        battle_pass.level += 1


def get_battle_pass_data(request):
    try:
        if not request.user.is_authenticated:
            return JsonResponse({
                'level': 1,
                'xp': 0,
                'xp_for_level': 100,
                'xp_progress': 0,
                'next_reward_level': 5,
            })

        battle_pass = request.user.battlepass
        xp_progress = (battle_pass.xp / battle_pass.xp_for_level) * 100

        return JsonResponse({
            'level': battle_pass.level,
            'xp': battle_pass.xp,
            'xp_for_level': battle_pass.xp_for_level,
            'xp_progress': xp_progress,
            'next_reward_level': ((battle_pass.level // 5) + 1) * 5,
        })

    except Exception:
        return JsonResponse({
            'level': 1,
            'xp': 0,
            'xp_for_level': 100,
            'xp_progress': 0,
            'next_reward_level': 5,
        })


def get_quests_data(request):
    try:
        if not request.user.is_authenticated:
            return JsonResponse({'daily': [], 'weekly': []})

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
                'progress_percent': (progress.current_progress / quest.objective_amount) * 100 if quest.objective_amount > 0 else 0,
            })

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
                'progress_percent': (progress.current_progress / quest.objective_amount) * 100 if quest.objective_amount > 0 else 0,
            })

        return JsonResponse({
            'daily': daily_quests,
            'weekly': weekly_quests,
        })

    except Exception:
        return JsonResponse({'daily': [], 'weekly': []})


@login_required
def shop(request):
    if request.method == 'POST':
        amount = int(request.POST.get('amount', 0))

        if amount in [10, 100, 1000]:
            profile = request.user.userprofile
            profile.balance += amount
            profile.save()
            messages.success(request, f'Successfully purchased {amount} credits!')
        else:
            messages.error(request, 'Invalid amount.')

        return redirect('shop')

    return render(request, 'main/shop.html', {'user': request.user})
