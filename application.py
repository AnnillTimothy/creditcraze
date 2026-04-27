# application.py
import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify
from flask_ckeditor import CKEditor
from werkzeug.utils import secure_filename
from flask_migrate import Migrate

from models import db, CreditCard, BlogPost, SiteSettings
from forms import CreditCardForm, BlogPostForm, ComparisonForm, SiteSettingsForm
from context_processors import choices

# ──────────────────────────────────────────────────────────────
# Config
# ──────────────────────────────────────────────────────────────
load_dotenv()

# OpenAI (optional)
try:
    from openai import OpenAI as _OpenAI
    _oai_key = os.getenv("OPENAI_API_KEY")
    openai_client = _OpenAI(api_key=_oai_key) if _oai_key else None
except ImportError:
    openai_client = None

# Mistral (optional, preferred)
try:
    from mistralai import Mistral as _Mistral
    _mis_key = os.getenv("MISTRAL_API_KEY")
    mistral_client = _Mistral(api_key=_mis_key) if _mis_key else None
except ImportError:
    mistral_client = None

application = Flask(__name__, static_folder="static", template_folder="templates")
ckeditor = CKEditor(application)

application.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL", "sqlite:///example.db")
application.config['SECRET_KEY'] = os.getenv("SECRET_KEY", os.urandom(24))
application.config['UPLOAD_FOLDER'] = os.getenv("UPLOAD_FOLDER", "static/uploads")
application.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024

os.makedirs(application.config['UPLOAD_FOLDER'], exist_ok=True)

db.init_app(application)
migrate = Migrate(application, db)

with application.app_context():
    db.create_all()

# ──────────────────────────────────────────────────────────────
# Context processors
# ──────────────────────────────────────────────────────────────
@application.context_processor
def inject_choices():
    try:
        return choices()
    except Exception:
        return {}

@application.context_processor
def inject_site_settings():
    try:
        settings = SiteSettings.query.first()
        if not settings:
            settings = SiteSettings()
        return {'site_settings': settings}
    except Exception:
        return {'site_settings': None}

# ──────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────
def join_if_list(val):
    if not val:
        return ""
    if isinstance(val, (list, tuple)):
        return ",".join(str(x).strip() for x in val if x is not None)
    return str(val)

def safe_filename_save(fileobj):
    if not fileobj:
        return None
    filename = secure_filename(fileobj.filename)
    if not filename:
        return None
    dest = os.path.join(application.config['UPLOAD_FOLDER'], filename)
    fileobj.save(dest)
    return filename

def gen_slug(text, max_len=100):
    if not text:
        return "post"
    slug = text.strip().lower().replace(" ", "-")
    return slug[:max_len]

def get_card_context_prompt():
    try:
        cards = CreditCard.query.order_by(CreditCard.name).limit(20).all()
        if cards:
            lines = []
            for c in cards:
                fee  = f"annual fee R{c.annual_fee:.0f}" if c.annual_fee is not None else "no annual fee info"
                rate = f"interest {c.interest_rate}" if c.interest_rate else ""
                rwd  = f"rewards: {c.reward_type}" if c.reward_type else ""
                lines.append(f"- {c.name} ({c.banks}): {fee}, {rate}, {rwd}")
            card_block = "\n".join(lines)
            return (
                "You are Credibot, a friendly AI assistant specialising in South African credit cards. "
                "Help users compare cards, understand fees, and find their best match. "
                "Here are some cards in our database:\n" + card_block + "\n"
                "Be concise, helpful, and always recommend users verify details with the issuing bank."
            )
    except Exception:
        pass
    return (
        "You are Credibot, a friendly AI assistant specialising in South African credit cards. "
        "Help users compare, understand, and choose the best credit card for their needs. "
        "Be concise, helpful, and always recommend users verify details with the issuing bank."
    )

