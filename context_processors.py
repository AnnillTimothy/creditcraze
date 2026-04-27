from models import CreditCard

def choices():
    default_banks = [
        "ABSA", "African Bank", "American Express", "British Airways",
        "Capitec", "Diners Club", "Discovery", "FNB", "Investec",
        "Nedbank", "RMB", "Sanlam", "Standard Bank", "Woolworths",
    ]
    default_card_types = ["Charge", "Credit", "Petro", "Fusion", "Business", "Student", "Fleet"]
    default_categories = ["Travel", "Petro", "Lifestyle", "Rewards", "Everyday", "Entertainment", "Student", "Business"]
    default_rewards = ["Avios", "eBucks", "Greenbacks", "Miles", "Wealth Bonus", "Clubmiles"]

    try:
        banks = sorted(set(
            b.strip()
            for card in CreditCard.query.all() if card.banks
            for b in card.banks.split(',')
            if b.strip()
        )) or default_banks

        categories = sorted(set(
            c.strip()
            for card in CreditCard.query.all() if card.categories
            for c in card.categories.split(',')
            if c.strip()
        )) or default_categories

        rewards = sorted(set(
            r.strip()
            for card in CreditCard.query.all() if card.reward_type
            for r in card.reward_type.split(',')
            if r.strip()
        )) or default_rewards

        card_types = sorted(set(
            t.strip() for card in CreditCard.query.all() if card.card_type
        )) or default_card_types

    except Exception:
        banks, categories, rewards, card_types = (
            default_banks, default_categories, default_rewards, default_card_types
        )

    return dict(
        banks=banks,
        card_types=card_types,
        categories=categories,
        rewards=rewards,
    )
