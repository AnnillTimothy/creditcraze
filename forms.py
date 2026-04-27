from flask_wtf import FlaskForm
from wtforms import (
    StringField, FileField, SubmitField, TextAreaField, SelectField,
    SelectMultipleField, BooleanField, DecimalField, IntegerField
)
from wtforms.validators import DataRequired, Optional, URL, NumberRange
from flask_ckeditor import CKEditorField

class CreditCardForm(FlaskForm):
    # Core
    name = StringField('Card Name', validators=[DataRequired()])
    banks = SelectMultipleField('Issuer Bank(s)', choices=[], coerce=str, validators=[DataRequired()])
    card_type = SelectField('Card Type', choices=[], validators=[DataRequired()])

    # Financials
    interest_rate = StringField('Interest Rate', validators=[Optional()])
    interest_free_days = IntegerField('Interest Free Days', validators=[Optional(), NumberRange(min=0)])
    monthly_fee = DecimalField('Monthly Fee', validators=[Optional()], places=2)
    annual_fee = DecimalField('Annual Fee', validators=[Optional()], places=2)
    min_income = StringField('Minimum Income / Profile', validators=[Optional()])
    limit_range = StringField('Typical Limit Range', validators=[Optional()])

    # Features & rewards
    reward_type = StringField('Reward Type', validators=[Optional()])
    rewards_summary = StringField('Rewards Summary', validators=[Optional()])
    travel_features = StringField('Travel Features', validators=[Optional()])
    lifestyle_features = StringField('Lifestyle Features', validators=[Optional()])
    insurance = StringField('Insurance', validators=[Optional()])
    discounts = StringField('Discounts', validators=[Optional()])

    # Text blocks / transparency
    requirements = TextAreaField('Requirements', validators=[Optional()])
    benefits = TextAreaField('Benefits', validators=[Optional()])
    risks = TextAreaField('Risks / Notes', validators=[Optional()])
    pros = TextAreaField('Pros', validators=[Optional()])
    cons = TextAreaField('Cons', validators=[Optional()])

    # Categorisation / metadata
    categories = SelectMultipleField('Categories', choices=[], coerce=str, validators=[DataRequired()])
    tier = SelectField('Card Tier', choices=[('', 'Select'), ('Standard','Standard'), ('Gold','Gold'), ('Platinum','Platinum'), ('Signature','Signature')], validators=[Optional()])
    is_featured = BooleanField('Featured (show in hero)')

    # Media & extras
    photo = FileField('Card Photo', validators=[Optional()])
    brochure_link = StringField('Brochure / More Info URL', validators=[Optional(), URL()])
    slug = StringField('Slug (optional)', validators=[Optional()])

    submit = SubmitField('Save Card')


class BlogPostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    subtitle = StringField('Subtitle', validators=[Optional()])
    introduction = StringField('Introduction', validators=[Optional()])
    slug = StringField('Slug', validators=[Optional()])
    category = SelectField('Category', choices=[], validators=[DataRequired()])
    content = CKEditorField('Content', validators=[DataRequired()])
    img1 = FileField('Image 1', validators=[Optional()])
    img2 = FileField('Image 2', validators=[Optional()])
    img3 = FileField('Image 3', validators=[Optional()])
    submit = SubmitField('Publish')

class ComparisonForm(FlaskForm):
    card1 = SelectField('Select Card 1', choices=[], coerce=int, validators=[DataRequired()])
    card2 = SelectField('Select Card 2', choices=[], coerce=int, validators=[DataRequired()])
    card3 = SelectField('Select Card 3', choices=[], coerce=int, validators=[Optional()])
    submit = SubmitField('Compare')