def call_ai(messages, max_tokens=350):
    """Try Mistral first, fall back to GPT-4o-mini."""
    if mistral_client:
        try:
            resp = mistral_client.chat.complete(
                model="mistral-small-latest",
                messages=messages,
                max_tokens=max_tokens,
            )
            return resp.choices[0].message.content
        except Exception:
            pass

    if openai_client:
        try:
            resp = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.7,
                max_tokens=max_tokens,
            )
            return resp.choices[0].message.content
        except Exception as e:
            return f"Credibot error: {e}"

    return "Credibot is temporarily unavailable — no AI API key is configured."

def _get_cp():
    try:
        return choices()
    except Exception:
        return {}

# ──────────────────────────────────────────────────────────────
# Error handlers
# ──────────────────────────────────────────────────────────────
@application.errorhandler(404)
def page_not_found(e):
    return render_template('error.html'), 404

# ──────────────────────────────────────────────────────────────
# Home
# ──────────────────────────────────────────────────────────────
@application.route('/')
def home():
    featured = CreditCard.query.filter_by(is_featured=True).limit(3).all()
    if not featured:
        featured = CreditCard.query.limit(3).all()
    blog_posts = BlogPost.query.order_by(BlogPost.id.desc()).limit(3).all()
    return render_template('index.html', credit_cards=featured, blog_posts=blog_posts)

# ──────────────────────────────────────────────────────────────
# Cards
# ──────────────────────────────────────────────────────────────
@application.route('/card-reviews')
def cardreviews():
    q             = request.args.get('q', '').strip()
    bank_filter   = request.args.get('bank', '').strip()
    cat_filter    = request.args.get('category', '').strip()
    tier_filter   = request.args.get('tier', '').strip()

    query = CreditCard.query
    if q:
        query = query.filter(CreditCard.name.ilike(f'%{q}%'))
    if bank_filter:
        query = query.filter(CreditCard.banks.ilike(f'%{bank_filter}%'))
    if cat_filter:
        query = query.filter(CreditCard.categories.ilike(f'%{cat_filter}%'))
    if tier_filter:
        query = query.filter(CreditCard.tier == tier_filter)

    credit_cards = query.order_by(CreditCard.name).all()

    # sidebar lists
    all_banks = sorted(set(
        b.strip()
        for card in CreditCard.query.all()
        for b in (card.banks or '').split(',')
        if b.strip()
    ))

    return render_template(
        'card-reviews.html',
        credit_cards=credit_cards,
        banks=all_banks,
        q=q,
        bank_filter=bank_filter,
        category_filter=cat_filter,
        tier_filter=tier_filter,
    )

@application.route('/cards')
def all_cards():
    return redirect(url_for('cardreviews'))

@application.route('/card-details/<int:card_id>')
def card_details(card_id):
    card = CreditCard.query.get_or_404(card_id)
    return render_template('card-details.html', card=card)

@application.route('/compare', methods=['GET', 'POST'])
def compare():
    form = ComparisonForm()
    all_cards = CreditCard.query.order_by(CreditCard.name).all()
    placeholder = [('', '— Select a card —')]
    form.card1.choices = placeholder + [(c.id, c.name) for c in all_cards]
    form.card2.choices = placeholder + [(c.id, c.name) for c in all_cards]
    form.card3.choices = placeholder + [(c.id, c.name) for c in all_cards]

    if form.validate_on_submit():
        selected = []
        for fname in ('card1', 'card2', 'card3'):
            val = getattr(form, fname).data
            if val:
                c = CreditCard.query.get(val)
                if c:
                    selected.append(c)
        return render_template('comparison.html', form=form, cards=selected)
    return render_template('comparison.html', form=form, cards=[])

# ──────────────────────────────────────────────────────────────
# AI endpoints
# ──────────────────────────────────────────────────────────────
@application.route('/ai_card_summary/<int:card_id>')
def ai_card_summary(card_id):
    card = CreditCard.query.get_or_404(card_id)
    prompt = (
        f"Give a concise 3-sentence AI summary of the {card.name} credit card by {card.banks}. "
        f"Key details: interest rate {card.interest_rate or 'N/A'}, "
        f"annual fee R{card.annual_fee or 0:.0f}, "
        f"rewards: {card.reward_type or 'none'}, "
        f"tier: {card.tier or 'Standard'}. "
        f"Who is this card best for? Keep it under 80 words."
    )
    messages = [
        {"role": "system", "content": "You are a concise credit card analyst for a South African fintech platform."},
        {"role": "user", "content": prompt},
    ]
    summary = call_ai(messages, max_tokens=150)
    return jsonify({"summary": summary})

