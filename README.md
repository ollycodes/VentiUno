# ❤️ VentiUno

VentiUno is a Django-based Blackjack webapp.

## ♠️ Preview
![Profile Preview Image](https://github.com/ollycodes/VentiUno/raw/main/blackjack/static/img/new_game.png)
![Betting Preview Image](https://github.com/ollycodes/VentiUno/raw/main/blackjack/static/img/bet.png)
![Game Preview Image](https://github.com/ollycodes/VentiUno/raw/main/blackjack/static/img/hand.png)

## ♦️ Instalation & Use
1. Clone repository.
```shell
git clone git@github.com:ollycodes/VentiUno.git
cd VentiUno
```

2. create python venv & activate
```shell
python3 -m venv .venv
source .venv/bin/activate
```

3. pip install requirements & set Django secret key
```shell
pip install -r requirements.txt
new_secret_key=$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')  
echo "SECRET_KEY=\"$new_secret_key\"\nDEBUG=\"True\"" >> .env
```

4. Run
```shell
python manage.py runserver
```
- Open in Browser: http://127.0.0.1:8000/

## ♣️ Credits
- [Playing Cards](https://tekeye.uk/playing_cards/svg-playing-cards)
