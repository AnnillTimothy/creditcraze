import json
import os
from datetime import datetime, timezone
from xml.etree import ElementTree as ET

from dotenv import load_dotenv
from flask import (
    Flask,
    Response,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
    flash,
)
from flask_ckeditor import CKEditor
from flask_migrate import Migrate
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.utils import secure_filename

from context_processors import choices
from forms import CreditCardForm, BlogPostForm, ComparisonForm, SiteSettingsForm
from models import db, CreditCard, BlogPost, SiteSettings

load_dotenv()

BRAND_NAME = "Credit Compass"
BRAND_TAGLINE = "Navigate. Choose. Thrive."
BRAND_DESCRIPTION = (
    "Credit Compass helps South Africans compare credit cards, understand revolving credit, "
    "and choose the right bank product with clear, modern guidance."
)
SITE_URL = os.getenv("SITE_URL", "https://www.creditcompass.co.za").rstrip("/")
DEFAULT_SHARE_IMAGE = "img/credit-compass-share.svg"
COOKIE_CATEGORIES = [
    {
        "key": "essential",
        "label": "Essential",
        "required": True,
        "description": "Needed for security, page rendering, and remembering your consent choices.",
    },
    {
        "key": "analytics",
        "label": "Analytics",
        "required": False,
        "description": "Helps us understand which guides, comparisons, and tools are useful so we can improve them.",
    },
    {
        "key": "personalization",
        "label": "Personalisation",
        "required": False,
        "description": "Keeps your experience relevant by tailoring prompts, comparison context, and education journeys.",
    },
]

try:
    from openai import OpenAI as _OpenAI

    _oai_key = os.getenv("OPENAI_API_KEY")
    openai_client = _OpenAI(api_key=_oai_key) if _oai_key else None
except ImportError:
    openai_client = None

try:
    from mistralai import Mistral as _Mistral

    _mis_key = os.getenv("MISTRAL_API_KEY")
    mistral_client = _Mistral(api_key=_mis_key) if _mis_key else None
except ImportError:
    mistral_client = None

application = Flask(__name__, static_folder="static", template_folder="templates")
application.wsgi_app = ProxyFix(application.wsgi_app, x_for=1, x_proto=1, x_host=1)
ckeditor = CKEditor(application)

application.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///example.db")
application.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
application.config["SECRET_KEY"] = os.getenv("SECRET_KEY", os.urandom(24))
application.config["UPLOAD_FOLDER"] = os.getenv("UPLOAD_FOLDER", "static/uploads")
application.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
application.config["SESSION_COOKIE_SAMESITE"] = "Lax"
application.config["SESSION_COOKIE_HTTPONLY"] = True
application.config["SESSION_COOKIE_SECURE"] = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
application.config["PREFERRED_URL_SCHEME"] = "https" if application.config["SESSION_COOKIE_SECURE"] else "http"

os.makedirs(application.config["UPLOAD_FOLDER"], exist_ok=True)

db.init_app(application)
migrate = Migrate(application, db)

with application.app_context():
    db.create_all()


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
    dest = os.path.join(application.config["UPLOAD_FOLDER"], filename)
    fileobj.save(dest)
    return filename


def gen_slug(text, max_len=100):
    if not text:
        return "post"
    slug = text.strip().lower().replace(" ", "-")
    return slug[:max_len]


