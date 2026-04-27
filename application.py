# application.py
import os
from dotenv import load_dotenv
from flask import Flask, render_template, url_for, request, session, redirect, flash
from flask_ckeditor import CKEditor
from werkzeug.utils import secure_filename
from openai import OpenAI

# project imports (your files)
from models import db, CreditCard, BlogPost
from forms import CreditCardForm, BlogPostForm, ComparisonForm
from context_processors import choices

# migrations
from flask_migrate import Migrate

# ---------------------------------------------------------------------
# Basic app config
# ---------------------------------------------------------------------
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

application = Flask(__name__, static_folder="static", template_folder="templates")
ckeditor = CKEditor(application)

application.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL", "sqlite:///example.db")
application.config['SECRET_KEY'] = os.getenv("SECRET_KEY", os.urandom(24))
application.config['UPLOAD_FOLDER'] = os.getenv("UPLOAD_FOLDER", "static/uploads")
application.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max file size (adjust if needed)

# ensure upload folder
os.makedirs(application.config['UPLOAD_FOLDER'], exist_ok=True)

# initialize DB + migrations
db.init_app(application)
migrate = Migrate(application, db)

with application.app_context():
    db.create_all()

# OpenAI key (optional - keep but won't break without it)

# expose choices to all templates
@application.context_processor
def inject_choices():
    try:
        return choices()
    except Exception:
        # safe fallback if context processor raises
        return {}

# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------
def join_if_list(maybe_list):
    if not maybe_list:
        return ""
    if isinstance(maybe_list, (list, tuple)):
        return ",".join(str(x).strip() for x in maybe_list if x is not None)
    return str(maybe_list)

def safe_filename_save(fileobj):
    """Save uploaded file and return filename or None."""
    if not fileobj:
        return None
    filename = secure_filename(fileobj.filename)
    if filename == "":
        return None
    dest = os.path.join(application.config['UPLOAD_FOLDER'], filename)
    fileobj.save(dest)
    return filename

def gen_slug(text, max_len=100):
    if not text:
        return None
    slug = text.strip().lower().replace(" ", "-")
    return slug[:max_len]

# ---------------------------------------------------------------------
# Home + misc
# ---------------------------------------------------------------------
@application.route('/')
def home():
    # featured cards first, fallback to first 3
    featured = CreditCard.query.filter_by(is_featured=True).limit(3).all()
    if not featured:
        featured = CreditCard.query.limit(3).all()
    blog_posts = BlogPost.query.order_by(BlogPost.id.desc()).limit(3).all() #should also have a boolean called featured
    return render_template('index.html', credit_cards=featured, blog_posts=blog_posts)

@application.errorhandler(404)
def page_not_found(e):
    return render_template('error.html'), 404


@application.route('/test')
def test():
    return render_template('card-comparison.html')

# ---------------------------------------------------------------------
# Credit card routes
# ---------------------------------------------------------------------
@application.route('/card-reviews')
def cardreviews():
    credit_cards = CreditCard.query.order_by(CreditCard.name).all() # should actually be calling for blog model - reviews are articles
    return render_template('card-reviews.html', credit_cards=credit_cards)

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
    credit_cards = CreditCard.query.order_by(CreditCard.name).all()
    # populate choices
    form.card1.choices = [(c.id, c.name) for c in credit_cards]
    form.card2.choices = [(c.id, c.name) for c in credit_cards]
    form.card3.choices = [(c.id, c.name) for c in credit_cards]

    if form.validate_on_submit():
        selected = []
        for field_name in ('card1', 'card2', 'card3'):
            val = getattr(form, field_name).data
            if val:
                selected.append(CreditCard.query.get(val))
        return render_template('comparison.html', form=form, cards=selected)
    return render_template('comparison.html', form=form)

# ---------------------------------------------------------------------
# Articles / blog
# ---------------------------------------------------------------------
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

# ---------------------------------------------------------------------
# Company / static pages
# ---------------------------------------------------------------------
@application.route('/mission')
def mission():
    return render_template('mission.html')

@application.route('/about')
def about():
    return render_template('about.html')

@application.route('/partnerships')
def partnerships():
    return render_template('partnerships.html')

@application.route('/sponsors')
def sponsors():
    return render_template('sponsors.html')

@application.route('/contact')
def contact():
    return render_template('contact.html')

# ---------------------------------------------------------------------
# Legal
# ---------------------------------------------------------------------
@application.route('/terms')
def terms():
    return render_template('terms.html')

@application.route('/privacy')
def privacy():
    return render_template('privacy.html')

@application.route('/disclaimer')
def disclaimer():
    return render_template('disclaimer.html')

# ---------------------------------------------------------------------
# Dashboard / admin (simple - protect later)
# ---------------------------------------------------------------------
@application.route('/dashboard')
def dashboard():
    total_cards = CreditCard.query.count()
    total_posts = BlogPost.query.count()
    featured = CreditCard.query.filter_by(is_featured=True).limit(3).all()
    return render_template('dashboard.html', total_cards=total_cards, total_posts=total_posts, featured=featured)

