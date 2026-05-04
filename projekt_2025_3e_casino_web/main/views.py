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
from .models import UserProfile, BattlePass, Quest, UserQuestProgress, PokerGame, PokerPlayer, PokerHand, PlayerHand, PlayerAction
from django.db.models import Max

ACTIVE_DAILY_QUESTS = 3
ACTIVE_WEEKLY_QUESTS = 3


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


def get_quest_cycle_key(quest_type, current_date=None):
    current_date = current_date or timezone.localdate()

    if quest_type == 'weekly':
        year, week, _ = current_date.isocalendar()
        return f'{year}-W{week:02d}'

    return current_date.isoformat()


def get_active_quests(quest_type, current_date=None):
    cycle_key = get_quest_cycle_key(quest_type, current_date)
    quest_limit = ACTIVE_WEEKLY_QUESTS if quest_type == 'weekly' else ACTIVE_DAILY_QUESTS
    quests = list(Quest.objects.filter(quest_type=quest_type).order_by('id'))

    if len(quests) <= quest_limit:
        return quests, cycle_key

    rng = random.Random(f'{quest_type}:{cycle_key}')
    rng.shuffle(quests)
    return quests[:quest_limit], cycle_key


def get_or_reset_quest_progress(user, quest, cycle_key):
    progress, created = UserQuestProgress.objects.get_or_create(
        user=user,
        quest=quest,
        defaults={
            'current_progress': 0,
            'completed': False,
            'cycle_key': cycle_key,
        }
    )

    if not created and progress.cycle_key != cycle_key:
        progress.current_progress = 0
        progress.completed = False
        progress.completed_at = None
        progress.cycle_key = cycle_key
        progress.save()

    return progress


def serialize_quest(quest, progress=None):
    current_progress = progress.current_progress if progress else 0
    completed = progress.completed if progress else False
    progress_percent = 0
    if quest.objective_amount > 0:
        progress_percent = min((current_progress / quest.objective_amount) * 100, 100)

    rewards = []
    if quest.reward_xp:
        rewards.append(f'+{quest.reward_xp} XP')
    if quest.reward_chips:
        rewards.append(f'+{quest.reward_chips} chips')
    if quest.reward_coins:
        rewards.append(f'+{quest.reward_coins} coins')

    return {
        'id': quest.id,
        'title': quest.title,
        'description': quest.description,
        'objective_type': quest.objective_type,
        'objective_amount': quest.objective_amount,
        'current_progress': min(current_progress, quest.objective_amount),
        'completed': completed,
        'reward_xp': quest.reward_xp,
        'reward_chips': quest.reward_chips,
        'reward_coins': quest.reward_coins,
        'reward_text': ' / '.join(rewards),
        'progress_percent': progress_percent,
    }


def get_quest_increment(quest, game=None, won=False, win_amount=0):
    if quest.objective_type == 'games_played' and game in ['blackjack', 'slots', 'roulette']:
        return 1
    if quest.objective_type == 'blackjack_games' and game == 'blackjack':
        return 1
    if quest.objective_type == 'slots_games' and game == 'slots':
        return 1
    if quest.objective_type == 'roulette_games' and game == 'roulette':
        return 1
    if quest.objective_type == 'games_won' and won:
        return 1
    if quest.objective_type == 'blackjack_wins' and game == 'blackjack' and won:
        return 1
    if quest.objective_type == 'slots_wins' and game == 'slots' and won:
        return 1
    if quest.objective_type == 'roulette_wins' and game == 'roulette' and won:
        return 1
    if quest.objective_type == 'money_won' and win_amount > 0:
        return int(win_amount)

    return 0


