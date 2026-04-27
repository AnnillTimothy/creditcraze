from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class CreditCard(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    # Core Info
    name = db.Column(db.String(100), nullable=False)
    banks = db.Column(db.String(255), nullable=False, default='Unknown')
    card_type = db.Column(db.String(50), nullable=False)

    # Financial Details
    interest_rate = db.Column(db.String(50))
    interest_free_days = db.Column(db.Integer)
    monthly_fee = db.Column(db.Float)
    annual_fee = db.Column(db.Float)
    min_income = db.Column(db.String(50))
    limit_range = db.Column(db.String(100))

    # Features & Rewards
    reward_type = db.Column(db.String(50))
    rewards_summary = db.Column(db.String(255))
    travel_features = db.Column(db.String(255))
    lifestyle_features = db.Column(db.String(255))
    insurance = db.Column(db.String(255))
    discounts = db.Column(db.String(255))

    # Educational / Transparency
    requirements = db.Column(db.String(255))
    benefits = db.Column(db.String(255))
    risks = db.Column(db.String(255))
    pros = db.Column(db.String(255))
    cons = db.Column(db.String(255))

    # Categories, Tiering, and Metadata
    categories = db.Column(db.String(255))
    tier = db.Column(db.String(50))
    is_featured = db.Column(db.Boolean, default=False)

    # Media & Links
    photo = db.Column(db.String(255))
    brochure_link = db.Column(db.String(255))  # used as "Apply Now" URL

    def bank_list(self):
        return [b.strip() for b in self.banks.split(',')] if self.banks else []

    def category_list(self):
        return [c.strip() for c in self.categories.split(',')] if self.categories else []


class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    subtitle = db.Column(db.String(100))
    introduction = db.Column(db.String(355))
    slug = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    content = db.Column(db.Text, nullable=False)
    img1 = db.Column(db.String(255))
    img2 = db.Column(db.String(255))
    img3 = db.Column(db.String(255))


class SiteSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    site_name = db.Column(db.String(100), default='CreditCraze')
    logo_filename = db.Column(db.String(255))
    contact_email = db.Column(db.String(100))
    contact_phone = db.Column(db.String(50))
    contact_address = db.Column(db.String(255))
    facebook_url = db.Column(db.String(255))
    twitter_url = db.Column(db.String(255))
    instagram_url = db.Column(db.String(255))
    footer_tagline = db.Column(db.String(255), default='Your AI-powered credit card companion.')