@application.route('/credibot')
def credibot():
    session['conversation'] = []
    return render_template('credibot.html', conversation=[])

@application.route('/get_response', methods=['POST'])
def get_response():
    user_input = request.form.get('user_input', '').strip()
    if not user_input:
        return redirect(url_for('credibot'))

    conversation = session.get('conversation', [])
    conversation.append({"role": "user", "content": user_input})

    system_prompt = get_card_context_prompt()
    messages = [{"role": "system", "content": system_prompt}] + conversation
    reply = call_ai(messages, max_tokens=300)

    conversation.append({"role": "assistant", "content": reply})
    session['conversation'] = conversation

    return render_template('credibot.html', conversation=conversation)

# ──────────────────────────────────────────────────────────────
# Articles / blog
# ──────────────────────────────────────────────────────────────
@application.route('/articles')
def articles():
    blog_posts = BlogPost.query.order_by(BlogPost.id.desc()).all()
    return render_template('articles.html', blog_posts=blog_posts)

@application.route('/article/<int:post_id>')
def article(post_id):
    blog_post = BlogPost.query.get_or_404(post_id)
    return render_template('blog-details.html', blog_post=blog_post)

@application.route('/news')
def news():
    posts = BlogPost.query.order_by(BlogPost.id.desc()).limit(10).all()
    return render_template('blog.html', posts=posts)

@application.route('/blog')
def blog():
    return redirect(url_for('news'))

# ──────────────────────────────────────────────────────────────
# Company pages
# ──────────────────────────────────────────────────────────────
@application.route('/about')
def about():
    return render_template('about.html')

@application.route('/contact')
def contact():
    return render_template('contact.html')

@application.route('/mission')
def mission():
    return redirect(url_for('about'))

@application.route('/partnerships')
def partnerships():
    return redirect(url_for('contact'))

@application.route('/sponsors')
def sponsors():
    return redirect(url_for('contact'))

# ──────────────────────────────────────────────────────────────
# Legal
# ──────────────────────────────────────────────────────────────
@application.route('/terms')
def terms():
    return render_template('terms.html')

@application.route('/privacy')
def privacy():
    return render_template('privacy.html')

@application.route('/disclaimer')
def disclaimer():
    return render_template('disclaimer.html')

# ──────────────────────────────────────────────────────────────
# Dashboard / admin
# ──────────────────────────────────────────────────────────────
@application.route('/dashboard')
def dashboard():
    total_cards = CreditCard.query.count()
    total_posts = BlogPost.query.count()
    featured    = CreditCard.query.filter_by(is_featured=True).limit(10).all()
    return render_template('dashboard.html',
                           total_cards=total_cards,
                           total_posts=total_posts,
                           featured=featured)

