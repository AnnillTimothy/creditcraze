from models import CreditCard

def choices():
    # Default static values (fallback)
    default_banks = ["ABSA", "FNB", "Investec", "Nedbank", "Standard Bank", "Discovery",
                     "Diners Club", "British Airways", "Sanlam", "American Express",
                     "Woolworths", "RMB", "Capitec", "African Bank"]

    default_card_types = ["Charge", "Credit", "Petro", "Fusion", "Business", "Student", "Fleet"]
    default_categories = ["Travel", "Petro", "Lifestyle", "Rewards", "Everyday", "Entertainment", "Student", "Business"]
    default_rewards = ["Avios", "Ebucks", "Greenbacks", "Miles", "Wealth Bonus", "Clubmiles"]

    try:
        # Fetch unique dynamic lists from DB
        banks = sorted(set(
            b.strip()
            for card in CreditCard.query.all() if card.banks
            for b in card.banks.split(',')
        )) or default_banks

        categories = sorted(set(
            c.strip()
            for card in CreditCard.query.all() if card.categories
            for c in card.categories.split(',')
        )) or default_categories

        rewards = sorted(set(
            r.strip()
            for card in CreditCard.query.all() if card.rewards
            for r in card.rewards.split(',')
        )) or default_rewards

        card_types = sorted(set(
            t.strip() for card in CreditCard.query.all() if card.card_type
        )) or default_card_types

    except Exception:
        # Fallback when DB empty or query fails
        banks, categories, rewards, card_types = default_banks, default_categories, default_rewards, default_card_types

    return dict(
        banks=banks,
        card_types=card_types,
        categories=categories,
        rewards=rewards
    )