def track_quest_progress(request, game=None, won=False, win_amount=0):
    try:
        active_quest_groups = [
            get_active_quests('daily'),
            get_active_quests('weekly'),
        ]

        for quests, cycle_key in active_quest_groups:
            for quest in quests:
                progress = get_or_reset_quest_progress(request.user, quest, cycle_key)

                if progress.completed:
                    continue

                increment = get_quest_increment(quest, game, won, win_amount)

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

                    if quest.reward_chips:
                        profile = request.user.userprofile
                        profile.balance += Decimal(quest.reward_chips)
                        profile.save()

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
        daily_quest_objs, daily_cycle_key = get_active_quests('daily')
        weekly_quest_objs, weekly_cycle_key = get_active_quests('weekly')

        if request.user.is_authenticated:
            daily_quests = [
                serialize_quest(quest, get_or_reset_quest_progress(request.user, quest, daily_cycle_key))
                for quest in daily_quest_objs
            ]
            weekly_quests = [
                serialize_quest(quest, get_or_reset_quest_progress(request.user, quest, weekly_cycle_key))
                for quest in weekly_quest_objs
            ]
        else:
            daily_quests = [serialize_quest(quest) for quest in daily_quest_objs]
            weekly_quests = [serialize_quest(quest) for quest in weekly_quest_objs]

        return JsonResponse({
            'daily': daily_quests,
            'weekly': weekly_quests,
            'daily_cycle_key': daily_cycle_key,
            'weekly_cycle_key': weekly_cycle_key,
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


# ============ POKER VIEWS ============

import itertools

CARD_SUITS = ['H', 'D', 'C', 'S']  # Hearts, Diamonds, Clubs, Spades
CARD_RANKS = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']
RANK_VALUES = {'A': 14, 'K': 13, 'Q': 12, 'J': 11, 'T': 10, '9': 9, '8': 8, '7': 7, '6': 6, '5': 5, '4': 4, '3': 3, '2': 2}

def create_deck():
    """Create a standard 52-card deck"""
    return [f'{rank}{suit}' for rank in CARD_RANKS for suit in CARD_SUITS]

def evaluate_hand(hole_cards, community_cards):
    """Evaluate best 5-card poker hand from 7 cards (2 hole + 5 community)"""
    all_cards = hole_cards + community_cards
    
    # Generate all possible 5-card combinations from 7 cards
    best_hand = None
    best_rank = None
    
    for combo in itertools.combinations(all_cards, 5):
        hand_rank = rank_hand(list(combo))
        if best_rank is None or hand_rank > best_rank:
            best_rank = hand_rank
            best_hand = combo
    
    return best_rank

def rank_hand(cards):
    """Rank a 5-card hand. Returns tuple for comparison: (hand_type, high_cards)"""
    # Parse cards
    ranks = [RANK_VALUES[card[0]] for card in cards]
    suits = [card[1] for card in cards]
    
    ranks.sort(reverse=True)
    
    # Check for flush
    is_flush = len(set(suits)) == 1
    
    # Check for straight
    is_straight = False
    sorted_ranks = sorted(ranks, reverse=True)
    if sorted_ranks[0] - sorted_ranks[4] == 4 and len(set(ranks)) == 5:
        is_straight = True
    # Check for A-2-3-4-5 (wheel/bicycle)
    elif set(sorted_ranks) == {14, 5, 4, 3, 2}:
        is_straight = True
        sorted_ranks = [5, 4, 3, 2, 1]  # Ace is low in this case
    
    # Count rank frequencies
    rank_counts = {}
    for rank in ranks:
        rank_counts[rank] = rank_counts.get(rank, 0) + 1
    
    counts = sorted(rank_counts.values(), reverse=True)
    unique_ranks = sorted(rank_counts.keys(), key=lambda x: (rank_counts[x], x), reverse=True)
    
    # Determine hand type
    if is_straight and is_flush:
        return (8, tuple(sorted_ranks))  # Straight flush
    elif counts == [4, 1]:
        return (7, tuple(unique_ranks))  # Four of a kind
    elif counts == [3, 2]:
        return (6, tuple(unique_ranks))  # Full house
    elif is_flush:
        return (5, tuple(sorted_ranks))  # Flush
    elif is_straight:
        return (4, tuple(sorted_ranks))  # Straight
    elif counts == [3, 1, 1]:
        return (3, tuple(unique_ranks))  # Three of a kind
    elif counts == [2, 2, 1]:
        return (2, tuple(unique_ranks))  # Two pair
    elif counts == [2, 1, 1, 1]:
        return (1, tuple(unique_ranks))  # One pair
    else:
        return (0, tuple(sorted_ranks))  # High card

def determine_winner(hand):
    """Determine winner of a poker hand and award pot"""
    try:
        # Get all non-folded players
        active_players = hand.game.players.filter(is_active=True).order_by('seat_number')
        
        best_player = None
        best_hand_rank = None
        
        # Evaluate each player's hand
        for player in active_players:
            player_hand = hand.player_hands.filter(player=player).first()
            
            # Skip if folded
            if not player_hand or player_hand.is_folded:
                continue
            
            # Evaluate this player's hand
            hand_rank = evaluate_hand(player_hand.hole_cards, hand.community_cards)
            
            # Update best hand
            if best_hand_rank is None or hand_rank > best_hand_rank:
                best_hand_rank = hand_rank
                best_player = player
        
        # Award pot to winner
        if best_player:
            hand.winner = best_player
            best_player.current_stack += hand.pot
            best_player.save()
            hand.save()
    except Exception as e:
        print(f"Error determining winner: {str(e)}")

@login_required
def poker_lobby(request):
    """Show list of poker games and allow creating/joining"""
    games = PokerGame.objects.filter(status='waiting').order_by('-created_at')
    active_games = PokerGame.objects.filter(status='active').order_by('-created_at')
    
    user_games = PokerGame.objects.filter(players__user=request.user).distinct()
    
    return render(request, 'main/poker_lobby.html', {
        'waiting_games': games,
        'active_games': active_games,
        'user_games': user_games,
    })

@login_required
@require_http_methods(["POST"])
def create_poker_game(request):
    """Create a new poker game"""
    try:
        min_buy_in = Decimal(request.POST.get('min_buy_in', '10.00'))
        max_buy_in = Decimal(request.POST.get('max_buy_in', '1000.00'))
        creator_buy_in = Decimal(request.POST.get('creator_buy_in', '100.00'))
        
        # Validate buy-in is within range
        if creator_buy_in < min_buy_in or creator_buy_in > max_buy_in:
            messages.error(request, f'Buy-in must be between ${min_buy_in} and ${max_buy_in}')
            return redirect('poker_lobby')
        
        # Check if user has enough balance
        user_profile = request.user.userprofile
        if user_profile.balance < creator_buy_in:
            messages.error(request, 'Insufficient balance for buy-in')
            return redirect('poker_lobby')
        
        # Deduct buy-in from user balance
        user_profile.balance -= creator_buy_in
        user_profile.save()
        
        # Create game
        game = PokerGame.objects.create(
            created_by=request.user,
            min_buy_in=min_buy_in,
            max_buy_in=max_buy_in,
        )
        
        # Add creator as a player
        PokerPlayer.objects.create(
            game=game,
            user=request.user,
            buy_in_amount=creator_buy_in,
            current_stack=creator_buy_in,
            seat_number=1,
            is_active=True,
        )
        
        return redirect('poker_game', game_id=game.id)
    except Exception as e:
        messages.error(request, f'Error creating game: {str(e)}')
        return redirect('poker_lobby')

@login_required
def poker_game(request, game_id):
    """Display poker game"""
    try:
        game = PokerGame.objects.get(id=game_id)
        user_balance = request.user.userprofile.balance
        player = game.players.filter(user=request.user).first()
        
        return render(request, 'main/poker_game.html', {
            'game': game,
            'player': player,
            'user_balance': user_balance,
        })
    except PokerGame.DoesNotExist:
        messages.error(request, 'Game not found')
        return redirect('poker_lobby')

@login_required
@require_http_methods(["POST"])
@csrf_exempt
def join_poker_game(request, game_id):
    """Join an existing poker game"""
    try:
        game = PokerGame.objects.get(id=game_id)
        user_profile = request.user.userprofile
        
        buy_in = Decimal(request.POST.get('buy_in', game.min_buy_in))
        
        if buy_in < game.min_buy_in or buy_in > game.max_buy_in:
            return JsonResponse({'success': False, 'error': 'Invalid buy-in amount'})
        
        if user_profile.balance < buy_in:
            return JsonResponse({'success': False, 'error': 'Insufficient balance'})
        
        # Check if player already in game
        if game.players.filter(user=request.user).exists():
            return JsonResponse({'success': False, 'error': 'Already in game'})
        
        # Deduct buy-in from balance
        user_profile.balance -= buy_in
        user_profile.save()
        
        # Get next seat number
        seat_number = game.players.count() + 1
        
        # Create player
        player = PokerPlayer.objects.create(
            game=game,
            user=request.user,
            buy_in_amount=buy_in,
            current_stack=buy_in,
            seat_number=seat_number,
        )
        
        return JsonResponse({'success': True, 'player_id': player.id})
    except PokerGame.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Game not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_http_methods(["POST"])
@csrf_exempt
def start_poker_hand(request, game_id):
    """Start a new poker hand"""
    try:
        game = PokerGame.objects.get(id=game_id)
        
        # Check if user is game creator
        if game.created_by != request.user:
            return JsonResponse({'success': False, 'error': 'Only game creator can start'})
        
        # Check if there are at least 2 players
        active_players_count = game.players.filter(is_active=True).count()
        if active_players_count < 2:
            return JsonResponse({'success': False, 'error': 'Need at least 2 players to start a hand'})
        
        # Create new hand
        deck = create_deck()
        random.shuffle(deck)
        
        # Get first player (smallest seat number)
        first_player = game.players.filter(is_active=True).order_by('seat_number').first()
        
        hand = PokerHand.objects.create(
            game=game,
            hand_number=game.current_hand_number + 1,
            dealer=game.players.first(),
            current_player_turn=first_player,
            status='pre-flop',
        )
        
        # Store deck in hand for later use (we'll deal flop when advancing)
        hand._deck = deck
        hand._card_index = 0
        
        game.current_hand_number += 1
        game.status = 'active'
        game.save()
        
        # Deal cards to players (2 hole cards each)
        card_index = 0
        for player in game.players.filter(is_active=True):
            hole_cards = [deck[card_index], deck[card_index + 1]]
            card_index += 2
            
            PlayerHand.objects.create(
                hand=hand,
                player=player,
                hole_cards=hole_cards,
            )
        
        # Store next card index for later stages
        hand.next_card_index = card_index
        hand.save()
        
        return JsonResponse({'success': True, 'hand_id': hand.id})
    except PokerGame.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Game not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_http_methods(["POST"])
@csrf_exempt
def advance_stage(request, hand_id):
    """Advance to next stage (pre-flop -> flop -> turn -> river)"""
    try:
        hand = PokerHand.objects.get(id=hand_id)
        game = hand.game
        
        # Check if user is game creator
        if game.created_by != request.user:
            return JsonResponse({'success': False, 'error': 'Only game creator can advance stage'})
        
        if hand.status == 'pre-flop':
            # Deal flop (3 cards)
            deck = create_deck()
            random.shuffle(deck)
            
            # Recalculate card index based on number of players
            active_players = game.players.filter(is_active=True).count()
            card_index = active_players * 2
            
            community_cards = deck[card_index:card_index + 3]
            hand.community_cards = community_cards
            hand.status = 'flop'
            hand.save()
            return JsonResponse({'success': True, 'message': 'Advanced to Flop', 'stage': 'flop'})
        
        elif hand.status == 'flop':
            # Deal turn (1 more card = 4 total)
            community_cards = list(hand.community_cards)
            deck = create_deck()
            random.shuffle(deck)
            active_players = game.players.filter(is_active=True).count()
            card_index = active_players * 2 + 3
            community_cards.append(deck[card_index])
            
            hand.community_cards = community_cards
            hand.status = 'turn'
            hand.save()
            return JsonResponse({'success': True, 'message': 'Advanced to Turn', 'stage': 'turn'})
        
        elif hand.status == 'turn':
            # Deal river (1 more card = 5 total)
            community_cards = list(hand.community_cards)
            deck = create_deck()
            random.shuffle(deck)
            active_players = game.players.filter(is_active=True).count()
            card_index = active_players * 2 + 4
            community_cards.append(deck[card_index])
            
            hand.community_cards = community_cards
            hand.status = 'river'
            hand.save()
            return JsonResponse({'success': True, 'message': 'Advanced to River', 'stage': 'river'})
        
        elif hand.status == 'river':
            # Hand is complete
            hand.status = 'completed'
            hand.save()
            return JsonResponse({'success': True, 'message': 'Hand completed', 'stage': 'completed'})
        
        return JsonResponse({'success': False, 'error': 'Invalid stage'})
    except PokerHand.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Hand not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_http_methods(["POST"])
@csrf_exempt
def player_action(request, hand_id):
    """Process player action (fold, check, call, bet, raise) and auto-advance stages"""
    try:
        hand = PokerHand.objects.get(id=hand_id)
        action_type = request.POST.get('action_type')
        amount = Decimal(request.POST.get('amount', '0'))
        
        player = hand.game.players.get(user=request.user)
        player_hand = hand.player_hands.get(player=player)
        
        # Check if it's this player's turn
        if hand.current_player_turn != player:
            return JsonResponse({'success': False, 'error': 'Not your turn'})
        
        # Initialize tracking dicts if needed
        if not hand.players_acted_this_round:
            hand.players_acted_this_round = {}
        
        # Track bet amount before action for pot calculation
        bet_before = player_hand.current_bet
        
        # Process action
        if action_type == 'fold':
            player_hand.is_folded = True
            player_hand.save()
        elif action_type == 'check':
            pass
        elif action_type == 'call':
            # Call the current bet
            max_bet = hand.player_hands.filter(is_folded=False).aggregate(Max('current_bet'))['current_bet__max'] or Decimal('0')
            call_amount = max_bet - player_hand.current_bet
            player.current_stack -= call_amount
            player_hand.current_bet = max_bet
            player_hand.total_invested += call_amount
            # Add to pot
            hand.pot += call_amount
            player.save()
            player_hand.save()
            hand.current_round_bet = max_bet
        elif action_type in ['bet', 'raise']:
            if amount > player.current_stack:
                return JsonResponse({'success': False, 'error': 'Insufficient stack'})
            player.current_stack -= amount
            player_hand.current_bet += amount
            player_hand.total_invested += amount
            # Add to pot
            hand.pot += amount
            player.save()
            player_hand.save()
            hand.current_round_bet = player_hand.current_bet
        
        # Mark player as acted
        hand.players_acted_this_round[str(player.id)] = True
        hand.save()
        
        # Log action
        PlayerAction.objects.create(
            hand=hand,
            player=player,
            action_type=action_type,
            amount=amount,
        )
        
        # Check if round is complete (all non-folded players have acted and have equal bets)
        active_non_folded_players = hand.game.players.filter(is_active=True).exclude(
            playerhand__hand=hand,
            playerhand__is_folded=True
        ).distinct()
        
        round_complete = True
        max_bet = Decimal('0')
        
        for p in active_non_folded_players:
            p_hand = hand.player_hands.filter(player=p).first()
            if p_hand:
                max_bet = max(max_bet, p_hand.current_bet)
            
            if str(p.id) not in hand.players_acted_this_round:
                round_complete = False
                break
        
        # Check all bets are equal
        if round_complete:
            for p in active_non_folded_players:
                p_hand = hand.player_hands.filter(player=p).first()
                if p_hand and p_hand.current_bet != max_bet:
                    round_complete = False
                    break
        
        # Auto-advance to next stage if round is complete
        if round_complete:
            hand.round_number += 1
            hand.players_acted_this_round = {}  # Reset for next round
            hand.current_round_bet = Decimal('0')
            
            # Advance stage based on current status
            if hand.status == 'pre-flop':
                # Deal flop (3 cards)
                deck = create_deck()
                random.shuffle(deck)
                active_players_count = hand.game.players.filter(is_active=True).count()
                card_index = active_players_count * 2
                community_cards = deck[card_index:card_index + 3]
                hand.community_cards = community_cards
                hand.status = 'flop'
            elif hand.status == 'flop':
                # Deal turn (1 more card = 4 total)
                community_cards = list(hand.community_cards)
                deck = create_deck()
                random.shuffle(deck)
                active_players_count = hand.game.players.filter(is_active=True).count()
                card_index = active_players_count * 2 + 3
                community_cards.append(deck[card_index])
                hand.community_cards = community_cards
                hand.status = 'turn'
            elif hand.status == 'turn':
                # Deal river (1 more card = 5 total)
                community_cards = list(hand.community_cards)
                deck = create_deck()
                random.shuffle(deck)
                active_players_count = hand.game.players.filter(is_active=True).count()
                card_index = active_players_count * 2 + 4
                community_cards.append(deck[card_index])
                hand.community_cards = community_cards
                hand.status = 'river'
            elif hand.status == 'river':
                # Hand complete - determine winner
                hand.status = 'completed'
                determine_winner(hand)
        
        # Move to next player (only if hand is not completed)
        if hand.status != 'completed':
            active_players = hand.game.players.filter(is_active=True).order_by('seat_number')
            current_index = list(active_players.values_list('id', flat=True)).index(player.id)
            next_index = (current_index + 1) % len(active_players)
            next_player = active_players[next_index]
            
            hand.current_player_turn = next_player
        else:
            hand.current_player_turn = None
        
        hand.save()
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_http_methods(["POST"])
@csrf_exempt
def get_game_state(request, game_id):
    """Get current game state as JSON"""
    try:
        game = PokerGame.objects.get(id=game_id)
        current_hand = game.hands.order_by('-created_at').first()
        
        players_data = []
        for player in game.players.all():
            player_hand = current_hand.player_hands.filter(player=player).first() if current_hand else None
            is_current_turn = current_hand and current_hand.current_player_turn_id == player.id
            is_winner = current_hand and current_hand.winner_id == player.id
            players_data.append({
                'id': player.id,
                'username': player.user.username,
                'seat': player.seat_number,
                'stack': float(player.current_stack),
                'is_active': player.is_active,
                'is_current_turn': is_current_turn,
                'is_winner': is_winner,
                'is_folded': player_hand.is_folded if player_hand else False,
                'hole_cards': player_hand.hole_cards if player_hand and (player.user == request.user or (current_hand and current_hand.status == 'completed')) else ['XX', 'XX'],
            })
        
        return JsonResponse({
            'success': True,
            'game_id': game.id,
            'status': game.status,
            'players': players_data,
            'community_cards': current_hand.community_cards if current_hand else [],
            'pot': float(current_hand.pot) if current_hand else 0,
            'current_hand': current_hand.id if current_hand else None,
            'current_player_turn': current_hand.current_player_turn_id if current_hand else None,
            'stage': current_hand.status if current_hand else 'pre-flop',
        })
    except PokerGame.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Game not found'})

@login_required
@require_http_methods(["POST"])
@csrf_exempt
def leave_poker_game(request, game_id):
    """Leave a poker game and return chips to balance"""
    try:
        game = PokerGame.objects.get(id=game_id)
        player = game.players.get(user=request.user)
        
        # Return remaining stack to user balance
        user_profile = request.user.userprofile
        user_profile.balance += player.current_stack
        user_profile.save()
        
        # Delete the player
        player.delete()
        
        # Delete game if no active players remain
        if not game.players.filter(is_active=True).exists():
            game.delete()
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

