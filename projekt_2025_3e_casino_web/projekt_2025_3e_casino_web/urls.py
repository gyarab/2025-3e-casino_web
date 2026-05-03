from django.contrib import admin
from django.urls import path, include
from main import views

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', views.home, name='home'),
    path('home/', views.home, name='home_page'),
    path('index/', views.home, name='index'),
    path('signin/', views.signin, name='signin'),

    path('blackjack/', views.blackjack, name='blackjack'),
    path('roulette/', views.roulette, name='roulette'),
    path('api/spin-roulette/', views.spin_roulette, name='spin_roulette'),
    path('shop/', views.shop, name='shop'),
    path('gamemodes/', views.gamemodes, name='gamemodes'),
    path('slots/', views.slots, name='slots'),
    path('battlepass/', views.battlepass, name='battlepass'),
    path('settings/', views.settings, name='settings'),

    path('claim_reward/', views.claim_reward, name='claim_reward'),
    path('update_balance/', views.update_balance, name='update_balance'),

    path('api/spin-slot/', views.spin_slot, name='spin_slot'),
    path('api/spin/', views.spin_slot, name='spin_slot_alt'),
    path('api/spin-roulette/', views.spin_roulette, name='spin_roulette'),

    path('api/battle-pass/', views.get_battle_pass_data, name='battle_pass_data'),
    path('api/battlepass/', views.get_battle_pass_data, name='battlepass_data'),
    path('api/quests/', views.get_quests_data, name='quests_data'),

    # Poker URLs
    path('poker/', views.poker_lobby, name='poker_lobby'),
    path('poker/create/', views.create_poker_game, name='create_poker_game'),
    path('poker/game/<int:game_id>/', views.poker_game, name='poker_game'),
    path('poker/game/<int:game_id>/join/', views.join_poker_game, name='join_poker_game'),
    path('poker/game/<int:game_id>/start-hand/', views.start_poker_hand, name='start_poker_hand'),
    path('poker/hand/<int:hand_id>/advance-stage/', views.advance_stage, name='advance_stage'),
    path('poker/game/<int:game_id>/state/', views.get_game_state, name='get_game_state'),
    path('poker/game/<int:game_id>/leave/', views.leave_poker_game, name='leave_poker_game'),
    path('poker/hand/<int:hand_id>/action/', views.player_action, name='player_action'),

    path('accounts/', include('allauth.urls')),
]
