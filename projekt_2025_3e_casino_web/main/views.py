from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.contrib import messages
from django.shortcuts import redirect
from django.utils import timezone
from decimal import Decimal
import json
import random
from .models import UserProfile, BattlePass, Quest, UserQuestProgress, PokerGame, PokerPlayer, PokerHand, PlayerHand, PlayerAction
from .quest_seed_data import seed_default_quests
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


def leaderboard(request):
    players = UserProfile.objects.select_related('user').order_by('-balance', 'user__username')
    return render(request, 'main/leaderboard.html', {'players': players})


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
    if not Quest.objects.exists():
        seed_default_quests(Quest)

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
    # NOTE: Deck creation and basic poker utilities were assisted by GitHub Copilot.
    return [f'{rank}{suit}' for rank in CARD_RANKS for suit in CARD_SUITS]

def evaluate_hand(hole_cards, community_cards):
    """Evaluate best 5-card poker hand from 7 cards (2 hole + 5 community)"""
    # NOTE: Hand evaluation logic was implemented with help from GitHub Copilot.
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
    # NOTE: Winner determination and pot-awarding logic was developed with GitHub Copilot assistance.
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

def reset_betting_round(hand):
    """Clear per-round bets when moving to the next street."""
    hand.player_hands.update(current_bet=Decimal('0'))
    hand.current_round_bet = Decimal('0')

def deal_remaining_community_cards(hand):
    """Deal the rest of the board from the stored deck."""
    used_cards = set(hand.community_cards)
    for player_hand in hand.player_hands.all():
        used_cards.update(player_hand.hole_cards or [])

    deck = hand.deck or create_deck()
    remaining_cards = [card for card in deck if card not in used_cards]
    if len(remaining_cards) < 5 - len(hand.community_cards):
        remaining_cards = [card for card in create_deck() if card not in used_cards]

    community_cards = list(hand.community_cards)
    while len(community_cards) < 5 and remaining_cards:
        next_card = remaining_cards.pop(0)
        community_cards.append(next_card)
        used_cards.add(next_card)

    hand.community_cards = community_cards
    hand.next_card_index = max(hand.next_card_index, len(used_cards))

def all_remaining_players_all_in(hand, players):
    """Return true when no non-folded player can make another betting decision."""
    if players.count() < 2:
        return False

    for poker_player in players:
        player_hand = hand.player_hands.filter(player=poker_player).first()
        if not player_hand or not player_hand.is_all_in:
            return False
    return True

def complete_all_in_showdown(hand):
    """Run an all-in hand straight to showdown."""
    deal_remaining_community_cards(hand)
    hand.status = 'completed'
    hand.current_player_turn = None
    determine_winner(hand)
    hand.save()