@application.route('/dashboard/add_card', methods=['GET', 'POST'])
def dashboard_add_card():
    form = CreditCardForm()

    # set dynamic choices before validation
    cp = {}
    try:
        cp = choices()
    except Exception:
        cp = {}
    banks_choices = cp.get('banks', [])
    categories_choices = cp.get('categories', [])
    card_types_choices = cp.get('card_types', [])

    form.banks.choices = [(b, b) for b in banks_choices]
    form.categories.choices = [(c, c) for c in categories_choices]
    form.card_type.choices = [(t, t) for t in card_types_choices]

    if form.validate_on_submit():
        # multi-selects -> CSV
        banks_csv = join_if_list(form.banks.data)
        categories_csv = join_if_list(form.categories.data)

        # save uploaded photo
        photo_filename = safe_filename_save(form.photo.data) if getattr(form, "photo", None) else None

        new_card = CreditCard(
            name=form.name.data,
            banks=banks_csv,
            card_type=form.card_type.data,
            interest_rate=form.interest_rate.data,
            interest_free_days=form.interest_free_days.data,
            monthly_fee=float(form.monthly_fee.data) if form.monthly_fee.data is not None else None,
            annual_fee=float(form.annual_fee.data) if form.annual_fee.data is not None else None,
            min_income=form.min_income.data,
            limit_range=form.limit_range.data,
            reward_type=form.reward_type.data if hasattr(form, "reward_type") else None,
            rewards_summary=form.rewards_summary.data if hasattr(form, "rewards_summary") else None,
            travel_features=form.travel_features.data,
            lifestyle_features=form.lifestyle_features.data,
            insurance=form.insurance.data,
            discounts=form.discounts.data,
            requirements=form.requirements.data,
            benefits=form.benefits.data,
            risks=form.risks.data,
            pros=form.pros.data,
            cons=form.cons.data,
            categories=categories_csv,
            tier=form.tier.data if hasattr(form, "tier") else None,
            is_featured=bool(form.is_featured.data) if hasattr(form, "is_featured") else False,
            photo=photo_filename,
            brochure_link=form.brochure_link.data if hasattr(form, "brochure_link") else None
        )

        db.session.add(new_card)
        db.session.commit()
        flash("Card added successfully", "success")
        return redirect(url_for('dashboard'))

    return render_template('dashboard_add_card.html', form=form)

@application.route('/dashboard/add_post', methods=['GET', 'POST'])
def dashboard_add_post():
    form = BlogPostForm()
    # dynamic categories for posts (re-use site categories fallback)
    cp = {}
    try:
        cp = choices()
    except Exception:
        cp = {}
    post_categories = cp.get('categories', [])
    form.category.choices = [(c, c) for c in post_categories]

    if form.validate_on_submit():
        slug = form.slug.data.strip() if getattr(form, "slug", None) and form.slug.data else gen_slug(form.title.data)
        post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            introduction=form.introduction.data,
            slug=slug,
            category=form.category.data,
            content=form.content.data
        )

        # save images if provided
        if getattr(form, "img1", None) and form.img1.data:
            post.img1 = safe_filename_save(form.img1.data)
        if getattr(form, "img2", None) and form.img2.data:
            post.img2 = safe_filename_save(form.img2.data)
        if getattr(form, "img3", None) and form.img3.data:
            post.img3 = safe_filename_save(form.img3.data)

        db.session.add(post)
        db.session.commit()
        flash("Post published", "success")
        return redirect(url_for('dashboard'))

    return render_template('dashboard_add_post.html', form=form)

# delete card (basic)
@application.route('/dashboard/delete_card/<int:card_id>', methods=['POST'])
def dashboard_delete_card(card_id):
    card = CreditCard.query.get_or_404(card_id)
    db.session.delete(card)
    db.session.commit()
    flash("Card deleted", "success")
    return redirect(url_for('dashboard'))

# delete post
@application.route('/dashboard/delete_post/<int:post_id>', methods=['POST'])
def dashboard_delete_post(post_id):
    post = BlogPost.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    flash("Post deleted", "success")
    return redirect(url_for('dashboard'))

# ---------------------------------------------------------------------
# AI assistant (minimal working)
# ---------------------------------------------------------------------
@application.route('/credibot')
def credibot():
    session['conversation'] = []
    return render_template('credibot.html')


@application.route('/get_response', methods=['POST'])
def get_response():
    user_input = request.form.get('user_input', '').strip()
    conversation = session.get('conversation', [])
    conversation.append({"role": "user", "content": user_input})

    assistant_text = ""

    # If the key is missing, fallback message
    if not os.getenv("OPENAI_API_KEY"):
        assistant_text = "Credibot is temporarily unavailable (no API key configured)."
    else:
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are Credibot, a friendly AI assistant that helps users understand and compare credit cards."},
                    *conversation
                ],
                temperature=0.7,
                max_tokens=200
            )
            assistant_text = response.choices[0].message.content

        except Exception as e:
            assistant_text = f"Credibot error: {str(e)}"

    conversation.append({"role": "assistant", "content": assistant_text})
    session['conversation'] = conversation

    return render_template('credibot.html', conversation=conversation)


# ---------------------------------------------------------------------
# Backwards-compatibility aliases (templates may use old names)
# ---------------------------------------------------------------------
# ----- Backwards-compatibility aliases for templates -----
# Templates still call 'blog' -> redirect to new 'news'
@application.route('/blog')
def blog():
    return redirect(url_for('news'))


# Templates might call 'card-details/<id>' -> redirect to new card details route
@application.route('/card-details/<int:card_id>')
def carddetails(card_id):
    return redirect(url_for('card_details', card_id=card_id))

# ---------------------------------------------------------------------
# Debug helper: print routes on launch
# ---------------------------------------------------------------------
if __name__ == '__main__':
    with application.app_context():
        print("\n--- Registered Endpoints ---")
        for rule in sorted(application.url_map.iter_rules(), key=lambda r: r.rule):
            print(f"{rule.endpoint:25} -> {rule.rule}")
        print("----------------------------\n")
    application.run(debug=True)
