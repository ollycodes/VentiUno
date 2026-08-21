# ❤️ VentiUno

VentiUno is a Django-based Blackjack webapp. No account, no login — open it and play. Game state lives in your browser session, so nothing about you is stored.

## ♠️ Features
- **No accounts.** Just play — your hand, bank, and bet live in your session.
- **htmx-driven table.** Hits, stands, bets, and bust/win screens swap in place for an SPA-like feel without a JS framework.
- **Deck styles.** Pick your card-back design (red, frog, fish, and more) on the Options page.
- **Leaderboard.** Go broke with a top-10 score and you can add your name to the global leaderboard.

## ♦️ Installation & Use
This project uses [uv](https://docs.astral.sh/uv/) to manage the virtual environment and dependencies.

1. Clone the repository.
   ```shell
   git clone git@github.com:ollycodes/VentiUno.git
   cd VentiUno
   ```

2. Install dependencies (creates `.venv` automatically).
   ```shell
   uv venv
   uv pip install -r requirements.txt
   ```

3. Set up your local environment. Copy `.env.example` to `.env` and fill in a real secret key:
   ```shell
   cp .env.example .env
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```
   Paste the generated value in as `SECRET_KEY` in `.env`. `.env` is loaded automatically and is gitignored, so it's safe to keep secrets there.

4. Migrate and run.
   ```shell
   uv run manage.py migrate
   uv run manage.py runserver
   ```
   Open in browser: http://127.0.0.1:8000/

5. (Optional) To use the Django admin at `/admin/` — e.g. to moderate leaderboard entries — create a superuser:
   ```shell
   uv run manage.py createsuperuser
   ```

## ♣️ Credits
- [Playing Cards](https://tekeye.uk/playing_cards/svg-playing-cards)
