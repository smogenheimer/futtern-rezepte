"""Build static recipe pages with schema.org Recipe data for MacroFactor's recipe import."""

import html
import json
import re
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "docs"

CSS = """
body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;max-width:640px;margin:2rem auto;padding:0 1rem;color:#1f2328;line-height:1.5}
h1{font-size:1.6rem;margin-bottom:.25rem}
.meta{color:#59636e;margin-bottom:1.5rem}
.macros{display:flex;gap:.5rem;flex-wrap:wrap;margin:1rem 0}
.macros span{background:#fff4e5;border-radius:6px;padding:.25rem .6rem}
li{margin:.3rem 0}
a{color:#0969da}
"""


def page(title, body, head_extra=""):
    return (
        "<!DOCTYPE html>\n<html lang=\"de\">\n<head>\n<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
        "<meta name=\"robots\" content=\"noindex\">\n"
        f"<title>{html.escape(title)}</title>\n<style>{CSS}</style>\n{head_extra}</head>\n"
        f"<body>\n{body}\n</body>\n</html>\n"
    )


def recipe_ld(r):
    n = r["nutrition"]
    return {
        "@context": "https://schema.org",
        "@type": "Recipe",
        "name": r["name"],
        "recipeCategory": r["category"],
        "recipeYield": f"{r['yield']} Portion" + ("en" if r["yield"] > 1 else ""),
        "totalTime": f"PT{r['time']}M",
        "recipeIngredient": r["ingredients"],
        "recipeInstructions": [{"@type": "HowToStep", "text": s} for s in r["steps"]],
        "nutrition": {
            "@type": "NutritionInformation",
            "servingSize": "1 Portion",
            "calories": f"{n['kcal']} kcal",
            "proteinContent": f"{n['protein']} g",
            "carbohydrateContent": f"{n['carbs']} g",
            "fatContent": f"{n['fat']} g",
        },
    }


def recipe_page(r):
    n = r["nutrition"]
    ld = json.dumps(recipe_ld(r), ensure_ascii=False, indent=1)
    ingredients = "\n".join(f"<li>{html.escape(i)}</li>" for i in r["ingredients"])
    steps = "\n".join(f"<li>{html.escape(s)}</li>" for s in r["steps"])
    body = f"""<p><a href="./">← Alle Rezepte</a></p>
<h1>{html.escape(r['name'])}</h1>
<div class="meta">{html.escape(r['category'])} · {r['yield']} Portion{'en' if r['yield'] > 1 else ''} · {r['time']} Min</div>
<div class="macros"><span>{n['kcal']} kcal</span><span>{n['protein']} g Protein</span><span>{n['carbs']} g KH</span><span>{n['fat']} g Fett</span><span>pro Portion</span></div>
<h2>Zutaten</h2>
<ul>
{ingredients}
</ul>
<h2>Zubereitung</h2>
<ol>
{steps}
</ol>"""
    return page(r["name"], body, f'<script type="application/ld+json">\n{ld}\n</script>\n')


MF_SOURCE = "futtern-plan"
PLAN_START = date(2026, 11, 8)  # Sunday that starts the first week A
PLAN_FROM = date(2026, 11, 1)
PLAN_UNTIL = date(2027, 12, 31)

ICONS = {
    "overnight-oats-beere-vanille": "overnightOats",
    "overnight-oats-apfel-zimt": "overnightOats",
    "overnight-oats-erdnuss-banane": "overnightOats",
    "ruehrei-spinat-wrap": "burritoEnchiladaRollGreen",
    "spiegelei-sucuk-brot": "mealPlateFullEnglishBreakfast",
    "beeren-protein-smoothie": "milkshake",
    "banane-erdnuss-shake": "milkshake",
    "milder-snack-teller": "saladPlate",
    "proteinquark-bowl-beeren-walnuss": "yogurt",
    "pre-gym-banane-soja-joghurt": "bananas",
    "spaghetti-bolo-gestreckt": "spaghettiRedSauce",
    "creamy-cajun-chicken-one-pot": "chicken",
    "kurkuma-haehnchen-curry": "riceWhiteBowl",
    "teriyaki-lachs-bowl": "chirashiBowlSushi",
    "lasagne-gestreckt": "lasagne",
    "haehnchen-gyros-teller": "breadPita",
    "puten-hackbaellchen-paprikasosse": "meatballs",
    "lachs-frikadellen-kartoffelsalat": "salmonFilet",
}

SLOTS = ["Frühstück", "Mittag", "Pre-Gym", "Abendessen", "Abendsnack"]
DAYS = ["So", "Mo", "Di", "Mi", "Do", "Fr", "Sa"]

