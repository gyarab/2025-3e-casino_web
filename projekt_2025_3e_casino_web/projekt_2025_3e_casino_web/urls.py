"""
URL configuration for projekt_2025_3e_casino_web project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
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
    path('shop/', views.shop, name='shop'),
    path('gamemodes/', views.gamemodes, name='gamemodes'),
    path('slots/', views.slots, name='slots'),
    path('battlepass/', views.battlepass, name='battlepass'),
    path('claim_reward/', views.claim_reward, name='claim_reward'),
    path('update_balance/', views.update_balance, name='update_balance'),
    path('api/spin-slot/', views.spin_slot, name='spin_slot'),
    path('api/spin/', views.spin_slot, name='spin_slot_alt'),
    path('api/battle-pass/', views.get_battle_pass_data, name='battle_pass_data'),
    path('api/quests/', views.get_quests_data, name='quests_data'),
    path('accounts/', include('allauth.urls')),
]