def get_card_context_prompt():
    try:
        cards = CreditCard.query.order_by(CreditCard.name).limit(25).all()
        if cards:
            lines = []
            for card in cards:
                fee = f"annual fee R{card.annual_fee:.0f}" if card.annual_fee is not None else "annual fee varies"
                rate = f"interest {card.interest_rate}" if card.interest_rate else "rate varies"
                rewards = f"rewards: {card.reward_type}" if card.reward_type else ""
                lines.append(f"- {card.name} ({card.banks}): {fee}, {rate}, {rewards}".strip().rstrip(","))
            card_block = "\n".join(lines)
            return (
                "You are Compass AI, a friendly assistant focused on South African credit cards and revolving credit. "
                "Help people compare cards, understand costs, and choose products that fit their lifestyle responsibly. "
                "Use plain language, be concise, and remind users to verify product terms with the issuing bank. "
                f"Here are some cards in the database:\n{card_block}"
            )
    except Exception:
        pass

    return (
        "You are Compass AI, a friendly assistant focused on South African credit cards and revolving credit. "
        "Help people compare cards, understand costs, and choose products that fit their lifestyle responsibly. "
        "Use plain language, be concise, and remind users to verify product terms with the issuing bank."
    )


def call_ai(messages, max_tokens=350):
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
        except Exception:
            return "Compass AI hit a temporary error. Please try again in a moment."

    return "Compass AI is temporarily unavailable because no AI API key is configured."


def _get_cp():
    try:
        return choices()
    except Exception:
        return {}


def build_meta(title=None, description=None, *, path=None, image=None, meta_type="website", keywords=None, noindex=False):
    canonical_url = f"{SITE_URL}{path or request.path}"
    image_path = image or DEFAULT_SHARE_IMAGE
    image_url = image_path if image_path.startswith("http") else f"{SITE_URL}{url_for('static', filename=image_path)}"
    return {
        "title": title or f"{BRAND_NAME} | {BRAND_TAGLINE}",
        "description": description or BRAND_DESCRIPTION,
        "canonical": canonical_url,
        "image": image_url,
        "type": meta_type,
        "keywords": keywords or "credit cards South Africa, compare credit cards, revolving credit, bank rewards",
        "noindex": noindex,
    }


def get_cookie_copy(endpoint):
    endpoint_copy = {
        "home": "We use essential cookies to power the experience, plus optional analytics and personalisation cookies to improve recommendations.",
        "compare": "Optional analytics cookies help us improve comparison journeys and understand which card filters matter most.",
        "credibot": "Optional personalisation cookies help preserve your AI guidance context while you explore credit options.",
        "card_details": "Optional analytics cookies show us which card pages and benefits shoppers engage with most.",
    }
    return endpoint_copy.get(endpoint, "We use essential cookies to keep Credit Compass secure and optional cookies to improve content and performance.")


