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

    path('accounts/', include('allauth.urls')),
]
