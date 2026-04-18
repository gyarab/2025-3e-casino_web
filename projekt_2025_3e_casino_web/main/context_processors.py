def battlepass_context(request):
    if request.user.is_authenticated:
        try:
            battlepass = request.user.battlepass
            unclaimed_count = sum(1 for l in range(1, battlepass.level + 1) if l not in battlepass.claimed_rewards)
        except:
            unclaimed_count = 0
    else:
        unclaimed_count = 0
    return {'unclaimed_count': unclaimed_count}