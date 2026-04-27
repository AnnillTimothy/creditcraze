<a class="nav-link {% if request.endpoint == 'compare' %}active{% endif %}">
``` |
| Duplicate “Discovery” in Issuer list | Cosmetic | Remove one. |
| About dropdown | “About Us” and “About Company” are redundant | Rename entire section to **“Our Story”** or **“Inside CreditCraze”**. |
| Credit Resources typo | “Resourses” | Fix to “Resources” in all files. |
| Footer quick links | Placeholder `.html` links | Convert all to proper `url_for()` once routes are built. |

---

## 🧩 3. Routes We Still Need to Implement

You’ve got all menu items defined — here’s the **route map** to make everything live.

| Section | Route | Template | Notes |
|----------|--------|-----------|-------|
Done | 🏠 Home | `/` | `index.html` | Already exists |
Done | 💳 Credit Compare™ | `/compare` | `compare.html` | AI-driven comparison tool |
Done | 📂 Card Reviews | `/card-reviews` | `card-reviews.html` | Already exists |
Done | 🏦 Card Details | `/card-details/<id>` | `card-details.html` | Already exists |
| 🌍 Card Category | `/category/<category>/<slug>` | `category.html` | Filter by Category |
| 🏢 Card Issuer | `/issuer/<bank>` | `issuer.html` | Cards filtered by bank |
Done | 📘 Credit Resources | `/resources` | `resources.html` | Overview |
(Necessary for a page?) | ├── Reviews | `/resources/reviews` | `reviews.html` | Links to posts or guides |
Done | ├── News | `/resources/news` | `news.html` | Same as blog maybe |
| ├── Education | `/resources/education` | `education.html` | Credit 101 and smart debt guides |
| ⚙️ Our Story (rename) | `/about` | `about.html` | “Our Story / Vision / Why We Exist” |
Done | 🤝 Partnerships | `/partnerships` | `partnerships.html` | Already routed |
Done | 🧭 Contact | `/contact` | `contact.html` | Already routed |
Done | ⚖️ T&Cs | `/terms` | `terms.html` | To create |
Done | 🚫 Disclaimer | `/disclaimer` | `disclaimer.html` | To create |
Done | 🚫 privacy | `/privacy` | `privacy.html` | To create |
{# include #} contact page | ❓ FAQ | `/faq` | `faq.html` | Move from `index` partial to separate full page |
| 🔐 Sign In | `/sign_in` | `sign-in.html` | Exists |
| 🧑‍💼 Dashboard | `/admin` | `admin/dashboard.html` | Superuser view |
Done | 🕳️ 404 Page | `/error` or global errorhandler | `error.html` | Custom design needed |

That’s **19 total endpoints**, most of which can share layouts and partials.

---

