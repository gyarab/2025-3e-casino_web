# 2025-3e-casino_web
WEBSITE LINK: casinoweb.duckdns.org

## How to Run

python -m venv venv

venv\Scripts\activate

pip install -r requirements.txt

cd projekt_2025_3e_casino_web

python manage.py migrate

python manage.py seed_quests

python manage.py runserver
```