def start_new_hand_after_completion(game):
    """Start a new hand after current hand completes, ready for players to get ready again"""
    try:
        # Create new hand in waiting status
        deck = create_deck()
        random.shuffle(deck)
        
        # Get players ordered by seat
        active_players = list(game.players.filter(is_active=True).order_by('seat_number'))
        
        # For heads-up (2 players): seat 0 is small blind, seat 1 is big blind
        small_blind_player = active_players[0] if len(active_players) > 0 else None
        big_blind_player = active_players[1] if len(active_players) > 1 else None
        
        hand = PokerHand.objects.create(
            game=game,
            hand_number=game.current_hand_number + 1,
            dealer=game.players.first(),
            small_blind_player=small_blind_player,
            big_blind_player=big_blind_player,
            current_player_turn=None,  # No turn until cards are dealt
            status='waiting',  # Start in waiting status
            players_ready={},  # Reset ready status
            deck=deck,  # Store shuffled deck
            next_card_index=0,  # Start dealing from first card
        )
        
        # Create PlayerHand objects for all players with empty hole cards
        for player in game.players.filter(is_active=True):
            PlayerHand.objects.create(
                hand=hand,
                player=player,
                hole_cards=[],  # Empty initially
            )
        
        game.current_hand_number += 1
        game.save()
    except Exception as e:
        print(f"Error starting new hand: {str(e)}")

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
@csrf_protect
@login_required
def create_poker_game(request):
    """Create a new poker game"""
    try:
        min_buy_in = Decimal(request.POST.get('min_buy_in', '100.00'))
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
        
        # Calculate blinds (big blind = 1/10 of min_buy_in, small blind = 1/2 of big blind)
        big_blind = min_buy_in / Decimal('10')
        small_blind = big_blind / Decimal('2')
        
        # Create game
        game = PokerGame.objects.create(
            created_by=request.user,
            min_buy_in=min_buy_in,
            max_buy_in=max_buy_in,
            big_blind=big_blind,
            small_blind=small_blind,
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
@csrf_protect
@login_required
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
@csrf_protect
@login_required
def start_poker_hand(request, game_id):
    """Start a new poker hand in waiting status without dealing cards yet"""
    try:
        game = PokerGame.objects.get(id=game_id)
        
        # Check if there are at least 2 players
        active_players_count = game.players.filter(is_active=True).count()
        if active_players_count < 2:
            return JsonResponse({'success': False, 'error': 'Need at least 2 players to start a hand'})
        
        # Check if a hand already exists
        current_hand = game.hands.order_by('-created_at').first()
        if current_hand and current_hand.status != 'completed':
            return JsonResponse({'success': False, 'error': 'Hand already in progress'})
        
        # Create new hand in waiting status
        deck = create_deck()
        random.shuffle(deck)
        
        # Get players ordered by seat
        active_players = list(game.players.filter(is_active=True).order_by('seat_number'))
        
        # For heads-up (2 players): seat 0 is small blind, seat 1 is big blind
        small_blind_player = active_players[0] if len(active_players) > 0 else None
        big_blind_player = active_players[1] if len(active_players) > 1 else None
        
        hand = PokerHand.objects.create(
            game=game,
            hand_number=game.current_hand_number + 1,
            dealer=game.players.first(),
            small_blind_player=small_blind_player,
            big_blind_player=big_blind_player,
            current_player_turn=None,  # No turn until cards are dealt
            status='waiting',  # Start in waiting status, not pre-flop
            players_ready={},  # Initialize empty ready dict
            deck=deck,  # Store shuffled deck
            next_card_index=0,  # Start dealing from first card
        )
        
        # Create PlayerHand objects for all players with empty hole cards
        # Cards will be dealt when all players are ready
        for player in game.players.filter(is_active=True):
            PlayerHand.objects.create(
                hand=hand,
                player=player,
                hole_cards=[],  # Empty initially
            )
        
        game.current_hand_number += 1
        game.status = 'active'
        game.save()
        
        return JsonResponse({'success': True, 'hand_id': hand.id})
    except PokerGame.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Game not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_http_methods(["POST"])
@csrf_protect
def player_ready(request, hand_id):
    """Toggle player ready status and deal cards + start hand when all players are ready"""
    # NOTE: Player-ready handling and initial dealing logic was implemented with Copilot assistance.
    try:
        hand = PokerHand.objects.get(id=hand_id)
        game = hand.game
        player = game.players.get(user=request.user)
        
        # Toggle player ready status
        if not hand.players_ready:
            hand.players_ready = {}
        
        # Toggle: if already ready, set to false; otherwise set to true
        is_currently_ready = hand.players_ready.get(str(player.id), False)
        hand.players_ready[str(player.id)] = not is_currently_ready
        
        # Check if all active players are ready
        active_players = game.players.filter(is_active=True)
        all_ready = all(str(p.id) in hand.players_ready and hand.players_ready[str(p.id)] for p in active_players)
        
        if all_ready and active_players.count() >= 2 and hand.status == 'waiting':
            # All players ready - deal cards and start the hand
            
            # Deal hole cards to all players
            card_index = hand.next_card_index
            for player_obj in active_players.order_by('seat_number'):
                player_hand = hand.player_hands.get(player=player_obj)
                player_hand.hole_cards = [hand.deck[card_index], hand.deck[card_index + 1]]
                player_hand.save()
                card_index += 2
            
            hand.next_card_index = card_index
            
            # Post blinds
            players_ordered = list(active_players.order_by('seat_number'))
            
            # Get small blind and big blind positions
            small_blind_index = 0
            big_blind_index = 1
            
            # Post small blind (dealer in heads-up)
            small_blind_player = players_ordered[small_blind_index]
            small_blind_amount = game.small_blind
            small_blind_actual = min(small_blind_amount, small_blind_player.current_stack)
            small_blind_player.current_stack -= small_blind_actual
            small_blind_player.save()
            
            player_hand_sb = hand.player_hands.get(player=small_blind_player)
            player_hand_sb.current_bet = small_blind_actual
            player_hand_sb.total_invested = small_blind_actual
            player_hand_sb.save()
            
            # Post big blind
            big_blind_player = players_ordered[big_blind_index]
            big_blind_amount = game.big_blind
            big_blind_actual = min(big_blind_amount, big_blind_player.current_stack)
            big_blind_player.current_stack -= big_blind_actual
            big_blind_player.save()
            
            player_hand_bb = hand.player_hands.get(player=big_blind_player)
            player_hand_bb.current_bet = big_blind_actual
            player_hand_bb.total_invested = big_blind_actual
            if big_blind_actual == big_blind_player.current_stack + big_blind_actual:
                # They're all-in if they had to post the whole remaining stack
                player_hand_bb.is_all_in = True
            player_hand_bb.save()
            
            # Add blinds to pot
            hand.pot = small_blind_actual + big_blind_actual
            hand.current_round_bet = big_blind_amount  # Current bet to match is the big blind
            
            # Start the hand - transition to pre-flop
            hand.status = 'pre-flop'
            
            # Small blind (dealer in heads-up) starts first action
            hand.current_player_turn = small_blind_player
            
            # Initialize players_acted_this_round for pre-flop
            hand.players_acted_this_round = {str(p.id): False for p in active_players}
        
        hand.save()
        
        return JsonResponse({
            'success': True,
            'players_ready': hand.players_ready,
            'hand_started': hand.status != 'waiting'
        })
    except PokerHand.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Hand not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_http_methods(["POST"])
@csrf_protect
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
            # Post-flop: small blind acts first
            hand.current_player_turn = hand.small_blind_player
            hand.players_acted_this_round = {str(p.id): False for p in game.players.filter(is_active=True)}
            reset_betting_round(hand)
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
            # Post-flop: small blind acts first
            hand.current_player_turn = hand.small_blind_player
            hand.players_acted_this_round = {str(p.id): False for p in game.players.filter(is_active=True)}
            reset_betting_round(hand)
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
            # Post-flop: small blind acts first
            hand.current_player_turn = hand.small_blind_player
            hand.players_acted_this_round = {str(p.id): False for p in game.players.filter(is_active=True)}
            reset_betting_round(hand)
            hand.save()
            return JsonResponse({'success': True, 'message': 'Advanced to River', 'stage': 'river'})
        
        elif hand.status == 'river':
            # Hand is complete
            hand.status = 'completed'
            hand.current_player_turn = None  # Clear turn
            hand.save()
            # Start new hand for next round
            start_new_hand_after_completion(hand.game)
            return JsonResponse({'success': True, 'message': 'Hand completed', 'stage': 'completed'})
        
        return JsonResponse({'success': False, 'error': 'Invalid stage'})
    except PokerHand.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Hand not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_http_methods(["POST"])
@csrf_protect
def player_action(request, hand_id):
    """Process player action (fold, check, call, bet, raise) and auto-advance stages"""
    # NOTE: Betting/action processing logic was implemented with assistance from GitHub Copilot.
    try:
        hand = PokerHand.objects.get(id=hand_id)
        action_type = request.POST.get('action_type')
        amount = Decimal(request.POST.get('amount', '0'))
        
        player = hand.game.players.get(user=request.user)
        player_hand = hand.player_hands.get(player=player)
        
        # ENFORCE: Game must not be in waiting status to take actions
        if hand.status == 'waiting':
            return JsonResponse({'success': False, 'error': 'Game has not started yet. Both players must be ready.'})
        
        # Check if it's this player's turn
        if hand.current_player_turn != player:
            return JsonResponse({'success': False, 'error': 'Not your turn'})
        
        # Initialize tracking dicts if needed
        if not hand.players_acted_this_round:
            hand.players_acted_this_round = {}
        
        # Track bet amount before action for pot calculation
        bet_before = player_hand.current_bet
        
        max_bet = hand.player_hands.filter(is_folded=False).aggregate(Max('current_bet'))['current_bet__max'] or Decimal('0')
        if action_type == 'call_check':
            action_type = 'call' if player_hand.current_bet < max_bet else 'check'

        # Process action
        if action_type == 'fold':
            player_hand.is_folded = True
            player_hand.save()
        elif action_type == 'check':
            # Can only check if no bet has been placed or if player has already matched the current bet
            if player_hand.current_bet != max_bet:
                return JsonResponse({'success': False, 'error': 'Cannot check when a bet has been placed. Must call or fold.'})
            pass
        elif action_type == 'call':
            # Call the current bet
            call_amount = max_bet - player_hand.current_bet
            
            # Track original call amount for all-in refund
            original_call_amount = call_amount
            
            # Limit call to available stack
            call_amount = min(call_amount, player.current_stack)
            
            player.current_stack -= call_amount
            player_hand.current_bet += call_amount
            player_hand.total_invested += call_amount
            
            # Check if going all-in
            is_all_in = False
            if player.current_stack == 0 and player_hand.current_bet > 0:
                player_hand.is_all_in = True
                is_all_in = True
            
            # Add to pot
            hand.pot += call_amount
            
            # Handle all-in refund: if player went all-in with less than the original bet,
            # refund the excess to the opponent
            if is_all_in and call_amount < original_call_amount:
                excess_refund = original_call_amount - call_amount
                # Find the player who made the original bet
                other_player = hand.game.players.exclude(id=player.id).first()
                if other_player:
                    other_player.current_stack += excess_refund
                    other_player.save()
                    # Reduce pot by refund amount
                    hand.pot -= excess_refund
            
            player.save()
            player_hand.save()
            hand.current_round_bet = player_hand.current_bet
        elif action_type in ['bet', 'raise']:
            if amount > player.current_stack:
                return JsonResponse({'success': False, 'error': 'Insufficient stack'})
            player.current_stack -= amount
            player_hand.current_bet += amount
            player_hand.total_invested += amount
            
            # Check if going all-in
            if player.current_stack == 0:
                player_hand.is_all_in = True
            
            # Add to pot
            hand.pot += amount
            player.save()
            player_hand.save()
            hand.current_round_bet = player_hand.current_bet
            hand.players_acted_this_round = {
                str(p.id): False
                for p in hand.game.players.filter(is_active=True)
            }
        
        # Mark player as acted
        hand.players_acted_this_round[str(player.id)] = True
        hand.save()
        
        # Log action with comprehensive info
        log_amount = Decimal('0')
        if action_type == 'fold':
            log_amount = Decimal('0')
        elif action_type == 'check':
            log_amount = Decimal('0')
        elif action_type == 'call':
            log_amount = call_amount if 'call_amount' in locals() else Decimal('0')
        elif action_type in ['bet', 'raise']:
            log_amount = amount
        
        PlayerAction.objects.create(
            hand=hand,
            player=player,
            action_type=action_type,
            amount=log_amount,
        )
        
        # Check if only one player remains (all others folded) - hand ends immediately
        active_non_folded_players = hand.game.players.filter(is_active=True).exclude(
            playerhand__hand=hand,
            playerhand__is_folded=True
        ).distinct()
        
        if active_non_folded_players.count() == 1:
            # Only one player left - they win the hand and get the pot
            winner = active_non_folded_players.first()
            hand.status = 'completed'
            hand.current_player_turn = None  # Clear turn
            hand.winner = winner
            
            # Award pot to winner
            winner.current_stack += hand.pot
            winner.save()
            
            hand.save()
            # Start new hand for next round
            start_new_hand_after_completion(hand.game)
            return JsonResponse({'success': True})

        if all_remaining_players_all_in(hand, active_non_folded_players):
            complete_all_in_showdown(hand)
            return JsonResponse({'success': True})
        
        # Check if round is complete (all non-folded players have acted and have equal bets)
        round_complete = True
        max_bet = Decimal('0')
        
        for p in active_non_folded_players:
            p_hand = hand.player_hands.filter(player=p).first()
            if p_hand:
                max_bet = max(max_bet, p_hand.current_bet)
            
            if not hand.players_acted_this_round.get(str(p.id), False):
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
            reset_betting_round(hand)
            
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
                # Post-flop: small blind acts first
                hand.current_player_turn = hand.small_blind_player
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
                # Post-flop: small blind acts first
                hand.current_player_turn = hand.small_blind_player
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
                # Post-flop: small blind acts first
                hand.current_player_turn = hand.small_blind_player
            elif hand.status == 'river':
                # Hand complete - determine winner
                hand.status = 'completed'
                hand.current_player_turn = None  # Clear turn
                determine_winner(hand)
                # Start new hand for next round
                start_new_hand_after_completion(hand.game)
        
        # Move to next player (only if hand is not completed and stage hasn't just advanced)
        if hand.status != 'completed' and not round_complete:
            active_players = hand.game.players.filter(is_active=True).order_by('seat_number')
            current_index = list(active_players.values_list('id', flat=True)).index(player.id)
            next_index = (current_index + 1) % len(active_players)
            next_player = active_players[next_index]
            
            # Skip folded players
            attempts = 0
            while next_player.playerhand_set.filter(hand=hand, is_folded=True).exists() and attempts < len(active_players):
                next_index = (next_index + 1) % len(active_players)
                next_player = active_players[next_index]
                attempts += 1
            
            hand.current_player_turn = next_player
        elif hand.status == 'completed':
            hand.current_player_turn = None
        
        hand.save()
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_http_methods(["POST"])
@csrf_protect
def get_game_state(request, game_id):
    """Get current game state as JSON"""
    try:
        game = PokerGame.objects.get(id=game_id)
        current_hand = game.hands.order_by('-created_at').first()
        latest_completed_hand = game.hands.filter(status='completed', winner__isnull=False).order_by('-created_at').first()
        last_hand_result = None
        if latest_completed_hand and current_hand and current_hand.status in ['waiting', 'completed']:
            last_hand_result = {
                'winner': latest_completed_hand.winner.user.username,
                'pot': float(latest_completed_hand.pot),
                'hand_id': latest_completed_hand.id,
                'community_cards': latest_completed_hand.community_cards,
            }
        
        players_data = []
        for player in game.players.all():
            player_hand = current_hand.player_hands.filter(player=player).first() if current_hand else None
            is_current_turn = current_hand and current_hand.current_player_turn_id == player.id
            is_winner = current_hand and current_hand.winner_id == player.id
            is_small_blind = current_hand and current_hand.small_blind_player_id == player.id
            is_big_blind = current_hand and current_hand.big_blind_player_id == player.id
            players_data.append({
                'id': player.id,
                'username': player.user.username,
                'seat': player.seat_number,
                'stack': float(player.current_stack),
                'is_active': player.is_active,
                'is_current_turn': is_current_turn,
                'is_winner': is_winner,
                'is_folded': player_hand.is_folded if player_hand else False,
                'current_bet': float(player_hand.current_bet) if player_hand else 0,
                'hole_cards': player_hand.hole_cards if player_hand and (player.user == request.user or (current_hand and current_hand.status == 'completed')) else ['XX', 'XX'],
                'is_small_blind': is_small_blind,
                'is_big_blind': is_big_blind,
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
            'players_ready': current_hand.players_ready if current_hand else {},
            'current_round_bet': float(current_hand.current_round_bet) if current_hand else 0,
            'last_hand_result': last_hand_result,
        })
    except PokerGame.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Game not found'})

@login_required
@require_http_methods(["POST"])
@csrf_protect
def get_hand_actions(request, hand_id):
    """Get action history for a poker hand"""
    try:
        hand = PokerHand.objects.get(id=hand_id)
        actions = hand.actions.select_related('player', 'player__user').order_by('created_at')
        
        actions_data = []
        for action in actions:
            # Get player hand info to check all-in status
            player_hand = hand.player_hands.filter(player=action.player).first()
            is_all_in = player_hand.is_all_in if player_hand else False
            
            actions_data.append({
                'player': action.player.user.username,
                'action_type': action.get_action_type_display(),
                'amount': float(action.amount),
                'timestamp': action.created_at.strftime('%H:%M:%S'),
                'is_all_in': is_all_in
            })
        
        return JsonResponse({
            'success': True,
            'actions': actions_data
        })
    except PokerHand.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Hand not found'})

@login_required
@require_http_methods(["POST"])
@csrf_protect
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