def resolve_seo_meta():
    endpoint = request.endpoint or "home"

    if endpoint == "home":
        return build_meta(
            title=f"{BRAND_NAME} | Find the right credit. Fuel your future.",
            description=(
                "Compare South African credit cards, learn how revolving credit works, and get matched to the right bank product with Credit Compass."
            ),
            keywords="Credit Compass, compare credit cards South Africa, revolving credit, rewards cards, travel cards",
        )

    if endpoint == "compare":
        return build_meta(
            title=f"Compare Credit Cards | {BRAND_NAME}",
            description="Compare South African credit cards side by side across fees, rewards, interest-free days, and income requirements.",
            keywords="compare credit cards, South Africa credit comparison, annual fee comparison, rewards cards",
        )

    if endpoint == "cardreviews":
        return build_meta(
            title=f"Cards & Banks | {BRAND_NAME}",
            description="Browse South African credit cards by bank, lifestyle fit, rewards style, and income profile.",
            keywords="credit cards by bank, ABSA cards, FNB cards, Nedbank cards, South Africa cards",
        )

    if endpoint == "credibot":
        return build_meta(
            title=f"Compass AI | {BRAND_NAME}",
            description="Ask Compass AI about travel cards, cashback, revolving credit, fees, and the right credit card for your goals.",
            keywords="AI credit card advisor, South Africa credit AI, revolving credit help",
        )

    if endpoint == "about":
        return build_meta(
            title=f"About {BRAND_NAME}",
            description="Learn how Credit Compass helps South Africans navigate credit with confidence, clarity, and modern tools.",
        )

    if endpoint == "contact":
        return build_meta(
            title=f"Contact {BRAND_NAME}",
            description="Contact Credit Compass for partnerships, product questions, campaign opportunities, and customer support.",
        )

    if endpoint == "privacy":
        return build_meta(
            title=f"Privacy & Cookies | {BRAND_NAME}",
            description="Read the Credit Compass privacy and cookie policy, including how we handle analytics, personalisation, and user data.",
        )

    if endpoint == "terms":
        return build_meta(
            title=f"Terms of Use | {BRAND_NAME}",
            description="Read the Credit Compass terms of use for content, comparisons, user responsibilities, and partner links.",
        )

    if endpoint == "disclaimer":
        return build_meta(
            title=f"Disclaimer | {BRAND_NAME}",
            description="Understand how Credit Compass presents card information, AI guidance, and partner links for educational use.",
        )

    if endpoint == "card_details":
        card_id = (request.view_args or {}).get("card_id")
        card = CreditCard.query.get(card_id) if card_id else None
        if card:
            description = (
                f"Review the {card.name} from {card.banks}, including fees, rewards, limits, and whether it suits your revolving credit goals."
            )
            image = f"uploads/{card.photo}" if card.photo else DEFAULT_SHARE_IMAGE
            return build_meta(
                title=f"{card.name} | {BRAND_NAME}",
                description=description,
                image=image,
                keywords=f"{card.name}, {card.banks}, credit card review, South Africa credit card",
                meta_type="product",
            )

    if endpoint == "article":
        post_id = (request.view_args or {}).get("post_id")
        post = BlogPost.query.get(post_id) if post_id else None
        if post:
            return build_meta(
                title=f"{post.title} | {BRAND_NAME}",
                description=post.introduction or post.subtitle or BRAND_DESCRIPTION,
                keywords=f"credit education, {post.category}, {post.title}",
                meta_type="article",
            )

    return build_meta()


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
            settings = SiteSettings(site_name=BRAND_NAME, footer_tagline="Your guide to smarter revolving credit decisions.")
        return {"site_settings": settings}
    except Exception:
        return {"site_settings": None}


@application.context_processor
def inject_brand_context():
    return {
        "brand_name": BRAND_NAME,
        "brand_tagline": BRAND_TAGLINE,
        "brand_description": BRAND_DESCRIPTION,
        "seo_meta": resolve_seo_meta(),
        "cookie_categories": COOKIE_CATEGORIES,
        "cookie_copy": get_cookie_copy(request.endpoint),
        "site_url": SITE_URL,
        "current_year": datetime.now(timezone.utc).year,
    }


@application.errorhandler(404)
def page_not_found(e):
    return render_template("error.html"), 404


@application.route("/")
def home():
    featured = CreditCard.query.filter_by(is_featured=True).limit(5).all()
    if not featured:
        featured = CreditCard.query.order_by(CreditCard.name).limit(5).all()
    blog_posts = BlogPost.query.order_by(BlogPost.id.desc()).limit(3).all()
    return render_template("index.html", credit_cards=featured, blog_posts=blog_posts)


@application.route("/card-reviews")
def cardreviews():
    q = request.args.get("q", "").strip()
    bank_filter = request.args.get("bank", "").strip()
    cat_filter = request.args.get("category", "").strip()
    tier_filter = request.args.get("tier", "").strip()

    query = CreditCard.query
    if q:
        query = query.filter(CreditCard.name.ilike(f"%{q}%"))
    if bank_filter:
        query = query.filter(CreditCard.banks.ilike(f"%{bank_filter}%"))
    if cat_filter:
        query = query.filter(CreditCard.categories.ilike(f"%{cat_filter}%"))
    if tier_filter:
        query = query.filter(CreditCard.tier == tier_filter)

    credit_cards = query.order_by(CreditCard.name).all()
    all_banks = sorted(
        set(
            bank.strip()
            for card in CreditCard.query.all()
            for bank in (card.banks or "").split(",")
            if bank.strip()
        )
    )

    return render_template(
        "card-reviews.html",
        credit_cards=credit_cards,
        banks=all_banks,
        q=q,
        bank_filter=bank_filter,
        category_filter=cat_filter,
        tier_filter=tier_filter,
    )