@application.route('/dashboard/add_card', methods=['GET', 'POST'])
def dashboard_add_card():
    form = CreditCardForm()
    cp = _get_cp()

    form.banks.choices      = [(b, b) for b in cp.get('banks', [])]
    form.categories.choices = [(c, c) for c in cp.get('categories', [])]
    form.card_type.choices  = [(t, t) for t in cp.get('card_types', [])]

    if form.validate_on_submit():
        photo_filename = safe_filename_save(form.photo.data) if form.photo.data and form.photo.data.filename else None
        new_card = CreditCard(
            name              = form.name.data,
            banks             = join_if_list(form.banks.data),
            card_type         = form.card_type.data,
            interest_rate     = form.interest_rate.data,
            interest_free_days= form.interest_free_days.data,
            monthly_fee       = float(form.monthly_fee.data) if form.monthly_fee.data is not None else None,
            annual_fee        = float(form.annual_fee.data)  if form.annual_fee.data  is not None else None,
            min_income        = form.min_income.data,
            limit_range       = form.limit_range.data,
            reward_type       = form.reward_type.data,
            rewards_summary   = form.rewards_summary.data,
            travel_features   = form.travel_features.data,
            lifestyle_features= form.lifestyle_features.data,
            insurance         = form.insurance.data,
            discounts         = form.discounts.data,
            requirements      = form.requirements.data,
            benefits          = form.benefits.data,
            risks             = form.risks.data,
            pros              = form.pros.data,
            cons              = form.cons.data,
            categories        = join_if_list(form.categories.data),
            tier              = form.tier.data or None,
            is_featured       = bool(form.is_featured.data),
            photo             = photo_filename,
            brochure_link     = form.brochure_link.data or None,
        )
        db.session.add(new_card)
        db.session.commit()
        flash("Card added successfully", "success")
        return redirect(url_for('dashboard'))

    return render_template('dashboard_add_card.html', form=form, edit_mode=False)

@application.route('/dashboard/add_post', methods=['GET', 'POST'])
def dashboard_add_post():
    form = BlogPostForm()
    cp = _get_cp()
    form.category.choices = [(c, c) for c in cp.get('categories', [])]

    if form.validate_on_submit():
        slug = form.slug.data.strip() if form.slug.data else gen_slug(form.title.data)
        post = BlogPost(
            title        = form.title.data,
            subtitle     = form.subtitle.data,
            introduction = form.introduction.data,
            slug         = slug,
            category     = form.category.data,
            content      = form.content.data,
        )
        if form.img1.data and form.img1.data.filename:
            post.img1 = safe_filename_save(form.img1.data)
        if form.img2.data and form.img2.data.filename:
            post.img2 = safe_filename_save(form.img2.data)
        if form.img3.data and form.img3.data.filename:
            post.img3 = safe_filename_save(form.img3.data)
        db.session.add(post)
        db.session.commit()
        flash("Post published", "success")
        return redirect(url_for('dashboard'))

    return render_template('dashboard_add_post.html', form=form)

@application.route('/dashboard/settings', methods=['GET', 'POST'])
def dashboard_settings():
    settings = SiteSettings.query.first()
    if not settings:
        settings = SiteSettings()
        db.session.add(settings)
        db.session.commit()

    form = SiteSettingsForm(obj=settings)

    if form.validate_on_submit():
        settings.site_name      = form.site_name.data or 'CreditCraze'
        settings.footer_tagline = form.footer_tagline.data
        settings.contact_email  = form.contact_email.data
        settings.contact_phone  = form.contact_phone.data
        settings.contact_address= form.contact_address.data
        settings.facebook_url   = form.facebook_url.data
        settings.twitter_url    = form.twitter_url.data
        settings.instagram_url  = form.instagram_url.data
        if form.logo.data and form.logo.data.filename:
            settings.logo_filename = safe_filename_save(form.logo.data)
        db.session.commit()
        flash("Settings saved", "success")
        return redirect(url_for('dashboard_settings'))

    return render_template('site_settings.html', form=form, settings=settings)

@application.route('/dashboard/delete_card/<int:card_id>', methods=['POST'])
def dashboard_delete_card(card_id):
    card = CreditCard.query.get_or_404(card_id)
    db.session.delete(card)
    db.session.commit()
    flash("Card deleted", "success")
    return redirect(url_for('dashboard'))

@application.route('/dashboard/delete_post/<int:post_id>', methods=['POST'])
def dashboard_delete_post(post_id):
    post = BlogPost.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    flash("Post deleted", "success")
    return redirect(url_for('dashboard'))

# ──────────────────────────────────────────────────────────────
# Dev helper
# ──────────────────────────────────────────────────────────────
if __name__ == '__main__':
    with application.app_context():
        print("\n--- Routes ---")
        for rule in sorted(application.url_map.iter_rules(), key=lambda r: r.rule):
            print(f"  {rule.endpoint:28} {rule.rule}")
        print("--------------\n")
    application.run(debug=True)
