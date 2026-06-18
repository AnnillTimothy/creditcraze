from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class CreditCard(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)
    banks = db.Column(db.String(255), nullable=False, default='Unknown')
    card_type = db.Column(db.String(50), nullable=False)

    interest_rate = db.Column(db.String(50))
    interest_free_days = db.Column(db.Integer)
    monthly_fee = db.Column(db.Float)
    annual_fee = db.Column(db.Float)
    min_income = db.Column(db.String(50))
    limit_range = db.Column(db.String(100))

    reward_type = db.Column(db.String(50))
    rewards_summary = db.Column(db.String(255))
    travel_features = db.Column(db.String(255))
    lifestyle_features = db.Column(db.String(255))
    insurance = db.Column(db.String(255))
    discounts = db.Column(db.String(255))

    requirements = db.Column(db.String(255))
    benefits = db.Column(db.String(255))
    risks = db.Column(db.String(255))
    pros = db.Column(db.String(255))
    cons = db.Column(db.String(255))

    categories = db.Column(db.String(255))
    tier = db.Column(db.String(50))
    is_featured = db.Column(db.Boolean, default=False)

    photo = db.Column(db.String(255))
    brochure_link = db.Column(db.String(255))

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
    site_name = db.Column(db.String(100), default='Credit Compass')
    logo_filename = db.Column(db.String(255))
    contact_email = db.Column(db.String(100))
    contact_phone = db.Column(db.String(50))
    contact_address = db.Column(db.String(255))
    facebook_url = db.Column(db.String(255))
    twitter_url = db.Column(db.String(255))
    instagram_url = db.Column(db.String(255))
    footer_tagline = db.Column(db.String(255), default='Navigate smarter revolving credit decisions with confidence.')
