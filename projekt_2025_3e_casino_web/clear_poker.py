import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projekt_2025_3e_casino_web.settings')
django.setup()

from main.models import PokerGame

deleted_count, _ = PokerGame.objects.all().delete()
print(f'✓ Deleted {deleted_count} poker-related records')
