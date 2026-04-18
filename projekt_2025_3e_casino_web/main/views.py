
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import UserProfile

@login_required
def blackjack(request):
    profile = request.user.userprofile
    context = {
        'balance': profile.balance,
    }
    return render(request, 'main/blackjack.html', context)

@login_required
def home(request):
    profile = request.user.userprofile
    context = {
        'balance': profile.balance,
        'user': request.user,
    }
    return render(request, 'main/home.html', context)

@login_required
def buy_money(request):
    if request.method == 'POST':
        amount = int(request.POST.get('amount', 0))
        if amount in [10, 100, 1000]:
            profile = request.user.userprofile
            profile.balance += amount
            profile.save()
            messages.success(request, f'Úspěšně jste zakoupili {amount} kreditů!')
        else:
            messages.error(request, 'Neplatná částka.')
    return redirect('home')

@login_required
def update_balance(request):
    if request.method == 'POST':
        new_balance = float(request.POST.get('balance', 0))
        profile = request.user.userprofile
        profile.balance = new_balance
        profile.save()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

def signin(request):
    return render(request, 'main/signin.html')

def gamemodes(request):
    return render(request, 'main/gamemodes.html')

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

    profile = request.user.userprofile
    context = {
        'user': request.user,
    }
    return render(request, 'main/shop.html', context)

