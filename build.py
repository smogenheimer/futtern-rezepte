"""Build static recipe pages with schema.org Recipe data for MacroFactor's recipe import."""

import html
import json
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


def main():
    recipes = json.loads((HERE / "recipes.json").read_text(encoding="utf-8"))
    OUT.mkdir(exist_ok=True)
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
