# Credit Compass

Credit Compass is a Flask web app for discovering, comparing, and understanding South African credit cards with a premium dark-finance experience, Compass AI guidance, and launch-ready deployment defaults.

## Highlights

- Credit Compass rebrand with custom SVG logo and premium navigation-inspired UI
- GSAP-powered motion, scroll reveals, orbit animation, and interactive card tilt
- Dynamic SEO metadata, Open Graph tags, JSON-LD, sitemap, robots.txt, and web manifest
- Consent-aware cookie controls for essential, analytics, and personalisation categories
- Credit card browsing, detail pages, side-by-side comparison, and AI summaries
- Seed script with launch-ready card data for ABSA, Nedbank, FNB, Discovery, Woolworths, Standard Bank, Diners, Investec, and RMB
- EC2-friendly Gunicorn setup with proxy support

## Project structure

- `/application.py` - Flask app, routes, SEO helpers, legal routes, sitemap, and deployment config
- `/models.py` - SQLAlchemy models
- `/templates` - Jinja templates for marketing, comparison, content, and admin screens
- `/static/css/style.css` - Credit Compass design system
- `/static/js/main.js` - GSAP interactions, cookie controls, counters, and UI effects
- `/seed_credit_cards.py` - Database seed script for major South African issuers

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # if you create one
python seed_credit_cards.py
python application.py
```

If you do not configure `OPENAI_API_KEY` or `MISTRAL_API_KEY`, Compass AI falls back to a friendly unavailable message rather than crashing.

## Required environment variables

| Variable | Purpose |
| --- | --- |
| `SECRET_KEY` | Flask session signing |
| `DATABASE_URL` | SQLAlchemy database connection string |
| `SITE_URL` | Canonical production URL used for sitemap and SEO |
| `UPLOAD_FOLDER` | Optional upload target for admin assets |
| `SESSION_COOKIE_SECURE` | Set to `true` in production behind HTTPS |
| `OPENAI_API_KEY` | Optional AI fallback provider |
| `MISTRAL_API_KEY` | Optional preferred AI provider |

## Seed the issuer catalogue

Populate the database with the included issuer set:

```bash
python seed_credit_cards.py
```

The script upserts card records, so it can be safely re-run after edits.

## Production / EC2 launch

Install dependencies, configure environment variables, and run Gunicorn:

```bash
pip install -r requirements.txt
python seed_credit_cards.py
GUNICORN_CMD_ARGS="--bind 0.0.0.0:8000 --workers 3 --threads 2 --timeout 120" gunicorn application:application
```

### Recommended Nginx proxy

Proxy traffic to `127.0.0.1:8000` and terminate TLS at Nginx or your load balancer. The app already uses `ProxyFix` so canonical URLs, secure cookies, and request scheme handling work correctly behind the proxy.

### systemd example

```ini
[Unit]
Description=Credit Compass
After=network.target

[Service]
User=ec2-user
WorkingDirectory=/var/www/creditcraze
Environment="SECRET_KEY=change-me"
Environment="DATABASE_URL=sqlite:////var/www/creditcraze/instance/example.db"
Environment="SITE_URL=https://www.creditcompass.co.za"
Environment="SESSION_COOKIE_SECURE=true"
ExecStart=/usr/bin/env gunicorn --bind 0.0.0.0:8000 --workers 3 --threads 2 --timeout 120 application:application
Restart=always

[Install]
WantedBy=multi-user.target
```

## SEO, cookies, and compliance notes

- Route-aware SEO metadata is generated in `application.py`
- `robots.txt`, `sitemap.xml`, and `manifest.webmanifest` are served by Flask
- Cookie preferences are stored in browser local storage and optional categories are off until consent
- Legal copy for privacy, terms, and disclaimer is included in the templates and should be reviewed before launch
- Product pricing and issuer benefits change often, so the bank remains the source of truth

## Validation

Recommended checks:

```bash
python -m compileall application.py context_processors.py forms.py models.py seed_credit_cards.py
python - <<'PY'
from application import application
client = application.test_client()
for path in ['/', '/card-reviews', '/compare', '/about', '/privacy', '/terms', '/disclaimer', '/robots.txt', '/sitemap.xml']:
    response = client.get(path)
    print(path, response.status_code)
PY
```
