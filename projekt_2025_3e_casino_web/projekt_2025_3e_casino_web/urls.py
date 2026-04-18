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
from main.views import signin, home, gamemodes, slots, spin_slot, get_battle_pass_data, get_quests_data
from main import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('home/', home, name='home'),
    path('gamemodes/', gamemodes, name='gamemodes'),
    path('blackjack/', views.blackjack, name='blackjack'),
    path('battlepass/', views.battlepass, name='battlepass'),
    path('claim_reward/', views.claim_reward, name='claim_reward'),
    path('slots/', slots, name='slots'),
    path('api/spin/', spin_slot, name='spin_slot'),
    path('api/battlepass/', get_battle_pass_data, name='get_battle_pass'),
    path('api/quests/', get_quests_data, name='get_quests'),
    path('accounts/', include('allauth.urls')),
]