# Per day: breakfast, lunch, pre-gym (None on rest days), evening snack. Dinners differ per week.
BASE_WEEK = {
    "So": ("ruehrei-spinat-wrap", "milder-snack-teller", None),
    "Mo": ("overnight-oats-beere-vanille", "beeren-protein-smoothie", "pre-gym-banane-soja-joghurt"),
    "Di": ("overnight-oats-apfel-zimt", "milder-snack-teller", "pre-gym-banane-soja-joghurt"),
    "Mi": ("overnight-oats-erdnuss-banane", "beeren-protein-smoothie", None),
    "Do": ("overnight-oats-beere-vanille", "banane-erdnuss-shake", None),
    "Fr": ("overnight-oats-apfel-zimt", "milder-snack-teller", "pre-gym-banane-soja-joghurt"),
    "Sa": ("spiegelei-sucuk-brot", "beeren-protein-smoothie", "pre-gym-banane-soja-joghurt"),
}
DINNERS = {
    "A": {"So": "creamy-cajun-chicken-one-pot", "Mo": "spaghetti-bolo-gestreckt", "Di": "creamy-cajun-chicken-one-pot",
          "Mi": "spaghetti-bolo-gestreckt", "Do": "teriyaki-lachs-bowl", "Fr": "kurkuma-haehnchen-curry",
          "Sa": "teriyaki-lachs-bowl"},
    "B": {"So": "haehnchen-gyros-teller", "Mo": "lasagne-gestreckt", "Di": "haehnchen-gyros-teller",
          "Mi": "lasagne-gestreckt", "Do": "lachs-frikadellen-kartoffelsalat", "Fr": "puten-hackbaellchen-paprikasosse",
          "Sa": "lachs-frikadellen-kartoffelsalat"},
}
EVENING_SNACK = "proteinquark-bowl-beeren-walnuss"


def portion_grams(r):
    """Sum gram/ml amounts of the ingredients and divide by the yield (1 ml counted as 1 g)."""
    total = 0
    for ing in r["ingredients"]:
        m = re.match(r"(\d+(?:[.,]\d+)?)\s*(g|ml)\b", ing)
        if m:
            total += float(m.group(1).replace(",", "."))
    return round(total / r["yield"])


def mf_food(r):
    """One portion in MacroFactor's 'Log by JSON' schema (github.com/macrofactor/apple-shortcuts)."""
    n = r["nutrition"]
    return {
        "source": MF_SOURCE,
        "icon": ICONS[r["slug"]],
        "name": r["name"],
        "nutrients": {"energy": n["kcal"], "protein": n["protein"], "carbs": n["carbs"], "fat": n["fat"]},
        "serving": {"amount": 1, "label": "Portion", "weight": portion_grams(r)},
        "notes": "Futtern-Plan: " + ", ".join(r["ingredients"]),
    }


def week_type(day):
    sunday = day - timedelta(days=(day.weekday() + 1) % 7)
    weeks = (sunday - PLAN_START).days // 7
    return "A" if weeks % 2 == 0 else "B"


def day_plan(week, dayname, by_slug):
    breakfast, lunch, pregym = BASE_WEEK[dayname]
    slugs = [breakfast, lunch, pregym, DINNERS[week][dayname], EVENING_SNACK]
    slots = {}
    labels = []
    for slot, slug in zip(SLOTS, slugs):
        if slug is None:
            continue
        food = mf_food(by_slug[slug])
        slots[slot] = food
        labels.append(f"{slot}: {food['name']}")
    return {"woche": week, "tag": dayname, "labels": labels, "slots": slots,
            "foods": {lab: slots[lab.split(":")[0]] for lab in labels}}


def write_macrofactor(recipes):
    by_slug = {r["slug"]: r for r in recipes}
    mf_dir = OUT / "mf"
    mf_dir.mkdir(exist_ok=True)
    for r in recipes:
        (mf_dir / f"{r['slug']}.json").write_text(
            json.dumps(mf_food(r), ensure_ascii=False, indent=1), encoding="utf-8")

    plans = {f"{w}-{d}": day_plan(w, d, by_slug) for w in "AB" for d in DAYS}
    dates = {}
    day = PLAN_FROM
    while day <= PLAN_UNTIL:
        dates[day.isoformat()] = f"{week_type(day)}-{DAYS[(day.weekday() + 1) % 7]}"
        day += timedelta(days=1)
    all_foods = {r["name"]: mf_food(r) for r in recipes}
    plan = {"gueltig_bis": PLAN_UNTIL.isoformat(), "dates": dates, "plans": plans,
            "alle_labels": list(all_foods), "alle": all_foods}
    (mf_dir / "plan.json").write_text(json.dumps(plan, ensure_ascii=False), encoding="utf-8")


def main():
    recipes = json.loads((HERE / "recipes.json").read_text(encoding="utf-8"))
    OUT.mkdir(exist_ok=True)
    write_macrofactor(recipes)
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    for r in recipes:
        (OUT / f"{r['slug']}.html").write_text(recipe_page(r), encoding="utf-8")

    groups = {}
    for r in recipes:
        groups.setdefault(r["category"], []).append(r)
    sections = []
    for cat, items in groups.items():
        links = "\n".join(
            f'<li><a href="{r["slug"]}.html">{html.escape(r["name"])}</a> · {r["nutrition"]["kcal"]} kcal</li>'
            for r in items
        )
        sections.append(f"<h2>{html.escape(cat)}</h2>\n<ul>\n{links}\n</ul>")
    body = "<h1>Futtern – Rezepte</h1>\n<div class=\"meta\">Zum Import in MacroFactor: Create Recipe → Import → Link einfügen.</div>\n" + "\n".join(sections)
    (OUT / "index.html").write_text(page("Futtern – Rezepte", body), encoding="utf-8")
    print(f"{len(recipes)} Rezeptseiten gebaut in {OUT}")


if __name__ == "__main__":
    main()