@application.route("/cards")
def all_cards():
    return redirect(url_for("cardreviews"))


@application.route("/card-details/<int:card_id>")
def card_details(card_id):
    card = CreditCard.query.get_or_404(card_id)
    return render_template("card-details.html", card=card)


@application.route("/compare", methods=["GET", "POST"])
def compare():
    form = ComparisonForm()
    cards = CreditCard.query.order_by(CreditCard.name).all()
    placeholder = [(0, "— Select a card —")]
    form.card1.choices = placeholder + [(card.id, card.name) for card in cards]
    form.card2.choices = placeholder + [(card.id, card.name) for card in cards]
    form.card3.choices = placeholder + [(card.id, card.name) for card in cards]

    if form.validate_on_submit():
        selected = []
        selected_ids = set()
        for field_name in ("card1", "card2", "card3"):
            selected_id = getattr(form, field_name).data
            if selected_id:
                card = CreditCard.query.get(selected_id)
                if card and card.id not in selected_ids:
                    selected.append(card)
                    selected_ids.add(card.id)
        return render_template("comparison.html", form=form, cards=selected)
    return render_template("comparison.html", form=form, cards=[])


@application.route("/quiz")
def quiz():
    return redirect(url_for("credibot"))


@application.route("/ai_card_summary/<int:card_id>")
def ai_card_summary(card_id):
    card = CreditCard.query.get_or_404(card_id)
    prompt = (
        f"Give a concise 3-sentence summary of the {card.name} credit card from {card.banks}. "
        f"Include its positioning, likely best-fit customer, annual fee R{card.annual_fee or 0:.0f}, "
        f"interest rate {card.interest_rate or 'N/A'}, and rewards type {card.reward_type or 'none'}. Keep it under 90 words."
    )
    messages = [
        {"role": "system", "content": "You are a concise South African credit card analyst."},
        {"role": "user", "content": prompt},
    ]
    summary = call_ai(messages, max_tokens=150)
    return jsonify({"summary": summary})


@application.route("/credibot")
def credibot():
    session["conversation"] = []
    return render_template("credibot.html", conversation=[])


@application.route("/get_response", methods=["POST"])
def get_response():
    user_input = request.form.get("user_input", "").strip()
    if not user_input:
        return redirect(url_for("credibot"))

    conversation = session.get("conversation", [])
    conversation.append({"role": "user", "content": user_input})
    system_prompt = get_card_context_prompt()
    messages = [{"role": "system", "content": system_prompt}] + conversation
    reply = call_ai(messages, max_tokens=300)
    conversation.append({"role": "assistant", "content": reply})
    session["conversation"] = conversation

    return render_template("credibot.html", conversation=conversation)


@application.route("/articles")
def articles():
    blog_posts = BlogPost.query.order_by(BlogPost.id.desc()).all()
    return render_template("articles.html", blog_posts=blog_posts)


@application.route("/article/<int:post_id>")
def article(post_id):
    blog_post = BlogPost.query.get_or_404(post_id)
    return render_template("blog-details.html", blog_post=blog_post)


@application.route("/news")
def news():
    posts = BlogPost.query.order_by(BlogPost.id.desc()).limit(10).all()
    return render_template("blog.html", posts=posts)


@application.route("/blog")
def blog():
    return redirect(url_for("news"))


@application.route("/about")
def about():
    return render_template("about.html")


@application.route("/contact")
def contact():
    return render_template("contact.html")


@application.route("/mission")
def mission():
    return redirect(url_for("about"))


@application.route("/partnerships")
def partnerships():
    return redirect(url_for("contact"))


@application.route("/sponsors")
def sponsors():
    return redirect(url_for("contact"))


@application.route("/sign-in")
def sign_in():
    return render_template("sign-in.html")


@application.route("/sign-up")
def sign_up():
    return render_template("sign-up.html")


@application.route("/login")
def login():
    return redirect(url_for("sign_in"))


@application.route("/terms")
def terms():
    return render_template("terms.html")


@application.route("/privacy")
def privacy():
    return render_template("privacy.html")


@application.route("/disclaimer")
def disclaimer():
    return render_template("disclaimer.html")


@application.route("/robots.txt")
def robots_txt():
    body = "\n".join(
        [
            "User-agent: *",
            "Allow: /",
            f"Sitemap: {SITE_URL}{url_for('sitemap_xml')}",
        ]
    )
    return Response(body, mimetype="text/plain")


@application.route("/manifest.webmanifest")
def manifest():
    payload = {
        "name": BRAND_NAME,
        "short_name": BRAND_NAME,
        "description": BRAND_DESCRIPTION,
        "start_url": "/",
        "display": "standalone",
        "background_color": "#07111f",
        "theme_color": "#0a1628",
        "icons": [
            {
                "src": url_for("static", filename="img/credit-compass-mark.svg"),
                "sizes": "any",
                "type": "image/svg+xml",
                "purpose": "any maskable",
            }
        ],
    }
    return Response(json.dumps(payload), mimetype="application/manifest+json")


@application.route("/sitemap.xml")
def sitemap_xml():
    entries = [
        (url_for("home", _external=True), "daily", "1.0"),
        (url_for("cardreviews", _external=True), "daily", "0.9"),
        (url_for("compare", _external=True), "weekly", "0.9"),
        (url_for("credibot", _external=True), "weekly", "0.8"),
        (url_for("articles", _external=True), "weekly", "0.8"),
        (url_for("news", _external=True), "weekly", "0.7"),
        (url_for("about", _external=True), "monthly", "0.6"),
        (url_for("contact", _external=True), "monthly", "0.6"),
        (url_for("privacy", _external=True), "monthly", "0.3"),
        (url_for("terms", _external=True), "monthly", "0.3"),
        (url_for("disclaimer", _external=True), "monthly", "0.3"),
    ]

    for card in CreditCard.query.order_by(CreditCard.id).all():
        entries.append((url_for("card_details", card_id=card.id, _external=True), "weekly", "0.8"))
    for post in BlogPost.query.order_by(BlogPost.id).all():
        entries.append((url_for("article", post_id=post.id, _external=True), "monthly", "0.7"))

    urlset = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    timestamp = datetime.now(timezone.utc).date().isoformat()
    for loc, changefreq, priority in entries:
        url = ET.SubElement(urlset, "url")
        ET.SubElement(url, "loc").text = loc
        ET.SubElement(url, "lastmod").text = timestamp
        ET.SubElement(url, "changefreq").text = changefreq
        ET.SubElement(url, "priority").text = priority

    return Response(ET.tostring(urlset, encoding="utf-8", xml_declaration=True), mimetype="application/xml")


@application.route("/dashboard")
def dashboard():
    total_cards = CreditCard.query.count()
    total_posts = BlogPost.query.count()
    featured = CreditCard.query.filter_by(is_featured=True).limit(10).all()
    return render_template(
        "dashboard.html",
        total_cards=total_cards,
        total_posts=total_posts,
        featured=featured,
    )


@application.route("/dashboard/add_card", methods=["GET", "POST"])
def dashboard_add_card():
    form = CreditCardForm()
    cp = _get_cp()
    form.banks.choices = [(bank, bank) for bank in cp.get("banks", [])]
    form.categories.choices = [(category, category) for category in cp.get("categories", [])]
    form.card_type.choices = [(card_type, card_type) for card_type in cp.get("card_types", [])]

    if form.validate_on_submit():
        photo_filename = safe_filename_save(form.photo.data) if form.photo.data and form.photo.data.filename else None
        new_card = CreditCard(
            name=form.name.data,
            banks=join_if_list(form.banks.data),
            card_type=form.card_type.data,
            interest_rate=form.interest_rate.data,
            interest_free_days=form.interest_free_days.data,
            monthly_fee=float(form.monthly_fee.data) if form.monthly_fee.data is not None else None,
            annual_fee=float(form.annual_fee.data) if form.annual_fee.data is not None else None,
            min_income=form.min_income.data,
            limit_range=form.limit_range.data,
            reward_type=form.reward_type.data,
            rewards_summary=form.rewards_summary.data,
            travel_features=form.travel_features.data,
            lifestyle_features=form.lifestyle_features.data,
            insurance=form.insurance.data,
            discounts=form.discounts.data,
            requirements=form.requirements.data,
            benefits=form.benefits.data,
            risks=form.risks.data,
            pros=form.pros.data,
            cons=form.cons.data,
            categories=join_if_list(form.categories.data),
            tier=form.tier.data or None,
            is_featured=bool(form.is_featured.data),
            photo=photo_filename,
            brochure_link=form.brochure_link.data or None,
        )
        db.session.add(new_card)
        db.session.commit()
        flash("Card added successfully", "success")
        return redirect(url_for("dashboard"))

    return render_template("dashboard_add_card.html", form=form, edit_mode=False)


@application.route("/dashboard/add_post", methods=["GET", "POST"])
def dashboard_add_post():
    form = BlogPostForm()
    cp = _get_cp()
    form.category.choices = [(category, category) for category in cp.get("categories", [])]

    if form.validate_on_submit():
        slug = form.slug.data.strip() if form.slug.data else gen_slug(form.title.data)
        post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            introduction=form.introduction.data,
            slug=slug,
            category=form.category.data,
            content=form.content.data,
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
        return redirect(url_for("dashboard"))

    return render_template("dashboard_add_post.html", form=form)


@application.route("/dashboard/settings", methods=["GET", "POST"])
def dashboard_settings():
    settings = SiteSettings.query.first()
    if not settings:
        settings = SiteSettings(site_name=BRAND_NAME, footer_tagline="Your guide to smarter revolving credit decisions.")
        db.session.add(settings)
        db.session.commit()

    form = SiteSettingsForm(obj=settings)

    if form.validate_on_submit():
        settings.site_name = form.site_name.data or BRAND_NAME
        settings.footer_tagline = form.footer_tagline.data
        settings.contact_email = form.contact_email.data
        settings.contact_phone = form.contact_phone.data
        settings.contact_address = form.contact_address.data
        settings.facebook_url = form.facebook_url.data
        settings.twitter_url = form.twitter_url.data
        settings.instagram_url = form.instagram_url.data
        if form.logo.data and form.logo.data.filename:
            settings.logo_filename = safe_filename_save(form.logo.data)
        db.session.commit()
        flash("Settings saved", "success")
        return redirect(url_for("dashboard_settings"))

    return render_template("site_settings.html", form=form, settings=settings)


@application.route("/dashboard/delete_card/<int:card_id>", methods=["POST"])
def dashboard_delete_card(card_id):
    card = CreditCard.query.get_or_404(card_id)
    db.session.delete(card)
    db.session.commit()
    flash("Card deleted", "success")
    return redirect(url_for("dashboard"))


@application.route("/dashboard/delete_post/<int:post_id>", methods=["POST"])
def dashboard_delete_post(post_id):
    post = BlogPost.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    flash("Post deleted", "success")
    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    with application.app_context():
        print("\n--- Routes ---")
        for rule in sorted(application.url_map.iter_rules(), key=lambda r: r.rule):
            print(f"  {rule.endpoint:28} {rule.rule}")
        print("--------------\n")
    application.run(debug=True)
